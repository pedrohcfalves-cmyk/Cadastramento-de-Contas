# Automação de Credores e Domicílios Bancários — SIGEF/RO

Automatiza, no SIGEF da SEFIN/RO, o cadastro de credores pessoa física e a
inclusão do respectivo domicílio bancário, a partir de uma lista digitada ou de
uma planilha do Excel.

Para cada pessoa, a automação:

1. pesquisa o CPF no cadastro de credores;
2. se **não** existir, cadastra o credor (consulta à Receita Federal e inclusão);
3. inclui o domicílio bancário (banco, agência, conta e nome da conta);
4. lê a mensagem de retorno do SIGEF e registra o resultado;
5. volta à tela inicial e segue para a próxima pessoa.

Há duas formas de usar: o **aplicativo com janelas** (`CadastroSIGEF.exe`),
pensado para qualquer pessoa, inclusive idosos, e o **modo terminal**
(`python Cadastrar.py`), o mesmo de antes.

---

## Aplicativo (CadastroSIGEF.exe)

Um único arquivo, sem instalação. Python, Playwright, o suporte ao Excel e as
fontes já estão dentro dele.

### Para quem vai usar

1. Dê dois cliques em **CadastroSIGEF.exe**. Aparece "Abrindo o programa…" e,
   em alguns segundos, a janela.
2. Clique em **Começar**. O programa abre o Google Chrome na página do SIGEF.
3. Entre no SIGEF com seu usuário e senha, volte ao programa e clique em
   **Já entrei no SIGEF**.
4. Escolha **Planilha do Excel** ou **Digitar ou colar**.
5. Escolha se quer **conferir cada pessoa antes de gravar** ou deixar o
   programa fazer tudo direto, e clique em **Começar o cadastro**.
6. Ao final, a tela de resultado mostra quantas pessoas foram cadastradas,
   quantas já tinham cadastro e quais tiveram problema (com o motivo).
7. Se alguma pessoa deu erro, o passo 3 oferece **Refazer as que deram erro**:
   o programa tenta de novo só com elas. No modo planilha, corrija a planilha
   antes — as linhas são lidas de novo. As pessoas com erro ficam guardadas
   enquanto o programa estiver aberto (o botão também aparece no resultado e
   no passo 2).

Recursos pensados para facilitar o uso:

- letras grandes, com os botões **Letra maior / Letra menor** no alto da
  janela (o tamanho escolhido fica guardado);
- a fonte Atkinson Hyperlegible, criada para pessoas com baixa visão;
- a trilha **1 Entrar → 2 Escolher os dados → 3 Cadastrar → 4 Ver o resultado**
  mostra sempre em que passo a pessoa está;
- um único botão verde por tela, sempre no canto inferior direito, e o
  **Voltar** sempre no canto inferior esquerdo;
- botão **Ajuda** (ou F1) com a explicação da tela atual;
- avisos em linguagem simples, com símbolo e cor (✔ cadastrado, ✖ problema);
- conferência do CPF (dígitos verificadores) e do banco enquanto se digita;
- a janela de conferência vem para a frente e toca um aviso sonoro, mesmo que
  a pessoa esteja olhando o Chrome;
- impede abrir o programa duas vezes por engano;
- botão **Parar o cadastro**, que termina a pessoa atual e para.

### Estatísticas e pesquisa de implantação

O botão **Estatísticas**, no alto da janela, mostra quanto tempo a automação
economizou, somando **todas as sessões**:

- cadastros concluídos, já cadastrados, erros e taxa de sucesso;
- tempo médio de um cadastro **à mão** e **com a automação**, e quantas vezes
  mais rápido;
- tempo total economizado e a lista de sessões.

Cada sessão é gravada automaticamente em
`~/.sigef-automacao/estatisticas/<computador>__<usuário>.jsonl` (uma linha por
sessão). **Não são gravados CPF, nome nem dados bancários**: só tempos, a
situação de cada item e o motivo dos erros, com números longos mascarados.

