"""Preparação do navegador: Chrome (ou Edge) em modo de depuração e login no SIGEF."""

import os
import shutil
import subprocess
import time
import urllib.request

from .config import (
    CDP_URL,
    DOMINIO,
    ESPERA_CHROME,
    NAVEGADORES,
    PERFIL_CHROME,
    PORTA_DEBUG,
    TIMEOUT,
    URL_MANTER_CREDOR,
    URL_SIGEF,
)


class ErroNavegador(RuntimeError):
    """Navegador ausente, fechado ou que não respondeu."""


def _candidatos_windows():
    import winreg

    for nome, pasta, executavel in NAVEGADORES:
        for variavel in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(variavel)

            if base:
                yield nome, os.path.join(base, *pasta, executavel)

        chave = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{executavel}"

        for raiz in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(raiz, chave) as registro:
                    yield nome, winreg.QueryValue(registro, None)
            except OSError:
                pass


def _candidatos_outros():
    for caminho in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ):
        yield "Google Chrome", caminho

    for comando in ("chrome", "google-chrome", "chromium", "msedge"):
        yield comando, shutil.which(comando)


def encontrar_navegador() -> tuple:
    """Localiza o Chrome (ou, na falta dele, o Edge): devolve (nome, caminho)."""
    candidatos = _candidatos_windows() if os.name == "nt" else _candidatos_outros()

    for nome, caminho in candidatos:
        if caminho and os.path.isfile(caminho):
            return nome, caminho

    return "", ""


def cdp_disponivel(segundos: float = 1.0) -> bool:
    """Espera o navegador responder na porta de depuração."""
    limite = time.time() + segundos

    while True:
        try:
            with urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=1):
                return True
        except Exception:
            if time.time() >= limite:
                return False

            time.sleep(0.5)


def abrir_navegador_debug() -> str:
    """Reaproveita um navegador já em depuração ou abre um com perfil próprio.

    Devolve o nome do navegador usado; levanta ErroNavegador se não conseguir.
    """
    if cdp_disponivel():
        return "navegador já aberto"

    nome, executavel = encontrar_navegador()

    if not executavel:
        raise ErroNavegador(
            "Não encontrei o Google Chrome nem o Microsoft Edge neste computador.\n"
            f"Abra o Chrome manualmente com: chrome.exe --remote-debugging-port={PORTA_DEBUG}"
        )

    PERFIL_CHROME.mkdir(parents=True, exist_ok=True)

    # Processo solto: o navegador continua aberto depois que o programa termina
    extras = {}

    if os.name == "nt":
        extras["creationflags"] = 0x00000008 | 0x00000200  # DETACHED | NEW_PROCESS_GROUP
    else:
        extras["start_new_session"] = True

    subprocess.Popen(
        [
            executavel,
            f"--remote-debugging-port={PORTA_DEBUG}",
            f"--user-data-dir={PERFIL_CHROME}",
            "--no-first-run",
            "--no-default-browser-check",
            URL_SIGEF,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **extras,
    )

    if not cdp_disponivel(ESPERA_CHROME):
        raise ErroNavegador(f"O {nome} não respondeu. Feche todas as janelas dele e tente de novo.")

    return nome


class Navegador:
    """Conexão do Playwright com o navegador do usuário (o navegador nunca é fechado)."""

    def __init__(self, playwright):
        self.playwright = playwright
        self.browser = None
        self.context = None
        self.page = None

    @property
    def conectado(self) -> bool:
        return bool(self.browser and self.browser.is_connected()
                    and self.page and not self.page.is_closed())

    def abrir(self) -> str:
        """Abre/reaproveita o navegador e deixa uma aba no SIGEF em primeiro plano."""
        nome = "navegador já conectado"

        if not (self.browser and self.browser.is_connected()):
            nome = abrir_navegador_debug()
            self.browser = self.playwright.chromium.connect_over_cdp(CDP_URL)
            self.context = (self.browser.contexts[0] if self.browser.contexts
                            else self.browser.new_context())
            self.context.set_default_timeout(TIMEOUT)

        if not self.page or self.page.is_closed():
            paginas = self.context.pages
            self.page = next((aba for aba in paginas if DOMINIO in aba.url.lower()), None)

            if self.page is None:
                self.page = paginas[0] if paginas else self.context.new_page()

        self.page.bring_to_front()

        if DOMINIO not in self.page.url.lower():
            self.page.goto(URL_SIGEF)

        return nome

    def logado(self) -> bool:
        """Confere o login abrindo a tela de credores (só abre se a sessão for válida)."""
        self.page.goto(URL_MANTER_CREDOR)
        self.page.wait_for_load_state("networkidle")
        return self.page.locator("#cmbTipoCredor").count() > 0

    def garantir(self) -> None:
        """Levanta ErroNavegador se o navegador foi fechado desde o login."""
        if not self.conectado:
            raise ErroNavegador("O navegador foi fechado. Abra o SIGEF e entre de novo.")
