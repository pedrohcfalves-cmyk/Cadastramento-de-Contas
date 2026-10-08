"""Preparação do navegador: Chrome em modo de depuração e login no SIGEF."""

import os
import shutil
import subprocess
import time
import urllib.request

from .config import (
    CDP_URL,
    DOMINIO,
    ESPERA_CHROME,
    PERFIL_CHROME,
    PORTA_DEBUG,
    TIMEOUT,
    URL_MANTER_CREDOR,
    URL_SIGEF,
)


def encontrar_chrome() -> str:
    """Localiza o executável do Chrome em qualquer computador."""
    candidatos = []

    if os.name == "nt":
        for variavel in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(variavel)

            if base:
                candidatos.append(os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"))

        try:
            import winreg

            chave = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"

            for raiz in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(raiz, chave) as registro:
                        candidatos.append(winreg.QueryValue(registro, None))
                except OSError:
                    pass

        except ImportError:
            pass

    else:
        candidatos += [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]

    candidatos += [shutil.which(nome) for nome in
                   ("chrome", "chrome.exe", "google-chrome", "chromium")]

    for candidato in candidatos:
        if candidato and os.path.isfile(candidato):
            return candidato

    return ""


def cdp_disponivel(segundos: float = 1.0) -> bool:
    """Espera o Chrome responder na porta de depuração."""
    limite = time.time() + segundos

    while True:
        try:
            with urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=1):
                return True
        except Exception:
            if time.time() >= limite:
                return False

            time.sleep(0.5)


def abrir_chrome_debug() -> bool:
    """Reaproveita um Chrome já em depuração ou abre um com perfil próprio."""
    if cdp_disponivel():
        print("Chrome em modo de depuração já estava aberto.")
        return True

    executavel = encontrar_chrome()

    if not executavel:
        print(
            "\nChrome não encontrado. Abra-o manualmente com:\n"
            f"   chrome.exe --remote-debugging-port={PORTA_DEBUG}"
        )
        return False

    PERFIL_CHROME.mkdir(parents=True, exist_ok=True)

    # Processo solto: o Chrome continua aberto depois que o script termina
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

    print("Abrindo o Chrome em modo de depuração...")

    return cdp_disponivel(ESPERA_CHROME)


def preparar_navegador(playwright):
    """Abre o Chrome, leva ao SIGEF e só retorna com a sessão confirmada."""
    if not abrir_chrome_debug():
        raise RuntimeError("Não foi possível iniciar o Chrome em modo de depuração.")

    browser = playwright.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    context.set_default_timeout(TIMEOUT)

    page = next((aba for aba in context.pages if DOMINIO in aba.url.lower()), None)

    if page is None:
        page = context.pages[0] if context.pages else context.new_page()

    page.bring_to_front()

    if DOMINIO not in page.url.lower():
        page.goto(URL_SIGEF)

    print(
        "\n========================================\n"
        " LOGIN NO SIGEF\n"
        "========================================\n"
        f" O Chrome foi aberto em {URL_SIGEF}\n"
        " Entre na sua conta e volte aqui."
    )

    while True:
        input("\n>> Pressione ENTER depois de concluir o login... ")

        try:
            page.goto(URL_MANTER_CREDOR)
            page.wait_for_load_state("networkidle")

            if page.locator("#cmbTipoCredor").count():
                print("Sessão confirmada.")
                return context, page

        except Exception as erro:
            print(f"   Não foi possível abrir a tela de credores: {str(erro).splitlines()[0]}")
            continue

        print("   A tela de credores não abriu — login incompleto ou sem permissão.")
