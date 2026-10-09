"""Peças reutilizáveis da janela: botões, caixas de aviso, escolhas e listas."""

import tkinter as tk
from tkinter import ttk

from . import estilo as e

# Variações de botão: (fundo, texto, fundo ao passar o mouse, borda)
VARIANTES = {
    "principal": (e.VERDE, "white", e.VERDE_ESCURO, e.VERDE_ESCURO),
    "perigo": (e.VERMELHO, "white", e.VERMELHO_ESCURO, e.VERMELHO_ESCURO),
    "secundario": (e.SUPERFICIE, e.TINTA, e.AZUL_CLARO, e.AZUL),
    "discreto": (e.FUNDO, e.AZUL, e.AZUL_CLARO, e.FUNDO),
    "topo": (e.AZUL, "white", "#08306F", e.AZUL),
}


class Botao(tk.Frame):
    """Botão grande e plano, com borda e foco do teclado bem visíveis (contorno amarelo).

    Feito com Frame + Label porque o botão nativo do Windows ignora a cor da borda.
    """

    def __init__(self, pai, texto: str, comando=None, variante: str = "secundario",
                 fonte=None, padx: int = 26, pady: int = 12):
        self._fundo, self._cor, self._sobre, self._borda = VARIANTES[variante]
        super().__init__(pai, bg=self._borda, padx=3, pady=3)
        self.tema = pai.tema
        self._comando = comando
        self._ativo = True

        self.rotulo = rotulo = tk.Label(
            self, text=texto, font=fonte or pai.tema["botao"], bg=self._fundo, fg=self._cor,
            padx=padx, pady=pady, cursor="hand2", takefocus=True,
        )
        rotulo.pack(fill="both", expand=True)
        rotulo.bind("<Enter>", lambda _: self._pintar(self._sobre))
        rotulo.bind("<Leave>", lambda _: self._pintar(self._fundo))
        rotulo.bind("<ButtonRelease-1>", self._soltar)
        rotulo.bind("<Return>", lambda _: self.invoke())
        rotulo.bind("<space>", lambda _: self.invoke())
        rotulo.bind("<FocusIn>", lambda _: tk.Frame.configure(self, bg=e.AMARELO))
        rotulo.bind("<FocusOut>", lambda _: tk.Frame.configure(self, bg=self._borda))

    def _pintar(self, cor: str) -> None:
        if self._ativo:
            self.rotulo.configure(bg=cor)

    def _soltar(self, evento) -> None:
        # Só conta o clique se o mouse foi solto em cima do botão
        if 0 <= evento.x < self.rotulo.winfo_width() and 0 <= evento.y < self.rotulo.winfo_height():
            self.invoke()

    def invoke(self):
        if self._ativo and self._comando:
            return self._comando()

        return None

    def ativar(self, ligado: bool = True) -> None:
        self._ativo = ligado
        self.rotulo.configure(bg=self._fundo if ligado else e.CINZA_CLARO,
                              fg=self._cor if ligado else "#5F6B7E",
                              cursor="hand2" if ligado else "arrow")

    def cget(self, chave):
        if chave == "text":
            return self.rotulo.cget("text")

        if chave == "state":
            return "normal" if self._ativo else "disabled"

        return super().cget(chave)

    def configure(self, cnf=None, **opcoes):
        if "text" in opcoes:
            self.rotulo.configure(text=opcoes.pop("text"))

        if "state" in opcoes:
            self.ativar(opcoes.pop("state") != "disabled")

        return super().configure(cnf, **opcoes) if (cnf or opcoes) else None

    config = configure

    def focus_set(self):
        self.rotulo.focus_set()

    def focus_force(self):
        self.rotulo.focus_force()


class Texto(tk.Label):
    """Parágrafo com quebra automática de linha (até ~70 caracteres por linha)."""

    def __init__(self, pai, texto: str = "", fonte: str = "texto", cor: str = e.TINTA,
                 largura: int = 70, fundo=None, **opcoes):
        self._fonte_nome = fonte
        self._largura = largura
        super().__init__(pai, text=texto, font=pai.tema[fonte], fg=cor,
                         bg=fundo or pai["bg"], justify="left", anchor="w", **opcoes)
        self.atualizar_quebra()

    def atualizar_quebra(self) -> None:
        fonte = self.master.tema[self._fonte_nome]
        self.configure(wraplength=fonte.measure("n") * self._largura)


class Quadro(tk.Frame):
    """Frame que conhece o tema (todos os filhos herdam `tema`)."""

    def __init__(self, pai, fundo=None, **opcoes):
        super().__init__(pai, bg=fundo or pai["bg"], **opcoes)
        self.tema = pai.tema


