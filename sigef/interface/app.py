"""Janela principal: faixa do topo, trilha de passos, conteúdo e barra de botões."""

import sys
import tkinter as tk

from .. import __version__
from ..log import configurar_log, garantir_saidas, logger
from . import dialogos
from . import estilo as e
from .componentes import Barras, Botao, Quadro, Rolagem, Texto
from .telas import PASSOS, TelaCadastro, TelaEstatisticas, TelaInicio
from .trabalhador import Trabalhador

NOME = "Cadastro de Credores no SIGEF"


class Trilha(tk.Canvas):
    """Os 4 passos no topo: feito (verde ✔), atual (amarelo) e próximos (contorno)."""

    def __init__(self, pai, tema):
        super().__init__(pai, bg=e.SUPERFICIE, highlightthickness=0, bd=0)
        self.tema = tema
        self.atual = 0
        self.bind("<Configure>", lambda _: self.desenhar())

    def marcar(self, passo: int) -> None:
        self.atual = passo
        self.desenhar()

    def desenhar(self) -> None:
        self.delete("all")
        fonte, forte = self.tema["passo"], self.tema["forte"]
        raio = round(18 * self.tema.escala)
        altura = raio * 2 + forte.metrics("linespace") + 30
        self.configure(height=altura)

        largura = max(self.winfo_width(), 400)
        meia_etiqueta = max(forte.measure(nome) for nome in PASSOS) // 2
        margem = 56 + max(raio, meia_etiqueta)
        espaco = (largura - 2 * margem) / (len(PASSOS) - 1)
        y = raio + 12

        for indice in range(len(PASSOS) - 1):
            x1, x2 = margem + indice * espaco + raio + 8, margem + (indice + 1) * espaco - raio - 8
            feito = indice + 1 < self.atual
            self.create_line(x1, y, x2, y, fill=e.VERDE if feito else e.BORDA, width=4)

        for indice, nome in enumerate(PASSOS, 1):
            x = margem + (indice - 1) * espaco

            if indice < self.atual:
                fundo, borda, cor, texto = e.VERDE, e.VERDE, "white", "✔"
            elif indice == self.atual:
                fundo, borda, cor, texto = e.AMARELO, e.TINTA, e.TINTA, str(indice)
            else:
                fundo, borda, cor, texto = e.SUPERFICIE, e.BORDA, e.TINTA_SUAVE, str(indice)

            self.create_oval(x - raio, y - raio, x + raio, y + raio, fill=fundo, outline=borda,
                             width=3)
            self.create_text(x, y, text=texto, fill=cor, font=fonte)
            self.create_text(x, y + raio + 10, text=nome, anchor="n",
                             fill=e.TINTA if indice <= self.atual else e.TINTA_SUAVE,
                             font=forte if indice == self.atual else self.tema["texto"])


