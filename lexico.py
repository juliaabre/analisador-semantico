
from dataclasses import dataclass

PALAVRAS_RESERVADAS = {
    "public", "class", "static", "void",
    "int", "float", "char",
    "if", "else", "while",
}

SIMBOLOS_SIMPLES = {"+", "-", "*", "/", "(", ")", "{", "}", ";"}


@dataclass
class Token:
    tipo: str
    lexema: str
    linha: int
    coluna: int

    def __str__(self):
        return f"<{self.tipo}, '{self.lexema}'> (linha {self.linha}, col {self.coluna})"


@dataclass
class ErroLexico:
    mensagem: str
    linha: int
    coluna: int

    def __str__(self):
        return f"Erro Léxico (linha {self.linha}, col {self.coluna}): {self.mensagem}"


class AnalisadorLexico:
    def __init__(self, fonte: str):
        self.fonte = fonte
        self.pos = 0
        self.linha = 1
        self.coluna = 1
        self.tokens: list[Token] = []
        self.erros: list[ErroLexico] = []

    def _atual(self) -> str:
        return self.fonte[self.pos] if self.pos < len(self.fonte) else ""

    def _proximo(self) -> str:
        p = self.pos + 1
        return self.fonte[p] if p < len(self.fonte) else ""

    def _avancar(self) -> str:
        c = self._atual()
        self.pos += 1
        if c == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return c

    def _erro(self, msg, linha, coluna):
        self.erros.append(ErroLexico(msg, linha, coluna))

    def tokenizar(self):
        """Retorna (tokens, erros). A lista de tokens sempre termina com '$'."""
        while self.pos < len(self.fonte):
            c = self._atual()
            lin, col = self.linha, self.coluna

            if c.isspace():
                self._avancar()
                continue

            if c == "/" and self._proximo() == "/":
                while self._atual() not in ("", "\n"):
                    self._avancar()
                continue
            if c == "/" and self._proximo() == "*":
                self._avancar(); self._avancar()
                while self._atual() and not (self._atual() == "*" and self._proximo() == "/"):
                    self._avancar()
                if not self._atual():
                    self._erro("comentário de bloco não fechado", lin, col)
                else:
                    self._avancar(); self._avancar()
                continue

            if c.isalpha() or c == "_":
                lexema = ""
                while self._atual() and (self._atual().isalnum() or self._atual() == "_"):
                    lexema += self._avancar()
                tipo = lexema if lexema in PALAVRAS_RESERVADAS else "id"
                self.tokens.append(Token(tipo, lexema, lin, col))
                continue

            if c.isdigit():
                lexema = ""
                while self._atual().isdigit():
                    lexema += self._avancar()
                if self._atual() == "." and self._proximo().isdigit():
                    lexema += self._avancar()
                    while self._atual().isdigit():
                        lexema += self._avancar()
                elif self._atual() == ".":
                    lexema += self._avancar()
                    self._erro(f"número real malformado '{lexema}'", lin, col)
                    continue
                if self._atual().isalpha() or self._atual() == "_":
                    while self._atual() and (self._atual().isalnum() or self._atual() == "_"):
                        lexema += self._avancar()
                    self._erro(f"identificador inválido '{lexema}' (não pode começar com dígito)", lin, col)
                    continue
                self.tokens.append(Token("num", lexema, lin, col))
                continue

            if c == "'":
                self._avancar()
                conteudo = ""
                if self._atual() == "\\":
                    conteudo += self._avancar()
                    if self._atual():
                        conteudo += self._avancar()
                elif self._atual() not in ("", "\n", "'"):
                    conteudo += self._avancar()
                if self._atual() == "'" and conteudo:
                    self._avancar()
                    self.tokens.append(Token("char_lit", f"'{conteudo}'", lin, col))
                else:
                    while self._atual() not in ("", "\n", "'", ";"):
                        self._avancar()
                    if self._atual() == "'":
                        self._avancar()
                    self._erro("literal de caractere malformado (use exatamente um caractere entre aspas simples)", lin, col)
                continue

            if c == "=":
                self._avancar()
                if self._atual() == "=":
                    self._avancar()
                    self.tokens.append(Token("==", "==", lin, col))
                else:
                    self.tokens.append(Token("=", "=", lin, col))
                continue
            if c == "!":
                self._avancar()
                if self._atual() == "=":
                    self._avancar()
                    self.tokens.append(Token("!=", "!=", lin, col))
                else:
                    self._erro("símbolo '!' inesperado (apenas '!=' é aceito)", lin, col)
                continue
            if c in ("<", ">"):
                self._avancar()
                self.tokens.append(Token(c, c, lin, col))
                continue

            if c in SIMBOLOS_SIMPLES:
                self._avancar()
                self.tokens.append(Token(c, c, lin, col))
                continue

            self._avancar()
            self._erro(f"caractere inválido '{c}'", lin, col)

        self.tokens.append(Token("$", "$", self.linha, self.coluna))
        return self.tokens, self.erros
