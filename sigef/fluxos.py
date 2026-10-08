"""Orquestração: percorre os lotes (digitados ou da planilha) e registra o resultado."""

from playwright.sync_api import Page

from .automacao import descrever_erro, fechar_popups, processar_lote
from .config import PREFIXO
from .console import (
    Confirmador,
    coletar_lotes,
    editar_lote,
    escolher_modo_manual,
    inteiro,
)
from .log import logger
from .modelos import ROTULOS, PularLote, ReiniciarLote
from .planilha import (
    abrir_planilha,
    confirmar_colunas,
    escolher_coluna_resultado,
    gravar_resultado,
    lote_da_planilha,
    texto_celula,
    ultima_linha,
)


def _resumo(sucesso, repetidos, pulados, erros) -> None:
    print("\n================ RESUMO ================")
    print(f"   Sucesso:        {sucesso}")
    print(f"   Já cadastrados: {repetidos}")
    print(f"   Pulados:        {pulados}")
    print(f"   Erros:          {erros}")
    logger.info("Resumo: %s ok, %s já cadastrados, %s pulados, %s erros",
                sucesso, repetidos, pulados, erros)


def executar_lotes(context, page: Page) -> None:
    """Modo lote: dados digitados, colados ou lidos de um arquivo."""
    lotes = coletar_lotes()

    if not lotes:
        return

    manual = escolher_modo_manual()
    concluidos, repetidos, pulados, falhas = [], [], [], []

    for numero, lote in enumerate(lotes, 1):

        while True:
            print(f"\n================ LOTE {numero}/{len(lotes)} ================")
            print(f"   {lote}")

            try:
                status, mensagem = processar_lote(page, lote, Confirmador(manual))
                {"OK": concluidos, "JA": repetidos}.get(status, falhas).append(numero)
                print(f"   {PREFIXO[status]}{mensagem}")
                break

            except ReiniciarLote:
                fechar_popups(context, page)
                print(f"\n   Corrija os dados do lote {numero}:")
                editar_lote(lote)
                continue

            except PularLote:
                pulados.append(numero)
                print(f"   Lote {numero} pulado.")
                break

            except Exception as erro:
                falhas.append(numero)
                print(f"   {descrever_erro(erro)}")
                break

            finally:
                fechar_popups(context, page)

    _resumo(len(concluidos), len(repetidos), len(pulados), len(falhas))


def executar_planilha(context, page: Page) -> None:
    """Modo planilha: lê o Excel aberto e devolve o diagnóstico em cada linha."""
    planilha = abrir_planilha()

    if planilha is None:
        return

    pasta, aba = planilha
    colunas, sugestao = confirmar_colunas(aba)

    primeira = inteiro("\nLinha inicial", sugestao)
    final = inteiro("Linha final", max(ultima_linha(aba, colunas), primeira))
    resultado = escolher_coluna_resultado()
    manual = escolher_modo_manual()

    sucesso = repetidos = pulados = erros = 0

    for linha in range(primeira, final + 1):

        lote = lote_da_planilha(aba, linha, colunas)
        banco_bruto = texto_celula(aba.Cells(linha, colunas["banco"]).Value)
        faltando = lote.faltando()

        if len(faltando) == len(ROTULOS) and not banco_bruto:  # linha vazia
            continue

        print(f"\n================ LINHA {linha} ================")
        print(f"   {lote}")

        if banco_bruto and not lote.banco:
            erros += 1
            gravar_resultado(pasta, aba, linha,
                             f"ERRO: banco não reconhecido - {banco_bruto}", resultado)
            continue

        if faltando:
            erros += 1
            gravar_resultado(pasta, aba, linha,
                             "ERRO: campos vazios - " + ", ".join(faltando), resultado)
            continue

        if not lote.cpf_valido():
            erros += 1
            gravar_resultado(pasta, aba, linha, "ERRO: CPF deve ter 11 dígitos", resultado)
            continue

        try:
            status, mensagem = processar_lote(page, lote, Confirmador(manual, editavel=False))

            if status == "ERRO":
                erros += 1
            elif status == "JA":
                repetidos += 1
            else:
                sucesso += 1

            gravar_resultado(pasta, aba, linha, f"{PREFIXO[status]}{mensagem}", resultado)

        except PularLote:
            pulados += 1
            gravar_resultado(pasta, aba, linha, "PULADO pelo usuário", resultado)

        # Timeout ou qualquer outra falha: desiste desta linha e segue para a próxima
        except Exception as erro:
            erros += 1
            gravar_resultado(pasta, aba, linha, descrever_erro(erro), resultado)

        finally:
            fechar_popups(context, page)

    _resumo(sucesso, repetidos, pulados, erros)
