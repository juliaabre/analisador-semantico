from dataclasses import dataclass

from intermediate_code import CodeGenerator
from semantic_table import SemanticSymbolTable
from tree import Node

ERROR_TYPE = "erro"  # tipo interno usado para não gerar erros em cascata
NUMERIC = {"int", "float"}
RELATIONAL = {"==", "!=", "<", ">"}

# Tipo do literal de acordo com o tipo do token do léxico (Trabalho 1).
LITERAL_TYPES = {
    "INTEGER_LITERAL": "int",
    "FLOAT_LITERAL": "float",
    "CHAR_LITERAL": "char",
}


@dataclass
class Attr:
    """Atributos sintetizados de uma expressão: tipo e endereço (variável, temporário ou constante)."""

    tipo: str
    addr: str


@dataclass(frozen=True)
class SemanticErrorInfo:
    linha: int
    coluna: int
    mensagem: str

    def __str__(self) -> str:
        return f"Erro Semântico [linha {self.linha}, coluna {self.coluna}]: {self.mensagem}"


class SemanticAnalyzer:
    """Tradução Dirigida pela Sintaxe (SDT) por caminhamento na árvore de derivação.

    A árvore é a mesma construída pelo analisador LL(1) do Trabalho 2. Cada
    não-terminal possui um método `visit_<NT>` com as regras semânticas das
    suas produções:
      - atributos SINTETIZADOS (tipo, addr) sobem como valor de retorno;
      - atributos HERDADOS (E'.inh, T'.inh) descem como parâmetro, pois a
        gramática LL(1) não tem recursão à esquerda (E -> T E').

    No mesmo percurso, preenche a tabela de símbolos, verifica escopo e tipos
    e emite o Código de Três Endereços em forma de quádruplas.
    """

    def __init__(self) -> None:
        self.tabela = SemanticSymbolTable()
        self.codigo = CodeGenerator()
        self.erros: list[SemanticErrorInfo] = []

    @property
    def aprovado(self) -> bool:
        return not self.erros

    def analyze(self, raiz: Node) -> "SemanticAnalyzer":
        self.visit(raiz)
        return self

    # -------------------------
    # Auxiliares
    # -------------------------

    def visit(self, no: Node, *herdados):
        metodo = "visit_" + no.simbolo.replace("'", "_linha")
        return getattr(self, metodo)(no, *herdados)

    def error(self, folha: Node, mensagem: str) -> None:
        self.erros.append(SemanticErrorInfo(folha.linha, folha.coluna, mensagem))

    def widen(self, attr: Attr, tipo_alvo: str) -> str:
        """Coerção de alargamento int -> float: emite `t = float(x)`."""
        if attr.tipo == "int" and tipo_alvo == "float":
            t = self.codigo.new_temp()
            self.codigo.emit("float", attr.addr, None, t)
            return t
        return attr.addr

    # -------------------------
    # Programa e comandos
    # -------------------------

    # PROG -> public class id { public static void id ( ) { CMDS } }
    def visit_PROG(self, no: Node) -> None:
        self.tabela.offset = 0  # offset inicializado em 0 no main
        self.visit(no.filhos[11])

    # CMDS -> CMD CMDS | ε   (percorrido em laço para não aprofundar a recursão)
    def visit_CMDS(self, no: Node) -> None:
        while not no.eh_vazio:
            self.visit(no.filhos[0])
            no = no.filhos[1]

    # CMD -> DECL | ATRIB | IF_STMT | WHILE_STMT
    def visit_CMD(self, no: Node) -> None:
        self.visit(no.filhos[0])

    # DECL -> TIPO id ;
    def visit_DECL(self, no: Node) -> None:
        tipo = self.visit(no.filhos[0])
        id_ = no.filhos[1]

        existente = self.tabela.lookup(id_.lexema)
        if existente:
            self.error(id_, f"redeclaração da variável '{id_.lexema}' "
                            f"(já declarada como {existente.tipo} na linha {existente.linha})")
        else:
            self.tabela.insert(id_.lexema, tipo, id_.linha)

    # TIPO -> int | float | char        { TIPO.tipo = lexema }
    def visit_TIPO(self, no: Node) -> str:
        return no.filhos[0].lexema

    # ATRIB -> id = E ;
    def visit_ATRIB(self, no: Node) -> None:
        id_ = no.filhos[0]
        simbolo = self.tabela.lookup(id_.lexema)
        if simbolo is None:
            self.error(id_, f"variável '{id_.lexema}' não declarada")

        expr = self.visit(no.filhos[2])
        if simbolo is None or expr.tipo == ERROR_TYPE:
            return  # erro já reportado

        destino, origem = simbolo.tipo, expr.tipo
        if destino == origem:
            addr = expr.addr
        elif destino == "float" and origem == "int":  # alargamento permitido
            addr = self.widen(expr, "float")
        elif destino == "int" and origem == "float":
            self.error(id_, f"estreitamento inválido: variável '{id_.lexema}' do tipo int "
                            f"não pode receber valor float")
            return
        else:
            self.error(id_, f"atribuição incompatível: variável '{id_.lexema}' do tipo "
                            f"{destino} não pode receber valor {origem}")
            return

        self.codigo.emit("=", addr, None, id_.lexema)

    # IF_STMT -> if ( COND ) { CMDS } SENAO
    def visit_IF_STMT(self, no: Node) -> None:
        cond = self.visit(no.filhos[2])
        l_falso = self.codigo.new_label()
        self.codigo.emit("ifFalse", cond.addr, None, l_falso)
        self.visit(no.filhos[5])  # bloco do if

        senao = no.filhos[7]
        if senao.eh_vazio:  # SENAO -> ε
            self.codigo.emit("label", resultado=l_falso)
        else:               # SENAO -> else { CMDS }
            l_fim = self.codigo.new_label()
            self.codigo.emit("goto", resultado=l_fim)
            self.codigo.emit("label", resultado=l_falso)
            self.visit(senao.filhos[2])
            self.codigo.emit("label", resultado=l_fim)

    # WHILE_STMT -> while ( COND ) { CMDS }        (diferencial)
    def visit_WHILE_STMT(self, no: Node) -> None:
        l_inicio = self.codigo.new_label()
        self.codigo.emit("label", resultado=l_inicio)
        cond = self.visit(no.filhos[2])
        l_fim = self.codigo.new_label()
        self.codigo.emit("ifFalse", cond.addr, None, l_fim)
        self.visit(no.filhos[5])
        self.codigo.emit("goto", resultado=l_inicio)
        self.codigo.emit("label", resultado=l_fim)

    # -------------------------
    # Condição e expressões
    # -------------------------

    # COND -> E OP_REL E
    def visit_COND(self, no: Node) -> Attr:
        esq = self.visit(no.filhos[0])
        op = no.filhos[1].filhos[0]  # OP_REL -> == | != | < | >
        dir_ = self.visit(no.filhos[2])
        resultado = self.binary_operation(op, esq, dir_)
        if resultado.tipo != ERROR_TYPE:
            resultado.tipo = "bool"
        return resultado

    # E -> T E'          { E'.inh = T ; E = E'.syn }
    def visit_E(self, no: Node) -> Attr:
        t = self.visit(no.filhos[0])
        return self.visit(no.filhos[1], t)

    # E' -> + T E'1 | - T E'1 | ε
    def visit_E_linha(self, no: Node, herdado: Attr) -> Attr:
        if no.eh_vazio:
            return herdado  # E'.syn = E'.inh
        t = self.visit(no.filhos[1])
        novo = self.binary_operation(no.filhos[0], herdado, t)
        return self.visit(no.filhos[2], novo)  # E'1.inh = novo

    # T -> F T'
    def visit_T(self, no: Node) -> Attr:
        f = self.visit(no.filhos[0])
        return self.visit(no.filhos[1], f)

    # T' -> * F T'1 | / F T'1 | ε
    def visit_T_linha(self, no: Node, herdado: Attr) -> Attr:
        if no.eh_vazio:
            return herdado
        f = self.visit(no.filhos[1])
        novo = self.binary_operation(no.filhos[0], herdado, f)
        return self.visit(no.filhos[2], novo)

    # F -> ( E ) | id | num | char_lit
    def visit_F(self, no: Node) -> Attr:
        folha = no.filhos[0]
        if folha.simbolo == "(":
            return self.visit(no.filhos[1])  # parênteses: F = E

        if folha.simbolo == "id":
            simbolo = self.tabela.lookup(folha.lexema)
            if simbolo is None:
                self.error(folha, f"variável '{folha.lexema}' não declarada")
                return Attr(ERROR_TYPE, folha.lexema)
            return Attr(simbolo.tipo, folha.lexema)

        # num ou char_lit: o tipo vem do token do léxico
        return Attr(LITERAL_TYPES[folha.tipo_lexico], folha.lexema)

    # -------------------------
    # Verificação de tipos
    # -------------------------

    def binary_operation(self, op: Node, esq: Attr, dir_: Attr) -> Attr:
        """Regra para + - * / e == != < >: só int e float.
        int op int = int; havendo float, o operando int é convertido com float(x)."""
        if ERROR_TYPE in (esq.tipo, dir_.tipo):
            return Attr(ERROR_TYPE, "?")

        categoria = "relacional" if op.lexema in RELATIONAL else "aritmético"
        for lado in (esq, dir_):
            if lado.tipo not in NUMERIC:
                self.error(op, f"operador {categoria} '{op.lexema}' não pode ser aplicado "
                               f"ao tipo {lado.tipo} (operando {lado.addr})")
                return Attr(ERROR_TYPE, "?")

        tipo = "float" if "float" in (esq.tipo, dir_.tipo) else "int"
        a1 = self.widen(esq, tipo)  # coerção implícita
        a2 = self.widen(dir_, tipo)
        t = self.codigo.new_temp()
        self.codigo.emit(op.lexema, a1, a2, t)
        return Attr(tipo, t)
