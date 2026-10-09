"""Roteiro automático da janela contra o SIGEF simulado (com capturas de tela).

Percorre o caminho completo como uma pessoa faria: entrar, digitar pessoas,
conferir cada uma, ver o resultado e depois rodar o modo planilha (com um Excel
falso). Uso (Linux com Xvfb):

    xvfb-run -s "-screen 0 1366x768x24" python testes/roteiro_janela.py pasta_capturas
"""

import subprocess
import sys
import time
import tkinter as tk
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "testes")]

from excel_falso import Aba, Excel, Pasta  # noqa: E402
from sigef.interface import app as modulo_app  # noqa: E402
from sigef.interface import telas  # noqa: E402
from sigef.interface.componentes import Botao  # noqa: E402

CAPTURAS = Path(sys.argv[1] if len(sys.argv) > 1 else "capturas")
CAPTURAS.mkdir(parents=True, exist_ok=True)

ABA = Aba("Servidores", [
    ["SECRETARIA DE EDUCAÇÃO - RELAÇÃO PARA PAGAMENTO"],
    [],
    ["Nº", "ESCOLA", "MUNICÍPIO", "SERVIDOR", "CPF", "BANCO", "AGÊNCIA", "C/C"],
    [1, "EEEF Rio Branco", "Porto Velho", "ANTÔNIO PEREIRA", "34608514300", "Caixa", "0001", "123-4"],
    [2, "EEEF Tiradentes", "Ji-Paraná", "LÚCIA FERREIRA", "73759516074", "Bradesco", "2211", "998"],
    [3, "EEEF Castelo", "Cacoal", "SEM CONTA", "26776235009", "001", "1", ""],
])
EXCEL = Excel(Pasta("pagamento_outubro.xlsx", [ABA, Aba("Resumo")]))
telas.conectar_excel = lambda: EXCEL

# Estatísticas e relatórios numa pasta temporária (nunca nos dados reais)
import tempfile  # noqa: E402

from sigef import estatisticas, relatorio  # noqa: E402

TEMP = Path(tempfile.mkdtemp(prefix="roteiro-"))
estatisticas.PASTA_ESTATISTICAS = TEMP / "estatisticas"
estatisticas.PASTA_IMPORTADOS = TEMP / "estatisticas" / "outros-computadores"
estatisticas.ARQUIVO_AJUSTES = TEMP / "estatisticas" / "ajustes.json"
relatorio.pasta_padrao = lambda: TEMP / "relatorios"
telas.e.abrir_pasta = lambda pasta: print("abriria a pasta", pasta, flush=True)

app = modulo_app.App()
raiz = app.raiz
passos, numero = [], [0]
falhas = []


def capturar(nome: str) -> None:
    raiz.update()
    numero[0] += 1
    destino = CAPTURAS / f"{numero[0]:02d}_{nome}.png"
    subprocess.run(["import", "-window", "root", str(destino)], check=False)
    print("captura", destino.name, flush=True)


def widgets(raiz_busca=None):
    pilha = [raiz_busca or raiz]

    while pilha:
        widget = pilha.pop()
        yield widget
        pilha.extend(widget.winfo_children())


def botao(texto: str) -> Botao:
    for widget in widgets():
        if isinstance(widget, Botao) and widget.cget("text") == texto and widget.winfo_viewable():
            return widget

    raise LookupError(texto)


def clicar(texto: str) -> None:
    botao(texto).invoke()


def dialogo_aberto():
    """O diálogo mais recente (um recado pode abrir por cima de outro diálogo)."""
    abertos = [w for w in raiz.winfo_children() if isinstance(w, tk.Toplevel) and w.winfo_exists()]
    return abertos[-1] if abertos else None


def tela(nome: str) -> bool:
    return type(app.tela).__name__ == nome


def esperar(condicao, acao):
    passos.append((condicao, acao))


LIMITE_SEGUNDOS = 60
inicio_passo = [time.time()]


def executar_passos():
    if not passos:
        print("ROTEIRO CONCLUÍDO:", "FALHAS: " + "; ".join(falhas) if falhas else "SEM FALHAS",
              flush=True)
        raiz.after(500, app.sair)
        return

    condicao, acao = passos[0]

    try:
        pronto = condicao()
    except Exception:
        pronto = False

    if pronto:
        passos.pop(0)
        inicio_passo[0] = time.time()

        # Agenda o próximo antes: a ação pode abrir um diálogo que espera resposta
        raiz.after(400, executar_passos)

        try:
            acao()
        except Exception as erro:  # registra e segue
            falhas.append(f"{getattr(acao, '__name__', acao)}: {erro!r}")
            print("FALHA", falhas[-1], flush=True)

        return

    if time.time() - inicio_passo[0] > LIMITE_SEGUNDOS:
        falhas.append(f"tempo esgotado no passo {len(falhas)}: {condicao}")
        print("FALHA", falhas[-1], flush=True)
        passos.pop(0)
        inicio_passo[0] = time.time()

    raiz.after(250, executar_passos)


