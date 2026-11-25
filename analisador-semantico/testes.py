"""Testes automáticos: python3 -m unittest testes.py (dentro de analisador-semantico)."""
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(1, str(BASE_DIR.parent / "analisador-lexico"))
sys.path.insert(1, str(BASE_DIR.parent / "analisador-sintatico"))

from lexer import Lexer  # noqa: E402
from grammar import Grammar  # noqa: E402
from ll1 import LL1  # noqa: E402
from ll1_parser import PredictiveParser  # noqa: E402
from token_adapter import tokens_to_input  # noqa: E402
from semantic_analyzer import SemanticAnalyzer  # noqa: E402

LL1_TABLE = LL1(Grammar.from_file(BASE_DIR.parent / "analisador-sintatico" / "gramatica.txt"))


def compilar(nome: str) -> SemanticAnalyzer:
    tokens = Lexer.from_file(BASE_DIR / "exemplos" / nome).tokenize()
    assert not [t for t in tokens if t.tipo == "ERROR"]
    resultado = PredictiveParser(LL1_TABLE).parse(tokens_to_input(tokens))
    assert resultado.aceito
    return SemanticAnalyzer().analyze(resultado.arvore)


class TestesTrabalho3(unittest.TestCase):
    def test_gramatica_continua_ll1(self):
        self.assertTrue(LL1_TABLE.is_ll1)

    def test_exemplo1_tabela_e_tac(self):
        sem = compilar("Exemplo1_SucessoTAC.java")
        self.assertTrue(sem.aprovado)
        tabela = [(s.lexema, s.tipo, s.width, s.offset) for s in sem.tabela.symbols()]
        self.assertEqual(tabela, [("a", "int", 4, 0), ("b", "int", 4, 4),
                                  ("resultado", "float", 8, 8)])
        esperado = [
            "a = 10", "t1 = a + 5", "t2 = t1 * 2", "b = t2", "t3 = b > 20",
            "if False t3 goto L1", "t4 = float(b)", "t5 = t4 / 2.5", "resultado = t5",
            "goto L2", "L1:", "t6 = a - 1", "t7 = float(t6)", "resultado = t7", "L2:",
        ]
        self.assertEqual(sem.codigo.tac(), esperado)

    def test_exemplo2_escopo(self):
        msgs = [str(e) for e in compilar("Exemplo2_ErroEscopo.java").erros]
        self.assertEqual(len(msgs), 2)
        self.assertIn("redeclaração da variável 'a'", msgs[0])
        self.assertIn("'b' não declarada", msgs[1])

    def test_exemplo3_tipos(self):
        msgs = [str(e) for e in compilar("Exemplo3_ErroTipos.java").erros]
        self.assertEqual(len(msgs), 2)
        self.assertIn("estreitamento inválido", msgs[0])
        self.assertIn("atribuição incompatível", msgs[1])

    def test_exemplo4_while(self):
        self.assertTrue(compilar("Exemplo4_While.java").aprovado)

    def test_exemplo5_char(self):
        self.assertEqual(len(compilar("Exemplo5_ErroChar.java").erros), 2)


if __name__ == "__main__":
    unittest.main()
