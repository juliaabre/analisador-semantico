import argparse
import json
import sys
from pathlib import Path

from lexer import Lexer


def print_tokens(tokens) -> None:
    print("\n=== TOKENS RECONHECIDOS ===")
    for index, token in enumerate(tokens, start=1):
        print(f"{index:03d}: {token}")


def print_symbol_table(symbol_table) -> None:
    print("\n=== TABELA DE SÍMBOLOS ===")
    print(f"{'Identificador':<25} {'Ocorrências':>12}")
    print("-" * 40)

    for item in symbol_table:
        print(f"{item['identificador']:<25} {item['ocorrencias']:>12}")

    if not symbol_table:
        print("(vazia)")


def print_token_table(tokens) -> None:
    print("\n=== TABELA DE TOKENS ===")
    print(f"{'Tipo':<22} {'Lexema':<22} {'Atributo':<28} {'Posição':>10}")
    print("-" * 90)

    for token in tokens:
        atributo = "" if token.atributo is None else repr(token.atributo)
        posicao = f"{token.linha}:{token.coluna}"
        print(
            f"{token.tipo:<22} "
            f"{token.lexema!r:<22} "
            f"{atributo:<28} "
            f"{posicao:>10}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analisador léxico manual para uma linguagem semelhante a Java."
    )
    parser.add_argument(
        "arquivo",
        help="arquivo-fonte Java (.java)",
    )
    parser.add_argument(
        "--buffer-size",
        type=int,
        default=4096,
        help="tamanho de cada buffer (padrão: 4096)",
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        help="salva o resultado em um arquivo JSON",
    )
    parser.add_argument(
        "--tokens",
        action="store_true",
        help="mostra somente os tokens",
    )

    args = parser.parse_args()

    path = Path(args.arquivo)

    try:
        lexer = Lexer.from_file(path, buffer_size=args.buffer_size)
        tokens = lexer.tokenize()
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    if args.tokens:
        print_tokens(tokens)
    else:
        print_tokens(tokens)
        print_symbol_table(lexer.symbol_table.as_list())
        print_token_table(tokens)

        errors = [token for token in tokens if token.tipo == "ERROR"]
        print("\n=== RESUMO ===")
        print(f"Tokens: {len(tokens)}")
        print(f"Identificadores distintos: {len(lexer.symbol_table)}")
        print(f"Erros léxicos: {len(errors)}")

    if args.json_path:
        output = lexer.result()
        Path(args.json_path).write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nResultado salvo em: {args.json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