def sempre():
    return True


def preencher(**valores):
    formulario = app.tela.formulario

    for campo, valor in valores.items():
        formulario.campos[campo].valor = valor


def responder_dialogo(texto):
    def acao():
        dialogo = dialogo_aberto()
        alvo = next(w for w in widgets(dialogo) if isinstance(w, Botao) and w.cget("text") == texto)
        alvo.invoke()

    acao.__name__ = f"responder '{texto}'"
    return acao


def situacao_ok():
    return app.tela.situacao.texto.cget("text").startswith("O ")


# ------------------------------------------------------------------ roteiro

esperar(sempre, lambda: capturar("inicio"))
esperar(sempre, lambda: clicar("Começar"))
esperar(lambda: tela("TelaLogin") and situacao_ok(), lambda: capturar("login"))
esperar(sempre, lambda: clicar("Já entrei no SIGEF"))
esperar(lambda: tela("TelaOrigem"), lambda: capturar("origem"))

# ---- modo digitar
esperar(sempre, lambda: app.ir(telas.TelaDigitar))
esperar(sempre, lambda: capturar("digitar_vazio"))
esperar(sempre, lambda: clicar("Adicionar à lista"))  # vazio: mostra o que falta
esperar(sempre, lambda: preencher(cpf="529.982.247-25", nome="Maria da Silva",
                                  banco="banco do brasil", agencia="1234", conta="56789-0"))
esperar(sempre, lambda: capturar("digitar_validacao"))
esperar(sempre, lambda: clicar("Adicionar à lista"))
esperar(sempre, lambda: preencher(cpf="529.982.247-24", nome="CPF Errado",
                                  banco="341", agencia="1", conta="2"))
esperar(sempre, lambda: clicar("Adicionar à lista"))
esperar(dialogo_aberto, lambda: capturar("cpf_suspeito"))
esperar(sempre, responder_dialogo("Corrigir o CPF"))
esperar(sempre, lambda: preencher(cpf="168.995.350-09", nome="João Batista Rocha",
                                  banco="Itaú", agencia="0450", conta="12345-6"))
esperar(sempre, lambda: clicar("Adicionar à lista"))
esperar(sempre, lambda: app.tela.conferencia.marcar("manual"))
esperar(sempre, lambda: capturar("digitar_lista"))
esperar(sempre, lambda: clicar("Começar o cadastro"))

esperar(dialogo_aberto, lambda: capturar("conferir_credor"))
esperar(sempre, responder_dialogo("Sim, está certo"))
esperar(dialogo_aberto, lambda: capturar("conferir_conta"))
esperar(sempre, responder_dialogo("Sim, está certo"))
esperar(dialogo_aberto, responder_dialogo("Corrigir os dados"))
esperar(dialogo_aberto, lambda: capturar("corrigir"))
esperar(sempre, lambda: setattr(next(
    w for w in widgets(dialogo_aberto()) if hasattr(w, "campos")).campos["banco"], "valor", "237"))
esperar(sempre, responder_dialogo("Salvar e tentar de novo"))
esperar(dialogo_aberto, responder_dialogo("Sim, e não perguntar mais sobre esta pessoa"))
esperar(lambda: tela("TelaResultado"), lambda: capturar("resultado_digitar"))

# ---- letras maiores
esperar(sempre, lambda: clicar("A+  Letra maior"))
esperar(sempre, lambda: clicar("A+  Letra maior"))
esperar(sempre, lambda: capturar("resultado_letra_grande"))
esperar(sempre, lambda: clicar("A−  Letra menor"))
esperar(sempre, lambda: clicar("A−  Letra menor"))

# ---- modo planilha
esperar(sempre, lambda: clicar("Fazer outro cadastro"))
esperar(lambda: tela("TelaOrigem"), lambda: app.ir(telas.TelaPlanilha))
esperar(lambda: app.tela.lista_pastas.size() > 0, lambda: capturar("planilha_lista"))
esperar(sempre, lambda: (app.tela.lista_abas.selection_clear(0, "end"),
                         app.tela.lista_abas.selection_set(0), app.tela.escolher_aba()))
