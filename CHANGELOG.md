# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [2.0.0] - 2026-10-08

### Adicionado
- Preparação automática do navegador: localiza o Chrome, abre em modo de
  depuração com perfil próprio, vai ao SIGEF e aguarda o login do usuário.
- Menu principal com os modos **lote** e **planilha**, retornando ao menu ao
  final de cada execução até o usuário escolher sair.
- Modo lote: entrada por colagem de linhas, digitação campo a campo ou arquivo
  `.csv`/`.txt`.
- Modo planilha (Excel via `pywin32`): escolha da pasta, da aba, da linha
  inicial/final e da coluna de diagnóstico.
- Detecção automática das colunas pelo cabeçalho, com confirmação e ajuste
  manual.
- Conversão do nome do banco para o código (25 bancos).
- Confirmação manual opcional antes de incluir o credor e de confirmar o
  domicílio bancário, com as opções continuar, liberar o lote, corrigir e
  reiniciar ou pular.
- Diagnóstico por linha na planilha, distinguindo sucesso, já cadastrado e erro.
- Registro das execuções em `~/.sigef-automacao/logs`.

### Alterado
- Código reorganizado no pacote `sigef/`, com `Cadastrar.py` como entrada.
- Timeout de elementos fixado em 10s; falha em uma linha não interrompe as
  demais.
- "Domicílio Bancário Credor já cadastrado(a)" deixa de ser contabilizado como
  erro.
