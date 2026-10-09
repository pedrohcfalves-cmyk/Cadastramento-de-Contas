"""Linha de execução que conversa com o navegador e o Excel.

O Playwright e o Excel (COM) só podem ser usados na linha de execução que os
criou, e a janela (Tkinter) só pode ser mexida na linha principal. Por isso todo
o trabalho pesado roda aqui e a janela recebe os resultados por uma fila,
sem nunca travar.
"""

import os
import queue
import sys
import threading

from ..config import PASTA_LOGS
from ..log import logger
from ..navegador import Navegador

INTERVALO_MS = 60


def _isolar_saida_do_driver() -> None:
    """No executável, o driver do Playwright (Node.js) escreve num arquivo de registro.

    Sem console, o "stderr" herdado pode ser inválido e o Node.js fecha ao iniciar
    ("Connection closed while reading from the driver"). Um arquivo comum sempre funciona.
    """
    if not getattr(sys, "frozen", False):
        return

    from playwright._impl import _transport

    try:
        PASTA_LOGS.mkdir(parents=True, exist_ok=True)
        arquivo = open(PASTA_LOGS / "navegador.log", "a", encoding="utf-8")  # noqa: SIM115
    except OSError:
        arquivo = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115

    _transport._get_stderr_fileno = arquivo.fileno


class Trabalhador:
    def __init__(self, raiz):
        self.raiz = raiz
        self.navegador = None
        self._tarefas = queue.Queue()
        self._para_janela = queue.Queue()
        self._ocupado = False
        threading.Thread(target=self._laco, name="sigef-trabalho", daemon=True).start()
        self.raiz.after(INTERVALO_MS, self._entregar)

    @property
    def ocupado(self) -> bool:
        return self._ocupado

    # ------------------------------------------------------ lado da janela

    def fazer(self, funcao, *args, ok=None, falha=None) -> None:
        """Agenda `funcao(*args)`; `ok(resultado)` ou `falha(erro)` rodam na janela."""
        self._ocupado = True
        self._tarefas.put((funcao, args, ok, falha))

    def encerrar(self) -> None:
        self._tarefas.put(None)

    def _entregar(self) -> None:
        try:
            while True:
                funcao, args, resposta = self._para_janela.get_nowait()

                try:
                    resultado = funcao(*args) if funcao else None
                except Exception as erro:  # nunca derruba a janela
                    logger.exception("Falha na janela")
                    resultado = erro

                if resposta is not None:
                    resposta.put(resultado)
        except queue.Empty:
            pass

        self.raiz.after(INTERVALO_MS, self._entregar)

    # ------------------------------------------------------ lado do trabalho

    def na_janela(self, funcao, *args, esperar: bool = False):
        """Chamado do trabalho: roda `funcao` na janela (e espera a resposta, se pedido)."""
        resposta = queue.Queue(maxsize=1) if esperar else None
        self._para_janela.put((funcao, args, resposta))
        return resposta.get() if esperar else None

    def _laco(self) -> None:
        try:
            import pythoncom  # Excel via COM exige inicializar nesta linha de execução

            pythoncom.CoInitialize()
        except ImportError:
            pass

        playwright = None

        while True:
            tarefa = self._tarefas.get()

            if tarefa is None:
                break

            funcao, args, ok, falha = tarefa

            try:
                if playwright is None:
                    from playwright.sync_api import sync_playwright

                    _isolar_saida_do_driver()
                    playwright = sync_playwright().start()
                    self.navegador = Navegador(playwright)

                resultado = funcao(*args)
            except Exception as erro:
                logger.exception("Falha em %s", getattr(funcao, "__name__", funcao))
                self._ocupado = False

                if falha:
                    self.na_janela(falha, erro)

                continue

            self._ocupado = False

            if ok:
                self.na_janela(ok, resultado)

        if playwright is not None:
            try:
                playwright.stop()  # desconecta; o navegador continua aberto
            except Exception:
                pass
