# Trabalho 3 – Analisador Semântico e Gerador de Código Intermediário

Disciplina de Compiladores – 2026.2 · Julia e Nayra

Analisador semântico e gerador de **Código de Três Endereços (TAC)** para um subconjunto
de Java, implementado manualmente em Python (sem geradores automáticos). Ele continua
diretamente os trabalhos anteriores e **reaproveita o analisador léxico do Trabalho 1 e o
analisador sintático LL(1) do Trabalho 2**.

## O que o programa faz

```text
arquivo.java → léxico (Trabalho 1) → tokens → sintático LL(1) (Trabalho 2) → árvore de derivação
             → SDT por caminhamento na árvore (Trabalho 3) → tabela de símbolos + veredito + TAC
```

Para cada arquivo `.java`, o programa mostra:

1. o resultado das análises léxica e sintática (com os erros, se houver);
2. a **Tabela de Símbolos** com lexema, tipo, largura (width) e endereço relativo (offset);
3. o **veredito da análise semântica**: aprovado, ou a lista de erros com linha e coluna;
4. o **Código de Três Endereços**, só quando não há erros léxicos, sintáticos nem semânticos.

### Diferenciais implementados

- Comando **`while`**.
- Código intermediário também representado em **Quádruplas** (op, arg1, arg2, resultado).

## Como rodar

Requisito: Python 3.10 ou superior. Não há dependências externas.

```bash
cd analisador-semantico
python3 main.py exemplos/Exemplo1_SucessoTAC.java
python3 main.py exemplos/Exemplo2_ErroEscopo.java
python3 main.py exemplos/Exemplo3_ErroTipos.java
python3 main.py exemplos/*.java             # todos os exemplos
python3 -m unittest testes.py               # testes automáticos
```

| Arquivo | O que mostra | Resultado esperado |
|---|---|---|
| `Exemplo1_SucessoTAC.java` | Offsets, coerção `float(...)` e rótulos do if-else | Aprovado + TAC |
| `Exemplo2_ErroEscopo.java` | Redeclaração de `a` e uso de `b` não declarada | Reprovado, sem TAC |
| `Exemplo3_ErroTipos.java` | `int = float` e `char = int` | Reprovado, sem TAC |
| `Exemplo4_While.java` | `while`, if sem else e `char` (diferencial) | Aprovado + TAC |
| `Exemplo5_ErroChar.java` | `char` em operação aritmética e relacional | Reprovado, sem TAC |

Opções para mostrar também a saída dos trabalhos anteriores: `--tokens`, `--tabelas`
(gramática, FIRST/FOLLOW e tabela M), `--trace` (pilha LL(1)) e `--arvore`.

## Estrutura do repositório

```text
.
├── analisador-lexico/       # Trabalho 1 (sem alterações)
├── analisador-sintatico/    # Trabalho 2 (com as adaptações abaixo)
└── analisador-semantico/    # Trabalho 3
    ├── main.py              # léxico → sintático → semântico → relatórios
    ├── semantic_analyzer.py # SDT: regras semânticas de cada não-terminal
    ├── semantic_table.py    # tabela de símbolos com tipo, width e offset
    ├── intermediate_code.py # quádruplas, temporários, rótulos e conversão para TAC
    ├── semantic_report.py   # impressão da tabela, do veredito, do TAC e das quádruplas
    ├── testes.py
    └── exemplos/
```

As três pastas precisam ficar lado a lado: o `main.py` do semântico importa o léxico de
`../analisador-lexico` e o sintático de `../analisador-sintatico`.

## Adaptações feitas nos trabalhos anteriores

| Arquivo | Adaptação |
|---|---|
| `analisador-sintatico/gramatica.txt` | `char_lit` na regra `F` (exigido pelo enunciado) e `WHILE_STMT -> while ( COND ) { CMDS }` (diferencial) |
| `analisador-sintatico/token_adapter.py` | `CHAR_LITERAL` do léxico vira o terminal `char_lit`; o tipo original do token é guardado (para saber se `num` é int ou float) |
| `analisador-sintatico/tree.py` | as folhas guardam linha, coluna e tipo do token; propriedade `eh_vazio` para produções ε |
| `analisador-sintatico/ll1_parser.py` | copia linha/coluna/tipo do token para a folha ao casar; `while` inicia comando no modo pânico |

O léxico do Trabalho 1 não precisou de mudanças: ele já reconhecia `while` e literais de
caractere (`CHAR_LITERAL`). FIRST, FOLLOW e a tabela M são recalculados a partir da
gramática atualizada, e a gramática continua LL(1).
