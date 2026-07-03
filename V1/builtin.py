from .types import FunctionType
from . import interpreter
from .interpreter import Function, Node, Number
from .compiler import NumOperand

BUILT_INS = ("plus", "minus", "mult", "div", "if")


class BuiltInFunction(Function):
    def __init__(self, name):
        self.name = name
        if self.name == "if":
            self.type = FunctionType(
                ("cond", "then", "else"), ("return",))
            self.type.connect(set(("cond", "then", "else")), "return")
        else:
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
                    self.type.get_input_list()
                )
            )
        return self.node

    def compile(self, compiler):
        return "_PAG_" + BUILT_IN_CODES[self.name]

    def ad_compile(self, compiler):
        return NumOperand(BUILT_INS.index(self.name))


def generate_builtins():
    return {
        name: BuiltInFunction(name) for name in
        BUILT_INS
    }


def builtins_compile(compiler):
    for name in ("plus", "minus", "mult", "div"):
        code = BUILT_IN_CODES[name]
        compiler.add_line(
            "Node *{} = create_rl_built_in({});"
            .format("_PAG_" + code, code)
        )
    code = BUILT_IN_CODES["if"]
    compiler.add_line(
        "Node *{} = create_if_built_in({});"
        .format("_PAG_" + code, code)
    )


class BuiltInNode(interpreter.InterpretedNode):
    def find_argument(self, arguments, name):
        for name_, node in arguments:
            if name_ == name:
                return node

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


class IfNode(BuiltInNode):
    def clone(self, arguments):
        cond = self.find_argument(arguments, "cond")
        cond.eval()
        if cond.content.value:
            ret = self.find_argument(arguments, "then")
        else:
            ret = self.find_argument(arguments, "else")
        ret.eval()
        return ret


BUILT_IN_NODES = {
    "plus": PlusNode(),
    "mult": MultNode(),
    "minus": MinusNode(),
    "div": DivNode(),
    "if": IfNode()
}


BUILT_IN_CODES = {
    "plus": "sum",
    "mult": "mult",
    "minus": "minus",
    "div": "divide",
    "if": "if_node"
}
