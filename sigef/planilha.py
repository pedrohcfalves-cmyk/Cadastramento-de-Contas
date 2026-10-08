"""Leitura e gravação da planilha do Excel via COM (pywin32)."""

import os
import time

from .bancos import normalizar
from .config import (
    COLUNAS_BUSCA_CABECALHO,
    COLUNAS_PADRAO,
    COLUNA_RESULTADO,
    LINHAS_BUSCA_CABECALHO,
    XL_UP,
)
from .console import escolher
from .modelos import ROTULOS, Lote, limpar

# Cabeçalhos aceitos na detecção automática das colunas (normalizados)
CABECALHOS = {
    "nome": ("SERVIDOR", "NOMEDOSERVIDOR", "NOMEDOCREDOR", "CREDOR", "FAVORECIDO",
             "BENEFICIARIO", "NOME"),
    "cpf": ("CPF", "NUCPF", "CPFCNPJ"),
    "banco": ("BANCO", "CODIGODOBANCO", "CODBANCO", "CDBANCO"),
    "agencia": ("AGENCIA", "AGBANCARIA", "AG"),
    "conta": ("CC", "CONTA", "CONTACORRENTE", "NUCONTA", "CONTABANCARIA"),
}

# Cabeçalhos que nunca são o nome do credor
CABECALHOS_IGNORADOS = ("ESCOLA", "MUNICIPIO", "EMPRESA", "ORGAO", "UNIDADE")


# ------------------------------------------------------------- utilidades

def letra_para_indice(letra: str) -> int:
    indice = 0

    for caractere in letra.strip().upper():
        if not caractere.isalpha():
            break

        indice = indice * 26 + (ord(caractere) - 64)

    return indice


def indice_para_letra(indice: int) -> str:
    letra = ""

    while indice > 0:
        indice, resto = divmod(indice - 1, 26)
        letra = chr(65 + resto) + letra

    return letra


def texto_celula(valor) -> str:
    if valor is None:
        return ""

    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))

    return str(valor).strip()


def endereco(celula) -> str:
    """Address é propriedade no late binding e método no early binding."""
    valor = celula.Address

    if not isinstance(valor, str):
        valor = valor(False, False)

    return valor.replace("$", "")


# ------------------------------------------------------- abertura do arquivo

def abrir_arquivo(excel, caminho: str):
    """Abre o arquivo, reaproveitando a pasta se ela já estiver aberta no Excel."""
    caminho = caminho.strip().strip('"').strip("'")
    nome = os.path.basename(caminho).lower()

    for pasta in excel.Workbooks:
        if pasta.Name.lower() == nome or pasta.FullName.lower() == caminho.lower():
            print("   (a pasta já estava aberta no Excel)")
            return pasta

    # Workbooks.Open pode devolver None: nesse caso a pasta ativa é a recém-aberta
    return excel.Workbooks.Open(caminho) or excel.ActiveWorkbook


def abrir_planilha():
    """Escolhe pasta de trabalho e aba; devolve (pasta, aba) ou None."""
    try:
        import win32com.client as win32
    except ImportError:
        print("\nBiblioteca pywin32 não encontrada. Instale com: pip install pywin32")
        return None

    try:
        excel = win32.GetActiveObject("Excel.Application")
    except Exception:
        excel = win32.Dispatch("Excel.Application")
        excel.Visible = True

    abertas = [pasta.Name for pasta in excel.Workbooks]
    escolha = escolher(abertas + ["Abrir outro arquivo...", "Voltar"],
                       "PLANILHAS ABERTAS NO EXCEL")

    if escolha == len(abertas) + 1:
        return None

    try:
        if escolha == len(abertas):
            pasta = abrir_arquivo(excel, input("Caminho completo do arquivo: "))
        else:
            pasta = excel.Workbooks(escolha + 1)

        if pasta is None:
            print("   Não foi possível obter a pasta de trabalho.")
            return None

        abas = [aba.Name for aba in pasta.Worksheets]
        aba = pasta.Worksheets(escolher(abas, f"ABAS DE {pasta.Name}") + 1)

    except Exception as erro:
        print(f"   Não foi possível abrir a planilha: {erro}")
        return None

    print(f"\nArquivo: {pasta.FullName}")
    print(f"Aba:     {aba.Name}")

    if pasta.ReadOnly:
        print("ATENÇÃO: a pasta está aberta somente para leitura — nada será gravado.")

    return pasta, aba


# ------------------------------------------------------- mapa das colunas

