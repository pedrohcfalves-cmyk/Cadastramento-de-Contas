"""Testes de ponta a ponta contra o SIGEF simulado (modo lote e modo planilha)."""

import pytest

from excel_falso import Aba, Excel, Pasta
from sigef.automacao import CONFIRMAR_DOMICILIO, INCLUIR_CREDOR
from sigef.fluxos import Relator, executar_lotes, executar_planilha
from sigef.modelos import Lote, Resposta, lote_de_linha
from sigef.navegador import ErroNavegador
from sigef.planilha import Planilha


class RelatorTeste(Relator):
    def __init__(self, corrigir_com=None, cancelar_apos=None):
        self.eventos, self.resultados, self.avisos = [], {}, []
        self.corrigir_com = corrigir_com
        self.cancelar_apos = cancelar_apos

    def inicio(self, chave, lote, atual, total):
        self.eventos.append(("inicio", chave, atual, total))

    def resultado(self, chave, lote, status, texto):
        self.resultados[chave] = (status, texto)

    def aviso(self, texto):
        self.avisos.append(texto)

    def corrigir(self, lote):
        if not self.corrigir_com:
            return False

        for campo, valor in self.corrigir_com.items():
            setattr(lote, campo, valor)

        self.corrigir_com = None
        return True

    def cancelado(self):
        return self.cancelar_apos is not None and len(self.resultados) >= self.cancelar_apos


def test_login_confirmado(navegador):
    assert navegador.logado()


def test_lote_novo_repetido_e_invalido(navegador, servidor):
    lotes = [
        Lote("52998224725", "MARIA DA SILVA", "001", "1234", "56789"),
        Lote("52998224725", "MARIA DA SILVA", "001", "1234", "56789"),  # mesmo domicílio
        Lote("52998224725", "MARIA DA SILVA", "104", "0001", "999"),    # credor já existe
        Lote("00000000000", "CPF RECUSADO", "001", "1", "2"),
    ]
    relator = RelatorTeste()
    resumo = executar_lotes(navegador, lotes, relator)

    assert relator.resultados[1] == ("OK", "Operação realizada com sucesso.")
    assert relator.resultados[2][0] == "JA", relator.resultados
    assert relator.resultados[2][1].startswith("JÁ CADASTRADO: Domicílio Bancário")
    assert relator.resultados[3] == ("OK", "Operação realizada com sucesso.")
    assert relator.resultados[4][0] == "ERRO"
    assert resumo.contagem == {"OK": 2, "JA": 1, "ERRO": 1, "PULADO": 0}

    assert servidor.estado.credores["52998224725"] == "MARIA DA SILVA"
    assert ("52998224725", "104", "0001", "999") in servidor.estado.domicilios

    # Só a aba principal sobra aberta entre os lotes
    assert len(navegador.context.pages) == 1


def test_agencia_e_conta_com_x_chegam_ao_sigef(navegador, servidor):
    lote = lote_de_linha("123.456.789-09,JOSE COM X,001,1234-X,56789-X")
    relator = RelatorTeste()

    executar_lotes(navegador, [lote], relator)

    assert relator.resultados[1][0] == "OK", relator.resultados
    assert ("12345678909", "001", "1234X", "56789X") in servidor.estado.domicilios


def test_confirmacao_manual(navegador, servidor):
    perguntas = []

    def perguntar(lote, acao, editavel):
        perguntas.append((lote.cpf, acao, editavel))

        if lote.cpf == "11144477735":
            return Resposta.PULAR

        if lote.cpf == "39053344705" and lote.banco == "999":
            return Resposta.CORRIGIR

        return Resposta.SIM_TODOS

    lotes = [
        Lote("11144477735", "PULAR ESTE", "001", "1", "1"),
        Lote("39053344705", "CORRIGIR ESTE", "999", "2", "2"),
    ]
    relator = RelatorTeste(corrigir_com={"banco": "237"})
    resumo = executar_lotes(navegador, lotes, relator, perguntar)

    assert relator.resultados[1] == ("PULADO", "PULADO pelo usuário")
    assert relator.resultados[2] == ("OK", "Operação realizada com sucesso.")
    assert "11144477735" not in servidor.estado.credores
    assert ("39053344705", "237", "2", "2") in servidor.estado.domicilios

    # Corrigido: o lote recomeça e "T" libera as demais perguntas do lote
    assert perguntas == [
        ("11144477735", INCLUIR_CREDOR, True),
        ("39053344705", INCLUIR_CREDOR, True),
        ("39053344705", INCLUIR_CREDOR, True),
    ]
    assert resumo.contagem["PULADO"] == 1


