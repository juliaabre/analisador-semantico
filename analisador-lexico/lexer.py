from pathlib import Path
from typing import Optional

from buffer import TwoBufferReader
from symbol_table import SymbolTable
from lexer_token import Token


class Lexer:

    KEYWORDS = {
        "abstract", "boolean", "break", "byte", "case", "catch", "char",
        "class", "const", "continue", "default", "do", "double", "else",
        "enum", "extends", "final", "finally", "float", "for", "if",
        "implements", "import", "instanceof", "int", "interface", "long",
        "native", "new", "package", "private", "protected", "public",
        "return", "short", "static", "strictfp", "super", "switch",
        "synchronized", "this", "throw", "throws", "transient", "try",
        "void", "volatile", "while", "true", "false", "null"
    }

    OPERATORS = {
        "==": "EQ",
        "!=": "NE",
        "<=": "LE",
        ">=": "GE",
        "&&": "AND",
        "||": "OR",
        "++": "INCREMENT",
        "--": "DECREMENT",
        "+=": "PLUS_ASSIGN",
        "-=": "MINUS_ASSIGN",
        "*=": "MULT_ASSIGN",
        "/=": "DIV_ASSIGN",
        "%=": "MOD_ASSIGN",
        "&=": "AND_ASSIGN",
        "|=": "OR_ASSIGN",
        "^=": "XOR_ASSIGN",
        "<<": "SHIFT_LEFT",
        ">>": "SHIFT_RIGHT",
    }

    SINGLE_OPERATORS = {
        "+": "PLUS",
        "-": "MINUS",
        "*": "MULT",
        "/": "DIV",
        "%": "MOD",
        "<": "LT",
        ">": "GT",
        "!": "NOT",
        "=": "ASSIGN",
        "&": "BIT_AND",
        "|": "BIT_OR",
        "^": "BIT_XOR",
        "~": "BIT_NOT",
        "?": "QUESTION",
        ":": "COLON",
    }

    DELIMITERS = {
        ";": "SEMICOLON",
        ",": "COMMA",
        ".": "DOT",
        "(": "LPAREN",
        ")": "RPAREN",
        "{": "LBRACE",
        "}": "RBRACE",
        "[": "LBRACKET",
        "]": "RBRACKET",
    }

    SIMPLE_ESCAPES = {
        "n": "\n",
        "t": "\t",
        "r": "\r",
        "b": "\b",
        "f": "\f",
        "\\": "\\",
        "'": "'",
        '"': '"',
    }

    def __init__(self, source: str, buffer_size: int = 4096) -> None:
        self.source = source
        self.reader = TwoBufferReader(source, buffer_size=buffer_size)
        self.symbol_table = SymbolTable()
        self.tokens: list[Token] = []

        self.line = 1
        self.column = 1

    @classmethod
    def from_file(cls, path: str | Path, buffer_size: int = 4096) -> "Lexer":
        path = Path(path)

        if path.suffix.lower() != ".java":
            raise ValueError("O arquivo de entrada deve possuir extensão .java")

        source = path.read_text(encoding="utf-8")
        return cls(source, buffer_size=buffer_size)

    # -------------------------
    # Controle de posição
    # -------------------------

    def _advance(self):
        char = self.reader.advance()

        if char is None:
            return None

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def _peek(self, offset: int = 0):
        return self.reader.peek(offset)

    def _consume_if(self, expected: str) -> bool:
        if self._peek() == expected:
            self._advance()
            return True
        return False

    def _make_token(
        self,
        tipo: str,
        lexema: str,
        atributo=None,
        linha: Optional[int] = None,
        coluna: Optional[int] = None,
    ) -> Token:
        return Token(
            tipo=tipo,
            lexema=lexema,
            atributo=atributo,
            linha=self.line if linha is None else linha,
            coluna=self.column if coluna is None else coluna,
        )

    # -------------------------
    # Ignorados
    # -------------------------

    def _skip_whitespace_and_comments(self) -> None:
        while True:
            # Espaços e quebras de linha.
            while (char := self._peek()) is not None and char.isspace():
                self._advance()

            if self._peek() == "/" and self._peek(1) == "/":
                # Comentário de linha.
                self._advance()
                self._advance()

                while (char := self._peek()) is not None and char != "\n":
                    self._advance()
                continue

            if self._peek() == "/" and self._peek(1) == "*":
                # Comentário de bloco.
                start_line = self.line
                start_column = self.column

                self._advance()
                self._advance()

                closed = False
                while self._peek() is not None:
                    if self._peek() == "*" and self._peek(1) == "/":
                        self._advance()
                        self._advance()
                        closed = True
                        break
                    self._advance()

                if not closed:
                    self.tokens.append(
                        self._make_token(
                            "ERROR",
                            self.source[self.reader.fp - 2 :],
                            "comentário de bloco não terminado",
                            start_line,
                            start_column,
                        )
                    )
                continue

            break

    # -------------------------
    # Identificadores / palavras-chave
    # -------------------------

    @staticmethod
    def _is_identifier_start(char: Optional[str]) -> bool:
        return char is not None and (char.isascii() and (char.isalpha() or char == "_"))

    @staticmethod
    def _is_identifier_part(char: Optional[str]) -> bool:
        return char is not None and (
            char.isascii() and (char.isalnum() or char == "_")
        )

    def _read_identifier_or_keyword(self) -> Token:
        start_line, start_column = self.line, self.column
        self.reader.mark()

        self._advance()
        while self._is_identifier_part(self._peek()):
            self._advance()

        lexema = self.reader.lexeme()

        if lexema in self.KEYWORDS:
            return self._make_token(
                lexema.upper(),
                lexema,
                None,
                start_line,
                start_column,
            )

        self.symbol_table.add(lexema)
        return self._make_token(
            "IDENTIFIER",
            lexema,
            lexema,
            start_line,
            start_column,
        )

    # -------------------------
    # Números
    # -------------------------

    def _read_number(self) -> Token:
        start_line, start_column = self.line, self.column
        self.reader.mark()

        # ==========================================================
        # LITERAL HEXADECIMAL: 0xFF, 0XFF
        # ==========================================================
        if self._peek() == "0" and self._peek(1) in ("x", "X"):
            self._advance()  # 0
            self._advance()  # x/X

            # Deve existir pelo menos um dígito hexadecimal
            if self._peek() is None or not (
                self._peek().isdigit()
                or self._peek().lower() in "abcdef"
            ):
                return self._make_token(
                    "ERROR",
                    self.reader.lexeme(),
                    "literal hexadecimal inválido ou incompleto",
                    start_line,
                    start_column,
                )

            while self._peek() is not None and (
                self._peek().isdigit()
                or self._peek().lower() in "abcdef"
            ):
                self._advance()

            lexema = self.reader.lexeme()

            # Não permite algo como 0xFFabc
            if self._is_identifier_start(self._peek()):
                while self._is_identifier_part(self._peek()):
                    self._advance()

                return self._make_token(
                    "ERROR",
                    self.reader.lexeme(),
                    "literal hexadecimal malformado",
                    start_line,
                    start_column,
                )

            return self._make_token(
                "INTEGER_LITERAL",
                lexema,
                int(lexema, 16),
                start_line,
                start_column,
            )

        # ==========================================================
        # LITERAL BINÁRIO: 0b1010, 0B1010
        # ==========================================================
        if self._peek() == "0" and self._peek(1) in ("b", "B"):
            self._advance()  # 0
            self._advance()  # b/B

            # Deve existir pelo menos um 0 ou 1
            if self._peek() not in ("0", "1"):
                return self._make_token(
                    "ERROR",
                    self.reader.lexeme(),
                    "literal binário inválido ou incompleto",
                    start_line,
                    start_column,
                )

            while self._peek() in ("0", "1"):
                self._advance()

            lexema = self.reader.lexeme()

            # Evita aceitar 0b102 ou 0b101abc parcialmente
            if self._peek() is not None and (
                self._peek().isdigit() or self._is_identifier_start(self._peek())
            ):
                while self._is_identifier_part(self._peek()):
                    self._advance()

                return self._make_token(
                    "ERROR",
                    self.reader.lexeme(),
                    "literal binário malformado",
                    start_line,
                    start_column,
                )

            return self._make_token(
                "INTEGER_LITERAL",
                lexema,
                int(lexema, 2),
                start_line,
                start_column,
            )

        # ==========================================================
        # PARTE INTEIRA DECIMAL
        # ==========================================================
        while (char := self._peek()) is not None and char.isdigit():
            self._advance()

        # ==========================================================
        # LITERAL REAL
        # Exemplos:
        # 10.5
        # 3.14
        # 10.5f
        # 10.5F
        # ==========================================================
        if self._peek() == "." and (self._peek(1) or "").isdigit():
            self._advance()  # .

            while (char := self._peek()) is not None and char.isdigit():
                self._advance()

            # Sufixo opcional f/F
            if self._peek() in ("f", "F"):
                self._advance()

            lexema = self.reader.lexeme()

            valor = lexema
            if lexema[-1] in ("f", "F"):
                valor = lexema[:-1]

            # Algo como 10.5abc é inválido
            if self._is_identifier_start(self._peek()):
                while self._is_identifier_part(self._peek()):
                    self._advance()

                return self._make_token(
                    "ERROR",
                    self.reader.lexeme(),
                    "literal real malformado",
                    start_line,
                    start_column,
                )

            return self._make_token(
                "FLOAT_LITERAL",
                lexema,
                float(valor),
                start_line,
                start_column,
            )

        # ==========================================================
        # VÍRGULA COMO SEPARADOR DECIMAL
        # Exemplo inválido: 3,14
        # ==========================================================
        if self._peek() == "," and (self._peek(1) or "").isdigit():
            self._advance()

            while (char := self._peek()) is not None and char.isdigit():
                self._advance()

            return self._make_token(
                "ERROR",
                self.reader.lexeme(),
                "vírgula não é separador decimal; use ponto",
                start_line,
                start_column,
            )

        # ==========================================================
        # SUFIXO LONG: 123L, 123l
        # ==========================================================
        if self._peek() in ("L", "l"):
            self._advance()

            lexema = self.reader.lexeme()

            # Ex.: 123Labc
            if self._is_identifier_start(self._peek()):
                while self._is_identifier_part(self._peek()):
                    self._advance()

                return self._make_token(
                    "ERROR",
                    self.reader.lexeme(),
                    "literal long malformado",
                    start_line,
                    start_column,
                )

            return self._make_token(
                "INTEGER_LITERAL",
                lexema,
                int(lexema[:-1]),
                start_line,
                start_column,
            )

        # ==========================================================
        # NÚMERO SEGUIDO DE LETRAS
        # Exemplo inválido:
        # 123abc
        # ==========================================================
        if self._is_identifier_start(self._peek()):
            while self._is_identifier_part(self._peek()):
                self._advance()

            return self._make_token(
                "ERROR",
                self.reader.lexeme(),
                "identificador não pode começar com número",
                start_line,
                start_column,
            )

        # ==========================================================
        # INTEIRO DECIMAL NORMAL
        # ==========================================================
        lexema = self.reader.lexeme()

        return self._make_token(
            "INTEGER_LITERAL",
            lexema,
            int(lexema),
            start_line,
            start_column,
        )

    # -------------------------
    # String / caractere
    # -------------------------

    def _decode_escape(self, escape: str) -> Optional[str]:
        return self.SIMPLE_ESCAPES.get(escape)

    def _read_string(self) -> Token:
        start_line, start_column = self.line, self.column
        self.reader.mark()

        self._advance()  # "

        value_chars = []
        closed = False

        while (char := self._peek()) is not None:
            if char == '"':
                self._advance()
                closed = True
                break

            # String não pode atravessar linha neste analisador simplificado.
            if char == "\n":
                break

            if char == "\\":
                self._advance()
                escaped = self._peek()

                if escaped is None:
                    break

                decoded = self._decode_escape(escaped)
                if decoded is None:
                    # Mantemos o lexema completo como erro.
                    self._advance()
                    while self._peek() is not None and self._peek() != "\n":
                        if self._peek() == '"':
                            self._advance()
                            closed = True
                            break
                        self._advance()
                    return self._make_token(
                        "ERROR",
                        self.reader.lexeme(),
                        f"escape inválido: \\{escaped}",
                        start_line,
                        start_column,
                    )

                value_chars.append(decoded)
                self._advance()
                continue

            value_chars.append(char)
            self._advance()

        if not closed:
            # Se a string terminou por quebra de linha, consumimos o restante
            # apenas até a linha atual para evitar mascarar os próximos tokens.
            return self._make_token(
                "ERROR",
                self.reader.lexeme(),
                "string não terminada",
                start_line,
                start_column,
            )

        return self._make_token(
            "STRING_LITERAL",
            self.reader.lexeme(),
            "".join(value_chars),
            start_line,
            start_column,
        )

    def _read_char_literal(self) -> Token:
        start_line, start_column = self.line, self.column
        self.reader.mark()

        self._advance()  # '

        value = None
        valid = True

        if self._peek() is None or self._peek() == "\n":
            valid = False
        elif self._peek() == "\\":
            self._advance()
            escaped = self._peek()

            if escaped is None:
                valid = False
            else:
                value = self._decode_escape(escaped)
                self._advance()
                if value is None:
                    valid = False
        else:
            value = self._peek()
            self._advance()

        if self._peek() == "'":
            self._advance()
        else:
            valid = False
            # Consome até fechar ou terminar a linha.
            while self._peek() is not None and self._peek() != "\n":
                if self._peek() == "'":
                    self._advance()
                    break
                self._advance()

        lexema = self.reader.lexeme()

        if not valid:
            return self._make_token(
                "ERROR",
                lexema,
                "literal de caractere inválido ou não terminado",
                start_line,
                start_column,
            )

        return self._make_token(
            "CHAR_LITERAL",
            lexema,
            value,
            start_line,
            start_column,
        )

    # -------------------------
    # Operadores / delimitadores
    # -------------------------

    def _read_operator_or_delimiter(self) -> Optional[Token]:
        start_line, start_column = self.line, self.column

        two = (self._peek() or "") + (self._peek(1) or "")
        if two in self.OPERATORS:
            self.reader.mark()
            self._advance()
            self._advance()
            return self._make_token(
                self.OPERATORS[two],
                two,
                two,
                start_line,
                start_column,
            )

        char = self._peek()
        if char in self.SINGLE_OPERATORS:
            self.reader.mark()
            self._advance()
            return self._make_token(
                self.SINGLE_OPERATORS[char],
                char,
                char,
                start_line,
                start_column,
            )

        if char in self.DELIMITERS:
            self.reader.mark()
            self._advance()
            return self._make_token(
                self.DELIMITERS[char],
                char,
                None,
                start_line,
                start_column,
            )

        return None

    # -------------------------
    # Análise principal
    # -------------------------

    def tokenize(self) -> list[Token]:
        self.tokens = []

        while not self.reader.eof():
            self._skip_whitespace_and_comments()

            if self.reader.eof():
                break

            char = self._peek()
            start_line, start_column = self.line, self.column

            if self._is_identifier_start(char):
                token = self._read_identifier_or_keyword()

            elif char.isdigit():
                token = self._read_number()

            elif char == '"':
                token = self._read_string()

            elif char == "'":
                token = self._read_char_literal()

            else:
                token = self._read_operator_or_delimiter()

                if token is None:
                    self.reader.mark()
                    self._advance()
                    token = self._make_token(
                        "ERROR",
                        self.reader.lexeme(),
                        f"caractere não reconhecido: {char!r}",
                        start_line,
                        start_column,
                    )

            self.tokens.append(token)

        return self.tokens

    def result(self) -> dict:
        return {
            "tokens": [token.to_dict() for token in self.tokens],
            "tabela_de_simbolos": self.symbol_table.as_list(),
            "tabela_de_tokens": [token.to_dict() for token in self.tokens],
            "quantidade_de_erros": sum(
                1 for token in self.tokens if token.tipo == "ERROR"
            ),
        }
