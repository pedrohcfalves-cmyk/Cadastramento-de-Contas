"""Janelas de diálogo: conferência antes de gravar, correção, colar lista e recados."""

import tkinter as tk

from ..automacao import CONFIRMAR_DOMICILIO, INCLUIR_CREDOR
from ..bancos import descrever_banco
from ..modelos import ROTULOS, Lote, Resposta, limpar, lotes_de_texto
from . import estilo as e
from .componentes import Botao, Caixa, Campo, Quadro, Texto, formatar_cpf

# O que cada ação significa, em palavras simples
PERGUNTAS = {
    INCLUIR_CREDOR: "Cadastrar esta pessoa como credor no SIGEF?",
    CONFIRMAR_DOMICILIO: "Gravar a conta bancária desta pessoa no SIGEF?",
}

# Dicas de cada campo nos formulários
DICAS = {
    "cpf": "Pode digitar com ou sem pontos. Ex.: 529.982.247-25",
    "nome": "Nome completo, como está no documento.",
    "banco": "Código ou nome. Ex.: 001 ou Banco do Brasil",
    "agencia": "Números da agência. Se terminar em X, digite o X.",
    "conta": "Número da conta com o dígito. Pode ser X. Ex.: 12345-X",
}
ROTULOS_SIMPLES = {
    "cpf": "CPF", "nome": "Nome", "banco": "Banco", "agencia": "Agência", "conta": "Conta",
}


