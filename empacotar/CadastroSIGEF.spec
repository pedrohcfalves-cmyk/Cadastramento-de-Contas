# -*- mode: python ; coding: utf-8 -*-
"""Receita do PyInstaller: gera um único CadastroSIGEF.exe com tudo dentro.

Embute o Python, a interface, o Playwright (com o Node.js dele), o pywin32 para o
Excel e as fontes. Não precisa instalar nada nos computadores.

Gerar (no Windows, na pasta do projeto):
    pip install -r requirements-dev.txt
    pyinstaller empacotar/CadastroSIGEF.spec --noconfirm
O executável sai em dist/CadastroSIGEF.exe
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

RAIZ = Path(SPECPATH).parent  # noqa: F821 - definido pelo PyInstaller
PASTA = Path(SPECPATH)  # noqa: F821

dados = [
    (str(RAIZ / "sigef" / "interface" / "fontes"), "sigef/interface/fontes"),
    (str(RAIZ / "sigef" / "interface" / "icone.png"), "sigef/interface"),
]
dados += collect_data_files("playwright")  # driver Node.js usado pela automação

# Runtime do Visual C++ junto: o programa abre mesmo em Windows sem ele instalado
binarios = [(str(dll), ".") for dll in Path(sys.base_prefix).glob("vcruntime140*.dll")]

analise = Analysis(  # noqa: F821
    [str(RAIZ / "CadastrarApp.pyw")],
    pathex=[str(RAIZ)],
    datas=dados,
    binaries=binarios,
    hiddenimports=["win32com.client", "pythoncom", "pywintypes"],
    excludes=["pytest", "PIL", "numpy", "pydoc_data", "test",
              "win32ui", "win32uiole", "pythonwin"],
    noarchive=False,
)

pyz = PYZ(analise.pure)  # noqa: F821

abertura = Splash(  # noqa: F821
    str(PASTA / "abertura.png"),
    binaries=analise.binaries,
    datas=analise.datas,
    text_pos=None,
    always_on_top=True,
)

exe = EXE(  # noqa: F821
    pyz,
    analise.scripts,
    abertura,
    abertura.binaries,
    analise.binaries,
    analise.datas,
    [],
    name="CadastroSIGEF",
    icon=str(PASTA / "icone.ico"),
    version=str(PASTA / "versao.txt"),
    console=False,
    upx=False,
    runtime_tmpdir=None,
)