**Tempo manual.** Em **Cronometrar um cadastro manual**, a pessoa escolhe o tipo
(credor novo + conta, ou só a conta), clica em **Começar**, faz o cadastro à mão
no SIGEF e clica em **Terminei**. A média das cronometragens substitui a
estimativa (ajustável em **Ajustar a estimativa**; o padrão é 5 min para credor
novo e 3 min para só a conta). O ideal é cronometrar pelo menos 5 de cada tipo.

**Juntar vários computadores.** Duas formas, que podem ser usadas juntas:

1. **Pasta da rede (automático):** em **Pasta da pesquisa…**, ou para todos os
   computadores de uma vez com um `CadastroSIGEF.ini` ao lado do `.exe` (veja
   `empacotar/CadastroSIGEF.ini.exemplo`). Cada computador grava o seu arquivo
   nessa pasta ao final de cada sessão.
2. **Pen drive / e-mail:** copie os arquivos `.jsonl` de cada computador e use
   **Trazer arquivos de outro computador…**.

Em **Todos os computadores** os dados são somados sem repetir sessões.

**Relatório.** **Gerar relatório** cria em `Documentos\Relatorios Cadastro SIGEF`:

| Arquivo | Conteúdo |
|---|---|
| `dados_pesquisa.xlsx` | Resumo com gráficos, Sessões, Itens, Tempos manuais, Por computador, Por dia, Motivos de erro e Metodologia |
| `relatorio.html` | Página com os números principais, para projetar ou imprimir em PDF |
| `dados_brutos.jsonl` | Todos os registros, para juntar com outros computadores |

**Metodologia (conservadora):** tempo manual equivalente = cadastros concluídos
× tempo manual médio do mesmo tipo; tempo da automação = soma do tempo de
máquina de **todos** os itens enviados ao SIGEF (inclusive erros e já
cadastrados); o tempo de pessoas conferindo na tela é contado à parte;
economia = manual equivalente − automação.

O modo terminal também grava as sessões e mostra a economia ao final de cada
lote.

### Distribuir para vários computadores

Copie **só o arquivo `dist/CadastroSIGEF.exe`** para cada computador (pen
drive, pasta da rede ou e-mail) e, se quiser, crie um atalho na Área de
Trabalho. Cada computador precisa apenas de:

- Windows 10 ou 11 (64 bits);
- Google Chrome **ou** Microsoft Edge (o Edge já vem no Windows e é usado
  quando o Chrome não existe);
- Microsoft Excel, só para o modo planilha;
- (opcional) acesso de gravação à pasta da pesquisa na rede;
- usuário do SIGEF com permissão nas transações 1028 e 351.

> Na primeira vez, o Windows pode mostrar "O Windows protegeu o computador"
> (SmartScreen), porque o arquivo não tem assinatura digital. Clique em
> **Mais informações → Executar assim mesmo**. Se o antivírus da rede
> bloquear, peça ao suporte para liberar o `CadastroSIGEF.exe`.

O navegador é aberto com um perfil próprio (`~/.sigef-automacao/chrome`), sem
misturar com o Chrome pessoal, e **continua aberto** quando o programa fecha.

### Gerar o executável de novo

No Windows, na pasta do projeto:

```bash
pip install -r requirements-dev.txt
pyinstaller empacotar/CadastroSIGEF.spec --noconfirm
```

O arquivo sai em `dist/CadastroSIGEF.exe`. A receita (`empacotar/`) embute o
driver do Playwright, o pywin32, as fontes, o ícone, a tela de abertura e o
runtime do Visual C++.

Para abrir a mesma janela sem gerar o executável: `pythonw CadastrarApp.pyw`.

---

## Modo terminal

### Requisitos

- Windows com Google Chrome ou Microsoft Edge (o modo planilha exige o Excel)
- Python 3.9 ou superior
- Acesso ao SIGEF com permissão nas transações 1028 e 351

### Instalação

```bash
pip install -r requirements.txt
```

> A automação usa o **seu** Chrome (via porta de depuração), por isso não é
> preciso rodar `playwright install`.

### Uso

```bash
python Cadastrar.py
```

1. O script procura o Chrome (ou o Edge), abre em modo de depuração (porta
   9222) com um perfil próprio e navega até `http://sigef.sefin.ro.gov.br/`.
2. Faça o login na janela do navegador e pressione **ENTER** no terminal.
   A sessão só é aceita depois que a tela de credores abrir de fato.