class Caixa(Quadro):
    """Caixa de recado com faixa colorida à esquerda: informação, atenção ou problema."""

    TIPOS = {
        "info": (e.AZUL_CLARO, e.AZUL),
        "atencao": (e.AMARELO_CLARO, "#B58A00"),
        "erro": (e.VERMELHO_CLARO, e.VERMELHO),
        "ok": (e.VERDE_CLARO, e.VERDE),
    }

    def __init__(self, pai, texto: str = "", tipo: str = "info", largura: int = 70):
        fundo, faixa = self.TIPOS[tipo]
        super().__init__(pai, fundo=fundo)
        self.faixa = tk.Frame(self, bg=faixa, width=8)
        self.faixa.pack(side="left", fill="y")
        self.texto = Texto(self, texto, fundo=fundo, largura=largura, padx=16, pady=12)
        self.texto.pack(side="left", fill="x", expand=True)

    def mudar(self, texto: str, tipo: str = None) -> None:
        if tipo:
            fundo, faixa = self.TIPOS[tipo]
            self.configure(bg=fundo)
            self.faixa.configure(bg=faixa)
            self.texto.configure(bg=fundo)

        self.texto.configure(text=texto)


class Escolha(Quadro):
    """Opções grandes e excludentes; a escolhida fica marcada com contorno azul e ✔."""

    def __init__(self, pai, opcoes: list, valor_inicial=None, ao_mudar=None):
        super().__init__(pai)
        self.variavel = tk.StringVar(value=valor_inicial if valor_inicial is not None
                                     else opcoes[0][0])
        self.ao_mudar = ao_mudar
        self.botoes = {}

        for valor, titulo, descricao in opcoes:
            botao = tk.Label(
                self, font=self.tema["texto"], justify="left", anchor="w", padx=18, pady=12,
                cursor="hand2", takefocus=True, highlightthickness=3, bd=0,
            )
            botao.pack(fill="x", pady=4)
            botao.bind("<Button-1>", lambda _, v=valor: self.marcar(v))
            botao.bind("<space>", lambda _, v=valor: self.marcar(v))
            botao.bind("<Return>", lambda _, v=valor: self.marcar(v))
            self.botoes[valor] = (botao, titulo, descricao)

        self._pintar()

    @property
    def valor(self) -> str:
        return self.variavel.get()

    def marcar(self, valor: str) -> None:
        self.variavel.set(valor)
        self._pintar()

        if self.ao_mudar:
            self.ao_mudar(valor)

    def _pintar(self) -> None:
        for valor, (botao, titulo, descricao) in self.botoes.items():
            marcado = valor == self.valor
            marca = "✔" if marcado else "○"
            botao.configure(
                text=f"{marca}   {titulo}\n      {descricao}",
                bg=e.AZUL_CLARO if marcado else e.SUPERFICIE,
                highlightbackground=e.AZUL if marcado else e.BORDA,
                highlightcolor=e.AMARELO, fg=e.TINTA,
            )


class Campo(Quadro):
    """Rótulo + dica + caixa de digitação grande."""

    def __init__(self, pai, rotulo: str, dica: str = "", largura: int = 28):
        super().__init__(pai)
        tk.Label(self, text=rotulo, font=self.tema["forte"], bg=self["bg"], fg=e.TINTA,
                 anchor="w").pack(fill="x")

        if dica:
            tk.Label(self, text=dica, font=self.tema["pequeno"], bg=self["bg"],
                     fg=e.TINTA_SUAVE, anchor="w").pack(fill="x")

        self.variavel = tk.StringVar()
        self.entrada = tk.Entry(
            self, textvariable=self.variavel, font=self.tema["texto"], width=largura,
            relief="solid", bd=1, highlightthickness=3, highlightcolor=e.AMARELO,
            highlightbackground=e.BORDA, bg=e.SUPERFICIE, fg=e.TINTA, insertwidth=3,
        )
        self.entrada.pack(fill="x", ipady=8, pady=(4, 0))
        self.retorno = tk.Label(self, text="", font=self.tema["pequeno"], bg=self["bg"],
                                anchor="w")
        self.retorno.pack(fill="x")
        # Ao digitar de novo, o aviso vermelho some (só volta se continuar errado)
        self.variavel.trace_add("write", lambda *_: self.avisar(""))

    @property
    def valor(self) -> str:
        return self.variavel.get().strip()

    @valor.setter
    def valor(self, texto: str) -> None:
        self.variavel.set(texto)

    def avisar(self, texto: str, problema: bool = False) -> None:
        self.retorno.configure(text=texto, fg=e.VERMELHO if problema else e.VERDE)
        self.entrada.configure(highlightbackground=e.VERMELHO if problema else e.BORDA)


