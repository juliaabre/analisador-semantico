
EPS = "ε"
FIM = "$"

GRAMATICA: dict[str, list[list[str]]] = {
    # 1. Início do programa
    "PROG": [["public", "class", "id", "{",
              "public", "static", "void", "id", "(", ")", "{", "CMDS", "}",
              "}"]],
    # 2. Comandos
    "CMDS": [["CMD", "CMDS"], []],
    "CMD": [["DECL"], ["ATRIB"], ["IF_STMT"], ["WHILE_STMT"]],
    # 3. Declarações
    "DECL": [["TIPO", "id", ";"]],
    "TIPO": [["int"], ["float"], ["char"]],
    # 4. Atribuição, if-else fatorado e while (diferencial)
    "ATRIB": [["id", "=", "E", ";"]],
    "IF_STMT": [["if", "(", "COND", ")", "{", "CMDS", "}", "SENAO"]],
    "SENAO": [["else", "{", "CMDS", "}"], []],
    "WHILE_STMT": [["while", "(", "COND", ")", "{", "CMDS", "}"]],
    # 5. Condição relacional
    "COND": [["E", "OP_REL", "E"]],
    "OP_REL": [["=="], ["!="], ["<"], [">"]],
    # 6. Expressões aritméticas (sem recursão à esquerda)
    "E": [["T", "E'"]],
    "E'": [["+", "T", "E'"], ["-", "T", "E'"], []],
    "T": [["F", "T'"]],
    "T'": [["*", "F", "T'"], ["/", "F", "T'"], []],
    "F": [["(", "E", ")"], ["id"], ["num"], ["char_lit"]],
}

SIMBOLO_INICIAL = "PROG"
NAO_TERMINAIS = set(GRAMATICA)


def eh_terminal(simbolo: str) -> bool:
    return simbolo not in NAO_TERMINAIS



def first_de_sequencia(seq, first):
    """FIRST de uma sequência de símbolos (contém ε se toda a sequência deriva ε)."""
    resultado = set()
    for s in seq:
        f = {s} if eh_terminal(s) else first[s]
        resultado |= f - {EPS}
        if EPS not in f:
            return resultado
    resultado.add(EPS)
    return resultado


def calcular_first():
    first = {A: set() for A in GRAMATICA}
    mudou = True
    while mudou:
        mudou = False
        for A, producoes in GRAMATICA.items():
            for prod in producoes:
                novo = first_de_sequencia(prod, first)
                if not novo <= first[A]:
                    first[A] |= novo
                    mudou = True
    return first


def calcular_follow(first):
    follow = {A: set() for A in GRAMATICA}
    follow[SIMBOLO_INICIAL].add(FIM)
    mudou = True
    while mudou:
        mudou = False
        for A, producoes in GRAMATICA.items():
            for prod in producoes:
                for i, B in enumerate(prod):
                    if eh_terminal(B):
                        continue
                    resto = first_de_sequencia(prod[i + 1:], first)
                    novo = (resto - {EPS}) | (follow[A] if EPS in resto else set())
                    if not novo <= follow[B]:
                        follow[B] |= novo
                        mudou = True
    return follow


def construir_tabela(first, follow):
    """M[A, a] = produção. Lança exceção se houver conflito (gramática não LL(1))."""
    tabela: dict[tuple[str, str], list[str]] = {}
    for A, producoes in GRAMATICA.items():
        for prod in producoes:
            f = first_de_sequencia(prod, first)
            destinos = (f - {EPS}) | (follow[A] if EPS in f else set())
            for a in destinos:
                if (A, a) in tabela:
                    raise ValueError(f"Conflito LL(1) em M[{A}, {a}]")
                tabela[(A, a)] = prod
    return tabela


FIRST = calcular_first()
FOLLOW = calcular_follow(FIRST)
TABELA = construir_tabela(FIRST, FOLLOW)



class No:

    def __init__(self, simbolo: str):
        self.simbolo = simbolo
        self.filhos: list["No"] = []
        self.token = None

    @property
    def eh_epsilon(self) -> bool:
        """True quando o não-terminal foi expandido pela produção vazia."""
        return len(self.filhos) == 1 and self.filhos[0].simbolo == EPS

    def imprimir(self, prefixo="", ultimo=True, raiz=True):
        rotulo = self.simbolo
        if self.token is not None and self.simbolo in ("id", "num", "char_lit"):
            rotulo += f" ({self.token.lexema})"
        conector = "" if raiz else ("└── " if ultimo else "├── ")
        linhas = [prefixo + conector + rotulo]
        novo_prefixo = prefixo if raiz else prefixo + ("    " if ultimo else "│   ")
        for i, filho in enumerate(self.filhos):
            linhas.extend(filho.imprimir(novo_prefixo, i == len(self.filhos) - 1, False))
        return linhas


class ErroSintatico(Exception):
    def __init__(self, mensagem, token):
        super().__init__(mensagem)
        self.token = token

    def __str__(self):
        t = self.token
        return f"Erro Sintático (linha {t.linha}, col {t.coluna}): {self.args[0]}"



class AnalisadorSintatico:
    def __init__(self, tokens):
        self.tokens = tokens

    def analisar(self) -> No:
        raiz = No(SIMBOLO_INICIAL)
        pilha = [No(FIM), raiz]
        i = 0

        while pilha:
            topo = pilha.pop()
            a = self.tokens[i]

            if topo.simbolo == FIM:
                if a.tipo == FIM:
                    return raiz
                raise ErroSintatico(f"símbolo '{a.lexema}' após o fim do programa", a)

            if eh_terminal(topo.simbolo):
                if topo.simbolo == a.tipo:
                    topo.token = a
                    i += 1
                else:
                    raise ErroSintatico(
                        f"esperado '{topo.simbolo}', encontrado '{a.lexema}'", a)
                continue

            producao = TABELA.get((topo.simbolo, a.tipo))
            if producao is None:
                esperados = sorted(t for (A, t) in TABELA if A == topo.simbolo)
                raise ErroSintatico(
                    f"token inesperado '{a.lexema}' ao analisar {topo.simbolo}; "
                    f"esperado um de: {', '.join(esperados)}", a)

            if producao:
                topo.filhos = [No(s) for s in producao]
                for filho in reversed(topo.filhos):
                    pilha.append(filho)
            else:
                topo.filhos = [No(EPS)]

        raise ErroSintatico("pilha esvaziada inesperadamente", self.tokens[i])
