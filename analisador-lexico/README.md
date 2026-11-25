# Analisador Léxico Manual para Java

Trabalho Prático – Implementação Manual de um Analisador Léxico.

## Características

- Implementado em Python, sem Lex/Flex/PLY/ANTLR.
- Recebe um arquivo `.java`.
- Carrega o código-fonte em memória.
- Implementa esquema de **dois buffers** com `begin pointer (bp)` e `forward pointer (fp)`.
- Reconhece palavras-chave, identificadores, inteiros, reais, caracteres, strings, operadores e delimitadores.
- Ignora espaços, quebras de linha e comentários `//` e `/* ... */`.
- Gera `ERROR` para erros léxicos, incluindo:
  - string não terminada;
  - comentário de bloco não terminado;
  - número seguido de identificador (`123abc`);
  - uso de vírgula como separador decimal (`3,14`);
  - caractere não reconhecido;
  - literal de caractere inválido/não terminado.
- Mantém tabela de símbolos com identificadores e quantidade de ocorrências.
- Mantém tabela de tokens com tipo, lexema, atributo e posição.
- Exporta os resultados em JSON.

## Requisitos

Python 3.10+.

## Execução

```bash
python main.py examples/sucesso.java
```

Salvar em JSON:

```bash
python main.py examples/sucesso.java --json saida.json
```

Mostrar somente os tokens:

```bash
python main.py examples/sucesso.java --tokens
```

## Estrutura

```text
analisador_lexico_java/
├── main.py
├── lexer.py
├── token.py
├── symbol_table.py
├── buffer.py
├── examples/
│   ├── sucesso.java
│   └── erro_lexico.java
└── README.md
```

## Observação sobre o esquema de buffers

O arquivo é carregado em memória, conforme solicitado no trabalho. O `TwoBufferReader`
organiza a leitura em dois buffers de tamanho fixo. O `bp` marca o início do lexema
e o `fp` percorre os caracteres à frente. O leitor permite lookahead e alterna os
buffers quando o final de um bloco é atingido.

A extração final do lexema é feita usando as posições absolutas `bp` e `fp` no
código-fonte mantido em memória. Isso permite que um lexema atravesse a fronteira
entre os dois buffers sem perda de caracteres.
