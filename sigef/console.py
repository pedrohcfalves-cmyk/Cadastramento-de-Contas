"""Interação com o usuário no terminal: menus, entrada de dados e confirmações."""

from .modelos import ROTULOS, Lote, PularLote, ReiniciarLote, limpar, lote_de_linha

TITULO = (
    "========================================\n"
    " CADASTRO DE CREDOR / DOMICÍLIO BANCÁRIO\n"
    "========================================"
)


# ------------------------------------------------------------- primitivas

def escolher(opcoes: list, titulo: str) -> int:
    """Menu numérico; devolve o índice da opção escolhida."""
    print(f"\n{titulo}")

    for numero, texto in enumerate(opcoes, 1):
        print(f"   {numero} - {texto}")

    while True:
        escolha = input("Opção > ").strip()

        if escolha.isdigit() and 1 <= int(escolha) <= len(opcoes):
            return int(escolha) - 1


def inteiro(pergunta: str, padrao: int) -> int:
    resposta = input(f"{pergunta} [{padrao}]: ").strip()
    return int(resposta) if resposta.isdigit() else padrao


def pedir(campo: str, atual: str = "") -> str:
    """Lê um campo do teclado, validando e normalizando o valor."""
    rotulo = ROTULOS[campo]
    sufixo = f" [{atual}]" if atual else ""

    while True:
        bruto = input(f"   {rotulo}{sufixo}: ").strip()
        valor = limpar(campo, bruto) if bruto else atual

        if not valor:
            if campo == "banco" and bruto:
                print(f"      Banco não reconhecido: {bruto}. Informe o código (ex. 001).")
            else:
                print(f"      {rotulo} não pode ficar vazio.")
            continue

        if campo == "cpf" and len(valor) != 11:
            print("      CPF deve ter 11 dígitos.")
            continue

        return valor


def editar_lote(lote: Lote) -> None:
    """Corrige os dados de um lote reprovado na conferência manual."""
    print("   (Enter mantém o valor atual)")

    for campo in ROTULOS:
        setattr(lote, campo, pedir(campo, getattr(lote, campo)))


# ----------------------------------------------------------------- menus

def menu_principal() -> int:
    return escolher(
        [
            "Modo lote (digitar / colar / arquivo)",
            "Modo planilha (Excel via win32)",
            "Sair",
        ],
        TITULO,
    )


def escolher_modo_manual() -> bool:
    return escolher(
        [
            "Automática (não interrompe o fluxo)",
            "Manual (pergunta antes de incluir credor e de confirmar o domicílio)",
        ],
        "CONFIRMAÇÃO DAS AÇÕES",
    ) == 1


# ------------------------------------------------------- entrada de lotes

def _lotes_colados() -> list:
    print(
        "\nCole/digite um lote por linha, na ordem:\n"
        "   CPF,Nome,Código do Banco,Agência,Conta\n"
        "(separador , ou ; ou TAB — linha vazia encerra)\n"
    )

    lotes = []

    while True:
        linha = input(f"{len(lotes) + 1}> ").strip()

        if not linha:
            return lotes

        try:
            lotes.append(lote_de_linha(linha))
        except ValueError as erro:
            print(f"   Linha ignorada ({erro}).")


def _lotes_digitados() -> list:
    lotes = []

    while True:
        print(f"\n--- Lote {len(lotes) + 1} ---")
        lotes.append(Lote(**{campo: pedir(campo) for campo in ROTULOS}))

        if input("Incluir outro lote? [s/N] ").strip().lower() not in ("s", "sim"):
            return lotes


def _lotes_de_arquivo() -> list:
    caminho = input("Caminho do arquivo (.csv/.txt): ").strip().strip('"')
    lotes = []

    try:
        with open(caminho, encoding="utf-8-sig") as arquivo:
            for numero, linha in enumerate(arquivo, 1):
                linha = linha.strip()

                if not linha or linha.lower().startswith("cpf"):
                    continue

                try:
                    lotes.append(lote_de_linha(linha))
                except ValueError as erro:
                    print(f"   Linha {numero} ignorada ({erro}).")

    except OSError as erro:
        print(f"   Não foi possível ler o arquivo: {erro}")

    return lotes


def coletar_lotes() -> list:
    """Menu de entrada dos lotes, com conferência da lista antes de executar."""
    entradas = (_lotes_colados, _lotes_digitados, _lotes_de_arquivo)

    while True:
        escolha = escolher(
            [
                "Colar lotes em linhas",
                "Digitar campo por campo",
                "Carregar de arquivo (.csv/.txt)",
                "Voltar",
            ],
            "ENTRADA DOS LOTES",
        )

        if escolha == len(entradas):
            return []

        lotes = entradas[escolha]()

        if not lotes:
            print("Nenhum lote válido informado.")
            continue

        print(f"\n{len(lotes)} lote(s) carregado(s):")

        for numero, lote in enumerate(lotes, 1):
            print(f"   {numero}. {lote}")

        if input("\nConfirmar esta lista? [S/n] ").strip().lower() in ("", "s", "sim"):
            return lotes


# ---------------------------------------------------------- confirmações

class Confirmador:
    """No modo automático clica direto; no manual valida os dados antes."""

    def __init__(self, manual: bool, editavel: bool = True):
        self.manual = manual
        self.editavel = editavel
        self.lote_liberado = False

    def clicar(self, locator, lote: Lote, acao: str) -> None:
        if self.manual and not self.lote_liberado:
            self._perguntar(lote, acao)

        locator.click()

    def _perguntar(self, lote: Lote, acao: str) -> None:
        opcao_n = "   [N] não, corrigir e reiniciar este lote\n" if self.editavel else ""

        while True:
            print(f"\n>> {acao}\n   {lote}")

            resposta = input(
                "   Os dados estão corretos?\n"
                "   [S] sim, continuar   [T] sim, e não perguntar mais neste lote\n"
                f"{opcao_n}"
                "   [P] pular este lote\n"
                "   > "
            ).strip().lower()

            if resposta in ("", "s"):
                return

            if resposta == "t":
                self.lote_liberado = True
                return

            if resposta == "n" and self.editavel:
                raise ReiniciarLote

            if resposta == "p":
                raise PularLote