class Rolagem(Quadro):
    """Área com barra de rolagem: nada some quando as letras ficam grandes."""

    def __init__(self, pai):
        super().__init__(pai)
        self.tela = tk.Canvas(self, bg=self["bg"], highlightthickness=0, bd=0)
        self.tela.tema = self.tema
        self.barra = ttk.Scrollbar(self, orient="vertical", command=self.tela.yview)
        self.conteudo = Quadro(self.tela)
        self._janela = self.tela.create_window((0, 0), window=self.conteudo, anchor="nw")

        self.tela.configure(yscrollcommand=self.barra.set)
        self.tela.pack(side="left", fill="both", expand=True)
        self.barra.pack(side="right", fill="y")

        self.conteudo.bind("<Configure>", self._ajustar)
        self.tela.bind("<Configure>", self._ajustar)
        self.bind_all("<MouseWheel>", self._rolar, add="+")
        self.bind_all("<Button-4>", lambda ev: self._rolar(ev, -1), add="+")
        self.bind_all("<Button-5>", lambda ev: self._rolar(ev, 1), add="+")

    def _ajustar(self, _evento=None) -> None:
        self.tela.itemconfigure(self._janela, width=self.tela.winfo_width())
        self.tela.configure(scrollregion=self.tela.bbox("all"))

        precisa = self.conteudo.winfo_reqheight() > self.tela.winfo_height()
        if precisa and not self.barra.winfo_ismapped():
            self.barra.pack(side="right", fill="y")
        elif not precisa and self.barra.winfo_ismapped():
            self.barra.pack_forget()
            self.tela.yview_moveto(0)

    def _rolar(self, evento, passo=None) -> None:
        # Só rola se o mouse estiver sobre esta área e a lista interna não for o alvo
        alvo = self.winfo_containing(evento.x_root, evento.y_root)

        if alvo is None or isinstance(alvo, (ttk.Treeview, tk.Listbox, tk.Text)):
            return

        if not str(alvo).startswith(str(self)) or not self.barra.winfo_ismapped():
            return

        passo = passo or (-1 if evento.delta > 0 else 1)
        self.tela.yview_scroll(passo * 3, "units")

    def topo(self) -> None:
        self.tela.yview_moveto(0)


class Tabela(Quadro):
    """Treeview com barra de rolagem e linhas coloridas por situação."""

    CORES = {
        "OK": e.VERDE_CLARO,
        "JA": e.AZUL_CLARO,
        "ERRO": e.VERMELHO_CLARO,
        "PULADO": e.CINZA_CLARO,
        "AGORA": e.AMARELO_CLARO,
    }

    def __init__(self, pai, colunas: list, altura: int = 8):
        super().__init__(pai)
        ids = [c[0] for c in colunas]
        self.arvore = ttk.Treeview(self, columns=ids, show="headings", height=altura,
                                   selectmode="browse")
        barra = ttk.Scrollbar(self, orient="vertical", command=self.arvore.yview)
        self.arvore.configure(yscrollcommand=barra.set)

        for ident, titulo, largura, esticar in colunas:
            self.arvore.heading(ident, text=titulo, anchor="w")
            self.arvore.column(ident, width=largura, minwidth=60, stretch=esticar, anchor="w")

        for situacao, cor in self.CORES.items():
            self.arvore.tag_configure(situacao, background=cor)

        self.arvore.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    def limpar(self) -> None:
        self.arvore.delete(*self.arvore.get_children())

    def inserir(self, iid: str, valores: tuple, situacao: str = "") -> None:
        if self.arvore.exists(iid):
            self.arvore.item(iid, values=valores, tags=(situacao,))
        else:
            self.arvore.insert("", "end", iid=iid, values=valores, tags=(situacao,))

        self.arvore.see(iid)

    def selecionado(self):
        selecao = self.arvore.selection()
        return selecao[0] if selecao else None