class Dialogo(tk.Toplevel):
    """Janela modal centralizada sobre a principal, sempre à frente."""

    def __init__(self, raiz, titulo: str):
        super().__init__(raiz, bg=e.FUNDO)
        self.tema = raiz.tema
        self.resposta = None
        self.title(titulo)
        self.transient(raiz)
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.fechar)

        self.corpo = Quadro(self, padx=36, pady=28)
        self.corpo.pack(fill="both", expand=True)

    def responder(self, valor) -> None:
        self.resposta = valor
        self.destroy()

    def fechar(self) -> None:
        self.destroy()

    def mostrar(self, foco=None):
        self.update_idletasks()
        raiz = self.master
        largura, altura = self.winfo_reqwidth(), self.winfo_reqheight()
        x = raiz.winfo_rootx() + max((raiz.winfo_width() - largura) // 2, 0)
        y = raiz.winfo_rooty() + max((raiz.winfo_height() - altura) // 3, 0)
        self.geometry(f"+{x}+{y}")

        # Traz para a frente mesmo se a pessoa estiver olhando o navegador
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.after(600, lambda: self.winfo_exists() and self.attributes("-topmost", False))
        self.grab_set()
        (foco or self).focus_force()
        self.bell()
        self.wait_window()
        return self.resposta


def _dados_da_pessoa(pai, lote: Lote) -> Quadro:
    quadro = Quadro(pai, fundo=e.SUPERFICIE, padx=24, pady=16,
                    highlightthickness=1, highlightbackground=e.BORDA)
    valores = {
        "nome": lote.nome,
        "cpf": formatar_cpf(lote.cpf),
        "banco": descrever_banco(lote.banco),
        "agencia": lote.agencia,
        "conta": lote.conta,
    }

    for linha, (campo, valor) in enumerate(valores.items()):
        tk.Label(quadro, text=ROTULOS_SIMPLES[campo], font=quadro.tema["texto"],
                 fg=e.TINTA_SUAVE, bg=e.SUPERFICIE, anchor="w").grid(
            row=linha, column=0, sticky="w", padx=(0, 28), pady=4)
        tk.Label(quadro, text=valor, font=quadro.tema["subtitulo"], fg=e.TINTA,
                 bg=e.SUPERFICIE, anchor="w").grid(row=linha, column=1, sticky="w", pady=4)

    return quadro


def conferir(raiz, lote: Lote, acao: str, editavel: bool) -> Resposta:
    """Mostra os dados antes do clique que grava no SIGEF e devolve a decisão."""
    dialogo = Dialogo(raiz, "Confira antes de gravar")
    corpo = dialogo.corpo

    Texto(corpo, PERGUNTAS.get(acao, acao), fonte="titulo", largura=40).pack(anchor="w")
    Texto(corpo, "Confira com atenção. Nada é gravado até você responder.",
          cor=e.TINTA_SUAVE).pack(anchor="w", pady=(4, 16))
    _dados_da_pessoa(corpo, lote).pack(fill="x", pady=(0, 20))

    sim = Botao(corpo, "Sim, está certo", lambda: dialogo.responder(Resposta.SIM),
                variante="principal")
    sim.pack(fill="x", pady=4)
    Botao(corpo, "Sim, e não perguntar mais sobre esta pessoa",
          lambda: dialogo.responder(Resposta.SIM_TODOS)).pack(fill="x", pady=4)

    if editavel:
        Botao(corpo, "Corrigir os dados",
              lambda: dialogo.responder(Resposta.CORRIGIR)).pack(fill="x", pady=4)

    Botao(corpo, "Pular esta pessoa", lambda: dialogo.responder(Resposta.PULAR),
          variante="discreto").pack(fill="x", pady=(12, 0))

    # Fechar no X equivale a pular: nada é gravado sem um "sim" explícito
    dialogo.fechar = lambda: dialogo.responder(Resposta.PULAR)
    dialogo.protocol("WM_DELETE_WINDOW", dialogo.fechar)
    return dialogo.mostrar(foco=sim) or Resposta.PULAR


class Formulario(Quadro):
    """Os cinco campos de uma pessoa, com validação e dica de banco reconhecido."""

    def __init__(self, pai, colunas: int = 1, largura: int = 26):
        super().__init__(pai)
        self.campos = {}

        for posicao, campo in enumerate(ROTULOS):
            caixa = Campo(self, ROTULOS_SIMPLES[campo], DICAS[campo], largura=largura)
            caixa.grid(row=posicao // colunas, column=posicao % colunas,
                       sticky="ew", padx=(0, 24), pady=6)
            self.campos[campo] = caixa

        for coluna in range(colunas):
            self.columnconfigure(coluna, weight=1)

        banco = self.campos["banco"]
        banco.variavel.trace_add("write", lambda *_: self._mostrar_banco())

        # Enter passa para o próximo campo, como numa ficha de papel
        ordem = list(self.campos.values())
        for atual, proximo in zip(ordem, ordem[1:]):
            atual.entrada.bind("<Return>", lambda _, p=proximo: p.entrada.focus_set())

    def _mostrar_banco(self) -> None:
        caixa = self.campos["banco"]

        if not caixa.valor:
            caixa.avisar("")
            return

        codigo = limpar("banco", caixa.valor)

        if codigo:
            caixa.avisar(f"✔ {descrever_banco(codigo)}")
        else:
            caixa.avisar("Banco não reconhecido. Digite o código (ex.: 001).", problema=True)

    def preencher(self, lote: Lote) -> None:
        for campo, caixa in self.campos.items():
            caixa.valor = getattr(lote, campo)

    def limpar(self) -> None:
        for caixa in self.campos.values():
            caixa.valor = ""
            caixa.avisar("")

        self.focar()

    def focar(self) -> None:
        self.campos["cpf"].entrada.focus_set()

    def ler(self):
        """Devolve (Lote, cpf_suspeito) ou None, marcando em vermelho o que falta."""
        lote, ok = Lote(), True

        for campo, caixa in self.campos.items():
            valor = limpar(campo, caixa.valor)
            setattr(lote, campo, valor)

            if not valor:
                ok = False
                motivo = ("Banco não reconhecido. Digite o código (ex.: 001)."
                          if campo == "banco" and caixa.valor else "Preencha este campo.")
                caixa.avisar(motivo, problema=True)
            elif campo == "cpf" and len(valor) != 11:
                ok = False
                caixa.avisar("O CPF precisa ter 11 números.", problema=True)
            elif campo != "banco":
                caixa.avisar("")

        return lote if ok else None


def corrigir(raiz, lote: Lote) -> bool:
    """Edita os dados de uma pessoa reprovada na conferência. False = pular."""
    dialogo = Dialogo(raiz, "Corrigir os dados")
    corpo = dialogo.corpo

    Texto(corpo, "Corrija os dados desta pessoa", fonte="titulo").pack(anchor="w")
    Texto(corpo, "Depois clique em Salvar e tentar de novo. O cadastro desta pessoa "
                 "recomeça do início.", cor=e.TINTA_SUAVE).pack(anchor="w", pady=(4, 12))

    formulario = Formulario(corpo, colunas=2)
    formulario.preencher(lote)
    formulario.pack(fill="x")

    def salvar():
        novo = formulario.ler()

        if novo:
            for campo in ROTULOS:
                setattr(lote, campo, getattr(novo, campo))

            dialogo.responder(True)

    barra = Quadro(corpo)
    barra.pack(fill="x", pady=(20, 0))
    Botao(barra, "Pular esta pessoa", lambda: dialogo.responder(False),
          variante="discreto").pack(side="left")
    Botao(barra, "Salvar e tentar de novo", salvar, variante="principal").pack(side="right")
    return bool(dialogo.mostrar(foco=formulario.campos["cpf"].entrada))


def colar_lista(raiz) -> list:
    """Caixa para colar várias pessoas de uma vez (do Excel ou de um texto)."""
    dialogo = Dialogo(raiz, "Colar uma lista")
    corpo = dialogo.corpo

    Texto(corpo, "Cole a lista de pessoas", fonte="titulo").pack(anchor="w")
    Texto(corpo, "Uma pessoa por linha, nesta ordem: CPF, Nome, Banco, Agência, Conta. "
                 "Pode copiar direto do Excel (as colunas nessa ordem) ou separar com ponto e "
                 "vírgula.", cor=e.TINTA_SUAVE).pack(anchor="w", pady=(4, 8))
    Texto(corpo, "Exemplo:  529.982.247-25; Maria da Silva; 001; 1234; 56789-0",
          fonte="forte").pack(anchor="w", pady=(0, 8))

    caixa = tk.Text(corpo, font=dialogo.tema["texto"], height=9, width=64, wrap="none",
                    relief="solid", bd=1, highlightthickness=3, highlightcolor=e.AMARELO,
                    highlightbackground=e.BORDA, bg=e.SUPERFICIE, fg=e.TINTA, insertwidth=3)
    caixa.pack(fill="both", expand=True)
    aviso = Caixa(corpo, "", tipo="erro", largura=64)

    def adicionar():
        lotes, ignoradas = lotes_de_texto(caixa.get("1.0", "end"))

        if ignoradas and not getattr(adicionar, "avisado", False):
            linhas = "\n".join(f"Linha {n}: {motivo}" for n, motivo in ignoradas[:6])
            mais = f"\n… e mais {len(ignoradas) - 6}" if len(ignoradas) > 6 else ""
            aviso.mudar(f"{len(ignoradas)} linha(s) com problema não serão adicionadas:\n"
                        f"{linhas}{mais}\n\nCorrija e clique de novo, ou clique em "
                        f"Adicionar mesmo assim.")
            aviso.pack(fill="x", pady=(12, 0))
            botao.configure(text="Adicionar mesmo assim")
            adicionar.avisado = True
            return

        dialogo.responder(lotes)

    barra = Quadro(corpo)
    barra.pack(fill="x", side="bottom", pady=(20, 0))
    Botao(barra, "Cancelar", dialogo.fechar, variante="discreto").pack(side="left")
    botao = Botao(barra, "Adicionar à lista", adicionar, variante="principal")
    botao.pack(side="right")
    return dialogo.mostrar(foco=caixa) or []


def recado(raiz, titulo: str, texto: str, tipo: str = "info",
           botoes=(("Entendi", True, "principal"),)):
    """Mensagem simples com um ou mais botões; devolve o valor do botão clicado."""
    dialogo = Dialogo(raiz, titulo)
    corpo = dialogo.corpo

    Texto(corpo, titulo, fonte="titulo", largura=44).pack(anchor="w", pady=(0, 12))
    Caixa(corpo, texto, tipo=tipo, largura=56).pack(fill="x")

    barra = Quadro(corpo)
    barra.pack(fill="x", pady=(24, 0))
    foco = None

    for rotulo, valor, variante in reversed(botoes):
        botao = Botao(barra, rotulo, lambda v=valor: dialogo.responder(v), variante=variante)
        botao.pack(side="right", padx=(12, 0))

        if variante == "principal" or foco is None:
            foco = botao

    return dialogo.mostrar(foco=foco)


# ================================================================ estatísticas

TIPOS_CADASTRO = (
    ("novo", "Credor novo + conta bancária",
     "A pessoa ainda não existe no SIGEF: cadastrar o credor e depois a conta."),
    ("existente", "Só a conta bancária",
     "A pessoa já é credora no SIGEF: só incluir o domicílio bancário."),
)


def _relogio(segundos: float) -> str:
    minutos, seg = divmod(int(segundos), 60)
    return f"{minutos:02d}:{seg:02d}"


def cronometrar(raiz):
    """Cronômetro de um cadastro feito à mão. Devolve (tipo, segundos) ou None."""
    import time

    from .componentes import Escolha

    dialogo = Dialogo(raiz, "Cronometrar um cadastro manual")
    corpo = dialogo.corpo
    estado = {"inicio": None, "agendado": None}

    Texto(corpo, "Cronometrar um cadastro feito à mão", fonte="titulo", largura=40).pack(anchor="w")
    for numero, passo in enumerate((
        "Escolha o tipo de cadastro que você vai fazer.",
        "Clique em Começar e faça o cadastro no SIGEF do jeito de sempre, à mão.",
        "Quando terminar, volte aqui e clique em Terminei.",
    ), 1):
        Texto(corpo, f"{numero}.  {passo}", largura=56).pack(anchor="w", pady=2)

    tipo = Escolha(corpo, TIPOS_CADASTRO, "novo")
    tipo.pack(fill="x", pady=(14, 10))

    mostrador = tk.Label(corpo, text="00:00", font=dialogo.tema["numero"], fg=e.AZUL, bg=e.FUNDO)
    mostrador.pack(pady=(4, 4))
    situacao = Texto(corpo, "O cronômetro ainda não começou.", cor=e.TINTA_SUAVE, largura=56)
    situacao.pack(pady=(0, 14))

    def contar():
        mostrador.configure(text=_relogio(time.perf_counter() - estado["inicio"]))
        estado["agendado"] = dialogo.after(500, contar)

    def comecar():
        if estado["inicio"] is None:
            estado["inicio"] = time.perf_counter()
            situacao.configure(text="Contando… faça o cadastro no SIGEF e depois clique em Terminei.")
            botao.configure(text="Terminei")
            contar()
            return

        segundos = time.perf_counter() - estado["inicio"]
        dialogo.after_cancel(estado["agendado"])

        if not 20 <= segundos <= 1800:
            guardar = recado(raiz, "Confira o tempo",
                             f"O tempo medido foi {_relogio(segundos)}. Parece muito "
                             f"{'curto' if segundos < 20 else 'longo'} para um cadastro. "
                             "Quer guardar mesmo assim?", "atencao",
                             botoes=(("Não guardar", False, "secundario"),
                                     ("Guardar mesmo assim", True, "principal")))
            if not guardar:
                dialogo.responder(None)
                return

        dialogo.responder((tipo.valor, segundos))

    barra = Quadro(corpo)
    barra.pack(fill="x", pady=(8, 0))
    Botao(barra, "Cancelar", dialogo.fechar, variante="discreto").pack(side="left")
    botao = Botao(barra, "Começar", comecar, variante="principal")
    botao.pack(side="right")
    return dialogo.mostrar(foco=botao)


def _ler_minutos(texto: str):
    """'4' -> 240; '4,5' -> 270; '4:30' -> 270. None se inválido."""
    texto = texto.strip().replace(",", ".")

    try:
        if ":" in texto:
            minutos, segundos = texto.split(":", 1)
            valor = int(minutos or 0) * 60 + int(segundos or 0)
        else:
            valor = float(texto) * 60
    except ValueError:
        return None

    return valor if valor > 0 else None


def _escrever_minutos(segundos: float) -> str:
    minutos, seg = divmod(int(round(segundos)), 60)
    return f"{minutos}:{seg:02d}"


def ajustar_estimativa(raiz, estimativa: dict):
    """Tempo manual estimado (usado só enquanto não houver cronometragens)."""
    dialogo = Dialogo(raiz, "Tempo manual estimado")
    corpo = dialogo.corpo

    Texto(corpo, "Quanto tempo leva um cadastro feito à mão?", fonte="titulo",
          largura=40).pack(anchor="w")
    Texto(corpo, "Use minutos. Exemplos: 5  ou  4:30  (4 minutos e 30 segundos). Este valor só "
                 "é usado enquanto ninguém tiver cronometrado cadastros manuais.",
          cor=e.TINTA_SUAVE, largura=56).pack(anchor="w", pady=(4, 12))

    campos = {}
    for chave, titulo, descricao in TIPOS_CADASTRO:
        campo = Campo(corpo, titulo, descricao, largura=12)
        campo.valor = _escrever_minutos(estimativa[chave])
        campo.pack(fill="x", pady=6)
        campos[chave] = campo

    def salvar():
        novo = {}

        for chave, campo in campos.items():
            valor = _ler_minutos(campo.valor)

            if valor is None:
                campo.avisar("Digite os minutos. Exemplo: 5 ou 4:30", problema=True)
                return

            novo[chave] = valor

        dialogo.responder(novo)

    barra = Quadro(corpo)
    barra.pack(fill="x", pady=(18, 0))
    Botao(barra, "Cancelar", dialogo.fechar, variante="discreto").pack(side="left")
    Botao(barra, "Salvar", salvar, variante="principal").pack(side="right")
    return dialogo.mostrar(foco=campos["novo"].entrada)
