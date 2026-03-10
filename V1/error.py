class CompilerError(Exception):
    pass


class LexicalError(CompilerError):
    def __init__(self, message, debug):
        row, col = debug
        super().__init__(
            "Error line {}, col {}: {}".format(row, col, message)
        )


class SyntacticError(CompilerError):
    def __init__(self, message, debug):
        row, col = debug
        super().__init__(
            "Error line {}, col {}: {}".format(row, col, message)
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


class AssignmentLoopError(SemanticError):
    def __init__(self, chain):
        super().__init__(
            "There is assignment loop: {}!"
            .format(", ".join(chain))
        )
