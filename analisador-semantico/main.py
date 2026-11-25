import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LEXER_DIR = BASE_DIR.parent / "analisador-lexico"
PARSER_DIR = BASE_DIR.parent / "analisador-sintatico"

# Integração com o analisador léxico (Trabalho 1) e o sintático LL(1) (Trabalho 2).
sys.path.insert(1, str(LEXER_DIR))
sys.path.insert(1, str(PARSER_DIR))

try:
    from lexer import Lexer  # noqa: E402
    from grammar import Grammar  # noqa: E402
except ImportError:
    sys.exit(f"ERRO: as pastas {LEXER_DIR.name} e {PARSER_DIR.name} devem estar ao lado desta.")

from ll1 import LL1  # noqa: E402
from ll1_parser import PredictiveParser  # noqa: E402
from token_adapter import tokens_to_input  # noqa: E402
import report  # noqa: E402  (relatórios do Trabalho 2)

from semantic_analyzer import SemanticAnalyzer  # noqa: E402
import semantic_report  # noqa: E402


def compile_file(path: str, ll1: LL1, args) -> bool:
    print("=" * 70)
    print(f"Arquivo: {path}")
    print("=" * 70)

    # 1. Análise léxica (Trabalho 1)
    try:
        tokens = Lexer.from_file(path).tokenize()
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERRO: {exc}")
        return False

    erros_lexicos = [token for token in tokens if token.tipo == "ERROR"]
    if erros_lexicos:
        report.print_lexical_errors(erros_lexicos)
        print("Código de Três Endereços NÃO gerado: o programa possui erros léxicos.")
        return False

    print("\n=== ANÁLISE LÉXICA ===")
    print(f"Nenhum erro léxico: {len(tokens)} tokens reconhecidos.")

    entrada = tokens_to_input(tokens)
    if args.tokens:
        report.print_token_mapping(tokens, entrada)

    # 2. Análise sintática LL(1) (Trabalho 2): valida e constrói a árvore de derivação
    resultado = PredictiveParser(ll1).parse(entrada)
    if args.trace:
        report.print_trace(resultado)
    report.print_verdict(resultado)
    if not resultado.aceito:
        print("\nCódigo de Três Endereços NÃO gerado: o programa possui erros sintáticos.")
        return False
    if args.arvore:
        report.print_tree(resultado.arvore)

    # 3. Análise semântica + geração de código intermediário (Trabalho 3)
    analisador = SemanticAnalyzer().analyze(resultado.arvore)
    semantic_report.print_symbol_table(analisador)
    semantic_report.print_verdict(analisador)
    if not analisador.aprovado:
        return False

    semantic_report.print_tac(analisador)
    semantic_report.print_quadruples(analisador)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analisador semântico e gerador de código de três endereços (Trabalho 3)."
    )
    parser.add_argument("arquivos", nargs="+", help="arquivo(s)-fonte Java (.java)")
    parser.add_argument(
        "--gramatica",
        default=str(PARSER_DIR / "gramatica.txt"),
        help="arquivo com as produções da gramática (padrão: ../analisador-sintatico/gramatica.txt)",
    )
    parser.add_argument("--tokens", action="store_true", help="mostra os tokens do léxico")
    parser.add_argument("--tabelas", action="store_true",
                        help="mostra a gramática, FIRST/FOLLOW e a tabela M")
    parser.add_argument("--trace", action="store_true", help="mostra o rastreamento da pilha LL(1)")
    parser.add_argument("--arvore", action="store_true", help="mostra a árvore de derivação")
    args = parser.parse_args()

    try:
        grammar = Grammar.from_file(args.gramatica)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERRO na gramática: {exc}", file=sys.stderr)
        return 1

    ll1 = LL1(grammar)
    if args.tabelas:
        report.print_grammar(grammar)
        report.print_first_follow(ll1)
        report.print_table(ll1)
    if not ll1.is_ll1:
        print("\nA gramática possui conflitos na tabela M; análise interrompida.", file=sys.stderr)
        return 1

    ok = True
    for i, path in enumerate(args.arquivos):
        if i:
            print("\n")
        ok = compile_file(path, ll1, args) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
