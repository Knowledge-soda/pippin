class CompilerError(Exception):
    pass


class LexicalError(CompilerError):
    def __init__(self, message, debug):
        row, col = debug
        super().__init__(
            "line {}, col {}: {}".format(row, col, message)
        )


class SyntacticError(CompilerError):
    def __init__(self, message, debug):
        row, col = debug
        super().__init__(
            "line {}, col {}: {}".format(row, col, message)
        )


class UnexpectedTokenError(SyntacticError):
    def __init__(self, token, expected_type):
        super().__init__(
            "Expected {} token, got {}".format(expected_type, token),
            token.debug
        )


class SemanticError(CompilerError):
    pass


class DuplicateNameError(SemanticError):
    def __init__(self, token1, token2):
        super().__init__(
            "'{}' assigned to twice ({}:{} and {}:{}) in one function!"
            .format(token1.text, *token1.debug, *token2.debug)
        )


class DuplicateParametarError(SemanticError):
    def __init__(self, token1, token2):
        super().__init__(
            "'{}' assigned to twice ({}:{} and {}:{}) in one application!"
            .format(token1.text, *token1.debug, *token2.debug)
        )


class AssignmentLoopError(SemanticError):
    def __init__(self, chain):
        super().__init__(
            "There is assignment loop: {}!"
            .format(", ".join(chain))
        )


class TypingError(SemanticError):
    def __init__(self, debug, wanted, got):
        super().__init__(
            "line {}, col {}: expected type {}, got {}"
            .format(debug[0], debug[1], wanted, repr(got))
        )


class UnknownNameError(SemanticError):
    def __init__(self, debug, text):
        super().__init__(
            "line {}, col {}: unknown name {}"
            .format(debug[0], debug[1], text)
        )