class App:
    def __init__(self):
        garantir_saidas()
        configurar_log()
        logger.info("Início da execução (janela) v%s", __version__)
        e.preparar_processo()

        self.raiz = raiz = tk.Tk()
        raiz.title(NOME)
        raiz.configure(bg=e.FUNDO)
        raiz.tema = e.Tema(raiz)
        raiz.minsize(960, 640)
        self._maximizar()
        self._icone()

        self.trabalhador = Trabalhador(raiz)
        self.tela = None
        self.cadastrando = False
        self.lotes = []           # lista digitada (mantida ao voltar de tela)
        self.conferencia = "auto"
        self.refazer = None       # itens com erro do último cadastro (só na memória)
        self.retorno = (TelaInicio, {})  # para onde o Voltar das estatísticas leva

        self._montar_topo()
        self.trilha = Trilha(raiz, raiz.tema)
        self.trilha.pack(fill="x")
        tk.Frame(raiz, bg=e.BORDA, height=1).pack(fill="x")

        self.barra = Quadro(raiz, fundo=e.SUPERFICIE, padx=56, pady=12)
        self.barra.pack(side="bottom", fill="x")
        tk.Frame(raiz, bg=e.BORDA, height=1).pack(side="bottom", fill="x")

        self.rolagem = Rolagem(raiz)
        self.rolagem.pack(fill="both", expand=True)

        raiz.protocol("WM_DELETE_WINDOW", self.sair)
        raiz.bind_all("<Control-plus>", lambda _: self.mudar_letra(1))
        raiz.bind_all("<Control-equal>", lambda _: self.mudar_letra(1))
        raiz.bind_all("<Control-minus>", lambda _: self.mudar_letra(-1))
        raiz.bind_all("<F1>", lambda _: self.mostrar_ajuda())
        raiz.report_callback_exception = self._erro_inesperado

        self.ir(TelaInicio)

    # ------------------------------------------------------------ montagem

    def _maximizar(self) -> None:
        try:
            if sys.platform == "win32":
                self.raiz.state("zoomed")
            else:
                largura = min(1280, self.raiz.winfo_screenwidth())
                altura = min(800, self.raiz.winfo_screenheight() - 30)
                self.raiz.geometry(f"{largura}x{altura}+0+0")
        except tk.TclError:
            pass

    def _icone(self) -> None:
        icone = e.PASTA_FONTES.parent / "icone.png"

        if icone.exists():
            try:
                self.raiz.iconphoto(True, tk.PhotoImage(file=str(icone)))
            except tk.TclError:
                pass

    def _montar_topo(self) -> None:
        topo = Quadro(self.raiz, fundo=e.AZUL, padx=56, pady=10)
        topo.pack(fill="x")
        tk.Label(topo, text=NOME, font=self.raiz.tema["subtitulo"], fg="white",
                 bg=e.AZUL).pack(side="left")

        pequeno = self.raiz.tema["forte"]
        Botao(topo, "Ajuda", self.mostrar_ajuda, variante="topo", fonte=pequeno,
              padx=16, pady=6).pack(side="right")
        Botao(topo, "Estatísticas", self.abrir_estatisticas, variante="topo", fonte=pequeno,
              padx=16, pady=6).pack(side="right", padx=(0, 8))
        Botao(topo, "A+  Letra maior", lambda: self.mudar_letra(1), variante="topo",
              fonte=pequeno, padx=16, pady=6).pack(side="right", padx=(0, 8))
        Botao(topo, "A−  Letra menor", lambda: self.mudar_letra(-1), variante="topo",
              fonte=pequeno, padx=16, pady=6).pack(side="right", padx=(0, 8))

    # ------------------------------------------------------------ navegação

    def ir(self, classe, **dados) -> None:
        """Troca a tela atual (e os botões da barra de baixo)."""
        if self.tela is not None:
            self.tela.ao_sair()
            self.tela.destroy()

        for widget in self.barra.winfo_children():
            widget.destroy()

        self.raiz.configure(cursor="")
        self.rolagem.topo()
        self.trilha.marcar(classe.passo)

        esquerda, direita = Quadro(self.barra), Quadro(self.barra)
        esquerda.pack(side="left")
        direita.pack(side="right")

        if classe.retornavel:
            self.retorno = (classe, dados)

        self.tela = classe(self, **dados)
        self.tela.pack(fill="both", expand=True)
        self.tela.barra(esquerda, direita)
        logger.info("Tela: %s", classe.__name__)

    def abrir_estatisticas(self) -> None:
        if self.cadastrando:
            dialogos.recado(self.raiz, "Espere o cadastro terminar",
                            "As estatísticas podem ser vistas quando o cadastro terminar.")
            return

        if not isinstance(self.tela, TelaEstatisticas):
            self.ir(TelaEstatisticas)

    def refazer_erros(self) -> None:
        """Cadastra de novo só as pessoas que deram erro no último cadastro completo."""
        if self.refazer:
            dados = {chave: valor for chave, valor in self.refazer.items() if chave != "chaves"}
            self.ir(TelaCadastro, **dados)

    def voltar(self) -> None:
        classe, dados = self.retorno
        self.ir(classe, **dados)

    def mudar_letra(self, passo: int) -> None:
        if not self.raiz.tema.mudar_escala(passo):
            return

        pilha = [self.raiz]

        while pilha:
            widget = pilha.pop()

            if isinstance(widget, Texto):
                widget.atualizar_quebra()
            elif isinstance(widget, Barras):
                widget.desenhar()

            pilha.extend(widget.winfo_children())

        self.trilha.desenhar()

    def mostrar_ajuda(self) -> None:
        texto = (self.tela.ajuda if self.tela and self.tela.ajuda else
                 "Siga as instruções escritas na tela e clique no botão verde.")
        dialogos.recado(self.raiz, "Ajuda", texto + "\n\nDica: os botões Letra maior e Letra "
                        "menor, no alto da janela, mudam o tamanho das letras.")

    def sair(self) -> None:
        if self.cadastrando and not dialogos.recado(
            self.raiz, "Sair do programa?",
            "O cadastro ainda está acontecendo. Se você sair agora, a pessoa atual pode ficar "
            "pela metade no SIGEF.", "atencao",
            botoes=(("Sair mesmo assim", True, "perigo"), ("Continuar o cadastro", False,
                                                          "principal")),
        ):
            return

        logger.info("Fim da execução (janela)")
        self.trabalhador.encerrar()
        self.raiz.destroy()

    def _erro_inesperado(self, tipo, valor, rastro) -> None:
        logger.error("Erro na janela", exc_info=(tipo, valor, rastro))
        dialogos.recado(self.raiz, "Algo deu errado",
                        f"{valor}\n\nO problema foi anotado na pasta de registros.", "erro")

    def executar(self) -> None:
        self.raiz.mainloop()


def _fechar_abertura() -> None:
    """Fecha a tela "Abrindo o programa…" do executável (não existe fora dele)."""
    try:
        import pyi_splash

        pyi_splash.close()
    except Exception:
        pass


def _ja_aberto() -> bool:
    """Evita duas cópias abertas (comum quando o clique duplo demora a responder)."""
    if sys.platform != "win32":
        return False

    import ctypes

    iniciar._trava = ctypes.windll.kernel32.CreateMutexW(None, False, "CadastroSIGEF.Unico")
    return ctypes.windll.kernel32.GetLastError() == 183  # ERROR_ALREADY_EXISTS


def iniciar() -> None:
    if _ja_aberto():
        _fechar_abertura()
        from tkinter import messagebox

        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showinfo(NOME, "O programa já está aberto.\n\n"
                                  "Procure a janela dele na barra de tarefas, embaixo da tela.")
        raiz.destroy()
        return

    app = App()
    _fechar_abertura()
    app.executar()
