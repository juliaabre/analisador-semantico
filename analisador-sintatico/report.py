from grammar import Grammar
from ll1 import LL1
from ll1_parser import ParseResult
from tree import Node, preorder, render_tree


def print_section(titulo: str) -> None:
    print(f"\n=== {titulo} ===")


def format_set(grammar: Grammar, simbolos: set[str]) -> str:
    return "{ " + ", ".join(grammar.ordered(simbolos)) + " }"


# -------------------------
# Léxico → sintático
# -------------------------

def print_token_mapping(tokens, entrada) -> None:
    print_section("TOKENS DO LÉXICO → TERMINAIS DA GRAMÁTICA")
    print(f"{'#':>4}  {'Tipo (léxico)':<18} {'Lexema':<16} {'Terminal':<10} {'Posição':>8}")
    print("-" * 62)

    for index, (token, simbolo) in enumerate(zip(tokens, entrada), start=1):
        posicao = f"{token.linha}:{token.coluna}"
        print(
            f"{index:>4}  {token.tipo:<18} {token.lexema!r:<16} "
            f"{simbolo.terminal:<10} {posicao:>8}"
        )


def print_lexical_errors(erros) -> None:
    print_section("ERROS LÉXICOS")
    for token in erros:
        print(f"Erro Léxico [linha {token.linha}, coluna {token.coluna}]: "
              f"{token.atributo} (lexema {token.lexema!r})")
    print("\nAnálise sintática não realizada: corrija os erros léxicos primeiro.")


# -------------------------
# Gramática, FIRST, FOLLOW e tabela M
# -------------------------

def print_grammar(grammar: Grammar) -> None:
    print_section("GRAMÁTICA (PRODUÇÕES NUMERADAS)")
    for production in grammar.productions:
        print(f"{production.numero:>3}. {production}")

    print(f"\nSímbolo de partida: {grammar.start}")
    print(f"Não-terminais ({len(grammar.nonterminals)}): {', '.join(grammar.nonterminals)}")
    print(f"Terminais ({len(grammar.terminals)}): {' '.join(grammar.terminals)}")


def print_first_follow(ll1: LL1) -> None:
    grammar = ll1.grammar
    largura = max(len(a) for a in grammar.nonterminals) + 2

    print_section("CONJUNTOS FIRST E FOLLOW")
    linhas = [
        (a, format_set(grammar, ll1.first[a]), format_set(grammar, ll1.follow[a]))
        for a in grammar.nonterminals
    ]
    largura_first = max(len(first) for _, first, _ in linhas)

    print(f"{'Não-terminal':<{max(largura, 12)}}  {'FIRST':<{largura_first}}  FOLLOW")
    print("-" * (max(largura, 12) + largura_first + 40))
    for a, first, follow in linhas:
        print(f"{a:<{max(largura, 12)}}  {first:<{largura_first}}  {follow}")


def print_table(ll1: LL1) -> None:
    grammar = ll1.grammar
    usados = {terminal for _, terminal in ll1.table}
    colunas = [t for t in grammar.terminals if t in usados]
    vazias = [t for t in grammar.terminals if t not in usados]

    print_section("TABELA DE ANÁLISE PREDITIVA M[não-terminal, terminal]")
    print("Cada célula contém o número da produção; célula vazia = erro sintático.")

    largura_linha = max(len(a) for a in grammar.nonterminals) + 1
    larguras = [max(len(t), 2) for t in colunas]

    cabecalho = " " * largura_linha + "|" + "|".join(
        f"{t:^{w + 2}}" for t, w in zip(colunas, larguras)
    ) + "|"
    separador = "-" * largura_linha + "+" + "+".join("-" * (w + 2) for w in larguras) + "+"

    print(cabecalho)
    print(separador)
    for a in grammar.nonterminals:
        celulas = []
        for t, w in zip(colunas, larguras):
            producao = ll1.table.get((a, t))
            celulas.append(f"{producao.numero if producao else '':^{w + 2}}")
        print(f"{a:<{largura_linha}}|" + "|".join(celulas) + "|")
    print(separador)

    if vazias:
        print(f"Colunas omitidas (todas as células vazias): {' '.join(vazias)}")

    if ll1.is_ll1:
        print("Nenhuma célula possui mais de uma produção: a gramática é LL(1).")
    else:
        print("\nCONFLITOS (a gramática NÃO é LL(1)):")
        for a, t, p1, p2 in ll1.conflicts:
            print(f"  M[{a}, {t}]: {p1.numero}. {p1}  x  {p2.numero}. {p2}")


# -------------------------
# Análise
# -------------------------

def _truncate_left(simbolos, largura: int) -> str:
    texto = " ".join(simbolos)
    if len(texto) <= largura:
        return texto

    partes = []
    tamanho = 2  # "… "
    for simbolo in reversed(simbolos):
        if tamanho + len(simbolo) + 1 > largura:
            break
        partes.append(simbolo)
        tamanho += len(simbolo) + 1
    return "… " + " ".join(reversed(partes))


def _truncate_right(simbolos, largura: int) -> str:
    texto = " ".join(simbolos)
    if len(texto) <= largura:
        return texto

    partes = []
    tamanho = 2  # " …"
    for simbolo in simbolos:
        if tamanho + len(simbolo) + 1 > largura:
            break
        partes.append(simbolo)
        tamanho += len(simbolo) + 1
    return " ".join(partes) + " …"


def print_trace(resultado: ParseResult, truncar: bool = True) -> None:
    terminais = [s.terminal for s in resultado.entrada]
    linhas = []

    for numero, passo in enumerate(resultado.passos, start=1):
        restante = terminais[passo.posicao:]
        if truncar:
            pilha = _truncate_left(passo.pilha, 46)
            entrada = _truncate_right(restante, 36)
        else:
            pilha = " ".join(passo.pilha)
            entrada = " ".join(restante)
        linhas.append((numero, pilha, entrada, passo.acao))

    largura_pilha = max(len("Pilha (topo à direita)"), *(len(p) for _, p, _, _ in linhas))
    largura_entrada = max(len("Entrada"), *(len(e) for _, _, e, _ in linhas))

    print_section("RASTREAMENTO DA ANÁLISE (TRACE)")
    print(f"{'Passo':>5}  {'Pilha (topo à direita)':<{largura_pilha}}  "
          f"{'Entrada':<{largura_entrada}}  Ação")
    print("-" * (largura_pilha + largura_entrada + 60))
    for numero, pilha, entrada, acao in linhas:
        print(f"{numero:>5}  {pilha:<{largura_pilha}}  {entrada:<{largura_entrada}}  {acao}")


def print_verdict(resultado: ParseResult) -> None:
    print_section("RESULTADO")
    if resultado.aceito:
        print("Programa ACEITO com sucesso: sintaticamente válido "
              "(a pilha esvaziou e $ casou com $).")
        return

    print(f"Programa REJEITADO: {len(resultado.erros)} erro(s) sintático(s) encontrado(s).")
    for erro in resultado.erros:
        print(f"  {erro}")


def print_tree(raiz: Node) -> None:
    print_section("ÁRVORE DE DERIVAÇÃO (PRÉ-ORDEM)")
    for linha in render_tree(raiz):
        print(linha)

    print("\nSequência de nós visitados em pré-ordem:")
    linha = ""
    for rotulo in preorder(raiz):
        if linha and len(linha) + 1 + len(rotulo) > 100:
            print(linha)
            linha = rotulo
        else:
            linha = f"{linha} {rotulo}" if linha else rotulo
    if linha:
        print(linha)