3. Escolha o modo de trabalho no menu.
4. Ao terminar, o menu reaparece: é possível rodar outro lote ou sair.
   **O navegador permanece aberto** depois que o script encerra.

### Modo lote

Três formas de informar os dados:

| Opção | Como |
|---|---|
| Colar lotes em linhas | `CPF,Nome,Código do Banco,Agência,Conta` — um por linha, separador `,` `;` ou TAB; linha vazia encerra |
| Digitar campo por campo | Guiado, campo a campo |
| Carregar de arquivo | `.csv` ou `.txt` no mesmo formato (UTF-8 ou o padrão do Excel) |

Cada linha é independente: os cinco campos pertencem sempre à mesma pessoa.

**Agência e conta** são enviadas ao SIGEF como estão escritas: aceitam qualquer
letra, número, `-` e `.` (ex.: `1234-5`, `12.345-X`, `0012345-P`). Letras viram
maiúsculas; espaços e outros símbolos são descartados. O CPF continua só com
números.

### Modo planilha

Lê uma pasta de trabalho **já aberta no Excel** (ou abre pelo caminho) e
processa linha a linha.

- As colunas são detectadas pelo cabeçalho (`SERVIDOR`, `CPF`, `BANCO`,
  `AGÊNCIA`, `C/C`, entre outros nomes aceitos) e exibidas para conferência,
  com exemplo da primeira linha de dados. É possível corrigir manualmente.
- Sem cabeçalho reconhecível, usa o padrão: **D** = Nome, **E** = CPF,
  **F** = Banco, **G** = Agência, **H** = Conta.
- O diagnóstico é gravado na coluna escolhida (padrão **J**), sobrescrevendo o
  conteúdo anterior, e a pasta é salva a cada linha. No aplicativo, a coluna
  do resultado não pode ser uma das colunas de dados.

Diagnóstico gravado:

| Situação | Texto na coluna |
|---|---|
| Sucesso | `Operação realizada com sucesso.` |
| Já existia | `JÁ CADASTRADO: ...` |
| Pulado na conferência | `PULADO pelo usuário` |
| Falha | `ERRO: ...` |

Filtrando a coluna por `ERRO:` aparecem apenas as linhas que exigem atenção.

### Refazer os itens com erro

Quando a execução passa por **todos** os itens (sem ser parada no meio), os
que deram erro ficam guardados na memória daquela sessão do programa:

- no aplicativo, o passo 3 mostra **Refazer as que deram erro (N)** e
  **Ver o resultado**; o botão também aparece no resultado e no passo 2;
- no terminal, a pergunta "Refazer só esses agora?" aparece ao fim;
- no modo planilha, só as linhas com erro são relidas do Excel (pegando as
  correções) e o diagnóstico é regravado nelas;
- cada repetição guarda só o que voltou a falhar. Nada disso é gravado em
  disco: ao fechar o programa, a lista some.

### Confirmação manual

Em qualquer modo é possível escolher confirmação **automática** ou **manual**.
No manual, antes de incluir o credor e antes de confirmar o domicílio bancário,
os dados são exibidos com as opções:

| Terminal | Aplicativo | Ação |
|---|---|---|
| `S` | Sim, está certo | Confirma e continua |
| `T` | Sim, e não perguntar mais sobre esta pessoa | Confirma e não pergunta mais neste lote |
| `N` | Corrigir os dados | Corrige e reinicia **apenas este lote** (modo lote) |
| `P` | Pular esta pessoa | Pula o lote/linha |

## Conversão do nome do banco

A coluna do banco aceita o código (`001`, `1`, `341`) ou o nome. São
reconhecidos, sem distinção de acento ou maiúsculas:

| | | | |
|---|---|---|---|
| 001 Banco do Brasil | 003 Banco da Amazônia | 004 Banco do Nordeste | 021 Banestes |
| 033 Santander | 041 Banrisul | 070 BRB | 077 Inter |
| 104 Caixa | 197 Stone | 208 BTG Pactual | 212 Original |
| 237 Bradesco | 260 Nubank | 290 PagBank | 323 Mercado Pago |
| 336 C6 Bank | 341 Itaú | 380 PicPay | 403 Cora |
| 422 Safra | 655 BV | 735 Neon | 748 Sicredi |
| 756 Sicoob | | | |

