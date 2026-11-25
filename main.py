
import argparse
import sys

from lexico import AnalisadorLexico
from sintatico import AnalisadorSintatico, ErroSintatico
from semantico import AnalisadorSemantico

LARGURA = 60


def titulo(texto):
    print("\n" + texto)
    print("-" * LARGURA)


def imprimir_tabela_simbolos(tabela):
    cab = ("Lexema", "Tipo", "Width", "Offset")
    linhas = [(s.lexema, s.tipo, str(s.largura), str(s.offset))
              for s in tabela.simbolos.values()]
    larg = [max(len(c), *(len(l[i]) for l in linhas)) if linhas else len(c)
            for i, c in enumerate(cab)]
    sep = "+" + "+".join("-" * (w + 2) for w in larg) + "+"
    fmt = lambda cols: "| " + " | ".join(c.ljust(w) for c, w in zip(cols, larg)) + " |"
    print(sep); print(fmt(cab)); print(sep)
    for l in linhas:
        print(fmt(l))
    if not linhas:
        print("| (vazia)".ljust(len(sep) - 1) + "|")
    print(sep)
    print(f"Tamanho total da área de dados: {tabela.offset} bytes")


def imprimir_quadruplas(codigo):
    cab = ("#", "op", "arg1", "arg2", "resultado")
    linhas = [(str(i), q.op, q.arg1 or "-", q.arg2 or "-", q.resultado or "-")
              for i, q in enumerate(codigo)]
    larg = [max(len(c), *(len(l[i]) for l in linhas)) for i, c in enumerate(cab)]
    sep = "+" + "+".join("-" * (w + 2) for w in larg) + "+"
    fmt = lambda cols: "| " + " | ".join(c.ljust(w) for c, w in zip(cols, larg)) + " |"
    print(sep); print(fmt(cab)); print(sep)
    for l in linhas:
        print(fmt(l))
    print(sep)


def compilar(caminho, mostrar_tokens=False, mostrar_arvore=False) -> bool:
    print("=" * LARGURA)
    print(f"Arquivo: {caminho}")
    print("=" * LARGURA)

    try:
        with open(caminho, encoding="utf-8") as f:
            fonte = f.read()
    except OSError as e:
        print(f"Não foi possível abrir o arquivo: {e}")
        return False

    tokens, erros_lexicos = AnalisadorLexico(fonte).tokenizar()
    titulo("[1] Análise Léxica")
    if mostrar_tokens:
        for t in tokens:
            print("   ", t)
    if erros_lexicos:
        for e in erros_lexicos:
            print("   ", e)
        print("\nCompilação interrompida: erros léxicos. TAC não gerado.")
        return False
    print(f"OK — {len(tokens) - 1} tokens reconhecidos.")

    titulo("[2] Análise Sintática LL(1)")
    try:
        arvore = AnalisadorSintatico(tokens).analisar()
    except ErroSintatico as e:
        print("   ", e)
        print("\nCompilação interrompida: erro sintático. TAC não gerado.")
        return False
    print("OK — programa sintaticamente correto.")
    if mostrar_arvore:
        print("\n".join(arvore.imprimir()))

    sem = AnalisadorSemantico().analisar(arvore)

    titulo("[3] Tabela de Símbolos")
    imprimir_tabela_simbolos(sem.tabela)

    titulo("[4] Veredito da Análise Semântica")
    if sem.erros:
        print(f"REPROVADO — {len(sem.erros)} erro(s) semântico(s) encontrado(s):")
        for e in sem.erros:
            print("   ", e)
        print("\nCódigo de Três Endereços NÃO gerado (programa com erros semânticos).")
        return False
    print("APROVADO — nenhum erro semântico encontrado.")

    titulo("[5] Código de Três Endereços (TAC)")
    for q in sem.codigo:
        print(q.para_tac())

    titulo("[6] Representação em Quádruplas")
    imprimir_quadruplas(sem.codigo)
    return True


def main():
    p = argparse.ArgumentParser(description="Analisador Semântico e Gerador de TAC")
    p.add_argument("arquivos", nargs="+", help="arquivo(s) .java de entrada")
    p.add_argument("--tokens", action="store_true", help="exibe a lista de tokens")
    p.add_argument("--arvore", action="store_true", help="exibe a árvore sintática")
    args = p.parse_args()

    ok = True
    for i, arq in enumerate(args.arquivos):
        if i:
            print("\n")
        ok &= compilar(arq, args.tokens, args.arvore)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