class Placar(Quadro):
    """Números grandes lado a lado, cada um com uma faixa colorida e uma legenda."""

    def __init__(self, pai, itens: list):
        super().__init__(pai)
        self.valores = []

        for coluna, (valor, legenda, cor) in enumerate(itens):
            self.columnconfigure(coluna, weight=1, uniform="placar")
            bloco = Quadro(self, fundo=e.SUPERFICIE, padx=20, pady=14,
                           highlightthickness=1, highlightbackground=e.BORDA)
            bloco.grid(row=0, column=coluna, sticky="nsew", padx=(0 if coluna == 0 else 12, 0))
            tk.Frame(bloco, bg=cor, height=6).pack(fill="x", pady=(0, 10))
            numero = tk.Label(bloco, text=str(valor), font=self.tema["numero"], fg=cor,
                              bg=e.SUPERFICIE, anchor="w")
            numero.pack(fill="x")
            # Número longo (ex.: "1 h 20 min") quebra a linha em vez de ser cortado
            bloco.bind("<Configure>", lambda ev, n=numero: n.configure(
                wraplength=max(ev.width - 40, 60), justify="left"))
            texto = Texto(bloco, legenda, largura=16)
            texto.pack(fill="x")
            self.valores.append((numero, texto))

    def mudar(self, indice: int, valor, legenda: str = None) -> None:
        numero, texto = self.valores[indice]
        numero.configure(text=str(valor))

        if legenda is not None:
            texto.configure(text=legenda)


class Alternador(Quadro):
    """Duas ou mais opções lado a lado; a escolhida fica azul (tipo abas)."""

    def __init__(self, pai, opcoes: list, valor, ao_mudar=None):
        super().__init__(pai, fundo=e.AZUL, padx=2, pady=2)
        self.valor, self.ao_mudar, self.rotulos = valor, ao_mudar, {}

        for chave, texto in opcoes:
            rotulo = tk.Label(self, text=texto, font=self.tema["forte"], padx=22, pady=10,
                              cursor="hand2", takefocus=True, highlightthickness=2,
                              highlightcolor=e.AMARELO)
            rotulo.pack(side="left", padx=(0, 2))
            for evento in ("<Button-1>", "<Return>", "<space>"):
                rotulo.bind(evento, lambda _, c=chave: self.marcar(c))
            self.rotulos[chave] = rotulo

        self._pintar()

    def marcar(self, chave) -> None:
        if chave != self.valor:
            self.valor = chave
            self._pintar()

            if self.ao_mudar:
                self.ao_mudar(chave)

    def _pintar(self) -> None:
        for chave, rotulo in self.rotulos.items():
            marcado = chave == self.valor
            rotulo.configure(bg=e.AZUL if marcado else e.SUPERFICIE,
                             fg="white" if marcado else e.TINTA,
                             highlightbackground=e.AZUL if marcado else e.SUPERFICIE)


class Barras(tk.Canvas):
    """Gráfico de barras horizontais simples: [(rótulo, valor, texto do valor, cor)]."""

    def __init__(self, pai, linhas: list = ()):
        super().__init__(pai, bg=pai["bg"], highlightthickness=0, bd=0)
        self.tema = pai.tema
        self.linhas = list(linhas)
        self.bind("<Configure>", lambda _: self.desenhar())

    def mudar(self, linhas: list) -> None:
        self.linhas = list(linhas)
        self.desenhar()

    def desenhar(self) -> None:
        self.delete("all")
        fonte, forte = self.tema["texto"], self.tema["forte"]
        altura_barra = fonte.metrics("linespace") + 14
        rotulo = max([fonte.measure(l[0]) for l in self.linhas] + [0]) + 24
        valor = max([forte.measure(l[2]) for l in self.linhas] + [0]) + 24
        largura = max(self.winfo_width(), 300)
        trilho = max(largura - rotulo - valor, 60)
        maximo = max([l[1] for l in self.linhas] + [0]) or 1

        for indice, (texto, numero, texto_valor, cor) in enumerate(self.linhas):
            y = indice * (altura_barra + 12)
            meio = y + altura_barra / 2
            self.create_text(0, meio, text=texto, anchor="w", font=fonte, fill=e.TINTA)
            self.create_rectangle(rotulo, y, rotulo + trilho, y + altura_barra,
                                  fill=e.CINZA_CLARO, width=0)
            cheio = max(trilho * numero / maximo, 4 if numero else 0)
            self.create_rectangle(rotulo, y, rotulo + cheio, y + altura_barra, fill=cor, width=0)
            self.create_text(rotulo + trilho + 14, meio, text=texto_valor, anchor="w",
                             font=forte, fill=e.TINTA)

        self.configure(height=max(len(self.linhas) * (altura_barra + 12), 1))


def formatar_cpf(cpf: str) -> str:
    if len(cpf) == 11 and cpf.isdigit():
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

    return cpf
