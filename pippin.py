import argparse

from V1 import lexer, parser, builtin, interpreter, compiler


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("filename")
    argparser.add_argument("-o", "--output", help="name of output file",
                           default="")
    argparser.add_argument("-d", "--debug", help="print debug info",
                           action="store_true")
    compile_type = argparser.add_mutually_exclusive_group()
    compile_type.add_argument("-i", "--interpret", action="store_true",
                              help="run interpreter")
    compile_type.add_argument("-c", "--ccompile", action="store_true",
                              help="compile to c")
    compile_type.add_argument("-b", "--bytecode", action="store_true",
                              help="compile to ad_hoc bytecode")
    args = argparser.parse_args()

    with open(args.filename) as file:
        text = file.read()
    tokens = lexer.tokenize(text)
    program = parser.program(parser.LL1(tokens))
    program.link(builtin.generate_builtins())

    if args.interpret:
        nodes = program.nodisate()
        interpreter.driver(nodes)
    elif args.ccompile:
        if not args.output:
            args.output = args.filename + ".c"
        comp = compiler.CCompiler()
        builtin.builtins_compile(comp)
        main_name = program.compile(comp)
        comp.finish(main_name, args.output)
    else:
        if not args.output:
            args.output = args.filename + ".ah"
        comp = compiler.AHCompiler()
        comp.set_builtins(builtin.BUILT_INS)
        program.ad_hoc_compile(comp)
        if args.debug:
            comp.print_instructions()
        comp.finish(args.output)
