"""Ponto de entrada da automação SIGEF no terminal.

Uso:
    python Cadastrar.py          (terminal)
    python CadastrarApp.pyw      (janela, a mesma do executável)

O script abre o Chrome em modo de depuração, aguarda o login no SIGEF e então
oferece o menu de execução. O navegador permanece aberto ao final.
"""

from playwright.sync_api import sync_playwright

from sigef.config import URL_MANTER_CREDOR
from sigef.console import menu_principal, modo_lotes, modo_planilha, preparar_navegador
from sigef.log import configurar_log, logger
from sigef.navegador import ErroNavegador, Navegador

MODOS = (modo_lotes, modo_planilha)


def main() -> None:
    configurar_log()
    logger.info("Início da execução (terminal)")

    with sync_playwright() as playwright:
        navegador = Navegador(playwright)
        preparar_navegador(navegador)

        while True:
            escolha = menu_principal()

            if escolha == len(MODOS):  # Sair
                break

            try:
                MODOS[escolha](navegador)
            except KeyboardInterrupt:
                print("\nExecução interrompida. Voltando ao menu.")
            except ErroNavegador as erro:
                print(f"\n{erro}")
                preparar_navegador(navegador)

            # Volta ao começo do fluxo e segue aguardando o próximo trabalho
            try:
                navegador.page.goto(URL_MANTER_CREDOR)
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
