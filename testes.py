import unittest

from lexico import AnalisadorLexico
from sintatico import AnalisadorSintatico
from semantico import AnalisadorSemantico


def compilar(caminho):
    with open(caminho, encoding="utf-8") as f:
        tokens, erros = AnalisadorLexico(f.read()).tokenizar()
    assert not erros
    return AnalisadorSemantico().analisar(AnalisadorSintatico(tokens).analisar())


class TestesTrabalho3(unittest.TestCase):
    def test_exemplo1_tabela_e_tac(self):
        sem = compilar("exemplos/Exemplo1_SucessoTAC.java")
        self.assertEqual(sem.erros, [])
        tabela = [(s.lexema, s.tipo, s.largura, s.offset) for s in sem.tabela.simbolos.values()]
        self.assertEqual(tabela, [("a", "int", 4, 0), ("b", "int", 4, 4), ("resultado", "float", 8, 8)])
        esperado = """a = 10
t1 = a + 5
t2 = t1 * 2
b = t2
t3 = b > 20
if False t3 goto L1
t4 = float(b)
t5 = t4 / 2.5
resultado = t5
goto L2
L1:
t6 = a - 1
t7 = float(t6)
resultado = t7
L2:""".splitlines()
        self.assertEqual([q.para_tac() for q in sem.codigo], esperado)

    def test_exemplo2_escopo(self):
        msgs = [str(e) for e in compilar("exemplos/Exemplo2_ErroEscopo.java").erros]
        self.assertEqual(len(msgs), 2)
        self.assertIn("redeclaração da variável 'a'", msgs[0])
        self.assertIn("'b' não declarada", msgs[1])

    def test_exemplo3_tipos(self):
        msgs = [str(e) for e in compilar("exemplos/Exemplo3_ErroTipos.java").erros]
        self.assertEqual(len(msgs), 2)
        self.assertIn("estreitamento inválido", msgs[0])
        self.assertIn("atribuição incompatível", msgs[1])

    def test_exemplo4_while(self):
        self.assertEqual(compilar("exemplos/Exemplo4_While.java").erros, [])

    def test_exemplo5_char(self):
        self.assertEqual(len(compilar("exemplos/Exemplo5_ErroChar.java").erros), 2)


if __name__ == "__main__":
    unittest.main()
