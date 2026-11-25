from dataclasses import dataclass
from collections import OrderedDict


@dataclass
class Symbol:
    nome: str
    ocorrencias: int = 0


class SymbolTable:
    """Tabela de símbolos do analisador léxico.

    Palavras-chave não são inseridas nesta tabela.
    """

    def __init__(self) -> None:
        self._symbols: OrderedDict[str, Symbol] = OrderedDict()

    def add(self, nome: str) -> Symbol:
        if nome not in self._symbols:
            self._symbols[nome] = Symbol(nome=nome, ocorrencias=0)
        self._symbols[nome].ocorrencias += 1
        return self._symbols[nome]

    def as_list(self) -> list[dict]:
        return [
            {"identificador": symbol.nome, "ocorrencias": symbol.ocorrencias}
            for symbol in self._symbols.values()
        ]

    def __len__(self) -> int:
        return len(self._symbols)
