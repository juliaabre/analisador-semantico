from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Node:
    """Nó da árvore de derivação."""

    simbolo: str
    lexema: Optional[str] = None
    filhos: list["Node"] = field(default_factory=list)
    # Preenchidos quando um terminal é casado (Trabalho 3: usados pelo semântico).
    linha: Optional[int] = None
    coluna: Optional[int] = None
    tipo_lexico: Optional[str] = None

    @property
    def eh_vazio(self) -> bool:
        """True quando o não-terminal foi derivado pela produção ε."""
        return len(self.filhos) == 1 and self.filhos[0].simbolo == "ε"

    def rotulo(self) -> str:
        if self.lexema is not None and self.lexema != self.simbolo:
            return f"{self.simbolo} ({self.lexema})"
        return self.simbolo


def render_tree(raiz: Node) -> list[str]:
    """Desenha a árvore percorrendo os nós em pré-ordem (raiz, filhos da esquerda para a direita)."""
    linhas = [raiz.rotulo()]

    # Iterativo para não depender do limite de recursão em programas longos.
    pendentes = [(filho, "", i == len(raiz.filhos) - 1) for i, filho in enumerate(raiz.filhos)]
    pendentes.reverse()

    while pendentes:
        no, prefixo, ultimo = pendentes.pop()
        linhas.append(prefixo + ("└── " if ultimo else "├── ") + no.rotulo())

        prefixo_filhos = prefixo + ("    " if ultimo else "│   ")
        for i in range(len(no.filhos) - 1, -1, -1):
            pendentes.append((no.filhos[i], prefixo_filhos, i == len(no.filhos) - 1))

    return linhas


def preorder(raiz: Node) -> list[str]:
    rotulos = []
    pendentes = [raiz]

    while pendentes:
        no = pendentes.pop()
        rotulos.append(no.rotulo())
        pendentes.extend(reversed(no.filhos))

    return rotulos