def detectar_colunas(aba) -> tuple:
    """Procura a linha de cabeçalho; devolve ({campo: índice}, 1ª linha de dados)."""
    for linha in range(1, LINHAS_BUSCA_CABECALHO + 1):
        titulos = {
            coluna: normalizar(texto_celula(aba.Cells(linha, coluna).Value))
            for coluna in range(1, COLUNAS_BUSCA_CABECALHO + 1)
        }

        if "CPF" not in titulos.values():
            continue

        colunas, usadas = {}, set()

        for campo, apelidos in CABECALHOS.items():
            achado = None

            for apelido in apelidos:
                for coluna, titulo in titulos.items():
                    if coluna in usadas or not titulo:
                        continue

                    if any(ruim in titulo for ruim in CABECALHOS_IGNORADOS):
                        continue

                    if titulo == apelido or (len(apelido) > 2 and apelido in titulo):
                        achado = coluna
                        break

                if achado:
                    break

            if achado:
                colunas[campo] = achado
                usadas.add(achado)

        if len(colunas) == len(CABECALHOS):
            return colunas, linha + 1

    return {}, 0


def confirmar_colunas(aba) -> tuple:
    """Mostra o mapa das colunas (detectado ou padrão) e permite ajustar."""
    colunas, primeira = detectar_colunas(aba)

    if colunas:
        print(f"\nCabeçalho encontrado. Colunas detectadas (dados a partir da linha {primeira}):")
    else:
        colunas = {campo: letra_para_indice(letra) for campo, letra in COLUNAS_PADRAO.items()}
        primeira = 2
        print("\nCabeçalho não encontrado. Usando as colunas padrão:")

    while True:
        for campo, coluna in colunas.items():
            letra = indice_para_letra(coluna)
            titulo = texto_celula(aba.Cells(max(primeira - 1, 1), coluna).Value)
            exemplo = texto_celula(aba.Cells(primeira, coluna).Value)
            print(f"   {ROTULOS[campo]:<16} -> {letra:>2}  ({titulo or 'sem título'})  ex.: {exemplo}")

        if input("\nAs colunas estão corretas? [S/n] ").strip().lower() in ("", "s", "sim"):
            return colunas, primeira

        print("\nInforme a letra de cada coluna:")

        for campo in colunas:
            letra = input(f"   {ROTULOS[campo]} [{indice_para_letra(colunas[campo])}]: ").strip()

            if letra:
                colunas[campo] = letra_para_indice(letra)


def escolher_coluna_resultado() -> str:
    """Coluna do diagnóstico; o conteúdo anterior da linha é sempre sobrescrito."""
    while True:
        letra = (input(f"\nColuna do diagnóstico [{COLUNA_RESULTADO}]: ").strip()
                 or COLUNA_RESULTADO).upper()

        if letra_para_indice(letra):
            return letra


# -------------------------------------------------------- leitura/gravação

def lote_da_planilha(aba, linha: int, colunas: dict) -> Lote:
    return Lote(
        **{
            campo: limpar(campo, texto_celula(aba.Cells(linha, coluna).Value))
            for campo, coluna in colunas.items()
        }
    )


def ultima_linha(aba, colunas: dict) -> int:
    return int(aba.Cells(aba.Rows.Count, colunas["cpf"]).End(XL_UP).Row)


def gravar_resultado(pasta, aba, linha: int, texto: str, coluna: str) -> None:
    """Escreve o diagnóstico da linha e salva a pasta."""
    celula = f"{coluna}{linha}"

    # Excel recusa chamadas COM enquanto uma célula está em edição: tenta de novo
    for tentativa in (1, 2, 3):
        try:
            alvo = aba.Range(celula)

            # Em célula mesclada só a primeira do bloco aceita valor
            if alvo.MergeCells:
                alvo = alvo.MergeArea.Cells(1, 1)

            alvo.Value = texto
            gravado = texto_celula(alvo.Value)
            print(f"   {endereco(alvo)}: {gravado}")

            if not gravado:
                print("   ATENÇÃO: a célula continua vazia após a gravação.")
            elif alvo.EntireColumn.Hidden:
                print("   ATENÇÃO: a coluna está oculta no Excel (botão direito > Reexibir).")

            break

        except Exception as erro:
            if tentativa == 3:
                print(f"   FALHA ao gravar em {celula}: {erro}")
                print("   (se houver célula em edição no Excel, pressione ESC)")
                return

            time.sleep(1)

    try:
        pasta.Save()
    except Exception as erro:
        print(f"   {celula} preenchida, mas a planilha não foi salva: {erro}")
