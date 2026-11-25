public class Calculadora {
    private int resultado = 10;
    private float taxa = 3.14;
    private char inicial = 'A';
    private String mensagem = "Olá\nMundo";

    public static int somar(int a, int b) {
        int total = a + b;
        if (total >= 20 && a != 0) {
            resultado += total;
        } else {
            resultado = resultado - 1;
        }
        return resultado;
    }

    public static void main(String[] args) {
        resultado *= 2;
        taxa /= 2.0;
        System.out.println(mensagem);
    }
}
