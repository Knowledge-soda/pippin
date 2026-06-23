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
                    {"return": BUILT_IN_NODES[self.name]},
                    (("l", None), ("r", None))
                )
            )
        return self.node

    def compile(self, compiler):
        return "_PAG_" + BUILT_IN_CODES[self.name]


def generate_builtins():
    return {
        name: BuiltInFunction(name) for name in
        ("plus", "minus", "mult", "div")
    }


def builtins_compile(compiler):
    for name in ("plus", "minus", "mult", "div"):
        code = BUILT_IN_CODES[name]
        compiler.add_line(
            "Node *{} = create_rl_built_in({});"
            .format("_PAG_" + code, code)
        )


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
    "plus": PlusNode(),
    "mult": MultNode(),
    "minus": MinusNode(),
    "div": DivNode()
}


BUILT_IN_CODES = {
    "plus": "sum",
    "mult": "mult",
    "minus": "minus",
    "div": "divide"
}
