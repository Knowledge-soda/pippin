from .types import FunctionType
from . import interpreter
from .interpreter import Function, Node, Number


class BuiltInFunction(Function):
    def __init__(self, name):
        self.name = name
        self.type = FunctionType(
            ("l", "r"), ("return",))
        self.type.connect(set(("l", "r")), "return")
        self.retfunc = True
        self.node = None

    def __repr__(self):
        return "BUILT_IN_FUNC({})".format(self.name)

    def outer_link(self, functions):
        return self

    def nodisate(self):
        if self.node is None:
            self.node = Node(
                Function(
                    {"l": None, "r": None},
                    {"return": BUILT_IN_NODES[self.name]},
                    ()))
        return self.node


def generate_builtins():
    return {
        name: BuiltInFunction(name) for name in "+-*/"
    }


class BuiltInNode(interpreter.InterpretedNode):
    def find_arguments(self, arguments):
        for name, node in arguments:
            if name == "l":
                node.eval()
                left = node.content
            if name == "r":
                node.eval()
                right = node.content
        return left, right


class PlusNode(BuiltInNode):
    def clone(self, arguments):
        left, right = self.find_arguments(arguments)
        return Node(Number(left.value + right.value))


class MultNode(BuiltInNode):
    def clone(self, arguments):
        left, right = self.find_arguments(arguments)
        return Node(Number(left.value * right.value))


class MinusNode(BuiltInNode):
    def clone(self, arguments):
        left, right = self.find_arguments(arguments)
        return Node(Number(left.value - right.value))


class DivNode(BuiltInNode):
    def clone(self, arguments):
        left, right = self.find_arguments(arguments)
        return Node(Number(left.value // right.value))


BUILT_IN_NODES = {
    "+": PlusNode(),
    "*": MultNode(),
    "-": MinusNode(),
    "/": DivNode()
}
