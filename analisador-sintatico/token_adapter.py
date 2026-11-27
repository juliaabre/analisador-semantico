from dataclasses import dataclass

from grammar import END


@dataclass(frozen=True)
class InputSymbol:

    terminal: str
    lexema: str
    linha: int
    coluna: int
    tipo_lexico: str = "" 

    def descricao(self) -> str:
        if self.terminal == END:
            return "fim do arquivo ($)"
        if self.lexema != self.terminal:
            return f"'{self.terminal}' ({self.lexema})"
        return f"'{self.terminal}'"


IDENTIFIER_TYPES = {"IDENTIFIER"}
NUMBER_TYPES = {"INTEGER_LITERAL", "FLOAT_LITERAL"}
CHAR_TYPES = {"CHAR_LITERAL"}  # Trabalho 3


def to_terminal(token) -> str:
    """Converte o tipo do token do léxico (Trabalho 1) no terminal da gramática.

    Identificadores viram `id`, literais numéricos viram `num` e literais de
    caractere viram `char_lit` (Trabalho 3). Palavras-chave,
    operadores e delimitadores usam o próprio lexema (`int`, `==`, `;` ...).
    Tokens que a gramática não conhece (ex.: `return`, `[`) mantêm o lexema e
    serão rejeitados pela tabela M.
    """
    if token.tipo in IDENTIFIER_TYPES:
        return "id"
    if token.tipo in NUMBER_TYPES:
        return "num"
    if token.tipo in CHAR_TYPES:
        return "char_lit"
    return token.lexema


def tokens_to_input(tokens) -> list[InputSymbol]:
    entrada = [
        InputSymbol(to_terminal(t), t.lexema, t.linha, t.coluna, t.tipo) for t in tokens
    ]

    if tokens:
        ultimo = tokens[-1]
        fim = InputSymbol(END, END, ultimo.linha, ultimo.coluna + len(ultimo.lexema))
    else:
        fim = InputSymbol(END, END, 1, 1)

    entrada.append(fim)
    return entrada
