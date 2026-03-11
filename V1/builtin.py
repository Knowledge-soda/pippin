from .types import FunctionType
from .parser import Function


class BuiltInFunction(Function):
    def __init__(self, name):
        self.name = name
        self.type = FunctionType(
            ("l", "r"), ("return",))
        self.type.connect(set(("l", "r")), "return")
        self.retfunc = True

    def __repr__(self):
        return "BUILT_IN_FUNC({})".format(self.name)

    def outer_link(self, functions):
        return self


def generate_builtins():
    return {
        name: BuiltInFunction(name) for name in "+-*/"
    }
