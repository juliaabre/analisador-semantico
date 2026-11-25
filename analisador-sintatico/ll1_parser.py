from dataclasses import dataclass
from typing import Optional

from grammar import END, EPSILON
from ll1 import LL1
from token_adapter import InputSymbol
from tree import Node


@dataclass(frozen=True)
class TraceStep:
    pilha: tuple[str, ...]  # base ($) no início, topo no fim
    posicao: int            # índice do símbolo atual da entrada
    acao: str


@dataclass(frozen=True)
class SyntaxErrorInfo:
    linha: int
    coluna: int
    mensagem: str

    def __str__(self) -> str:
        return f"Erro Sintático [linha {self.linha}, coluna {self.coluna}]: {self.mensagem}"


@dataclass
class ParseResult:
    entrada: list[InputSymbol]
    passos: list[TraceStep]
    erros: list[SyntaxErrorInfo]
    arvore: Optional[Node]

    @property
    def aceito(self) -> bool:
        return not self.erros


def format_alternatives(itens: list[str]) -> str:
    itens = [f"'{item}'" for item in itens]
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + " ou " + itens[-1]


class PredictiveParser:
    """Analisador sintático descendente preditivo dirigido por tabela (LL(1)).

    A pilha guarda pares (símbolo, nó da árvore). A cada passo:
      - topo terminal: compara com o token atual (casa ou erro);
      - topo não-terminal: consulta M[topo, token] e deriva (ou erro se vazia);
      - topo $ e entrada $: fim da análise.

    Recuperação de erros:
      - terminal faltando: se o topo é um terminal que não casa, mas o símbolo
        logo abaixo dele aceita o token atual, o terminal é desempilhado como
        se tivesse sido inserido (ex.: `)` ou `{` esquecidos);
      - modo pânico: descarta tokens até um ponto de sincronização (`;`, `}`
        ou uma palavra que só pode iniciar comando, como `int`, `if` e `while`) e
        desempilha até um não-terminal âncora (`CMDS` ou `SENAO`), que sabe
        continuar a partir do próximo comando ou do fechamento do bloco.
    """

    MAX_ERRORS = 50

    def __init__(
        self,
        ll1: LL1,
        recuperar: bool = True,
        sincronizacao: str = ";",
        abre_bloco: str = "{",
        fecha_bloco: str = "}",
        ancoras: tuple[str, ...] = ("CMDS", "SENAO"),
        inicio_comando: tuple[str, ...] = ("int", "float", "char", "if", "while"),
    ) -> None:
        self.ll1 = ll1
        self.grammar = ll1.grammar
        self.recuperar = recuperar
        self.sincronizacao = sincronizacao
        self.abre_bloco = abre_bloco
        self.fecha_bloco = fecha_bloco
        self.ancoras = set(ancoras)
        self.inicio_comando = set(inicio_comando)

    def parse(self, entrada: list[InputSymbol]) -> ParseResult:
        if not entrada or entrada[-1].terminal != END:
            raise ValueError("a entrada deve terminar com o marcador $")

        raiz = Node(self.grammar.start)
        pilha: list[tuple[str, Optional[Node]]] = [(END, None), (self.grammar.start, raiz)]
        pos = 0
        passos: list[TraceStep] = []
        erros: list[SyntaxErrorInfo] = []

        def registrar(acao: str) -> None:
            passos.append(TraceStep(tuple(s for s, _ in pilha), pos, acao))

        while True:
            topo, no = pilha[-1]
            atual = entrada[pos]

            if topo == END and atual.terminal == END:
                if erros:
                    registrar("Fim da análise: pilha e entrada chegaram a $ (com erros)")
                else:
                    registrar("Aceitar: pilha e entrada chegaram a $")
                break

            if not self.grammar.is_nonterminal(topo):
                if topo == atual.terminal:
                    registrar(f"Comparar topo da pilha com a entrada: casar '{topo}'")
                    no.lexema = atual.lexema
                    no.linha, no.coluna = atual.linha, atual.coluna
                    no.tipo_lexico = atual.tipo_lexico
                    pilha.pop()
                    pos += 1
                    continue

                if topo == END:
                    mensagem = (
                        f"encontrado {atual.descricao()}, mas esperava-se o fim do programa ($)"
                    )
                else:
                    mensagem = (
                        f"encontrado {atual.descricao()}, mas esperava-se '{topo}' no topo da pilha"
                    )
            else:
                producao = self.ll1.table.get((topo, atual.terminal))

                if producao is not None:
                    registrar(f"Derivar {producao}")
                    pilha.pop()

                    if producao.corpo:
                        no.filhos = [Node(simbolo) for simbolo in producao.corpo]
                        for filho in reversed(no.filhos):
                            pilha.append((filho.simbolo, filho))
                    else:
                        no.filhos = [Node(EPSILON)]
                    continue

                esperados = format_alternatives(self.ll1.expected(topo))
                mensagem = (
                    f"token {atual.descricao()} inesperado; "
                    f"esperava-se {esperados} para derivar {topo}"
                )

            erros.append(SyntaxErrorInfo(atual.linha, atual.coluna, mensagem))
            registrar(f"Erro: {mensagem}")

            if not self.recuperar or len(erros) >= self.MAX_ERRORS:
                break

            if self._insert_missing(pilha, atual, registrar):
                continue

            pos = self._recover(pilha, entrada, pos, passos)
            if pos is None:
                break

        return ParseResult(entrada, passos, erros, raiz if not erros else None)

    # -------------------------
    # Recuperação de erros
    # -------------------------

    def _accepts(self, simbolo: str, terminal: str) -> bool:
        if self.grammar.is_nonterminal(simbolo):
            return (simbolo, terminal) in self.ll1.table
        return simbolo == terminal

    def _insert_missing(self, pilha, atual: InputSymbol, registrar) -> bool:
        topo = pilha[-1][0]
        if topo == END or self.grammar.is_nonterminal(topo) or len(pilha) < 2:
            return False
        if not self._accepts(pilha[-2][0], atual.terminal):
            return False

        registrar(
            f"Recuperação: considerar '{topo}' como faltando "
            f"(desempilhar '{topo}' sem consumir a entrada)"
        )
        pilha.pop()
        return True

    def _recover(self, pilha, entrada, pos, passos) -> Optional[int]:
        pilha_antes = tuple(s for s, _ in pilha)
        pos_antes = pos

        if entrada[pos].terminal == END:
            passos.append(TraceStep(
                pilha_antes, pos, "Recuperação impossível: fim da entrada atingido"
            ))
            return None

        descartados: list[str] = []

        if pilha[-1][0] == END:
            # Sobrou código depois do fim do programa: descarta tudo.
            while entrada[pos].terminal != END:
                descartados.append(entrada[pos].terminal)
                pos += 1
        else:
            # Descarta até `;`, `}` ou início de comando. Um bloco `{ ... }`
            # encontrado no caminho é descartado por inteiro, para não
            # confundir o fechamento de chaves.
            profundidade = 0
            while (terminal := entrada[pos].terminal) != END:
                if profundidade == 0 and (
                    terminal == self.fecha_bloco or terminal in self.inicio_comando
                ):
                    break  # fica na entrada: fecha o bloco atual / inicia o próximo comando

                descartados.append(terminal)
                pos += 1

                if terminal == self.abre_bloco:
                    profundidade += 1
                elif terminal == self.fecha_bloco:
                    profundidade -= 1
                    if profundidade == 0:
                        break
                elif terminal == self.sincronizacao and profundidade == 0:
                    break

        # Desempilha até a âncora (CMDS/SENAO) cujo bloco está aberto na entrada.
        # `saldo` conta os `{` desempilhados sem terem sido casados: enquanto
        # for diferente de zero, o CMDS encontrado pertence a um bloco que a
        # entrada não abriu (ou já fechou), então continua desempilhando.
        desempilhados: list[str] = []
        saldo = 0
        while pilha[-1][0] != END:
            simbolo = pilha[-1][0]
            if simbolo in self.ancoras and saldo == 0:
                break

            pilha.pop()
            desempilhados.append(simbolo)
            if simbolo == self.abre_bloco:
                saldo += 1
            elif simbolo == self.fecha_bloco:
                saldo -= 1

        if pos == pos_antes and not desempilhados:
            # Garante progresso: descarta ao menos o token atual.
            descartados.append(entrada[pos].terminal)
            pos += 1

        acao = (
            "Recuperação (modo pânico): "
            f"descartar da entrada [{' '.join(descartados) or 'nada'}]; "
            f"desempilhar [{' '.join(desempilhados) or 'nada'}]"
        )
        passos.append(TraceStep(pilha_antes, pos_antes, acao))
        return pos
