from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Quadruple:
    """Instrução de três endereços representada como quádrupla (op, arg1, arg2, resultado)."""

    op: str
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    resultado: Optional[str] = None

    def to_tac(self) -> str:
        """Converte a quádrupla na linha de Código de Três Endereços."""
        if self.op == "label":
            return f"{self.resultado}:"
        if self.op == "goto":
            return f"goto {self.resultado}"
        if self.op == "ifFalse":
            return f"if False {self.arg1} goto {self.resultado}"
        if self.op == "=":
            return f"{self.resultado} = {self.arg1}"
        if self.op == "float":
            return f"{self.resultado} = float({self.arg1})"
        # Operador binário aritmético ou relacional.
        return f"{self.resultado} = {self.arg1} {self.op} {self.arg2}"


class CodeGenerator:
    """Guarda o código gerado e cria temporários (t1, t2, ...) e rótulos (L1, L2, ...)."""

    def __init__(self) -> None:
        self.quadruplas: list[Quadruple] = []
        self._temps = 0
        self._labels = 0

    def new_temp(self) -> str:
        self._temps += 1
        return f"t{self._temps}"

    def new_label(self) -> str:
        self._labels += 1
        return f"L{self._labels}"

    def emit(self, op: str, arg1=None, arg2=None, resultado=None) -> None:
        self.quadruplas.append(Quadruple(op, arg1, arg2, resultado))

    def tac(self) -> list[str]:
        return [q.to_tac() for q in self.quadruplas]
