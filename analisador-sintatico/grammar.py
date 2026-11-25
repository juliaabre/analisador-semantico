from dataclasses import dataclass
from pathlib import Path

EPSILON = "ε"
END = "$"


@dataclass(frozen=True)
class Production:
    numero: int
    cabeca: str
    corpo: tuple[str, ...]  # tupla vazia representa ε

    def __str__(self) -> str:
        corpo = " ".join(self.corpo) if self.corpo else EPSILON
        return f"{self.cabeca} → {corpo}"


class Grammar:
    """Gramática livre de contexto lida de um arquivo texto.

    Cada linha tem o formato `A -> α | β | ε`. Comentários começam com `//`.
    O símbolo de partida é a cabeça da primeira produção. Todo símbolo que
    não aparece como cabeça de produção é considerado terminal.
    """

    TERMINALS_DIRECTIVE = "%terminais"

    def __init__(
        self,
        productions: list[Production],
        declared_terminals: list[str] | None = None,
    ) -> None:
        if not productions:
            raise ValueError("a gramática não possui produções")

        self.productions = productions
        self.start = productions[0].cabeca
        self.nonterminals = list(dict.fromkeys(p.cabeca for p in productions))
        self._nonterminal_set = set(self.nonterminals)

        used = []
        for production in productions:
            for simbolo in production.corpo:
                if simbolo not in self._nonterminal_set and simbolo not in used:
                    used.append(simbolo)

        if declared_terminals is None:
            terminals = used
        else:
            for simbolo in declared_terminals:
                if simbolo in self._nonterminal_set:
                    raise ValueError(
                        f"{simbolo!r} foi declarado como terminal, mas possui produções"
                    )
            for simbolo in used:
                if simbolo not in declared_terminals:
                    raise ValueError(
                        f"símbolo {simbolo!r} não possui produções nem foi "
                        f"declarado em {self.TERMINALS_DIRECTIVE}"
                    )
            terminals = [t for t in declared_terminals if t != END]

        self.terminals = terminals + [END]
        self._order = {simbolo: i for i, simbolo in enumerate(self.terminals)}

    @classmethod
    def from_file(cls, path: str | Path) -> "Grammar":
        return cls.from_text(Path(path).read_text(encoding="utf-8"))

    @classmethod
    def from_text(cls, text: str) -> "Grammar":
        productions: list[Production] = []
        declared_terminals = None

        for numero_linha, linha in enumerate(text.splitlines(), start=1):
            linha = linha.split("//", 1)[0].strip()
            if not linha:
                continue

            if linha.startswith(cls.TERMINALS_DIRECTIVE):
                declared_terminals = linha[len(cls.TERMINALS_DIRECTIVE):].split()
                continue

            linha = linha.replace("→", "->")
            if "->" not in linha:
                raise ValueError(f"linha {numero_linha}: produção sem '->': {linha!r}")

            cabeca, corpo = (parte.strip() for parte in linha.split("->", 1))
            if not cabeca or len(cabeca.split()) != 1:
                raise ValueError(f"linha {numero_linha}: cabeça inválida: {cabeca!r}")

            for alternativa in corpo.split("|"):
                simbolos = alternativa.split()
                if simbolos == [EPSILON]:
                    simbolos = []
                elif not simbolos or EPSILON in simbolos:
                    raise ValueError(
                        f"linha {numero_linha}: alternativa inválida em {cabeca}: "
                        f"{alternativa.strip()!r}"
                    )
                productions.append(
                    Production(len(productions) + 1, cabeca, tuple(simbolos))
                )

        return cls(productions, declared_terminals)

    def is_nonterminal(self, simbolo: str) -> bool:
        return simbolo in self._nonterminal_set

    def ordered(self, simbolos: set[str]) -> list[str]:
        """Ordena terminais na ordem da gramática, com ε por último."""
        return sorted(simbolos, key=lambda s: self._order.get(s, len(self._order)))
