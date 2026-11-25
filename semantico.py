"""
Analisador Semântico + Gerador de Código Intermediário (Trabalho 3).

Implementa uma Tradução Dirigida pela Sintaxe (SDT) por CAMINHAMENTO na
árvore sintática produzida pelo parser LL(1). Cada não-terminal tem um
método `visitar_<NT>` que executa as ações semânticas da sua produção:

  * Atributos SINTETIZADOS (tipo, addr) sobem como valor de retorno.
  * Atributos HERDADOS (ex.: E'.inh, T'.inh) descem como parâmetro —
    necessário porque a gramática LL(1) eliminou a recursão à esquerda.

No mesmo percurso:
  1. preenche a Tabela de Símbolos (lexema, tipo, width, offset);
  2. verifica escopo (redeclaração / não declarada) e tipos (coerção,
     alargamento, estreitamento, uso indevido de char);
  3. emite o Código de Três Endereços, guardado internamente como
     QUÁDRUPLAS (op, arg1, arg2, resultado).
"""

from dataclasses import dataclass

LARGURAS = {"int": 4, "float": 8, "char": 1}

TIPO_ERRO = "erro"
NUMERICOS = {"int", "float"}
OPS_ARITMETICOS = {"+", "-", "*", "/"}
OPS_RELACIONAIS = {"==", "!=", "<", ">"}

@dataclass
class Simbolo:
    lexema: str
    tipo: str
    largura: int
    offset: int
    linha: int


class TabelaSimbolos:
    def __init__(self):
        self.simbolos: dict[str, Simbolo] = {}
        self.offset = 0

    def buscar(self, lexema):
        return self.simbolos.get(lexema)

    def inserir(self, lexema, tipo, linha) -> Simbolo:
        largura = LARGURAS[tipo]
        s = Simbolo(lexema, tipo, largura, self.offset, linha)
        self.simbolos[lexema] = s
        self.offset += largura
        return s

@dataclass
class Quadrupla:
    op: str
    arg1: str | None = None
    arg2: str | None = None
    resultado: str | None = None

    def para_tac(self) -> str:
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
        # operador binário aritmético ou relacional
        return f"{self.resultado} = {self.arg1} {self.op} {self.arg2}"


@dataclass
class Atributo:
    """Atributos sintetizados de uma expressão: tipo e endereço (nome/temp/constante)."""
    tipo: str
    addr: str


@dataclass
class ErroSemantico:
    mensagem: str
    linha: int

    def __str__(self):
        return f"Erro Semântico (linha {self.linha}): {self.mensagem}"


