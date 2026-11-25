class TwoBufferReader:

    EOF = None

    def __init__(self, source: str, buffer_size: int = 4096) -> None:
        if buffer_size <= 0:
            raise ValueError("buffer_size deve ser positivo")

        self.source = source
        self.buffer_size = buffer_size

        self.buffer_a = ""
        self.buffer_b = ""

        self._load_buffer_a()
        self.active_buffer = "A"

        self.bp = 0
        self.fp = 0

    def _load_buffer_a(self) -> None:
        self.buffer_a = self.source[:self.buffer_size]

    def _load_buffer_b(self, start: int) -> None:
        self.buffer_b = self.source[start:start + self.buffer_size]

    def _refresh_for_position(self, position: int) -> None:
        """Garante que a posição esteja no buffer correspondente."""
        if position < 0 or position >= len(self.source):
            return

        block = position // self.buffer_size
        if block % 2 == 0:
            start = block * self.buffer_size
            self.buffer_a = self.source[start:start + self.buffer_size]
            self.active_buffer = "A"
        else:
            start = block * self.buffer_size
            self.buffer_b = self.source[start:start + self.buffer_size]
            self.active_buffer = "B"

    def peek(self, offset: int = 0):
        """Lookahead sem avançar fp."""
        position = self.fp + offset
        if position >= len(self.source):
            return self.EOF

        self._refresh_for_position(position)
        return self.source[position]

    def advance(self):
        """Consome um caractere e avança fp."""
        char = self.peek()
        if char is not self.EOF:
            self.fp += 1
        return char

    def rewind(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count não pode ser negativo")
        self.fp = max(0, self.fp - count)
        self._refresh_for_position(self.fp)

    def mark(self) -> None:
        """bp recebe a posição atual de fp."""
        self.bp = self.fp

    def lexeme(self) -> str:
        return self.source[self.bp:self.fp]

    def eof(self) -> bool:
        return self.fp >= len(self.source)

    def reset_lexeme(self) -> None:
        self.bp = self.fp

    def buffer_state(self) -> dict:
        return {
            "bp": self.bp,
            "fp": self.fp,
            "buffer_ativo": self.active_buffer,
            "tamanho_buffer": self.buffer_size,
        }