Para incluir outros, acrescente o apelido normalizado (sem acento, sem espaço,
em maiúsculas) ao dicionário `BANCOS` e o nome de exibição a `NOMES`, em
`sigef/bancos.py`.

## Tolerância a falhas

- Timeout de 10 s para localizar qualquer elemento e de 30 s para a tela
  carregar; 60 s para o aviso de retorno do botão **Incluir** do credor.
- Troca de telas só começa depois que a tela anterior assenta; se o SIGEF
  disparar um postback no meio, a navegação é repetida (até 3 vezes).
- Falha em uma linha não interrompe as demais: o motivo é registrado e a
  automação recomeça na linha seguinte, a partir da tela inicial.
- Se o navegador for fechado no meio, o cadastro para (em vez de marcar erro em
  todas as linhas restantes) e o aplicativo volta à tela de login.
- Abas de pesquisa do SIGEF são fechadas entre as linhas.
- Execuções ficam registradas em `~/.sigef-automacao/logs` (botão **Abrir a
  pasta de registros** no aplicativo).

## Testes

Os testes rodam a automação de verdade contra um **SIGEF simulado**
(`testes/sigef_simulado.py`), que imita as telas 1028 e 351 com os mesmos IDs,
pop-ups e mensagens, e contra um Excel falso (`testes/excel_falso.py`):

```bash
pip install -r requirements-dev.txt
pytest testes
```

`testes/roteiro_janela.py` percorre o aplicativo inteiro clicando como uma
pessoa (modo digitar com conferência e correção, modo planilha, letras
maiores) e salva capturas de cada tela.

## Estrutura

```
Cadastrar.py           entrada do modo terminal
CadastrarApp.pyw       entrada do aplicativo (janelas)
sigef/
  config.py            URLs, timeouts, âncoras de tela, colunas, navegadores
  bancos.py            tabela e conversão nome <-> código
  modelos.py           Lote, validação, CPF e leitura de listas
  navegador.py         Chrome/Edge em depuração, conexão e login no SIGEF
  automacao.py         fluxo das telas do SIGEF e conferência antes do clique
  fluxos.py            execução dos modos lote e planilha (sem interface)
  planilha.py          Excel via COM: colunas, leitura em bloco e gravação
  console.py           interface de terminal
  log.py               registro em arquivo
  estatisticas.py      coleta, gravação e cálculo das estatísticas da pesquisa
  relatorio.py         relatório: Excel, página HTML e dados brutos
  interface/           aplicativo em janelas (Tkinter)
    app.py             janela principal, trilha de passos e navegação
    telas.py           as telas do assistente
    dialogos.py        conferência, correção, colar lista e recados
    componentes.py     botões, caixas de aviso, tabelas
    estilo.py          cores, fontes e tamanho das letras
    trabalhador.py     linha de execução do navegador e do Excel
    fontes/            Atkinson Hyperlegible (licença OFL)
empacotar/             receita do PyInstaller, ícone e tela de abertura
testes/                SIGEF simulado, Excel falso e testes
legado/                versão original, mantida para referência
```

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| "Não encontrei o Google Chrome nem o Microsoft Edge" | Instalação fora do padrão — abra o Chrome com `--remote-debugging-port=9222` e tente de novo |
| "Ainda não consegui abrir a tela de credores" | Login incompleto ou usuário sem permissão na transação 1028 |
| "FALHA ao gravar em J5" | Célula em edição no Excel (pressione ESC) ou pasta somente leitura |
| Diagnóstico não aparece | Coluna oculta — o programa avisa quando a coluna está oculta |
| `ERRO: timeout` | Página lenta ou elemento ausente; a linha é registrada e a automação segue |
| Windows bloqueia o .exe | SmartScreen/antivírus: veja "Distribuir para vários computadores" |

## Licença

MIT — veja [LICENSE](LICENSE). A fonte Atkinson Hyperlegible é distribuída sob
a SIL Open Font License (`sigef/interface/fontes/OFL.txt`).
