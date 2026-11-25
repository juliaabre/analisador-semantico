import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LEXER_DIR = BASE_DIR.parent / "analisador-lexico"

# Integração com o analisador léxico do Trabalho 1.
sys.path.insert(0, str(LEXER_DIR))

try:
    from lexer import Lexer  # noqa: E402
except ImportError:
    sys.exit(f"ERRO: analisador léxico não encontrado em {LEXER_DIR}")

from grammar import Grammar  # noqa: E402
from ll1 import LL1  # noqa: E402
from ll1_parser import PredictiveParser  # noqa: E402
from token_adapter import tokens_to_input  # noqa: E402
import report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analisador sintático descendente preditivo LL(1) para um subconjunto de Java."
    )
    parser.add_argument(
        "arquivo",
        help="arquivo-fonte Java (.java)",
    )
    parser.add_argument(
        "--gramatica",
        default=str(BASE_DIR / "gramatica.txt"),
        help="arquivo com as produções da gramática (padrão: gramatica.txt)",
    )
    parser.add_argument(
        "--sem-tokens",
        action="store_true",
        help="não mostra a lista de tokens do léxico",
    )
    parser.add_argument(
        "--sem-tabelas",
        action="store_true",
        help="não mostra a gramática, os conjuntos FIRST/FOLLOW e a tabela M",
    )
    parser.add_argument(
        "--sem-trace",
        action="store_true",
        help="não mostra o rastreamento passo a passo da pilha",
    )
    parser.add_argument(
        "--sem-arvore",
        action="store_true",
        help="não mostra a árvore de derivação",
    )
    parser.add_argument(
        "--sem-truncar",
        action="store_true",
        help="mostra a pilha e a entrada completas no trace",
    )
    parser.add_argument(
        "--parar-no-primeiro-erro",
        action="store_true",
        help="desativa a recuperação em modo pânico",
    )

    args = parser.parse_args()

    try:
        grammar = Grammar.from_file(args.gramatica)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERRO na gramática: {exc}", file=sys.stderr)
        return 1

    ll1 = LL1(grammar)

    if not args.sem_tabelas:
        report.print_grammar(grammar)
        report.print_first_follow(ll1)
        report.print_table(ll1)

    if not ll1.is_ll1:
        print("\nA gramática possui conflitos na tabela M; análise interrompida.", file=sys.stderr)
        return 1

    try:
        lexer = Lexer.from_file(args.arquivo)
        tokens = lexer.tokenize()
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    erros_lexicos = [token for token in tokens if token.tipo == "ERROR"]
    if erros_lexicos:
        report.print_lexical_errors(erros_lexicos)
        return 1

    entrada = tokens_to_input(tokens)

    if not args.sem_tokens:
        report.print_token_mapping(tokens, entrada)

    resultado = PredictiveParser(
        ll1, recuperar=not args.parar_no_primeiro_erro
    ).parse(entrada)

    if not args.sem_trace:
        report.print_trace(resultado, truncar=not args.sem_truncar)

    report.print_verdict(resultado)

    if resultado.aceito and not args.sem_arvore:
        report.print_tree(resultado.arvore)

    return 0 if resultado.aceito else 1


if __name__ == "__main__":
    raise SystemExit(main())
