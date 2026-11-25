# Analisador Sintático Preditivo LL(1) para Java

Trabalho Prático 2 – Implementação Manual de um Analisador Sintático.

## Características

- Implementado em Python, sem Yacc/Bison/PLY/ANTLR.
- Analisador **descendente preditivo dirigido por tabela** (LL(1)), com pilha explícita.
- Integrado ao analisador léxico do Trabalho 1 (`../analisador-lexico`).
- Mostra:
  - os tokens do léxico e o terminal da gramática correspondente;
  - as produções numeradas da gramática;
  - os conjuntos **FIRST** e **FOLLOW** de todos os não-terminais;
  - a **Tabela de Análise Preditiva M**;
  - o **rastreamento passo a passo** (Pilha, Entrada e Ação);
  - o **veredito final** (aceito ou erros com linha, coluna, token encontrado e esperado).
- Diferenciais:
  - FIRST, FOLLOW e a tabela M são **calculados pelo código** a partir de `gramatica.txt`
    (com detecção de conflitos LL(1));
  - **árvore de derivação** em pré-ordem;
  - **recuperação de erros em modo pânico**, sincronizando em `;`, `}` e no início
    de comandos, para encontrar vários erros no mesmo arquivo.

## Requisitos

Python 3.10+. A pasta `analisador-lexico` deve estar ao lado desta pasta.

## Execução

```bash
python3 main.py exemplos/Exemplo1_Sucesso.java
python3 main.py exemplos/Exemplo2_ErroTabela.java
python3 main.py exemplos/Exemplo3_ErroPilha.java
python3 main.py exemplos/Exemplo4_MultiplosErros.java
```

Opções:

| Opção | Efeito |
|---|---|
| `--sem-tokens` | não mostra a lista de tokens |
| `--sem-tabelas` | não mostra gramática, FIRST/FOLLOW e tabela M |
| `--sem-trace` | não mostra o rastreamento da pilha |
| `--sem-arvore` | não mostra a árvore de derivação |
| `--sem-truncar` | mostra pilha e entrada completas no trace |
| `--parar-no-primeiro-erro` | desativa o modo pânico |
| `--gramatica ARQ` | usa outro arquivo de gramática |

Para salvar a saída em arquivo: `python3 main.py exemplos/Exemplo1_Sucesso.java > saida.txt`.

## Estrutura

```text
analisador-sintatico/
├── main.py            # ponto de entrada: léxico → sintático → relatórios
├── gramatica.txt      # produções da gramática LL(1) do trabalho
├── grammar.py         # leitura da gramática (produções, terminais, não-terminais)
├── ll1.py             # cálculo de FIRST, FOLLOW e da tabela M
├── token_adapter.py   # converte tokens do léxico em terminais (IDENTIFIER → id ...)
├── ll1_parser.py      # algoritmo da pilha, mensagens de erro e modo pânico
├── tree.py            # árvore de derivação
├── report.py          # impressão das tabelas, do trace e do resultado
└── exemplos/
```

## Integração com o léxico

O sintático trabalha com o **tipo** do token, não com o lexema:

| Tipo do léxico | Terminal |
|---|---|
| `IDENTIFIER` | `id` |
| `INTEGER_LITERAL`, `FLOAT_LITERAL` | `num` |
| `CHAR_LITERAL` (Trabalho 3) | `char_lit` |
| palavras-chave, operadores e delimitadores | o próprio lexema (`int`, `==`, `;` ...) |

O léxico classifica `main` como `IDENTIFIER`, por isso a produção inicial usa `id`
para o nome do método. Se houver erros léxicos, eles são listados e a análise
sintática não é executada.

## Algoritmo

```text
pilha = [$, PROG]
repita:
    se topo == $ e entrada == $       → fim (aceito se não houve erros)
    se topo é terminal:
        topo == token                 → desempilha e avança ("casar")
        senão                         → erro de topo da pilha
    se topo é não-terminal:
        M[topo, token] = A → α        → desempilha A e empilha α invertido
        célula vazia                  → erro de tabela
```

## Recuperação de erros

Ao encontrar um erro, o analisador o registra e tenta continuar:

1. **Terminal faltando:** se o topo é um terminal que não casa com a entrada, mas o
   símbolo logo abaixo dele aceita o token atual, o terminal é desempilhado como se
   tivesse sido inserido (ex.: `a = (10 + 5;` ou `main()` sem `{`).
2. **Modo pânico** (demais casos):
   1. descarta tokens da entrada até um `;` (consumido), um `}` ou uma palavra que só
      pode iniciar comando (`int`, `float`, `char`, `if`). Um bloco `{ ... }`
      encontrado no caminho é descartado inteiro;
   2. desempilha até o `CMDS` (ou `SENAO`) do bloco que está aberto na entrada,
      contando os `{` desempilhados sem serem casados;
   3. continua a análise a partir do próximo comando.
