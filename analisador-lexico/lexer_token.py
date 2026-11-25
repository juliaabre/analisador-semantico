from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Token:
    tipo: str
    lexema: str
    atributo: Optional[object] = None
    linha: int = 1
    coluna: int = 1

    def __str__(self) -> str:
        atributo = "" if self.atributo is None else f", atributo={self.atributo!r}"
        return (
            f"<{self.tipo}, lexema={self.lexema!r}{atributo}>"
            f" [{self.linha}:{self.coluna}]"
        )

    def to_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "lexema": self.lexema,
            "atributo": self.atributo,
            "linha": self.linha,
            "coluna": self.coluna,
        }
