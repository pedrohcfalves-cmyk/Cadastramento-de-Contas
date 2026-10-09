"""As telas do assistente, na ordem em que a pessoa passa por elas.

Início → 1 Entrar no SIGEF → 2 Escolher os dados → 3 Cadastrar → 4 Resultado
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk

from .. import estatisticas, relatorio
from ..bancos import descrever_banco
from ..config import COLUNA_RESULTADO, PASTA_LOGS, PREFIXO
from ..fluxos import Relator, executar_lotes, executar_planilha
from ..modelos import cpf_confere, ler_arquivo_lotes
from ..navegador import ErroNavegador
from ..planilha import (
    ErroPlanilha,
    Planilha,
    abas_da_pasta,
    abrir_arquivo,
    conectar_excel,
    indice_para_letra,
    letra_para_indice,
    pastas_abertas,
)
from . import dialogos
from . import estilo as e
from .componentes import (
    Alternador,
    Barras,
    Botao,
    Caixa,
    Escolha,
    Placar,
    Quadro,
    Tabela,
    Texto,
    formatar_cpf,
)

PASSOS = ("Entrar no SIGEF", "Escolher os dados", "Cadastrar", "Ver o resultado")

CONFERENCIA = (
    ("auto", "Cadastrar direto, sem perguntar",
     "O programa faz tudo sozinho. É o jeito mais rápido."),
    ("manual", "Mostrar os dados de cada pessoa antes de gravar",
     "Você confere e confirma cada pessoa. Mais devagar, porém mais seguro."),
)

COLUNAS_RESULTADO = (
    ("chave", "Nº", 90, False),
    ("nome", "Nome", 300, True),
    ("cpf", "CPF", 170, False),
    ("situacao", "Resultado", 380, True),
)

LETRAS = [indice_para_letra(i) for i in range(1, 53)]  # A até AZ


def situacao_amigavel(status: str, texto: str) -> str:
    """Texto curto para a lista de resultados, sempre com símbolo e palavra."""
    motivo = texto[len(PREFIXO[status]):] if texto.startswith(PREFIXO[status]) else texto

    return {
        "OK": "✔ Cadastrado",
        "JA": "✔ Já estava cadastrado",
        "PULADO": "– Pulado",
    }.get(status, f"✖ Problema: {motivo}")


def mensagem_de_erro(erro: Exception) -> str:
    if isinstance(erro, (ErroNavegador, ErroPlanilha)):
        return str(erro)

    primeira = (str(erro).splitlines() or [type(erro).__name__])[0]
    return f"Aconteceu um problema inesperado: {primeira}"


# ============================================================== base

class Tela(Quadro):
    passo = 0          # 0 = antes de começar; 1 a 4 = trilha do topo
    titulo = ""
    explicacao = ""
    ajuda = ""

    def __init__(self, app, **dados):
        super().__init__(app.rolagem.conteudo, padx=56, pady=28)
        self.app = app
        self.trabalhador = app.trabalhador

        if self.passo:
            tk.Label(self, text=f"Passo {self.passo} de {len(PASSOS)}", font=self.tema["forte"],
                     fg=e.AZUL, bg=self["bg"], anchor="w").pack(fill="x")

        self.rotulo_titulo = Texto(self, self.titulo, fonte="titulo", largura=48)
        self.rotulo_titulo.pack(fill="x", pady=(2, 6))

        if self.explicacao:
            Texto(self, self.explicacao, cor=e.TINTA_SUAVE).pack(fill="x", pady=(0, 18))

        self.montar(**dados)

    def montar(self, **dados) -> None:
        """Conteúdo da tela."""

    def barra(self, esquerda: Quadro, direita: Quadro) -> None:
        """Botões da barra inferior: Voltar à esquerda, ação principal à direita."""

    def ao_sair(self) -> None:
        """Chamado antes de trocar de tela."""

    def voltar_para(self, esquerda: Quadro, destino) -> Botao:
        botao = Botao(esquerda, "Voltar", lambda: self.app.ir(destino), variante="secundario")
        botao.pack(side="left")
        return botao


class Cartao(Quadro):
    """Opção grande e clicável, com título e descrição (mouse ou teclado)."""

    def __init__(self, pai, simbolo: str, titulo: str, descricao: str, comando):
        super().__init__(pai, fundo=e.SUPERFICIE, padx=28, pady=24, cursor="hand2",
                         highlightthickness=3, highlightbackground=e.BORDA,
                         highlightcolor=e.AMARELO, takefocus=True)
        self.comando = comando
        tk.Label(self, text=simbolo, font=self.tema["numero"], fg=e.AZUL,
                 bg=e.SUPERFICIE).pack(anchor="w")
        tk.Label(self, text=titulo, font=self.tema["subtitulo"], fg=e.TINTA,
                 bg=e.SUPERFICIE).pack(anchor="w", pady=(6, 6))
        Texto(self, descricao, cor=e.TINTA_SUAVE, largura=34).pack(anchor="w")
        tk.Label(self, text="Escolher esta opção", font=self.tema["botao"], fg="white",
                 bg=e.VERDE, padx=18, pady=10).pack(anchor="w", pady=(18, 0))

        for widget in (self, *self.winfo_children()):
            widget.bind("<Button-1>", lambda _: comando())

        self.bind("<Return>", lambda _: comando())
        self.bind("<space>", lambda _: comando())
        self.bind("<Enter>", lambda _: self.configure(highlightbackground=e.AZUL))
        self.bind("<Leave>", lambda _: self.configure(highlightbackground=e.BORDA))


# ============================================================== início

class TelaInicio(Tela):
    titulo = "Cadastrar credores no SIGEF"
    explicacao = ("Este programa cadastra pessoas como credores no SIGEF e grava a conta "
                  "bancária de cada uma, uma pessoa de cada vez, sem você precisar digitar "
                  "nada no SIGEF.")
    ajuda = ("Clique no botão verde Começar. O programa vai abrir o Google Chrome na página "
             "do SIGEF para você entrar com seu usuário e senha.")

    def montar(self):
        Texto(self, "Antes de começar, tenha em mãos:", fonte="subtitulo").pack(fill="x")

        for item in ("Seu usuário e sua senha do SIGEF.",
                     "A planilha do Excel com os dados das pessoas, ou os dados para digitar."):
            Texto(self, f"•  {item}").pack(fill="x", padx=(12, 0), pady=3)

        Texto(self, "Como funciona:", fonte="subtitulo").pack(fill="x", pady=(22, 0))

        for numero, passo in enumerate(PASSOS, 1):
            Texto(self, f"{numero}.  {passo}").pack(fill="x", padx=(12, 0), pady=3)

        Caixa(self, "O programa abre o Google Chrome sozinho. Enquanto o cadastro estiver "
                    "acontecendo, não feche o Chrome. Você pode acompanhar tudo por ele.",
              tipo="atencao").pack(fill="x", pady=(24, 0))

    def barra(self, esquerda, direita):
        Botao(direita, "Começar", lambda: self.app.ir(TelaLogin), variante="principal").pack()


# ============================================================== passo 1

class TelaLogin(Tela):
    passo = 1
    titulo = "Entre no SIGEF"
    ajuda = ("O programa abriu o Google Chrome na página do SIGEF. Entre com seu usuário e "
             "senha, como você faz todos os dias. Depois volte para esta janela e clique no "
             "botão verde Já entrei no SIGEF.\n\nSe a janela do Chrome sumiu, clique em "
             "Abrir o Chrome de novo.")

    def montar(self):
        self.situacao = Caixa(self, "Abrindo o Google Chrome… aguarde.", tipo="info")
        self.situacao.pack(fill="x", pady=(0, 20))

        Texto(self, "Faça assim:", fonte="subtitulo").pack(fill="x")

        for numero, passo in enumerate((
            "Clique na janela do Google Chrome que acabou de abrir.",
            "Digite seu usuário e sua senha e entre no SIGEF, como você faz todos os dias.",
            "Volte para esta janela e clique no botão verde Já entrei no SIGEF.",
        ), 1):
            Texto(self, f"{numero}.  {passo}").pack(fill="x", padx=(12, 0), pady=4)

        self.abrir_navegador()

    def barra(self, esquerda, direita):
        self.voltar_para(esquerda, TelaInicio)
        self.botao_entrei = Botao(direita, "Já entrei no SIGEF", self.conferir_login,
                                  variante="principal")
        self.botao_entrei.pack(side="right")
        self.botao_abrir = Botao(direita, "Abrir o Chrome de novo", self.abrir_navegador)
        self.botao_abrir.pack(side="right", padx=(0, 16))

    def _ocupar(self, ocupado: bool) -> None:
        for botao in (getattr(self, "botao_entrei", None), getattr(self, "botao_abrir", None)):
            if botao:
                botao.ativar(not ocupado)

        self.app.raiz.configure(cursor="watch" if ocupado else "")

    def abrir_navegador(self):
        self._ocupar(True)
        self.situacao.mudar("Abrindo o Google Chrome… aguarde.", "info")

        def pronto(nome):
            self._ocupar(False)
            aberto = "O navegador já estava aberto" if "já" in nome else f"O {nome} foi aberto"
            self.situacao.mudar(f"{aberto} na página do SIGEF. Entre com seu usuário e senha.",
                                "ok")

        self.trabalhador.fazer(lambda: self.trabalhador.navegador.abrir(),
                               ok=pronto, falha=self._falhou)

    def conferir_login(self):
        self._ocupar(True)
        self.situacao.mudar("Conferindo se você já entrou no SIGEF… aguarde.", "info")

        def conferir():
            navegador = self.trabalhador.navegador
            navegador.abrir()
            return navegador.logado()

        def pronto(logado):
            self._ocupar(False)

            if logado:
                self.app.ir(TelaOrigem)
            else:
                self.situacao.mudar(
                    "Ainda não consegui abrir a tela de credores do SIGEF. Confira se você "
                    "terminou de entrar com usuário e senha e clique de novo em Já entrei no "
                    "SIGEF.\n\nSe continuar assim, seu usuário pode não ter permissão na tela "
                    "de credores (transação 1028).", "erro")

        self.trabalhador.fazer(conferir, ok=pronto, falha=self._falhou)

    def _falhou(self, erro):
        self._ocupar(False)
        self.situacao.mudar(mensagem_de_erro(erro) + "\n\nClique em Abrir o Chrome de novo.",
                            "erro")


# ============================================================== passo 2

class TelaOrigem(Tela):
    passo = 2
    titulo = "De onde vêm os dados?"
    explicacao = "Escolha uma das duas opções."
    ajuda = ("Se os dados das pessoas estão numa planilha do Excel, escolha Planilha do Excel. "
             "Se você vai digitar os dados, ou copiar de outro lugar, escolha Digitar ou colar.")

    def montar(self):
        grade = Quadro(self)
        grade.pack(fill="x")
        grade.columnconfigure((0, 1), weight=1, uniform="cartao")

        Cartao(grade, "▦", "Planilha do Excel",
               "Os dados já estão numa planilha. O resultado de cada pessoa é escrito na "
               "própria planilha.", lambda: self.app.ir(TelaPlanilha)
               ).grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        Cartao(grade, "✎", "Digitar ou colar",
               "Você digita os dados de cada pessoa ou cola uma lista copiada de outro lugar.",
               lambda: self.app.ir(TelaDigitar)
               ).grid(row=0, column=1, sticky="nsew", padx=(16, 0))

    def barra(self, esquerda, direita):
        self.voltar_para(esquerda, TelaLogin)


class TelaPlanilha(Tela):
    passo = 2
    titulo = "Escolha a planilha"
    explicacao = ("Clique na planilha com os dados das pessoas. Se ela não estiver na lista, "
                  "clique em Procurar arquivo.")
    ajuda = ("A lista mostra as planilhas que estão abertas no Excel agora. Clique na planilha "
             "certa e depois na aba (a folha) onde estão os dados. Se a planilha não aparecer, "
             "clique em Procurar arquivo e escolha o arquivo no computador.\n\nImportante: o "
             "resultado de cada pessoa será escrito na planilha e ela será salva a cada linha.")

    def montar(self):
        self.pasta = None
        self.excel = None

        self.situacao = Caixa(self, "Procurando planilhas abertas no Excel… aguarde.")
        self.situacao.pack(fill="x", pady=(0, 16))

        grade = Quadro(self)
        grade.pack(fill="both", expand=True)
        grade.columnconfigure((0, 1), weight=1, uniform="lista")

        Texto(grade, "Planilhas abertas no Excel", fonte="subtitulo").grid(
            row=0, column=0, sticky="w")
        Texto(grade, "Aba (folha) da planilha", fonte="subtitulo").grid(
            row=0, column=1, sticky="w", padx=(32, 0))

        self.lista_pastas = self._lista(grade, self.escolher_pasta)
        self.lista_pastas.grid(row=1, column=0, sticky="nsew", pady=8)
        self.lista_abas = self._lista(grade, self.escolher_aba)
        self.lista_abas.grid(row=1, column=1, sticky="nsew", pady=8, padx=(32, 0))

        botoes = Quadro(grade)
        botoes.grid(row=2, column=0, sticky="w")
        Botao(botoes, "Procurar arquivo…", self.procurar).pack(side="left")
        Botao(botoes, "Atualizar a lista", self.carregar, variante="discreto").pack(
            side="left", padx=(12, 0))

        self.carregar()

    def _lista(self, pai, ao_escolher) -> tk.Listbox:
        lista = tk.Listbox(pai, font=self.tema["texto"], height=7, activestyle="none",
                           exportselection=False, relief="solid", bd=1,
                           highlightthickness=3, highlightcolor=e.AMARELO,
                           highlightbackground=e.BORDA, selectbackground=e.AZUL,
                           selectforeground="white", bg=e.SUPERFICIE, fg=e.TINTA)
        lista.bind("<<ListboxSelect>>", lambda _: ao_escolher())
        return lista

    def barra(self, esquerda, direita):
        self.voltar_para(esquerda, TelaOrigem)
        self.botao_continuar = Botao(direita, "Continuar", self.continuar, variante="principal")
        self.botao_continuar.pack(side="right")
        self.botao_continuar.ativar(False)

    # ---- ações (o Excel só é tocado pelo trabalhador)

    def carregar(self, selecionar: str = None):
        def buscar():
            self.excel = self.excel or conectar_excel()
            return pastas_abertas(self.excel)

        def pronto(nomes):
            self.lista_pastas.delete(0, "end")
            self.lista_abas.delete(0, "end")
            self.botao_continuar.ativar(False)

            for nome in nomes:
                self.lista_pastas.insert("end", f"  {nome}")

            if not nomes:
                self.situacao.mudar("Nenhuma planilha aberta no Excel. Clique em Procurar "
                                    "arquivo para escolher uma no computador.", "atencao")
                return

            self.situacao.mudar("Clique na planilha com os dados das pessoas.", "info")
            indice = nomes.index(selecionar) if selecionar in nomes else (
                0 if len(nomes) == 1 else None)

            if indice is not None:
                self.lista_pastas.selection_set(indice)
                self.escolher_pasta()

        self.trabalhador.fazer(buscar, ok=pronto, falha=self._falhou)

    def procurar(self):
        caminho = filedialog.askopenfilename(
            parent=self.app.raiz, title="Escolha a planilha",
            filetypes=[("Planilhas do Excel", "*.xlsx *.xlsm *.xls"), ("Todos os arquivos", "*.*")],
        )

        if not caminho:
            return

        self.situacao.mudar("Abrindo a planilha no Excel… aguarde.", "info")

        def abrir():
            self.excel = self.excel or conectar_excel()
            pasta, _ = abrir_arquivo(self.excel, caminho.replace("/", "\\"))
            return pasta.Name

        self.trabalhador.fazer(abrir, ok=lambda nome: self.carregar(selecionar=nome),
                               falha=self._falhou)

    def escolher_pasta(self):
        selecao = self.lista_pastas.curselection()

        if not selecao:
            return

        indice = selecao[0] + 1
        self.botao_continuar.ativar(False)

        def ler_abas():
            self.pasta = self.excel.Workbooks(indice)
            return abas_da_pasta(self.pasta)

        def pronto(abas):
            self.lista_abas.delete(0, "end")

            for aba in abas:
                self.lista_abas.insert("end", f"  {aba}")

            if len(abas) == 1:
                self.lista_abas.selection_set(0)
                self.escolher_aba()
            else:
                self.situacao.mudar("Agora clique na aba (folha) onde estão os dados.", "info")

        self.trabalhador.fazer(ler_abas, ok=pronto, falha=self._falhou)

    def escolher_aba(self):
        if self.lista_abas.curselection():
            self.botao_continuar.ativar(True)
            self.situacao.mudar("Tudo certo. Clique em Continuar.", "ok")

    def continuar(self):
        aba = self.lista_abas.get(self.lista_abas.curselection()[0]).strip()
        self.botao_continuar.ativar(False)
        self.situacao.mudar("Lendo a planilha… aguarde.", "info")

        def ler():
            planilha = Planilha.da_pasta(self.pasta, aba)
            colunas, primeira, detectou = planilha.colunas_sugeridas()
            return {
                "planilha": planilha,
                "colunas": colunas,
                "primeira": primeira,
                "detectou": detectou,
                "final": max(planilha.ultima_linha(colunas), primeira),
                "amostra": planilha.amostra(colunas, primeira),
                "nome": f"{self.pasta.Name} › {aba}",
                "somente_leitura": planilha.somente_leitura,
            }

        self.trabalhador.fazer(ler, ok=lambda info: self.app.ir(TelaColunas, info=info),
                               falha=self._falhou)

    def _falhou(self, erro):
        self.situacao.mudar(mensagem_de_erro(erro), "erro")


class TelaColunas(Tela):
    passo = 2
    titulo = "Confira as colunas da planilha"
    ajuda = ("Cada informação da pessoa fica numa coluna da planilha (A, B, C…). Olhe o "
             "exemplo ao lado de cada uma: ele mostra o que está escrito na primeira pessoa. "
             "Se algum exemplo estiver errado, troque a letra da coluna.\n\nO resultado de cada "
             "pessoa (cadastrado, já cadastrado ou o problema) será escrito na coluna do "
             "resultado, apagando o que houver nela.")

    def montar(self, info):
        self.info = info
        self.planilha = info["planilha"]
        self._agendado = None

        Texto(self, f"Planilha: {info['nome']}", fonte="forte").pack(fill="x", pady=(0, 10))

        if info["somente_leitura"]:
            Caixa(self, "Esta planilha está aberta só para leitura. O programa não conseguirá "
                        "escrever o resultado. Feche a planilha e abra de novo normalmente.",
                  tipo="erro").pack(fill="x", pady=(0, 12))

        if info["detectou"]:
            aviso = (f"Encontrei os títulos das colunas na linha {info['primeira'] - 1}. "
                     "Confira os exemplos abaixo.")
        else:
            aviso = ("Não encontrei os títulos das colunas, então usei as colunas de costume "
                     "(D, E, F, G e H). Confira os exemplos com bastante atenção.")

        Caixa(self, aviso, tipo="ok" if info["detectou"] else "atencao").pack(fill="x")

        # ---- mapa das colunas
        grade = Quadro(self, fundo=e.SUPERFICIE, padx=20, pady=14,
                       highlightthickness=1, highlightbackground=e.BORDA)
        grade.pack(fill="x", pady=18)

        for coluna, titulo in enumerate(("Informação", "Coluna", "Título na planilha",
                                         "Exemplo (1ª pessoa)")):
            tk.Label(grade, text=titulo, font=self.tema["forte"], bg=e.SUPERFICIE,
                     fg=e.TINTA_SUAVE, anchor="w").grid(row=0, column=coluna, sticky="w",
                                                         padx=(0, 28), pady=(0, 8))

        self.seletores, self.titulos, self.exemplos = {}, {}, {}

        for linha, (campo, letra, titulo, exemplo) in enumerate(info["amostra"], 1):
            tk.Label(grade, text=dialogos.ROTULOS_SIMPLES[campo], font=self.tema["forte"],
                     bg=e.SUPERFICIE, fg=e.TINTA, anchor="w").grid(
                row=linha, column=0, sticky="w", pady=5)

            variavel = tk.StringVar(value=letra)
            seletor = ttk.Combobox(grade, textvariable=variavel, values=LETRAS, width=4,
                                   state="readonly", font=self.tema["forte"])
            seletor.grid(row=linha, column=1, sticky="w", padx=(0, 28), pady=5)
            seletor.bind("<<ComboboxSelected>>", lambda _: self.atualizar_amostra())
            self.seletores[campo] = variavel

            self.titulos[campo] = tk.Label(grade, font=self.tema["texto"], bg=e.SUPERFICIE,
                                           fg=e.TINTA_SUAVE, anchor="w")
            self.titulos[campo].grid(row=linha, column=2, sticky="w", padx=(0, 28))
            self.exemplos[campo] = tk.Label(grade, font=self.tema["forte"], bg=e.SUPERFICIE,
                                            fg=e.TINTA, anchor="w")
            self.exemplos[campo].grid(row=linha, column=3, sticky="w")

        self._mostrar_amostra(info["amostra"])

        # ---- linhas e coluna do resultado
        opcoes = self.opcoes = Quadro(self)
        opcoes.pack(fill="x")

        self.primeira = tk.IntVar(value=info["primeira"])
        self.final = tk.IntVar(value=info["final"])
        self.resultado = tk.StringVar(value=COLUNA_RESULTADO)

        for linha, (rotulo, widget) in enumerate((
            ("Começar na linha", self._numero(opcoes, self.primeira)),
            ("Terminar na linha", self._numero(opcoes, self.final)),
            ("Escrever o resultado na coluna",
             ttk.Combobox(opcoes, textvariable=self.resultado, values=LETRAS, width=4,
                          state="readonly", font=self.tema["forte"])),
        )):
            tk.Label(opcoes, text=rotulo, font=self.tema["forte"], bg=self["bg"], fg=e.TINTA,
                     anchor="w").grid(row=linha, column=0, sticky="w", pady=6, padx=(0, 20))
            widget.grid(row=linha, column=1, sticky="w", pady=6)

        self.primeira.trace_add("write", lambda *_: self._agendar_amostra())
        self.resultado.trace_add("write", lambda *_: self.validar())
        self.final.trace_add("write", lambda *_: self.validar())

        self.problema = Caixa(self, "", tipo="erro")

        Texto(self, "Quer conferir cada pessoa antes de gravar?", fonte="subtitulo").pack(
            fill="x", pady=(22, 6))
        self.conferencia = Escolha(self, CONFERENCIA, self.app.conferencia)
        self.conferencia.pack(fill="x")

    def _numero(self, pai, variavel) -> ttk.Spinbox:
        return ttk.Spinbox(pai, from_=1, to=1_048_576, textvariable=variavel, width=8,
                           font=self.tema["forte"])

    def barra(self, esquerda, direita):
        self.voltar_para(esquerda, TelaPlanilha)
        self.botao_comecar = Botao(direita, "Começar o cadastro", self.comecar,
                                   variante="principal")
        self.botao_comecar.pack(side="right")
        self.validar()

    def colunas(self) -> dict:
        return {campo: letra_para_indice(var.get()) for campo, var in self.seletores.items()}

    def _ler_inteiro(self, variavel):
        try:
            return int(variavel.get())
        except (tk.TclError, ValueError):
            return None

    def _agendar_amostra(self):
        if self._agendado:
            self.after_cancel(self._agendado)

        self._agendado = self.after(400, self.atualizar_amostra)

    def atualizar_amostra(self):
        self._agendado = None
        primeira = self._ler_inteiro(self.primeira)
        self.validar()

        if not primeira:
            return

        colunas = self.colunas()
        self.trabalhador.fazer(lambda: self.planilha.amostra(colunas, primeira),
                               ok=self._mostrar_amostra)

    def _mostrar_amostra(self, amostra):
        if not self.winfo_exists():
            return

        for campo, _letra, titulo, exemplo in amostra:
            self.titulos[campo].configure(text=titulo or "(sem título)")
            self.exemplos[campo].configure(text=exemplo or "(vazio)",
                                           fg=e.TINTA if exemplo else e.VERMELHO)

    def validar(self) -> bool:
        primeira, final = self._ler_inteiro(self.primeira), self._ler_inteiro(self.final)
        resultado = letra_para_indice(self.resultado.get())
        problema = ""

        if not primeira or not final:
            problema = "Informe os números da primeira e da última linha."
        elif primeira > final:
            problema = "A linha de começo precisa ser menor que a linha do fim."
        elif resultado in self.colunas().values():
            problema = ("A coluna do resultado não pode ser uma das colunas com os dados. "
                        "Escolha uma coluna vazia.")

        if problema:
            self.problema.mudar(problema)
            self.problema.pack(fill="x", pady=(12, 0), after=self.opcoes)
        else:
            self.problema.pack_forget()

        if hasattr(self, "botao_comecar"):
            self.botao_comecar.ativar(not problema)

        return not problema

    def comecar(self):
        if not self.validar():
            return

        self.app.conferencia = self.conferencia.valor
        self.app.ir(
            TelaCadastro,
            modo="planilha",
            planilha=self.planilha,
            colunas=self.colunas(),
            primeira=self._ler_inteiro(self.primeira),
            final=self._ler_inteiro(self.final),
            coluna_resultado=self.resultado.get(),
            manual=self.conferencia.valor == "manual",
        )


class TelaDigitar(Tela):
    passo = 2
    titulo = "Digite os dados das pessoas"
    explicacao = ("Preencha os dados de uma pessoa e clique em Adicionar à lista. Repita para "
                  "cada pessoa. Quando terminar, clique em Começar o cadastro.")
    ajuda = ("Preencha os cinco campos de uma pessoa e clique em Adicionar à lista (ou aperte "
             "Enter no último campo). A pessoa aparece na lista do lado direito.\n\nPara tirar "
             "alguém da lista, clique na pessoa e depois em Tirar da lista.\n\nSe você tem uma "
             "lista pronta (do Excel ou de um texto), use Colar uma lista ou Abrir arquivo.")

    def montar(self):
        grade = Quadro(self)
        grade.pack(fill="both", expand=True)
        grade.columnconfigure(1, weight=1)

        # ---- formulário
        esquerda = Quadro(grade)
        esquerda.grid(row=0, column=0, sticky="nw", padx=(0, 40))
        self.formulario = dialogos.Formulario(esquerda, largura=24)
        self.formulario.pack(fill="x")
        self.formulario.campos["conta"].entrada.bind("<Return>", lambda _: self.adicionar())
        Botao(esquerda, "Adicionar à lista", self.adicionar).pack(fill="x", pady=(10, 0))

        # ---- lista
        direita = Quadro(grade)
        direita.grid(row=0, column=1, sticky="nsew")
        self.contador = Texto(direita, "", fonte="subtitulo")
        self.contador.pack(fill="x", pady=(0, 6))
        self.tabela = Tabela(direita, [
            ("cpf", "CPF", 120, True), ("nome", "Nome", 130, True),
            ("banco", "Banco", 90, True), ("agencia", "Agência", 70, True),
            ("conta", "Conta", 80, True),
        ], altura=8)
        self.tabela.pack(fill="both", expand=True)

        botoes = Quadro(direita)
        botoes.pack(fill="x", pady=(10, 0))
        Botao(botoes, "Tirar da lista", self.remover, variante="discreto").pack(side="left")
        Botao(botoes, "Abrir arquivo…", self.abrir_arquivo).pack(side="right")
        Botao(botoes, "Colar uma lista…", self.colar).pack(side="right", padx=(0, 12))

        Texto(self, "Quer conferir cada pessoa antes de gravar?", fonte="subtitulo").pack(
            fill="x", pady=(26, 6))
        self.conferencia = Escolha(self, CONFERENCIA, self.app.conferencia)
        self.conferencia.pack(fill="x")

        for lote in self.app.lotes:
            self._mostrar(lote)

        self.after(100, self.formulario.focar)

    def barra(self, esquerda, direita):
        self.voltar_para(esquerda, TelaOrigem)
        self.botao_comecar = Botao(direita, "Começar o cadastro", self.comecar,
                                   variante="principal")
        self.botao_comecar.pack(side="right")
        self._atualizar()

    def _atualizar(self):
        quantidade = len(self.app.lotes)
        self.contador.configure(
            text={0: "A lista está vazia", 1: "1 pessoa na lista"}.get(
                quantidade, f"{quantidade} pessoas na lista"))

        if hasattr(self, "botao_comecar"):
            self.botao_comecar.ativar(quantidade > 0)

    def _mostrar(self, lote):
        self.tabela.inserir(str(id(lote)), (formatar_cpf(lote.cpf), lote.nome,
                                            descrever_banco(lote.banco), lote.agencia,
                                            lote.conta))

    def _incluir(self, lotes):
        for lote in lotes:
            self.app.lotes.append(lote)
            self._mostrar(lote)

        self._atualizar()

    def adicionar(self):
        lote = self.formulario.ler()

        if lote is None:
            return

        if not cpf_confere(lote.cpf):
            decisao = dialogos.recado(
                self.app.raiz, "Confira o CPF",
                f"O CPF {formatar_cpf(lote.cpf)} parece ter algum número errado. "
                "Confira no documento da pessoa.", tipo="atencao",
                botoes=(("Adicionar mesmo assim", True, "secundario"),
                        ("Corrigir o CPF", False, "principal")))

            if not decisao:
                self.formulario.campos["cpf"].entrada.focus_set()
                return

        self._incluir([lote])
        self.formulario.limpar()

    def remover(self):
        iid = self.tabela.selecionado()

        if iid is None:
            dialogos.recado(self.app.raiz, "Tirar da lista",
                            "Primeiro clique na pessoa que você quer tirar da lista.")
            return

        self.app.lotes[:] = [lote for lote in self.app.lotes if str(id(lote)) != iid]
        self.tabela.arvore.delete(iid)
        self._atualizar()

    def colar(self):
        self._incluir(dialogos.colar_lista(self.app.raiz))

    def abrir_arquivo(self):
        caminho = filedialog.askopenfilename(
            parent=self.app.raiz, title="Escolha o arquivo com a lista",
            filetypes=[("Arquivos de texto ou CSV", "*.csv *.txt"), ("Todos os arquivos", "*.*")],
        )

        if not caminho:
            return

        try:
            lotes, ignoradas = ler_arquivo_lotes(caminho)
        except OSError as erro:
            dialogos.recado(self.app.raiz, "Não consegui abrir o arquivo", str(erro), "erro")
            return

        self._incluir(lotes)

        if ignoradas:
            linhas = "\n".join(f"Linha {n}: {motivo}" for n, motivo in ignoradas[:8])
            dialogos.recado(self.app.raiz, "Algumas linhas ficaram de fora",
                            f"{len(lotes)} pessoa(s) adicionada(s). Estas linhas têm problema e "
                            f"não entraram na lista:\n\n{linhas}", "atencao")

    def comecar(self):
        self.app.conferencia = self.conferencia.valor
        self.app.ir(TelaCadastro, modo="lotes", lotes=list(self.app.lotes),
                    manual=self.conferencia.valor == "manual")


# ============================================================== passo 3

class RelatorJanela(Relator):
    """Leva os acontecimentos do trabalhador para a tela de cadastro."""

    def __init__(self, tela: "TelaCadastro"):
        self.tela = tela
        self.na_janela = tela.trabalhador.na_janela
        self.parar = threading.Event()

    def inicio(self, chave, lote, atual, total):
        self.na_janela(self.tela.mostrar_inicio, chave, lote, atual, total)

    def resultado(self, chave, lote, status, texto):
        self.na_janela(self.tela.mostrar_resultado, chave, lote, status, texto)

    def aviso(self, texto):
        self.na_janela(self.tela.mostrar_aviso, texto)

    def corrigir(self, lote):
        return self.na_janela(dialogos.corrigir, self.tela.app.raiz, lote, esperar=True)

    def cancelado(self):
        return self.parar.is_set()


class TelaCadastro(Tela):
    passo = 3
    titulo = "Cadastrando…"
    explicacao = ("Não feche esta janela nem o Google Chrome. Você pode acompanhar o que o "
                  "programa está fazendo pela janela do Chrome.")
    ajuda = ("O programa está cadastrando as pessoas no SIGEF, uma de cada vez. Espere até "
             "aparecer a tela de resultado.\n\nSe precisar interromper, clique em Parar o "
             "cadastro: o programa termina a pessoa atual e para.")

    def montar(self, modo, manual, **parametros):
        self.modo = modo
        self.resultados = []

        self.progresso_texto = Texto(self, "Preparando…", fonte="subtitulo")
        self.progresso_texto.pack(fill="x")
        self.progresso = ttk.Progressbar(self, mode="determinate", maximum=1)
        self.progresso.pack(fill="x", pady=(8, 10))
        self.agora = Caixa(self, "Abrindo a tela de credores do SIGEF…", tipo="info")
        self.agora.pack(fill="x", pady=(0, 14))

        self.avisos = Caixa(self, "", tipo="atencao")

        self.tabela = Tabela(self, COLUNAS_RESULTADO, altura=7)
        self.tabela.pack(fill="both", expand=True)
        self.tabela.arvore.heading("chave", text="Linha" if modo == "planilha" else "Nº")

        self.relator = RelatorJanela(self)
        self.sessao = estatisticas.Sessao(modo, "manual" if manual else "auto")
        navegador = self.trabalhador.navegador
        perguntar = self._perguntar if manual else None

        def tarefa():
            try:
                if modo == "planilha":
                    return executar_planilha(
                        navegador, parametros["planilha"], parametros["colunas"],
                        parametros["primeira"], parametros["final"],
                        parametros["coluna_resultado"], self.relator, perguntar, self.sessao)

                return executar_lotes(navegador, parametros["lotes"], self.relator, perguntar,
                                      self.sessao)
            finally:
                # Gravado aqui (no trabalhador) para a rede lenta não travar a janela
                estatisticas.salvar_sessao(self.sessao)

        self.app.cadastrando = True
        self.trabalhador.fazer(tarefa, ok=self.terminou, falha=self.falhou)

    def barra(self, esquerda, direita):
        self.botao_parar = Botao(direita, "Parar o cadastro", self.parar, variante="perigo")
        self.botao_parar.pack(side="right")

    def _perguntar(self, lote, acao, editavel):
        return self.trabalhador.na_janela(dialogos.conferir, self.app.raiz, lote, acao,
                                          editavel, esperar=True)

    # ---- chamados na janela pelo RelatorJanela

    def mostrar_inicio(self, chave, lote, atual, total):
        self.progresso_texto.configure(text=f"Pessoa {atual} de {total}")
        self.progresso.configure(maximum=total, value=atual - 1)
        self.agora.mudar(f"Agora: {lote.nome or '(sem nome)'}   —   CPF {formatar_cpf(lote.cpf)}")
        self.tabela.inserir(str(chave), (chave, lote.nome, formatar_cpf(lote.cpf),
                                         "… cadastrando"), "AGORA")

    def mostrar_resultado(self, chave, lote, status, texto):
        self.progresso.step(1)
        linha = (chave, lote.nome, formatar_cpf(lote.cpf), situacao_amigavel(status, texto))
        self.resultados = [r for r in self.resultados if r[0][0] != chave]
        self.resultados.append((linha, status))
        self.tabela.inserir(str(chave), linha, status)

    def mostrar_aviso(self, texto):
        atual = self.avisos.texto.cget("text")

        if texto not in atual:
            self.avisos.mudar(f"{atual}\n{texto}".strip())
            self.avisos.pack(fill="x", pady=(0, 14), before=self.tabela)

    # ---- fim

    def parar(self):
        self.relator.parar.set()
        self.botao_parar.configure(text="Parando depois desta pessoa…")
        self.botao_parar.ativar(False)

    def terminou(self, resumo):
        self.app.cadastrando = False

        if self.modo == "lotes":
            self.app.lotes.clear()

        self.app.ir(TelaResultado, resumo=resumo, resultados=self.resultados, modo=self.modo,
                    interrompido=self.relator.parar.is_set(), sessao=self.sessao)

    def falhou(self, erro):
        self.app.cadastrando = False
        dialogos.recado(self.app.raiz, "O cadastro parou",
                        mensagem_de_erro(erro) + "\n\nAs pessoas que já foram feitas estão na "
                        "lista do resultado.", "erro")

        if isinstance(erro, ErroNavegador):
            self.app.ir(TelaLogin)
        else:
            self.app.ir(TelaResultado, resumo=None, resultados=self.resultados,
                        modo=self.modo, interrompido=True, sessao=self.sessao)


# ============================================================== passo 4

class TelaResultado(Tela):
    passo = 4
    titulo = "Cadastro concluído"
    ajuda = ("Esta tela mostra o que aconteceu com cada pessoa. As pessoas com problema estão "
             "marcadas com ✖ e o motivo aparece ao lado.\n\nCorrija os dados dessas pessoas e "
             "faça um novo cadastro só com elas.\n\nO registro completo fica na pasta de "
             "registros (botão no canto inferior esquerdo).")

    def montar(self, resumo, resultados, modo, interrompido, sessao=None):
        if interrompido:
            self.rotulo_titulo.configure(text="Cadastro interrompido")

        contagem = dict.fromkeys(PREFIXO, 0)
        for _linha, status in resultados:
            contagem[status] += 1

        if resumo:
            contagem = resumo.contagem

        Placar(self, [
            (contagem["OK"], "cadastrados", e.VERDE),
            (contagem["JA"], "já tinham cadastro", e.AZUL),
            (contagem["PULADO"], "pulados", e.TINTA_SUAVE),
            (contagem["ERRO"], "com problema", e.VERMELHO),
        ]).pack(fill="x", pady=(0, 18))

        if sessao is not None and contagem["OK"]:
            _, automacao, economia = estatisticas.resumo_da_sessao(sessao)
            Caixa(self, f"A automação levou {estatisticas.formatar_duracao(automacao)}. "
                        f"Feito à mão, levaria cerca de "
                        f"{estatisticas.formatar_duracao(automacao + economia)}: uma economia de "
                        f"{estatisticas.formatar_duracao(economia)}. Veja o total no botão "
                        "Estatísticas, no alto da janela.",
                  tipo="info").pack(fill="x", pady=(0, 14))

        if contagem["ERRO"]:
            onde = (" e na coluna do resultado da planilha, começando com ERRO"
                    if modo == "planilha" else "")
            Caixa(self, f"Algumas pessoas tiveram problema. Elas estão marcadas com ✖ na lista "
                        f"abaixo{onde}. Corrija os dados e cadastre de novo só essas pessoas.",
                  tipo="erro").pack(fill="x", pady=(0, 14))
        elif not interrompido:
            Caixa(self, "Todas as pessoas foram feitas sem problema.", tipo="ok").pack(
                fill="x", pady=(0, 14))

        tabela = Tabela(self, COLUNAS_RESULTADO, altura=8)
        tabela.pack(fill="both", expand=True)
        tabela.arvore.heading("chave", text="Linha" if modo == "planilha" else "Nº")

        for linha, status in resultados:
            tabela.inserir(str(linha[0]), linha, status)

    def barra(self, esquerda, direita):
        Botao(esquerda, "Abrir a pasta de registros", lambda: e.abrir_pasta(PASTA_LOGS),
              variante="discreto").pack(side="left")
        Botao(direita, "Fazer outro cadastro", lambda: self.app.ir(TelaOrigem),
              variante="principal").pack(side="right")
        Botao(direita, "Fechar o programa", self.app.sair).pack(side="right", padx=(0, 16))



# ============================================================== estatísticas

class TelaEstatisticas(Tela):
    titulo = "Estatísticas"
    explicacao = ("Quanto tempo a automação economizou, somando todas as sessões. Esses dados "
                  "servem para a pesquisa de implantação.")
    ajuda = ("Esta tela compara o tempo de um cadastro feito à mão com o tempo da automação.\n\n"
             "O tempo manual fica mais preciso quando você cronometra alguns cadastros feitos à "
             "mão: clique em Cronometrar um cadastro manual, faça o cadastro no SIGEF e clique "
             "em Terminei.\n\nEste computador mostra só os dados desta máquina. Todos os "
             "computadores soma também os dados da pasta da pesquisa e os arquivos trazidos de "
             "outras máquinas.\n\nGerar relatório cria uma planilha do Excel e uma página para "
             "apresentar, na pasta Documentos.")

    def montar(self):
        ajustes = estatisticas.ler_ajustes()
        self.escopo = estatisticas.TODOS if ajustes["pasta_pesquisa"] else estatisticas.LOCAL

        topo = Quadro(self)
        topo.pack(fill="x", pady=(0, 16))
        self.alternador = Alternador(topo, [(estatisticas.LOCAL, "Este computador"),
                                            (estatisticas.TODOS, "Todos os computadores")],
                                     self.escopo, self.mudar_escopo)
        self.alternador.pack(side="left")
        self.situacao = Texto(topo, "Carregando…", cor=e.TINTA_SUAVE, largura=40)
        self.situacao.pack(side="left", padx=(20, 0))

        self.placar = Placar(self, [
            ("-", "cadastros concluídos", e.VERDE),
            ("-", "de tempo economizado", e.VERDE),
            ("-", "tempo médio à mão", e.TINTA_SUAVE),
            ("-", "tempo médio com a automação", e.AZUL),
        ])
        self.placar.pack(fill="x")

        Texto(self, "Tempo de um cadastro", fonte="subtitulo").pack(fill="x", pady=(22, 8))
        self.barras = Barras(self)
        self.barras.pack(fill="x")
        self.detalhe = Texto(self, "", cor=e.TINTA_SUAVE, largura=90)
        self.detalhe.pack(fill="x", pady=(6, 0))
        self.aviso_manual = Caixa(self, "", tipo="atencao")

        # ---- medir o tempo manual
        Texto(self, "Tempo manual", fonte="subtitulo").pack(fill="x", pady=(24, 4))
        Texto(self, "Para a pesquisa ficar precisa, cronometre alguns cadastros feitos à mão "
                    "(o ideal é pelo menos 5 de cada tipo).", cor=e.TINTA_SUAVE).pack(fill="x")
        manual = Quadro(self)
        manual.pack(fill="x", pady=(10, 0))
        Botao(manual, "Cronometrar um cadastro manual", self.cronometrar).pack(side="left")
        Botao(manual, "Ajustar a estimativa", self.ajustar, variante="discreto").pack(
            side="left", padx=(12, 0))

        # ---- sessões
        Texto(self, "Sessões", fonte="subtitulo").pack(fill="x", pady=(24, 8))
        self.tabela = Tabela(self, [
            ("data", "Data", 130, False), ("computador", "Computador", 150, True),
            ("pessoas", "Pessoas", 105, False), ("feitos", "Cadastrados", 140, False),
            ("erros", "Erros", 80, False), ("automacao", "Automação", 130, False),
            ("economia", "Economia", 130, False),
        ], altura=6)
        self.tabela.pack(fill="both", expand=True)

        # ---- dados de vários computadores
        Texto(self, "Juntar dados de vários computadores", fonte="subtitulo").pack(
            fill="x", pady=(24, 4))
        self.pasta = Texto(self, "", cor=e.TINTA_SUAVE, largura=90)
        self.pasta.pack(fill="x")
        dados = Quadro(self)
        dados.pack(fill="x", pady=(10, 0))
        Botao(dados, "Pasta da pesquisa…", self.escolher_pasta).pack(side="left")
        Botao(dados, "Trazer arquivos de outro computador…", self.importar).pack(
            side="left", padx=(12, 0))
        Botao(dados, "Abrir a pasta dos dados", self.abrir_dados, variante="discreto").pack(
            side="left", padx=(12, 0))

        self._mostrar_pasta(ajustes["pasta_pesquisa"])
        self.carregar()

    def barra(self, esquerda, direita):
        Botao(esquerda, "Voltar", self.app.voltar).pack(side="left")
        self.botao_relatorio = Botao(direita, "Gerar relatório", self.gerar_relatorio,
                                     variante="principal")
        self.botao_relatorio.pack(side="right")

    # ---- dados

    def mudar_escopo(self, escopo):
        self.escopo = escopo
        self.carregar()

    def carregar(self):
        self.situacao.configure(text="Carregando…")
        escopo = self.escopo

        def ler():
            sessoes, manuais = estatisticas.carregar(escopo)
            return sessoes, estatisticas.calcular(sessoes, manuais,
                                                  estatisticas.ler_ajustes()["estimativa"])

        self.trabalhador.fazer(ler, ok=self._mostrar, falha=self._falhou)

    def _mostrar(self, dados):
        if not self.winfo_exists():
            return

        sessoes, ind = dados
        def fmt(segundos):
            return estatisticas.formatar_duracao(segundos, curto=True)

        self.situacao.configure(
            text=f"{ind.sessoes} sessões · {ind.computadores} computador(es)" if ind.sessoes
            else "Ainda não há sessões registradas.")

        self.placar.mudar(0, ind.feitos)
        self.placar.mudar(1, fmt(ind.segundos_economizados) if ind.feitos else "-")
        self.placar.mudar(2, fmt(ind.media_manual_geral))
        self.placar.mudar(3, fmt(ind.media_automacao) if ind.feitos else "-")

        self.barras.mudar([
            ("À mão", ind.media_manual_geral, fmt(ind.media_manual_geral), "#8C9AB0"),
            ("Com a automação", ind.media_automacao,
             fmt(ind.media_automacao) if ind.feitos else "sem dados", e.VERDE),
        ])

        vezes = estatisticas.formatar_vezes(ind.vezes_mais_rapido)
        self.detalhe.configure(text=(
            f"{vezes} mais rápido  ·  {ind.contagem['JA']} já tinham cadastro  ·  "
            f"{ind.contagem['ERRO']} com erro  ·  {ind.taxa_sucesso:.0%} de sucesso"
            if ind.feitos else "Faça um cadastro com a automação para ver a comparação."))

        estimados = [estatisticas.ROTULO_CAMINHO[c].lower() for c in ind.amostras_manuais
                     if not ind.amostras_manuais[c]]
        if estimados:
            self.aviso_manual.mudar(
                "O tempo à mão ainda é uma estimativa para: " + "; ".join(estimados) +
                ". Cronometre alguns cadastros feitos à mão para ter o valor real.")
            self.aviso_manual.pack(fill="x", pady=(12, 0), after=self.detalhe)
        else:
            self.aviso_manual.pack_forget()

        self.tabela.limpar()
        for indice, sessao in enumerate(reversed(sessoes[-200:])):
            itens = sessao.get("itens", [])
            manual, automacao = estatisticas.economia_de(itens, ind.media_manual)
            feitos = sum(i.get("status") == "OK" for i in itens)
            erros = sum(i.get("status") == "ERRO" for i in itens)
            self.tabela.inserir(str(indice), (
                estatisticas.formatar_data(sessao.get("inicio", "")), sessao.get("computador", ""),
                len(itens), feitos, erros, fmt(automacao), fmt(manual - automacao) if feitos else "-",
            ), "OK" if feitos and not erros else ("ERRO" if erros else ""))

    def _mostrar_pasta(self, pasta):
        self.pasta.configure(text=(
            f"Pasta da pesquisa: {pasta}\nCada computador grava os seus dados nela "
            "automaticamente ao final de cada sessão." if pasta else
            "Nenhuma pasta da pesquisa escolhida. Escolha uma pasta da rede para juntar os "
            "dados de todos os computadores automaticamente, ou traga os arquivos de cada "
            "computador (pen drive ou e-mail)."))

    def _falhou(self, erro):
        self.situacao.configure(text=mensagem_de_erro(erro))

    # ---- ações

    def cronometrar(self):
        medido = dialogos.cronometrar(self.app.raiz)

        if not medido:
            return

        caminho, segundos = medido
        self.trabalhador.fazer(lambda: estatisticas.salvar_tempo_manual(caminho, segundos),
                               ok=lambda _: (self.carregar(), dialogos.recado(
                                   self.app.raiz, "Tempo guardado",
                                   f"Cadastro manual de {estatisticas.formatar_duracao(segundos)} "
                                   "guardado para a pesquisa. Obrigado!", "ok")),
                               falha=self._falhou)

    def ajustar(self):
        ajustes = estatisticas.ler_ajustes()
        novo = dialogos.ajustar_estimativa(self.app.raiz, ajustes["estimativa"])

        if novo:
            ajustes["estimativa"] = novo
            estatisticas.gravar_ajustes(ajustes)
            self.carregar()

    def escolher_pasta(self):
        ajustes = estatisticas.ler_ajustes()
        atual = ajustes["pasta_pesquisa"]

        if atual:
            decisao = dialogos.recado(
                self.app.raiz, "Pasta da pesquisa", f"A pasta atual é:\n{atual}", "info",
                botoes=(("Parar de usar", "parar", "discreto"),
                        ("Escolher outra", "outra", "secundario"),
                        ("Manter", None, "principal")))
            if decisao is None:
                return
            if decisao == "parar":
                ajustes["pasta_pesquisa"] = ""
                estatisticas.gravar_ajustes(ajustes)
                self._mostrar_pasta("")
                return

        pasta = filedialog.askdirectory(parent=self.app.raiz, title="Escolha a pasta da pesquisa",
                                        mustexist=True)
        if not pasta:
            return

        ajustes["pasta_pesquisa"] = os.path.normpath(pasta)
        estatisticas.gravar_ajustes(ajustes)
        self._mostrar_pasta(ajustes["pasta_pesquisa"])

        def pronto(copiou):
            if not copiou and estatisticas.arquivo_local().exists():
                dialogos.recado(self.app.raiz, "Não consegui gravar na pasta",
                                "Confira se você tem permissão para gravar nessa pasta da rede.",
                                "erro")
            self.carregar()

        self.trabalhador.fazer(estatisticas.sincronizar, ok=pronto, falha=self._falhou)

    def importar(self):
        arquivos = filedialog.askopenfilenames(
            parent=self.app.raiz, title="Arquivos de dados de outros computadores",
            filetypes=[("Dados da pesquisa", "*.jsonl"), ("Todos os arquivos", "*.*")])

        if not arquivos:
            return

        def pronto(total):
            dialogos.recado(self.app.raiz, "Dados juntados",
                            f"{total} arquivo(s) de outros computadores foram juntados. Eles "
                            "aparecem em Todos os computadores.", "ok")
            if self.alternador.valor == estatisticas.TODOS:
                self.carregar()
            else:
                self.alternador.marcar(estatisticas.TODOS)

        self.trabalhador.fazer(lambda: estatisticas.importar_arquivos(arquivos), ok=pronto,
                               falha=self._falhou)

    def abrir_dados(self):
        e.abrir_pasta(estatisticas.PASTA_ESTATISTICAS)

    def gerar_relatorio(self):
        self.botao_relatorio.ativar(False)
        self.botao_relatorio.configure(text="Gerando…")
        escopo = self.escopo

        def pronto(pasta):
            self.botao_relatorio.ativar(True)
            self.botao_relatorio.configure(text="Gerar relatório")
            e.abrir_pasta(pasta)
            dialogos.recado(self.app.raiz, "Relatório pronto",
                            f"O relatório foi salvo em:\n{pasta}\n\n"
                            "• dados_pesquisa.xlsx: planilha com todos os números\n"
                            "• relatorio.html: página para apresentar (abre no navegador)\n"
                            "• dados_brutos.jsonl: dados para juntar com outros computadores",
                            "ok")

        def falhou(erro):
            self.botao_relatorio.ativar(True)
            self.botao_relatorio.configure(text="Gerar relatório")
            dialogos.recado(self.app.raiz, "Não consegui gerar o relatório",
                            mensagem_de_erro(erro), "erro")

        self.trabalhador.fazer(lambda: relatorio.gerar(escopo), ok=pronto, falha=falhou)
