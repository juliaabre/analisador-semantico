public class TesteWhile {
    public static void main() {
        int i;
        float soma;
        char c;

        i = 0;
        soma = 0;
        c = 'x';

        while (i < 5) {
            soma = soma + i * 2;
            i = i + 1;
        }

        if (soma != 20) {
            c = 'n';
        }
    }
}
