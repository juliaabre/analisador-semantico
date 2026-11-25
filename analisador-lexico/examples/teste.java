package teste;

import java.util.List;
import java.util.ArrayList;

// Classe utilizada para testar o analisador léxico
public class TesteLexer {

    // Constantes
    private static final int LIMITE = 100;
    private static final double PI = 3.14159;
    private static final String MENSAGEM = "Olá, mundo!";

    /*
     * Método principal.
     * Este comentário também deve ser ignorado pelo lexer.
     */
    public static void main(String[] args) {

        int idade = 25;
        double altura = 1.75;
        boolean estudante = true;
        char inicial = 'J';
        String nome = "Julia";

        // Operadores aritméticos
        int soma = idade + 10;
        int subtracao = idade - 5;
        int multiplicacao = idade * 2;
        int divisao = idade / 5;
        int resto = idade % 2;

        // Operadores relacionais e lógicos
        if (idade >= 18 && estudante == true) {
            System.out.println("Maior de idade e estudante.");
        } else {
            System.out.println("Menor de idade ou não estudante.");
        }

        // Estrutura de repetição for
        for (int i = 0; i < 10; i++) {
            System.out.println("Valor: " + i);
        }

        // Estrutura while
        int contador = 0;

        while (contador < 5) {
            contador++;
        }

        // Array
        int[] numeros = {10, 20, 30, 40, 50};

        for (int numero : numeros) {
            System.out.println(numero);
        }

        // Lista
        List<String> nomes = new ArrayList<>();
        nomes.add("Ana");
        nomes.add("Bruno");
        nomes.add("Carlos");

        // Chamada de método
        calcularMedia(10.0, 8.5, 9.0);

        // Operador ternário
        String resultado = idade >= 18 ? "Adulto" : "Menor";

        // Operadores de atribuição
        idade += 1;
        idade -= 2;
        idade *= 2;
        idade /= 2;

        // Operadores de incremento/decremento
        idade++;
        ++idade;
        idade--;
        --idade;

        // Valores especiais
        int hexadecimal = 0xFF;
        int binario = 0b1010;
        int octal = 077;
        long grande = 123456789L;
        float decimal = 10.5f;

        // Escape em String e char
        String texto = "Linha 1\nLinha 2\tTab";
        char aspas = '\"';

        System.out.println(MENSAGEM);
        System.out.println("Nome: " + nome);
        System.out.println("Inicial: " + inicial);
        System.out.println("Altura: " + altura);
        System.out.println("Resultado: " + resultado);
    }

    /**
     * Calcula a média de três valores.
     */
    public static double calcularMedia(
            double nota1,
            double nota2,
            double nota3) {

        return (nota1 + nota2 + nota3) / 3.0;
    }
}