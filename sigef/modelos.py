"""Estruturas de dados e validação de um lote de cadastro."""

import re
from dataclasses import dataclass

from .bancos import resolver_banco

ROTULOS = {
    "cpf": "CPF",
    "nome": "Nome",
    "banco": "Código do Banco",
    "agencia": "Agência",
    "conta": "Conta",
}

SOMENTE_DIGITOS = ("cpf", "agencia", "conta")

TAMANHO_CPF = 11


class ReiniciarLote(Exception):
    """Usuário reprovou os dados: corrigir e refazer somente este lote."""


class PularLote(Exception):
    """Usuário optou por descartar este lote/linha."""


@dataclass
class Lote:
    """Um credor e seu domicílio bancário."""

    cpf: str = ""
    nome: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""

    def __str__(self) -> str:
        return " | ".join(f"{ROTULOS[campo]}: {getattr(self, campo)}" for campo in ROTULOS)

    def faltando(self) -> list:
        """Rótulos dos campos vazios."""
        return [ROTULOS[campo] for campo in ROTULOS if not getattr(self, campo)]

    def cpf_valido(self) -> bool:
        return len(self.cpf) == TAMANHO_CPF


def limpar(campo: str, valor: str) -> str:
    """Normaliza o valor de um campo conforme a sua natureza."""
    valor = (valor or "").strip()

    if campo == "banco":
        return resolver_banco(valor)

    if campo not in SOMENTE_DIGITOS:
        return valor

    valor = re.sub(r"\D", "", valor)

    # O Excel come o zero à esquerda do CPF
    if campo == "cpf" and 0 < len(valor) < TAMANHO_CPF:
        valor = valor.zfill(TAMANHO_CPF)

    return valor


def lote_de_linha(linha: str) -> Lote:
    """Converte 'CPF,Nome,Banco,Agência,Conta' em um Lote validado."""
    separador = ";" if ";" in linha else ("\t" if "\t" in linha else ",")
    partes = [parte.strip() for parte in linha.split(separador)]

    if len(partes) != len(ROTULOS):
        raise ValueError(f"esperado {len(ROTULOS)} campos, encontrado {len(partes)}")

    lote = Lote(**{campo: limpar(campo, valor) for campo, valor in zip(ROTULOS, partes)})

    if partes[2] and not lote.banco:
        raise ValueError(f"banco não reconhecido: {partes[2]}")

    if lote.faltando():
        raise ValueError("campos vazios: " + ", ".join(lote.faltando()))

    if not lote.cpf_valido():
        raise ValueError(f"CPF deve ter {TAMANHO_CPF} dígitos")

    return lote