class AnalisadorSemantico:
    def __init__(self):
        self.tabela = TabelaSimbolos()
        self.erros: list[ErroSemantico] = []
        self.codigo: list[Quadrupla] = []
        self.cont_temp = 0
        self.cont_rotulo = 0

    def novo_temp(self) -> str:
        self.cont_temp += 1
        return f"t{self.cont_temp}"

    def novo_rotulo(self) -> str:
        self.cont_rotulo += 1
        return f"L{self.cont_rotulo}"

    def emitir(self, op, arg1=None, arg2=None, resultado=None):
        self.codigo.append(Quadrupla(op, arg1, arg2, resultado))

    def erro(self, mensagem, linha):
        self.erros.append(ErroSemantico(mensagem, linha))

    def ampliar(self, attr: Atributo, tipo_alvo: str) -> str:
        """Coerção de alargamento int -> float: emite t = float(x)."""
        if attr.tipo == "int" and tipo_alvo == "float":
            t = self.novo_temp()
            self.emitir("float", attr.addr, None, t)
            return t
        return attr.addr

    def visitar(self, no, *args):
        nome = "visitar_" + no.simbolo.replace("'", "_linha")
        return getattr(self, nome)(no, *args)

    def analisar(self, raiz):
        self.visitar(raiz)
        return self

    def visitar_PROG(self, no):
        self.tabela.offset = 0
        self.visitar(no.filhos[11])

    def visitar_CMDS(self, no):
        while not no.eh_epsilon:
            self.visitar(no.filhos[0])
            no = no.filhos[1]

    def visitar_CMD(self, no):
        self.visitar(no.filhos[0])

    def visitar_DECL(self, no):
        tipo = self.visitar(no.filhos[0])
        tok = no.filhos[1].token
        existente = self.tabela.buscar(tok.lexema)
        if existente:
            self.erro(f"redeclaração da variável '{tok.lexema}' "
                      f"(já declarada como {existente.tipo} na linha {existente.linha})",
                      tok.linha)
        else:
            self.tabela.inserir(tok.lexema, tipo, tok.linha)

    def visitar_TIPO(self, no):
        return no.filhos[0].token.lexema


    def visitar_ATRIB(self, no):
        tok = no.filhos[0].token
        simbolo = self.tabela.buscar(tok.lexema)
        if simbolo is None:
            self.erro(f"variável '{tok.lexema}' não declarada", tok.linha)

        expr = self.visitar(no.filhos[2])

        if simbolo is None or expr.tipo == TIPO_ERRO:
            return
        destino, origem = simbolo.tipo, expr.tipo

        if destino == origem:
            addr = expr.addr
        elif destino == "float" and origem == "int":
            addr = self.ampliar(expr, "float")
        elif destino == "int" and origem == "float":
            self.erro(f"estreitamento inválido: variável '{tok.lexema}' do tipo int "
                      f"não pode receber valor float", tok.linha)
            return
        else:
            self.erro(f"atribuição incompatível: variável '{tok.lexema}' do tipo "
                      f"{destino} não pode receber valor {origem}", tok.linha)
            return

        self.emitir("=", addr, None, tok.lexema)

    def visitar_IF_STMT(self, no):
        cond = self.visitar(no.filhos[2])
        l_falso = self.novo_rotulo()
        self.emitir("ifFalse", cond.addr, None, l_falso)
        self.visitar(no.filhos[5])

        senao = no.filhos[7]
        if senao.eh_epsilon:
            self.emitir("label", resultado=l_falso)
        else:
            l_fim = self.novo_rotulo()
            self.emitir("goto", resultado=l_fim)
            self.emitir("label", resultado=l_falso)
            self.visitar(senao.filhos[2])
            self.emitir("label", resultado=l_fim)

    def visitar_WHILE_STMT(self, no):
        l_inicio = self.novo_rotulo()
        self.emitir("label", resultado=l_inicio)
        cond = self.visitar(no.filhos[2])
        l_fim = self.novo_rotulo()
        self.emitir("ifFalse", cond.addr, None, l_fim)
        self.visitar(no.filhos[5])
        self.emitir("goto", resultado=l_inicio)
        self.emitir("label", resultado=l_fim)

    def visitar_COND(self, no):
        esq = self.visitar(no.filhos[0])
        op_tok = no.filhos[1].filhos[0].token
        dir_ = self.visitar(no.filhos[2])
        res = self.operacao_binaria(op_tok.lexema, esq, dir_, op_tok.linha)
        if res.tipo != TIPO_ERRO:
            res.tipo = "bool"
        return res

    def visitar_E(self, no):
        t = self.visitar(no.filhos[0])
        return self.visitar(no.filhos[1], t)

    def visitar_E_linha(self, no, herdado):
        if no.eh_epsilon:
            return herdado
        op_tok = no.filhos[0].token
        t = self.visitar(no.filhos[1])
        novo = self.operacao_binaria(op_tok.lexema, herdado, t, op_tok.linha)
        return self.visitar(no.filhos[2], novo)

    def visitar_T(self, no):
        f = self.visitar(no.filhos[0])
        return self.visitar(no.filhos[1], f)

    def visitar_T_linha(self, no, herdado):
        if no.eh_epsilon:
            return herdado
        op_tok = no.filhos[0].token
        f = self.visitar(no.filhos[1])
        novo = self.operacao_binaria(op_tok.lexema, herdado, f, op_tok.linha)
        return self.visitar(no.filhos[2], novo)

    def visitar_F(self, no):
        primeiro = no.filhos[0]
        if primeiro.simbolo == "(":
            return self.visitar(no.filhos[1])

        tok = primeiro.token
        if primeiro.simbolo == "id":
            simbolo = self.tabela.buscar(tok.lexema)
            if simbolo is None:
                self.erro(f"variável '{tok.lexema}' não declarada", tok.linha)
                return Atributo(TIPO_ERRO, tok.lexema)
            return Atributo(simbolo.tipo, tok.lexema)
        if primeiro.simbolo == "num":
            return Atributo("float" if "." in tok.lexema else "int", tok.lexema)
        return Atributo("char", tok.lexema)

    def operacao_binaria(self, op, esq: Atributo, dir_: Atributo, linha) -> Atributo:
        """Regra comum a operadores aritméticos e relacionais:
        só int/float; int op int = int; havendo float, o int é convertido."""
        if TIPO_ERRO in (esq.tipo, dir_.tipo):
            return Atributo(TIPO_ERRO, "?")

        tipo_op = "relacional" if op in OPS_RELACIONAIS else "aritmético"
        for lado in (esq, dir_):
            if lado.tipo not in NUMERICOS:
                self.erro(f"operador {tipo_op} '{op}' não pode ser aplicado ao tipo "
                          f"{lado.tipo} (operando {lado.addr})", linha)
                return Atributo(TIPO_ERRO, "?")

        tipo = "float" if "float" in (esq.tipo, dir_.tipo) else "int"
        a1 = self.ampliar(esq, tipo)
        a2 = self.ampliar(dir_, tipo)
        t = self.novo_temp()
        self.emitir(op, a1, a2, t)
        return Atributo(tipo, t)
