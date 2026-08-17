from .types import FunctionType
from . import interpreter
from .interpreter import Function, Node, Number, Property, Application, String
from .compiler import NumOperand

BUILT_INS = ("plus", "minus", "mult", "div", "less", "more",
             "equal", "geq", "leq", "if", "get", "apply",
             "strhead", "strtail", "strempty")


class BuiltInFunction(Function):
    def __init__(self, name):
        self.name = name
        if self.name == "if":
            self.type = FunctionType(
                ("cond", "then", "else"), ("return",))
            self.type.connect(set(("cond", "then", "else")), "return")
        elif self.name == "get":
            self.type = FunctionType(
                ("function", "property"), ("return",))
            self.type.connect(set(("function", "property")), "return")
        elif self.name == "apply":
            self.type = FunctionType(
                ("function", "name", "value"), ("return",))
            self.type.connect(set(("function", "name", "value")), "return")
        elif self.name.startswith("str"):
            self.type = FunctionType(
                ("str", ), ("return",)
            )
            self.type.connect(set(("str",)), "return")
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
    for name in BUILT_INS:
        code = BUILT_IN_CODES[name]
        if name == "if":
            compiler.add_line(
                "Node *{} = create_ternary_built_in({},"
                "\"cond\", \"then\", \"else\");"
                .format("_PAG_" + code, code)
            )
        elif name == "apply":
            compiler.add_line(
                "Node *{} = create_ternary_built_in({},"
                "\"function\", \"name\", \"value\");"
                .format("_PAG_" + code, code)
            )
        elif name == "get":
            compiler.add_line(
                "Node *{} = create_ternary_built_in({},"
                "\"function\", \"property\", NULL);"
                .format("_PAG_" + code, code)
            )
        elif name.startswith("str"):
            compiler.add_line(
                "Node *{} = create_str_built_in({});"
                .format("_PAG_" + code, code)
            )
        else:
            compiler.add_line(
                "Node *{} = create_rl_built_in({});"
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


class LessNode(BuiltInNode):
    def clone(self, arguments):
        left, right = self.find_arguments(arguments)
        return Node(Number(int(left.value < right.value)))


class MoreNode(BuiltInNode):
    def clone(self, arguments):
        left, right = self.find_arguments(arguments)
        return Node(Number(int(left.value > right.value)))


class EqualNode(BuiltInNode):
    def clone(self, arguments):
        left, right = self.find_arguments(arguments)
        return Node(Number(int(left.value == right.value)))


class GeqNode(BuiltInNode):
    def clone(self, arguments):
        left, right = self.find_arguments(arguments)
        return Node(Number(int(left.value >= right.value)))


class LeqNode(BuiltInNode):
    def clone(self, arguments):
        left, right = self.find_arguments(arguments)
        return Node(Number(int(left.value <= right.value)))


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


class GetNode(BuiltInNode):
    def clone(self, arguments):
        function = self.find_argument(arguments, "function")
        name = self.find_argument(arguments, "property")
        name.eval()
        return Node(Property(function, name.content.value))


class ApplyNode(BuiltInNode):
    def clone(self, arguments):
        function = self.find_argument(arguments, "function")
        name = self.find_argument(arguments, "name")
        name.eval()
        value = self.find_argument(arguments, "value")
        return Node(Application(function, ((name.content.value, value),)))


class StrHead(BuiltInNode):
    def clone(self, arguments):
        string = self.find_argument(arguments, "str")
        string.eval()
        return Node(Number(ord(string.content.value[0])))


class StrTail(BuiltInNode):
    def clone(self, arguments):
        string = self.find_argument(arguments, "str")
        string.eval()
        return Node(String(string.content.value[1:]))


class StrEmpty(BuiltInNode):
    def clone(self, arguments):
        string = self.find_argument(arguments, "str")
        string.eval()
        return Node(Number(int(len(string.content.value) == 0)))


BUILT_IN_NODES = {
    "plus": PlusNode(),
    "mult": MultNode(),
    "minus": MinusNode(),
    "div": DivNode(),
    "less": LessNode(),
    "more": MoreNode(),
    "equal": EqualNode(),
    "geq": GeqNode(),
    "leq": LeqNode(),
    "if": IfNode(),
    "get": GetNode(),
    "apply": ApplyNode(),
    "strhead": StrHead(),
    "strtail": StrTail(),
    "strempty": StrEmpty()
}


BUILT_IN_CODES = {
    "plus": "sum",
    "mult": "mult",
    "minus": "minus",
    "div": "divide",
    "less": "less",
    "more": "more",
    "equal": "equal",
    "geq": "geq",
    "leq": "leq",
    "if": "if_node",
    "get": "get_node",
    "apply": "apply_node",
    "strhead": "str_head",
    "strtail": "str_tail",
    "strempty": "str_empty"
}
