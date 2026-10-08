"""Registro das execuções em arquivo, para auditoria posterior."""

import logging
from datetime import date

from .config import PASTA_LOGS

logger = logging.getLogger("sigef")


def configurar_log() -> None:
    """Grava um arquivo por dia em ~/.sigef-automacao/logs."""
    if logger.handlers:
        return

    try:
        PASTA_LOGS.mkdir(parents=True, exist_ok=True)
        arquivo = PASTA_LOGS / f"cadastrar-{date.today():%Y-%m-%d}.log"
        manipulador = logging.FileHandler(arquivo, encoding="utf-8")
        manipulador.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%H:%M:%S"))
        logger.addHandler(manipulador)
        logger.setLevel(logging.INFO)
    except OSError:
        logger.addHandler(logging.NullHandler())
