from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

WIDTHS = {"int": 4, "float": 8, "char": 1}


@dataclass
class SemanticSymbol:
    lexema: str
    tipo: str
    width: int
    offset: int
    linha: int


class SemanticSymbolTable:

    def __init__(self) -> None:
        self._symbols: OrderedDict[str, SemanticSymbol] = OrderedDict()
        self.offset = 0 

    def lookup(self, lexema: str) -> Optional[SemanticSymbol]:
        return self._symbols.get(lexema)

    def insert(self, lexema: str, tipo: str, linha: int) -> SemanticSymbol:
        width = WIDTHS[tipo]
        symbol = SemanticSymbol(lexema, tipo, width, self.offset, linha)
        self._symbols[lexema] = symbol
        self.offset += width 
        return symbol

    def symbols(self) -> list[SemanticSymbol]:
        return list(self._symbols.values())

    def __len__(self) -> int:
        return len(self._symbols)
