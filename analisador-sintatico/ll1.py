from grammar import END, EPSILON, Grammar, Production


class LL1:
    """Calcula FIRST, FOLLOW e a tabela de análise preditiva M (Aula 9)."""

    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar
        self.first: dict[str, set[str]] = {}
        self.follow: dict[str, set[str]] = {}
        self.table: dict[tuple[str, str], Production] = {}
        self.conflicts: list[tuple[str, str, Production, Production]] = []

        self._compute_first()
        self._compute_follow()
        self._build_table()

    @property
    def is_ll1(self) -> bool:
        return not self.conflicts

    def first_of(self, simbolos: tuple[str, ...]) -> set[str]:
        """FIRST de uma sequência Y1 Y2 ... Yk.

        Acrescenta FIRST(Y1) - {ε}; se Y1 deriva ε, acrescenta FIRST(Y2) - {ε},
        e assim por diante. Se todos derivam ε (ou a sequência é vazia),
        acrescenta ε.
        """
        resultado: set[str] = set()

        for simbolo in simbolos:
            if self.grammar.is_nonterminal(simbolo):
                first = self.first[simbolo]
            else:
                first = {simbolo}

            resultado |= first - {EPSILON}
            if EPSILON not in first:
                return resultado

        resultado.add(EPSILON)
        return resultado

    def expected(self, nonterminal: str) -> list[str]:
        """Terminais que possuem célula preenchida na linha do não-terminal."""
        return [
            terminal
            for terminal in self.grammar.terminals
            if (nonterminal, terminal) in self.table
        ]

    # -------------------------
    # FIRST
    # -------------------------

    def _compute_first(self) -> None:
        self.first = {a: set() for a in self.grammar.nonterminals}

        # Ponto fixo: repete até nenhum conjunto mudar.
        mudou = True
        while mudou:
            mudou = False
            for production in self.grammar.productions:
                novos = self.first_of(production.corpo) - self.first[production.cabeca]
                if novos:
                    self.first[production.cabeca] |= novos
                    mudou = True

    # -------------------------
    # FOLLOW
    # -------------------------

    def _compute_follow(self) -> None:
        self.follow = {a: set() for a in self.grammar.nonterminals}
        self.follow[self.grammar.start].add(END)

        mudou = True
        while mudou:
            mudou = False
            for production in self.grammar.productions:
                for i, simbolo in enumerate(production.corpo):
                    if not self.grammar.is_nonterminal(simbolo):
                        continue

                    # A → αBβ: FIRST(β) - {ε} entra em FOLLOW(B).
                    # Se β deriva ε (ou é vazio), FOLLOW(A) entra em FOLLOW(B).
                    first_beta = self.first_of(production.corpo[i + 1:])
                    novos = first_beta - {EPSILON}
                    if EPSILON in first_beta:
                        novos |= self.follow[production.cabeca]

                    novos -= self.follow[simbolo]
                    if novos:
                        self.follow[simbolo] |= novos
                        mudou = True

    # -------------------------
    # Tabela M
    # -------------------------

    def _build_table(self) -> None:
        for production in self.grammar.productions:
            first_alpha = self.first_of(production.corpo)

            # A → α entra em M[A, x] para cada x em FIRST(α).
            # Se ε ∈ FIRST(α), entra também em M[A, y] para cada y em FOLLOW(A).
            terminais = first_alpha - {EPSILON}
            if EPSILON in first_alpha:
                terminais |= self.follow[production.cabeca]

            for terminal in self.grammar.ordered(terminais):
                self._add(production.cabeca, terminal, production)

    def _add(self, nonterminal: str, terminal: str, production: Production) -> None:
        atual = self.table.get((nonterminal, terminal))

        if atual is None:
            self.table[(nonterminal, terminal)] = production
        elif atual != production:
            self.conflicts.append((nonterminal, terminal, atual, production))
