from semantic_analyzer import SemanticAnalyzer


def print_section(titulo: str) -> None:
    print(f"\n=== {titulo} ===")


def _print_grid(cabecalho: tuple[str, ...], linhas: list[tuple[str, ...]]) -> None:
    larguras = [
        max([len(c)] + [len(linha[i]) for linha in linhas]) for i, c in enumerate(cabecalho)
    ]
    separador = "+" + "+".join("-" * (w + 2) for w in larguras) + "+"

    def formatar(colunas):
        return "| " + " | ".join(c.ljust(w) for c, w in zip(colunas, larguras)) + " |"

    print(separador)
    print(formatar(cabecalho))
    print(separador)
    for linha in linhas:
        print(formatar(linha))
    print(separador)


def print_symbol_table(analisador: SemanticAnalyzer) -> None:
    print_section("TABELA DE SÍMBOLOS (SEMÂNTICA)")
    simbolos = analisador.tabela.symbols()
    if not simbolos:
        print("(vazia)")
    else:
        _print_grid(
            ("Lexema", "Tipo", "Width", "Offset"),
            [(s.lexema, s.tipo, str(s.width), str(s.offset)) for s in simbolos],
        )
    print(f"Tamanho total da área de dados: {analisador.tabela.offset} bytes")


def print_verdict(analisador: SemanticAnalyzer) -> None:
    print_section("VEREDITO DA ANÁLISE SEMÂNTICA")
    if analisador.aprovado:
        print("Programa APROVADO: nenhum erro semântico encontrado.")
        return

    print(f"Programa REPROVADO: {len(analisador.erros)} erro(s) semântico(s) encontrado(s).")
    for erro in analisador.erros:
        print(f"  {erro}")
    print("\nCódigo de Três Endereços NÃO gerado: o programa possui erros semânticos.")


def print_tac(analisador: SemanticAnalyzer) -> None:
    print_section("CÓDIGO DE TRÊS ENDEREÇOS (TAC)")
    for linha in analisador.codigo.tac():
        print(linha)


def print_quadruples(analisador: SemanticAnalyzer) -> None:
    print_section("QUÁDRUPLAS")
    _print_grid(
        ("#", "op", "arg1", "arg2", "resultado"),
        [
            (str(i), q.op, q.arg1 or "-", q.arg2 or "-", q.resultado or "-")
            for i, q in enumerate(analisador.codigo.quadruplas)
        ],
    )
