"""Ponto de entrada da automação SIGEF.

Uso:
    python Cadastrar.py

O script abre o Chrome em modo de depuração, aguarda o login no SIGEF e então
oferece o menu de execução. O navegador permanece aberto ao final.
"""

from playwright.sync_api import sync_playwright

from sigef.config import URL_MANTER_CREDOR
from sigef.console import menu_principal
from sigef.fluxos import executar_lotes, executar_planilha
from sigef.log import configurar_log, logger
from sigef.navegador import preparar_navegador

MODOS = (executar_lotes, executar_planilha)


def main() -> None:
    configurar_log()
    logger.info("Início da execução")

    with sync_playwright() as playwright:
        context, page = preparar_navegador(playwright)

        while True:
            escolha = menu_principal()

            if escolha == len(MODOS):  # Sair
                break

            try:
                MODOS[escolha](context, page)
            except KeyboardInterrupt:
                print("\nExecução interrompida. Voltando ao menu.")

            # Volta ao começo do fluxo e segue aguardando o próximo trabalho
            try:
                page.goto(URL_MANTER_CREDOR)
            except Exception:
                pass

    logger.info("Fim da execução")
    print("\nAutomação encerrada. O Chrome continua aberto para uso normal.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")
    except Exception as erro:
        print(f"\nFalha: {erro}")
