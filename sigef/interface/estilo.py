"""Cores, fontes e tema da janela.

Pensado para pessoas idosas: letras grandes (ajustáveis), contraste alto, uma
ação principal por tela e o mesmo lugar para cada tipo de botão.
"""

import json
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont
from tkinter import ttk

from ..config import PASTA_DADOS

# Cores inspiradas na bandeira de Rondônia (azul, verde e amarelo)
FUNDO = "#F3F6FA"        # papel azulado, sem o brilho do branco puro
SUPERFICIE = "#FFFFFF"
TINTA = "#14213D"        # texto principal (contraste ~15:1 sobre o fundo)
TINTA_SUAVE = "#3D4B66"  # texto de apoio (contraste ~8:1)
AZUL = "#0B3D91"         # faixa do topo e seleção
AZUL_CLARO = "#DCE7F7"
VERDE = "#1F7A3A"        # ação principal
VERDE_ESCURO = "#165C2B"
VERDE_CLARO = "#E3F3E7"
AMARELO = "#FFD84D"      # "você está aqui" e foco do teclado
AMARELO_CLARO = "#FFF4C2"
VERMELHO = "#B42318"
VERMELHO_ESCURO = "#8E1B12"
VERMELHO_CLARO = "#FDE7E5"
CINZA_CLARO = "#E7EBF1"
BORDA = "#8C9AB0"

FAMILIA = "Atkinson Hyperlegible"
FAMILIA_RESERVA = "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"
PASTA_FONTES = Path(__file__).resolve().parent / "fontes"

# Tamanhos-base em pontos; o botão A+/A− multiplica todos de uma vez
TAMANHOS = {
    "texto": (15, "normal"),
    "forte": (15, "bold"),
    "pequeno": (13, "normal"),
    "titulo": (26, "bold"),
    "subtitulo": (18, "bold"),
    "botao": (16, "bold"),
    "numero": (34, "bold"),
    "passo": (14, "bold"),
}
ESCALAS = (0.85, 1.0, 1.15, 1.3, 1.5)
ARQUIVO_PREFERENCIAS = PASTA_DADOS / "preferencias.json"


def preparar_processo() -> None:
    """Antes de criar a janela: nitidez em telas de alta resolução e fontes embutidas."""
    if sys.platform != "win32":
        return

    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    # Registra as fontes só para este programa (não instala nada no Windows)
    for arquivo in PASTA_FONTES.glob("*.ttf"):
        try:
            ctypes.windll.gdi32.AddFontResourceExW(str(arquivo), 0x10, 0)  # FR_PRIVATE
        except Exception:
            pass


def _ler_preferencias() -> dict:
    try:
        return json.loads(ARQUIVO_PREFERENCIAS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _gravar_preferencias(dados: dict) -> None:
    try:
        ARQUIVO_PREFERENCIAS.parent.mkdir(parents=True, exist_ok=True)
        ARQUIVO_PREFERENCIAS.write_text(json.dumps(dados), encoding="utf-8")
    except OSError:
        pass


class Tema:
    """Fontes nomeadas: mudar o tamanho aqui atualiza todos os textos da janela."""

    def __init__(self, raiz: tk.Tk):
        self.raiz = raiz
        familia = FAMILIA if FAMILIA in tkfont.families(raiz) else FAMILIA_RESERVA
        self.fontes = {nome: tkfont.Font(raiz, family=familia, size=tamanho, weight=peso)
                       for nome, (tamanho, peso) in TAMANHOS.items()}
        self.indice_escala = _ler_preferencias().get("escala", 1)
        self.indice_escala = min(max(self.indice_escala, 0), len(ESCALAS) - 1)
        self.estilo = ttk.Style(raiz)
        self.estilo.theme_use("clam")
        self.aplicar()

    def __getitem__(self, nome: str) -> tkfont.Font:
        return self.fontes[nome]

    @property
    def escala(self) -> float:
        return ESCALAS[self.indice_escala]

    def mudar_escala(self, passo: int) -> bool:
        novo = min(max(self.indice_escala + passo, 0), len(ESCALAS) - 1)

        if novo == self.indice_escala:
            return False

        self.indice_escala = novo
        _gravar_preferencias({"escala": novo})
        self.aplicar()
        return True

    def aplicar(self) -> None:
        for nome, (tamanho, _peso) in TAMANHOS.items():
            self.fontes[nome].configure(size=round(tamanho * self.escala))

        altura_linha = self.fontes["texto"].metrics("linespace") + 14
        e = self.estilo
        e.configure(".", font=self.fontes["texto"], background=FUNDO, foreground=TINTA)
        e.configure("Treeview", rowheight=altura_linha, fieldbackground=SUPERFICIE,
                    background=SUPERFICIE, foreground=TINTA, borderwidth=1)
        e.configure("Treeview.Heading", font=self.fontes["forte"], background=CINZA_CLARO,
                    foreground=TINTA, relief="flat", padding=(8, 8))
        e.map("Treeview", background=[("selected", AZUL)], foreground=[("selected", "white")])
        e.configure("Horizontal.TProgressbar", troughcolor=CINZA_CLARO, background=VERDE,
                    thickness=max(22, altura_linha // 2), borderwidth=0)
        e.configure("TCombobox", padding=8, arrowsize=24, fieldbackground=SUPERFICIE)
        e.configure("TSpinbox", padding=8, arrowsize=22, fieldbackground=SUPERFICIE)
        e.configure("Vertical.TScrollbar", arrowsize=22, troughcolor=CINZA_CLARO)
        self.raiz.option_add("*TCombobox*Listbox.font", self.fontes["texto"])
        self.raiz.option_add("*Font", self.fontes["texto"])


def abrir_pasta(caminho: Path) -> None:
    """Abre uma pasta no Explorador de Arquivos."""
    caminho.mkdir(parents=True, exist_ok=True)

    if sys.platform == "win32":
        os.startfile(caminho)  # noqa: S606 - pasta do próprio programa
    else:
        import subprocess

        subprocess.Popen(["xdg-open", str(caminho)])
