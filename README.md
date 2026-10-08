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

---

## Requisitos

- Windows com Google Chrome instalado (o modo planilha exige o Microsoft Excel)
- Python 3.9 ou superior
- Acesso ao SIGEF com permissão nas transações 1028 e 351

## Instalação

```bash
pip install -r requirements.txt
playwright install chromium
```

> O `playwright install` é necessário apenas uma vez. A automação usa o **seu**
> Chrome, não o navegador do Playwright, mas a biblioteca exige o passo.

## Uso

```bash
python Cadastrar.py
```

1. O script procura o Chrome, abre em modo de depuração (porta 9222) com um
   perfil próprio e navega até `http://sigef.sefin.ro.gov.br/`.
2. Faça o login na janela do Chrome e pressione **ENTER** no terminal.
   A sessão só é aceita depois que a tela de credores abrir de fato.
3. Escolha o modo de trabalho no menu.
4. Ao terminar, o menu reaparece: é possível rodar outro lote ou sair.
   **O Chrome permanece aberto** depois que o script encerra.

### Modo lote

Três formas de informar os dados:

| Opção | Como |
|---|---|
| Colar lotes em linhas | `CPF,Nome,Código do Banco,Agência,Conta` — um por linha, separador `,` `;` ou TAB; linha vazia encerra |
| Digitar campo por campo | Guiado, campo a campo |
| Carregar de arquivo | `.csv` ou `.txt` no mesmo formato |

Cada linha é independente: os cinco campos pertencem sempre à mesma pessoa.

### Modo planilha

Lê uma pasta de trabalho **já aberta no Excel** (ou abre pelo caminho) e
processa linha a linha.

- As colunas são detectadas pelo cabeçalho (`SERVIDOR`, `CPF`, `BANCO`,
  `AGÊNCIA`, `C/C`, entre outros nomes aceitos) e exibidas para conferência,
  com exemplo da primeira linha de dados. É possível corrigir manualmente.
- Sem cabeçalho reconhecível, usa o padrão: **D** = Nome, **E** = CPF,
  **F** = Banco, **G** = Agência, **H** = Conta.
- O diagnóstico é gravado na coluna escolhida (padrão **J**), sobrescrevendo o
  conteúdo anterior, e a pasta é salva a cada linha.

Diagnóstico gravado:

| Situação | Texto na coluna |
|---|---|
| Sucesso | `Operação realizada com sucesso.` |
| Já existia | `JÁ CADASTRADO: ...` |
| Falha | `ERRO: ...` |

Filtrando a coluna por `ERRO:` aparecem apenas as linhas que exigem atenção.

### Confirmação manual

Em qualquer modo é possível escolher confirmação **automática** ou **manual**.
No manual, antes de incluir o credor e antes de confirmar o domicílio bancário,
os dados são exibidos com as opções:

| Tecla | Ação |
|---|---|
| `S` | Confirma e continua |
| `T` | Confirma e não pergunta mais neste lote |
| `N` | Corrige os dados e reinicia **apenas este lote** (modo lote) |
| `P` | Pula o lote/linha |

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
em maiúsculas) ao dicionário `BANCOS` em `sigef/bancos.py`.

## Tolerância a falhas

- Timeout de 10 s para localizar qualquer elemento.
- Falha em uma linha não interrompe as demais: o motivo é registrado e a
  automação recomeça na linha seguinte, a partir da tela inicial.
- Abas de pesquisa do SIGEF são fechadas entre as linhas.
- Execuções ficam registradas em `~/.sigef-automacao/logs`.

## Estrutura

```
Cadastrar.py           ponto de entrada e laço do menu
sigef/
  config.py            URLs, timeouts, colunas padrão, seletores
  bancos.py            tabela e conversão nome -> código
  modelos.py           Lote, validação e normalização dos campos
  console.py           menus, entrada de dados e confirmação manual
  planilha.py          Excel via COM: colunas, leitura e gravação
  navegador.py         Chrome em depuração e login no SIGEF
  automacao.py         fluxo das telas do SIGEF
  fluxos.py            execução dos modos lote e planilha
  log.py               registro em arquivo
legado/                versão original, mantida para referência
```

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| "Chrome não encontrado" | Instalação fora do padrão — abra o Chrome com `--remote-debugging-port=9222` e rode de novo |
| "A tela de credores não abriu" | Login incompleto ou usuário sem permissão na transação 1028 |
| "FALHA ao gravar em J5" | Célula em edição no Excel (pressione ESC) ou pasta somente leitura |
| Diagnóstico não aparece | Coluna oculta ou fora da área visível — o script avisa quando a coluna está oculta |
| `ERRO: timeout` | Página lenta ou elemento ausente; a linha é registrada e a automação segue |

## Licença

MIT — veja [LICENSE](LICENSE).