def test_parar_no_meio(navegador):
    lotes = [Lote(f"0000000000{n}", f"P{n}", "001", "1", "1") for n in range(1, 4)]
    relator = RelatorTeste(cancelar_apos=1)
    executar_lotes(navegador, lotes, relator)
    assert list(relator.resultados) == [1]


def test_modo_planilha(navegador, servidor):
    aba = Aba("Folha", [
        ["RELAÇÃO DE SERVIDORES"],
        [],
        ["Nº", "ESCOLA", "MUNICÍPIO", "SERVIDOR", "CPF", "BANCO", "AGÊNCIA", "C/C"],
        [1, "EEEF A", "Porto Velho", "JOSÉ SOUZA", 86288366757.0, "Banco do Brasil", 3456, "77-1"],
        [2, "EEEF B", "Ji-Paraná", "ANA LIMA", "123", "Itaú", "1", "2"],
        [],
        [3, "EEEF C", "Ariquemes", "SEM BANCO", "71428793860", "Banco Imaginário", "1", "2"],
        [4, "EEEF D", "Cacoal", "FALTA CONTA", "71428793860", "Caixa", "1", ""],
        [5, "EEEF E", "Vilhena", "JOSÉ SOUZA", "86288366757", "001", "3456", "771"],
    ])
    servidor.estado.cpfs_invalidos.add("00000000123")
    pasta = Pasta("servidores.xlsx", [aba])
    planilha = Planilha.da_pasta(Excel(pasta).Workbooks(1), "Folha")

    colunas, primeira, detectou = planilha.colunas_sugeridas()
    assert detectou and primeira == 4
    assert colunas == {"nome": 4, "cpf": 5, "banco": 6, "agencia": 7, "conta": 8}

    final = planilha.ultima_linha(colunas)
    assert final == 9

    relator = RelatorTeste()
    resumo = executar_planilha(navegador, planilha, colunas, primeira, final, "J", relator)

    assert aba.valor("J4") == "Operação realizada com sucesso."
    assert aba.valor("J5").startswith("ERRO:")          # CPF 00000000123 recusado
    assert aba.valor("J6") is None                      # linha vazia é ignorada
    assert aba.valor("J7") == "ERRO: banco não reconhecido - Banco Imaginário"
    assert aba.valor("J8") == "ERRO: campos vazios - Conta"
    assert aba.valor("J9").startswith("JÁ CADASTRADO:")
    assert resumo.contagem == {"OK": 1, "JA": 1, "ERRO": 3, "PULADO": 0}
    assert pasta.salvamentos == 5
    assert ("86288366757", "001", "3456", "771") in servidor.estado.domicilios


def test_planilha_le_x_da_agencia_e_da_conta():
    aba = Aba("Folha", [
        ["CPF", "SERVIDOR", "BANCO", "AGÊNCIA", "C/C"],
        ["52998224725", "MARIA", "Banco do Brasil", "1234-X", "56789-x"],
    ])
    planilha = Planilha.da_pasta(Excel(Pasta("x.xlsx", [aba])).Workbooks(1), "Folha")
    colunas, _, _ = planilha.colunas_sugeridas()

    lote, _ = planilha.ler_lote(2, colunas)

    assert (lote.agencia, lote.conta) == ("1234X", "56789X")


def test_coluna_oculta_gera_aviso(navegador):
    aba = Aba("A", [["SERVIDOR", "CPF", "BANCO", "AGÊNCIA", "CONTA"],
                    ["X", "", "", "", ""], ["Y", "1", "", "", ""]])
    aba.colunas_ocultas.add(10)
    planilha = Planilha(Pasta("p.xlsx", [aba]), aba)
    colunas, primeira, _ = planilha.colunas_sugeridas()
    relator = RelatorTeste()
    executar_planilha(navegador, planilha, colunas, primeira, 3, "J", relator)
    assert any("oculta" in aviso for aviso in relator.avisos)


def test_navegador_fechado_interrompe(navegador):
    navegador.page.close()

    with pytest.raises(ErroNavegador):
        executar_lotes(navegador, [Lote("52998224725", "X", "001", "1", "1")], RelatorTeste())

    # Ao abrir de novo, o programa recupera uma aba do SIGEF
    navegador.abrir()
    assert navegador.conectado


def test_acoes_conferidas_no_domicilio(navegador):
    """Credor já existente: só a confirmação do domicílio é perguntada."""
    acoes = []

    def perguntar(lote, acao, editavel):
        acoes.append(acao)
        return Resposta.SIM

    relator = RelatorTeste()
    executar_lotes(navegador, [Lote("52998224725", "MARIA DA SILVA", "341", "9", "9")],
                   relator, perguntar)
    assert relator.resultados[1][0] == "OK", relator.resultados
    assert acoes == [CONFIRMAR_DOMICILIO]
