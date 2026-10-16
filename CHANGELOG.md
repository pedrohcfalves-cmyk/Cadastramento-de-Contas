# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [2.3.0] - 2026-10-16

### Adicionado
- **Refazer as que deram erro**: quando o cadastro passa por todas as pessoas e
  alguma dá erro, o passo 3 (Cadastrar) não pula mais direto para o resultado —
  mostra quantas falharam e oferece **Refazer as que deram erro** ou **Ver o
  resultado**. As pessoas com erro ficam guardadas só na memória enquanto o
  programa estiver aberto (nada vai para o disco); o mesmo botão aparece na tela
  de resultado e no passo 2 (De onde vêm os dados?). Cada repetição guarda só o
  que voltou a falhar; quando nada mais falha, a memória é esvaziada.
- Modo planilha: ao refazer, só as linhas que deram erro são lidas **de novo**
  do Excel — o que for corrigido na planilha antes é aproveitado — e o
  diagnóstico é regravado nelas.
- Modo lote: ao refazer, a numeração original (Nº) é mantida.
- Terminal: ao fim de cada execução com erro, pergunta se quer refazer só os
  itens com erro.

### Corrigido
- **Erro no dígito da agência e da conta**: o traço e o ponto eram apagados
  (`12345-6` ia ao SIGEF como `123456`) e só a letra X era aceita, então contas
  com dígito separado ou com outra letra davam erro ou nem eram lidas. Agora
  agência e conta aceitam **qualquer letra, número, `-` e `.`** e vão ao SIGEF
  exatamente como foram escritas (letras em maiúscula). Só espaços e outros
  símbolos são descartados. Vale para a planilha, a lista colada, o arquivo e o
  formulário.

### Alterado
- `executar_planilha` recebe as `linhas` a processar (ex.: `range(primeira,
  final + 1)`) em vez de `primeira` e `final`; `executar_lotes` aceita
  `numeros` para manter a numeração.
- `Resumo.falhas` guarda `(chave, Lote)` de cada item com erro.
- O botão **Voltar** das estatísticas nunca reabre a tela de cadastro (o que
  recomeçaria o cadastro).

## [2.2.2] - 2026-10-09

### Corrigido
- `ERRO: Navigation to ... is interrupted by another navigation to ...`: a troca
  de telas (tela do credor ↔ tela do domicílio bancário) só começa depois que a
  tela anterior assenta, e a navegação é repetida até 3 vezes se o SIGEF
  disparar um postback no meio do caminho.
- A contagem do resultado da pesquisa no pop-up era feita antes de a tela de
  resposta carregar: um credor existente podia ser tratado como inexistente em
  conexões lentas.
- Cada campo passou a ser esperado até ficar visível antes de receber dados, com
  prazo de 30 s para a tela carregar (o prazo geral de 10 s continua valendo
  para procurar elementos).

### Alterado
- Depois do botão **Incluir** da tela de credores, o aviso de sucesso ou de erro
  é aguardado por até 60 s — antes o prazo de 10 s estourava com o SIGEF lento.
- Banco, agência e conta são digitados com 20 ms entre teclas, dando tempo à
  pesquisa automática desses campos.
- `sigef/navegador.py` ganhou `ir_para`, `esperar_carregar` e
  `esperar_elemento`, usados por toda a automação.

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
