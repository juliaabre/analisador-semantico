# Analisador Semântico e Gerador de Código de Três Endereços

Trabalho Prático 3. Usa o léxico de `../analisador-lexico` e o sintático LL(1) de
`../analisador-sintatico`.

## Execução

```bash
python3 main.py exemplos/Exemplo1_SucessoTAC.java
python3 main.py exemplos/*.java
python3 main.py exemplos/Exemplo1_SucessoTAC.java --tokens --tabelas --trace --arvore
python3 -m unittest testes.py
```

## Tradução Dirigida pela Sintaxe

A SDT é feita por **caminhamento na árvore de derivação** gerada pelo parser LL(1).
`SemanticAnalyzer.visit` chama `visit_<NÃO-TERMINAL>` para cada nó:

- atributos **sintetizados** (`tipo`, `addr`) sobem como retorno;
- atributos **herdados** (`E'.inh`, `T'.inh`) descem como parâmetro, porque a gramática
  LL(1) usa `E -> T E'` no lugar de `E -> E + T`.

## Regras semânticas

| Regra | Implementação |
|---|---|
| Larguras `int=4`, `float=8`, `char=1`; `offset` começa em 0 | `semantic_table.py` |
| Redeclaração e variável não declarada | `visit_DECL`, `visit_ATRIB`, `visit_F` |
| `+ - * /` e `== != < >` só com int/float; int com float gera `float(x)`; char é erro | `binary_operation` |
| Atribuição: tipos iguais ou `float = int` (com `float(...)`); `int = float` e char ↔ número são erro | `visit_ATRIB` |
| Tipo interno `erro` para não repetir mensagens em cascata | `ERROR_TYPE` |

## Código intermediário

Cada instrução é guardada como quádrupla (`intermediate_code.Quadruple`) e convertida
em TAC por `to_tac()`:

| Quádrupla | TAC |
|---|---|
| `(+, a, 5, t1)` | `t1 = a + 5` |
| `(float, b, -, t4)` | `t4 = float(b)` |
| `(=, t2, -, b)` | `b = t2` |
| `(ifFalse, t3, -, L1)` | `if False t3 goto L1` |
| `(goto, -, -, L2)` | `goto L2` |
| `(label, -, -, L1)` | `L1:` |

Padrões gerados:

```text
if-else:  cond → if False t goto L1 → bloco if → goto L2 → L1: → bloco else → L2:
if:       cond → if False t goto L1 → bloco if → L1:
while:    L1: → cond → if False t goto L2 → corpo → goto L1 → L2:
```