esperar(sempre, lambda: capturar("planilha_escolhida"))
esperar(sempre, lambda: clicar("Continuar"))
esperar(lambda: tela("TelaColunas"), lambda: capturar("colunas"))
esperar(sempre, lambda: app.tela.resultado.set("E"))  # coluna de dados: bloqueia
esperar(sempre, lambda: capturar("colunas_conflito"))
esperar(sempre, lambda: app.tela.resultado.set("J"))
esperar(sempre, lambda: app.tela.conferencia.marcar("auto"))
esperar(sempre, lambda: clicar("Começar o cadastro"))
esperar(lambda: tela("TelaCadastro") and len(app.tela.resultados) >= 1,
        lambda: capturar("cadastrando"))
esperar(lambda: tela("TelaResultado"), lambda: capturar("resultado_planilha"))


def conferir_planilha():
    print("J4 =", ABA.valor("J4"))
    print("J5 =", ABA.valor("J5"))
    print("J6 =", ABA.valor("J6"))
    assert ABA.valor("J4") == "Operação realizada com sucesso."
    assert ABA.valor("J5") == "Operação realizada com sucesso."
    assert ABA.valor("J6") == "ERRO: campos vazios - Conta"


esperar(sempre, conferir_planilha)

# ---- estatísticas
esperar(sempre, lambda: clicar("Estatísticas"))
esperar(lambda: tela("TelaEstatisticas") and "sessões" in app.tela.situacao.cget("text"),
        lambda: capturar("estatisticas"))
esperar(sempre, lambda: clicar("Cronometrar um cadastro manual"))
esperar(dialogo_aberto, lambda: capturar("cronometro"))
esperar(sempre, responder_dialogo("Começar"))
esperar(lambda: time.sleep(2) or True, lambda: capturar("cronometro_contando"))
esperar(sempre, responder_dialogo("Terminei"))
esperar(dialogo_aberto, responder_dialogo("Guardar mesmo assim"))  # 2 s é curto demais
esperar(dialogo_aberto, responder_dialogo("Entendi"))
esperar(sempre, lambda: clicar("Ajustar a estimativa"))


def preencher_estimativa():
    dialogo = dialogo_aberto()
    campos = sorted((w for w in widgets(dialogo) if hasattr(w, "entrada")),
                    key=lambda w: w.winfo_y())  # novo (em cima), existente (embaixo)
    campos[0].valor = "6"
    campos[1].valor = "2:30"
    capturar("estimativa")


esperar(dialogo_aberto, preencher_estimativa)
esperar(sempre, responder_dialogo("Salvar"))
esperar(lambda: "cronometragens" not in app.tela.aviso_manual.texto.cget("text"),
        lambda: capturar("estatisticas_atualizadas"))
esperar(sempre, lambda: app.rolagem.tela.yview_moveto(0.45))
esperar(sempre, lambda: capturar("estatisticas_meio"))
esperar(sempre, lambda: app.rolagem.tela.yview_moveto(1))
esperar(sempre, lambda: capturar("estatisticas_fim"))
esperar(sempre, lambda: clicar("Gerar relatório"))
esperar(dialogo_aberto, lambda: capturar("relatorio_pronto"))
esperar(sempre, responder_dialogo("Entendi"))


def conferir_estatisticas():
    sessoes, manuais = estatisticas.carregar(estatisticas.LOCAL)
    ind = estatisticas.calcular(sessoes, manuais, estatisticas.ler_ajustes()["estimativa"])
    print("sessões:", len(sessoes), "manuais:", len(manuais), "feitos:", ind.feitos,
          "economia:", estatisticas.formatar_duracao(ind.segundos_economizados), flush=True)
    assert len(sessoes) == 2 and len(manuais) == 1 and ind.feitos == 4
    assert ind.media_manual["existente"] == 150
    pastas = list((TEMP / "relatorios").iterdir())
    assert len(pastas) == 1 and (pastas[0] / "dados_pesquisa.xlsx").exists()


esperar(sempre, conferir_estatisticas)
esperar(sempre, lambda: clicar("Voltar"))
esperar(lambda: tela("TelaResultado"), lambda: capturar("voltou_resultado"))
esperar(sempre, lambda: clicar("Ajuda"))
esperar(dialogo_aberto, lambda: capturar("ajuda"))
esperar(sempre, responder_dialogo("Entendi"))

raiz.after(1500, executar_passos)
app.executar()
