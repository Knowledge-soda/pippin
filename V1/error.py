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
