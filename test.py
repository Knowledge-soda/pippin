from itertools import pairwise

from V1 import lexer, parser, builtin, interpreter


def test_lexer(filename):
    with open(filename) as file:
        text = file.read()
    tokens = lexer.tokenize(text)
    print(tokens)


def test_parser(filename):
    with open(filename) as file:
        text = file.read()
    tokens = lexer.tokenize(text)
    program = parser.program(pairwise(tokens))
    print(program)
    return program


def test_linker(filename):
    with open(filename) as file:
        text = file.read()
    tokens = lexer.tokenize(text)
    program = parser.program(pairwise(tokens))
    program.link(builtin.generate_builtins())
    return program


def test_interpreter(filename):
    with open(filename) as file:
        text = file.read()
    tokens = lexer.tokenize(text)
    program = parser.program(pairwise(tokens))
    program.link(builtin.generate_builtins())
    nodes = program.nodisate()
    interpreter.driver(nodes)
