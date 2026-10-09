# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [2.2.1] - 2026-10-09

### Corrigido
- Agência e conta com **X** (dígito verificador, ex.: `12345-X`): o X deixou de
  ser descartado ao ler a planilha, o formulário ou a lista colada. Pontos,
  traços e espaços continuam sendo removidos, e `x` minúsculo vira `X`.
  O CPF segue aceitando só números.

## [2.2.0] - 2026-10-09

### Adicionado
- Tela **Estatísticas**: cadastros concluídos, tempo médio à mão × com a
  automação, vezes mais rápido, tempo economizado, taxa de sucesso e sessões.
- Coleta automática de cada sessão (janela e terminal), sem CPF, nome ou dados
  bancários, em `~/.sigef-automacao/estatisticas`.
- Cronômetro de cadastros manuais (por tipo) e estimativa ajustável.
- Pasta da pesquisa na rede (pela tela ou por `CadastroSIGEF.ini`) e importação
  de arquivos de outros computadores, somando todos sem repetir sessões.
- Relatório: `dados_pesquisa.xlsx` (com gráficos e metodologia),
  `relatorio.html` e `dados_brutos.jsonl`.
- Tela de resultado mostra o tempo da automação e a economia da sessão.

### Alterado
- `Confirmador` passou a anotar o caminho (credor novo/existente) e o tempo de
  conferência; `executar_lotes`/`executar_planilha` aceitam uma `Sessao`.
- Dependência nova: `openpyxl` (embutida no executável).

## [2.1.0] - 2026-10-08

### Adicionado
- Aplicativo com janelas (`CadastrarApp.pyw`) e executável único
  `CadastroSIGEF.exe` (PyInstaller), com todas as dependências embutidas.
- Interface pensada para pessoas idosas: assistente em 4 passos, letras grandes
  ajustáveis, fonte Atkinson Hyperlegible, alto contraste, ajuda em cada tela,
  um botão principal por tela sempre no mesmo lugar.
- Conferência manual em janela (com som e trazida para a frente) e correção dos
  dados em formulário.
- Validação dos dígitos do CPF e reconhecimento do banco enquanto se digita.
- Colar lista e abrir `.csv`/`.txt` (UTF-8 ou cp1252) no aplicativo.
- Botão "Parar o cadastro" e proteção contra abrir o programa duas vezes.
- Microsoft Edge usado quando o Chrome não está instalado.
- SIGEF simulado, Excel falso e testes automatizados (`testes/`).

### Alterado
- Núcleo separado da interface: `fluxos.py` não lê mais o teclado; o terminal
  e a janela usam o mesmo código por meio de um `Relator`.
- `planilha.py` lê o cabeçalho e cada linha em uma única chamada ao Excel.
- Se o navegador for fechado durante o cadastro, a execução para em vez de
  marcar erro em todas as linhas restantes.
- `navegador.py` passou a expor a classe `Navegador`.

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
