"""Parâmetros de configuração da automação do SIGEF."""

from pathlib import Path

# ----------------------------------------------------------------- SIGEF
DOMINIO = "sigef.sefin.ro.gov.br"
URL_SIGEF = f"http://{DOMINIO}/"
URL_MANTER_CREDOR = f"http://{DOMINIO}/SIGEF2026/ADM/ADMManterCredorGeral.aspx?CdTransacao=1028"
URL_INCLUIR_DOMICILIO = (
    f"http://{DOMINIO}/SIGEF2026/FIN/FINIncluirDomicilioBancarioCredor.aspx?CdTransacao=351"
)

# Tipo de credor usado na tela de manutenção (10 = pessoa física)
TIPO_CREDOR = "10"

# Mensagem de retorno do SIGEF
SELETOR_MENSAGEM = "td[class^='SIGEFMensagem']"
JA_CADASTRADO = "JACADASTRAD"  # texto normalizado de "já cadastrado(a)"
PREFIXO = {"OK": "", "JA": "JÁ CADASTRADO: ", "ERRO": "ERRO: "}

# ------------------------------------------------------------- Navegador
TIMEOUT = 10_000  # 10s para localizar qualquer elemento
PORTA_DEBUG = 9222
CDP_URL = f"http://127.0.0.1:{PORTA_DEBUG}"
ESPERA_CHROME = 45  # segundos aguardando a porta de depuração responder

# --------------------------------------------------------------- Arquivos
PASTA_DADOS = Path.home() / ".sigef-automacao"
PERFIL_CHROME = PASTA_DADOS / "chrome"  # perfil próprio: não conflita com o Chrome pessoal
PASTA_LOGS = PASTA_DADOS / "logs"

# --------------------------------------------------------------- Planilha
COLUNAS_PADRAO = {"nome": "D", "cpf": "E", "banco": "F", "agencia": "G", "conta": "H"}
COLUNA_RESULTADO = "J"
XL_UP = -4162  # xlUp
LINHAS_BUSCA_CABECALHO = 30
COLUNAS_BUSCA_CABECALHO = 40
