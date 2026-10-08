"""Conversão do nome do banco para o código usado pelo SIGEF."""

import re
import unicodedata

# Bancos mais usados no Brasil (+ os de peso regional): apelido -> código
BANCOS = {
    "BANCODOBRASIL": "001", "BRASIL": "001", "BB": "001",
    "BANCODAAMAZONIA": "003", "AMAZONIA": "003", "BASA": "003",
    "BANCODONORDESTE": "004", "NORDESTE": "004", "BNB": "004",
    "BANESTES": "021",
    "SANTANDER": "033",
    "BANRISUL": "041",
    "BRB": "070", "BRASILIA": "070",
    "BANCOINTER": "077", "INTER": "077", "INTERMEDIUM": "077",
    "CAIXA": "104", "CAIXAECONOMICAFEDERAL": "104", "CEF": "104",
    "STONE": "197",
    "BTG": "208", "BTGPACTUAL": "208",
    "ORIGINAL": "212",
    "BRADESCO": "237",
    "NUBANK": "260", "NUPAGAMENTOS": "260",
    "PAGBANK": "290", "PAGSEGURO": "290",
    "MERCADOPAGO": "323",
    "C6": "336", "C6BANK": "336",
    "ITAU": "341", "ITAUUNIBANCO": "341",
    "PICPAY": "380",
    "CORA": "403",
    "SAFRA": "422",
    "VOTORANTIM": "655", "BANCOBV": "655",
    "NEON": "735",
    "SICREDI": "748",
    "SICOOB": "756", "BANCOOB": "756",
}

# Apelidos maiores primeiro, para "Banco de Brasília" não casar com "Brasil"
APELIDOS = sorted(BANCOS, key=len, reverse=True)


def normalizar(texto: str) -> str:
    """Maiúsculas, sem acento e sem pontuação: 'C/C' -> 'CC', 'Itaú' -> 'ITAU'."""
    return re.sub(r"[^A-Z0-9]", "", unicodedata.normalize("NFKD", (texto or "").upper()))


def resolver_banco(valor: str) -> str:
    """Aceita o código (001, 1, 341) ou o nome do banco e devolve o código."""
    bruto = (valor or "").strip()

    if not bruto:
        return ""

    digitos = re.sub(r"\D", "", bruto)

    # Só números: é o próprio código (o Excel come o zero à esquerda)
    if digitos and not re.search(r"[A-Za-z]", bruto):
        return digitos.zfill(3) if len(digitos) < 3 else digitos

    texto = normalizar(bruto)

    if texto in BANCOS:
        return BANCOS[texto]

    for apelido in APELIDOS:
        if apelido in texto:
            return BANCOS[apelido]

    return ""
