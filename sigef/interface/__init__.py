"""Interface em janelas (Tkinter) da automação, pensada para uso por pessoas idosas."""


def iniciar() -> None:
    from .app import iniciar as _iniciar

    _iniciar()
