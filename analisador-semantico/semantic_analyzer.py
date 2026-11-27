from dataclasses import dataclass

from intermediate_code import CodeGenerator
from semantic_table import SemanticSymbolTable
from tree import Node

ERROR_TYPE = "erro"  
NUMERIC = {"int", "float"}
RELATIONAL = {"==", "!=", "<", ">"}

LITERAL_TYPES = {
    "INTEGER_LITERAL": "int",
    "FLOAT_LITERAL": "float",
    "CHAR_LITERAL": "char",
}


@dataclass
class Attr:
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



    def visit(self, no: Node, *herdados):
        metodo = "visit_" + no.simbolo.replace("'", "_linha")
        return getattr(self, metodo)(no, *herdados)

    def error(self, folha: Node, mensagem: str) -> None:
        self.erros.append(SemanticErrorInfo(folha.linha, folha.coluna, mensagem))

    def widen(self, attr: Attr, tipo_alvo: str) -> str:
        if attr.tipo == "int" and tipo_alvo == "float":
            t = self.codigo.new_temp()
            self.codigo.emit("float", attr.addr, None, t)
            return t
        return attr.addr



    def visit_PROG(self, no: Node) -> None:
        self.tabela.offset = 0 
        self.visit(no.filhos[11])

    def visit_CMDS(self, no: Node) -> None:
        while not no.eh_vazio:
            self.visit(no.filhos[0])
            no = no.filhos[1]

    def visit_CMD(self, no: Node) -> None:
        self.visit(no.filhos[0])

    def visit_DECL(self, no: Node) -> None:
        tipo = self.visit(no.filhos[0])
        id_ = no.filhos[1]

        existente = self.tabela.lookup(id_.lexema)
        if existente:
            self.error(id_, f"redeclaração da variável '{id_.lexema}' "
                            f"(já declarada como {existente.tipo} na linha {existente.linha})")
        else:
            self.tabela.insert(id_.lexema, tipo, id_.linha)

    def visit_TIPO(self, no: Node) -> str:
        return no.filhos[0].lexema

    def visit_ATRIB(self, no: Node) -> None:
        id_ = no.filhos[0]
        simbolo = self.tabela.lookup(id_.lexema)
        if simbolo is None:
            self.error(id_, f"variável '{id_.lexema}' não declarada")

        expr = self.visit(no.filhos[2])
        if simbolo is None or expr.tipo == ERROR_TYPE:
            return  

        destino, origem = simbolo.tipo, expr.tipo
        if destino == origem:
            addr = expr.addr
        elif destino == "float" and origem == "int":
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

    def visit_IF_STMT(self, no: Node) -> None:
        cond = self.visit(no.filhos[2])
        l_falso = self.codigo.new_label()
        self.codigo.emit("ifFalse", cond.addr, None, l_falso)
        self.visit(no.filhos[5])  # bloco do if

        senao = no.filhos[7]
        if senao.eh_vazio: 
            self.codigo.emit("label", resultado=l_falso)
        else:
            l_fim = self.codigo.new_label()
            self.codigo.emit("goto", resultado=l_fim)
            self.codigo.emit("label", resultado=l_falso)
            self.visit(senao.filhos[2])
            self.codigo.emit("label", resultado=l_fim)

    def visit_WHILE_STMT(self, no: Node) -> None:
        l_inicio = self.codigo.new_label()
        self.codigo.emit("label", resultado=l_inicio)
        cond = self.visit(no.filhos[2])
        l_fim = self.codigo.new_label()
        self.codigo.emit("ifFalse", cond.addr, None, l_fim)
        self.visit(no.filhos[5])
        self.codigo.emit("goto", resultado=l_inicio)
        self.codigo.emit("label", resultado=l_fim)


    def visit_COND(self, no: Node) -> Attr:
        esq = self.visit(no.filhos[0])
        op = no.filhos[1].filhos[0]
        dir_ = self.visit(no.filhos[2])
        resultado = self.binary_operation(op, esq, dir_)
        if resultado.tipo != ERROR_TYPE:
            resultado.tipo = "bool"
        return resultado

    def visit_E(self, no: Node) -> Attr:
        t = self.visit(no.filhos[0])
        return self.visit(no.filhos[1], t)

    def visit_E_linha(self, no: Node, herdado: Attr) -> Attr:
        if no.eh_vazio:
            return herdado  
        t = self.visit(no.filhos[1])
        novo = self.binary_operation(no.filhos[0], herdado, t)
        return self.visit(no.filhos[2], novo)  # E'1.inh = novo

    def visit_T(self, no: Node) -> Attr:
        f = self.visit(no.filhos[0])
        return self.visit(no.filhos[1], f)

    def visit_T_linha(self, no: Node, herdado: Attr) -> Attr:
        if no.eh_vazio:
            return herdado
        f = self.visit(no.filhos[1])
        novo = self.binary_operation(no.filhos[0], herdado, f)
        return self.visit(no.filhos[2], novo)

    def visit_F(self, no: Node) -> Attr:
        folha = no.filhos[0]
        if folha.simbolo == "(":
            return self.visit(no.filhos[1])

        if folha.simbolo == "id":
            simbolo = self.tabela.lookup(folha.lexema)
            if simbolo is None:
                self.error(folha, f"variável '{folha.lexema}' não declarada")
                return Attr(ERROR_TYPE, folha.lexema)
            return Attr(simbolo.tipo, folha.lexema)

        return Attr(LITERAL_TYPES[folha.tipo_lexico], folha.lexema)


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
        a1 = self.widen(esq, tipo) 
        a2 = self.widen(dir_, tipo)
        t = self.codigo.new_temp()
        self.codigo.emit(op.lexema, a1, a2, t)
        return Attr(tipo, t)
