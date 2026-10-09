"""O modo terminal continua funcionando sobre o mesmo núcleo."""

from sigef import console


def _respostas(monkeypatch, *respostas):
    fila = iter(respostas)
    monkeypatch.setattr("builtins.input", lambda *_: next(fila))


def test_modo_lote_no_terminal(navegador, servidor, monkeypatch, capsys):
    _respostas(
        monkeypatch,
        "1",                                  # colar lotes em linhas
        "16899535009;JOAO TERMINAL;237;10;20",
        "",                                   # linha vazia encerra
        "",                                   # confirma a lista
        "2",                                  # confirmação manual
        "s",                                  # incluir credor
        "s",                                  # confirmar domicílio
    )
    console.modo_lotes(navegador)
    saida = capsys.readouterr().out

    assert "Operação realizada com sucesso." in saida
    assert "Sucesso:        1" in saida
    assert ("16899535009", "237", "10", "20") in servidor.estado.domicilios


def test_preparar_navegador_confirma_sessao(navegador, monkeypatch, capsys):
    _respostas(monkeypatch, "")
    console.preparar_navegador(navegador)
    assert "Sessão confirmada." in capsys.readouterr().out
