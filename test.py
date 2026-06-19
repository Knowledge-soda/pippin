from V1 import lexer, parser, builtin, interpreter, compiler


def test_lexer(filename):
    with open(filename) as file:
        text = file.read()
    tokens = lexer.tokenize(text)
    print(tokens)


def test_parser(filename):
    with open(filename) as file:
        text = file.read()
    tokens = lexer.tokenize(text)
    program = parser.program(parser.LL1(tokens))
    print(program)
    return program


def test_linker(filename):
    with open(filename) as file:
        text = file.read()
    tokens = lexer.tokenize(text)
    program = parser.program(parser.LL1(tokens))
    program.link(builtin.generate_builtins())
    return program


def test_interpreter(filename):
    with open(filename) as file:
        text = file.read()
    tokens = lexer.tokenize(text)
    program = parser.program(parser.LL1(tokens))
    program.link(builtin.generate_builtins())
    nodes = program.nodisate()
    interpreter.driver(nodes)


def test_compiler(filename, compiled_filename):
    with open(filename) as file:
        text = file.read()
    tokens = lexer.tokenize(text)
    program = parser.program(parser.LL1(tokens))
    program.link(builtin.generate_builtins())
    comp = compiler.Compiler()
    builtin.builtins_compile(comp)
    main_name = program.compile(comp)
    comp.finish(main_name, compiled_filename)
