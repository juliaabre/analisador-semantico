from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

# Larguras de memória (width) em bytes de cada tipo (Aula 13).
WIDTHS = {"int": 4, "float": 8, "char": 1}


@dataclass
class SemanticSymbol:
    lexema: str
    tipo: str
    width: int
    offset: int
    linha: int


class SemanticSymbolTable:
    """Tabela de Símbolos da análise semântica.

    Diferente da tabela do léxico (Trabalho 1), que só conta ocorrências de
    identificadores, esta guarda as variáveis DECLARADAS com tipo, largura
    (width) e endereço relativo (offset).
    """

    def __init__(self) -> None:
        self._symbols: OrderedDict[str, SemanticSymbol] = OrderedDict()
        self.offset = 0  # inicializado em 0 no main

    def lookup(self, lexema: str) -> Optional[SemanticSymbol]:
        return self._symbols.get(lexema)

    def insert(self, lexema: str, tipo: str, linha: int) -> SemanticSymbol:
        width = WIDTHS[tipo]
        symbol = SemanticSymbol(lexema, tipo, width, self.offset, linha)
        self._symbols[lexema] = symbol
        self.offset += width  # offset = offset + width
        return symbol

    def symbols(self) -> list[SemanticSymbol]:
        return list(self._symbols.values())

    def __len__(self) -> int:
        return len(self._symbols)
