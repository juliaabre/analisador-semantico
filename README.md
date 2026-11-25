# Trabalho 3 — Analisador Semântico e Gerador de Código Intermediário

Compilador em **Python 3** (sem bibliotecas externas e sem geradores automáticos) que
continua os Trabalhos 1 (Léxico) e 2 (Sintático LL(1)). Recebe um `.java`, valida-o
léxica e sintaticamente e, por **Tradução Dirigida pela Sintaxe** (caminhamento na
árvore sintática), produz:

1. Tabela de Símbolos (lexema, tipo, width, offset);
2. Veredito da Análise Semântica (aprovado ou lista de erros);
3. Código de Três Endereços (só se não houver erros);
4. **Diferenciais:** comando `while` e representação em **Quádruplas**.

## Estrutura

| Arquivo | Papel |
|---|---|
| `lexico.py` | Analisador léxico manual (tokens com linha/coluna; reconhece `char_lit`) |
| `sintatico.py` | Gramática, FIRST/FOLLOW, tabela LL(1) e parser com pilha que monta a árvore |
| `semantico.py` | SDT: tabela de símbolos, verificação de escopo/tipos, geração de TAC/quádruplas |
| `main.py` | Interface de linha de comando que encadeia as fases e imprime os resultados |
| `testes.py` | Testes automáticos dos exemplos |
| `exemplos/` | Exemplos 1–3 do enunciado + 4 (while) e 5 (erros com char) |

## Como executar

```bash
python3 main.py exemplos/Exemplo1_SucessoTAC.java
python3 main.py exemplos/Exemplo2_ErroEscopo.java
python3 main.py exemplos/Exemplo3_ErroTipos.java
python3 main.py exemplos/*.java                 # todos de uma vez
python3 main.py exemplos/Exemplo1_SucessoTAC.java --tokens --arvore
python3 -m unittest testes.py                   # testes
```

## Gramática (Trabalho 2 + `char_lit` + `while`)

```
PROG       -> public class id { public static void id ( ) { CMDS } }
CMDS       -> CMD CMDS | ε
CMD        -> DECL | ATRIB | IF_STMT | WHILE_STMT
DECL       -> TIPO id ;
TIPO       -> int | float | char
ATRIB      -> id = E ;
IF_STMT    -> if ( COND ) { CMDS } SENAO
SENAO      -> else { CMDS } | ε
WHILE_STMT -> while ( COND ) { CMDS }          (diferencial)
COND       -> E OP_REL E
OP_REL     -> == | != | < | >
E  -> T E'        E' -> + T E' | - T E' | ε
T  -> F T'        T' -> * F T' | / F T' | ε
F  -> ( E ) | id | num | char_lit
```

## Regras semânticas implementadas

- `offset` começa em 0 no `main`; larguras `int=4`, `float=8`, `char=1`; `offset += width`.
- Redeclaração e uso de variável não declarada são erros de escopo.
- `+ - * /` e `== != < >` aceitam só `int`/`float`; `int op int = int`; havendo `float`,
  o `int` é convertido com `float(x)`; qualquer `char` gera erro.
- Atribuição: tipos iguais ou alargamento `float = int` (gera `float(...)`);
  estreitamento `int = float` e `char`↔numérico são erros.
- Um tipo interno `erro` evita mensagens em cascata (ex.: `a = b + 10` com `b` não
  declarada gera só um erro).
