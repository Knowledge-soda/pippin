from .lexer import Number, Name, Literal, END
from .error import UnexpectedTokenError, DuplicateNameError, \
        TypingError
from .types import FunctionType, NumberType
from .interpreter import Node
from . import interpreter


def check_token_type(token, token_class):
    if token == END:
        return False
    if isinstance(token_class, Literal):
        return isinstance(token, Literal) and token.ch == token_class.ch
    return isinstance(token, token_class)


def expect_token_type(token, token_class):
    if not check_token_type(token, token_class):
        raise UnexpectedTokenError(token, token_class.name)


def expect_token_types(token, class_list):
    for token_class in class_list:
        if check_token_type(token, token_class):
            return
    raise UnexpectedTokenError(
        token,
        "/".join(token_class.name for token_class in class_list)
    )


class Application:
    def __init__(self, name):
        self.name = name
        self.params = []
        self.linked = False
        self.retfunc = False
        self.node = None

    def __repr__(self):
        if isinstance(self.params, dict):
            return "APPL({}, ({}))".format(
                repr(self.name),
                ", ".join(
                    "{}={}".format(repr(name), repr(rhs))
                    for name, rhs in self.params.items()
                )
            )
        return "APPL({}, ({}))".format(
            repr(self.name),
            ", ".join(
                "{}={}".format(repr(name), repr(rhs))
                for name, rhs in self.params
            )
        )

    def add_param(self, name, rhs):
        self.params.append((name, rhs))

    def inner_link(self, code, chain):
        self.func = self.name.inner_link(code, chain)
        new_params = {}
        for name, value in self.params:
            new_params[name.text] = value.inner_link(code, chain)
        self.params = new_params
        return self

    def find_arguments(self):
        return self.func.find_arguments().union(
            *(value.find_arguments() for value in self.params.values()))

    def find_deps(self, result, context):
        self.name.find_deps(result, context)
        for _, value in self.params:
            value.find_deps(result, context)

    def outer_link(self, functions):
        if self.linked:
            return self
        self.linked = True
        self.func = self.func.outer_link(functions)
        for name, value in self.params.items():
            self.params[name] = value.outer_link(functions)
            if not isinstance(self.params[name].type, NumberType):
                raise TypingError(self.name.debug, "int",
                                  self.params[name].type)
        self.type = self.func.type.apply(self.params.keys())
        if self.func.retfunc:
            ret = Property(self, Name("return", self.name.debug))
            ret.type = NumberType()
            ret.linked = True
            return ret
        return self

    def nodisate(self):
        if self.node is None:
            func = self.func.nodisate()
            params = tuple(
                (key, node.nodisate()) for key, node in self.params.items())
            self.node = Node(interpreter.Application(func, params))
        return self.node


class Property:
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.linked = False
        self.node = None

    def __repr__(self):
        return "PROP({}, {})".format(self.left, self.right)

    def inner_link(self, code, chain):
        self.left = self.left.inner_link(code, chain)
        return self

    def find_arguments(self):
        return self.left.find_arguments()

    def find_deps(self, result, context):
        self.left.find_deps(result, context)

    def outer_link(self, functions):
        if self.linked:
            return self
        self.linked = True
        self.left = self.left.outer_link(functions)
        if not isinstance(self.left.type, FunctionType):
            raise TypingError(self.right.debug,
                              "function",
                              self.left.type)
        if not self.left.type.free(self.right.text):
            raise TypingError(self.right.debug,
                              "[{}]".format(self.right.text),
                              self.left.type)
        self.type = NumberType()
        return self

    def nodisate(self):
        if self.node is None:
            self.node = Node(interpreter.Property(self.left.nodisate(),
                                                  self.right.get_text()))
        return self.node


class Assignment:
    def __init__(self, name, right):
        self.name = name
        self.right = right
        self.linked = False

    def __repr__(self):
        return "ASSIGN({}={})".format(repr(self.name), repr(self.right))

    def inner_link(self, code, chain):
        if not self.linked:
            self.linked = True
            self.right = self.right.inner_link(code, chain + (self.name.text,))
        return self.right

    def find_arguments(self):
        return self.right.find_arguments()

    def get_text(self):
        return self.name.text

    def outer_link(self, functions):
        self.right = self.right.outer_link(functions)

    def nodisate(self):
        return self.right.nodisate()


class Argument:
    def __init__(self, name):
        self.name = name
        self.linked = True
        self.node = None

    def __repr__(self):
        return "({})".format(self.name)

    def inner_link(self, code, chain):
        return self

    def get_text(self):
        return self.name.text

    def find_arguments(self):
        return frozenset((self.name.text,))

    def outer_link(self, functions):
        self.type = NumberType()
        return self

    def nodisate(self):
        if self.node is None:
            self.node = Node(interpreter.Argument(self.name.text))
        return self.node


class Function:
    def __init__(self, varlist, statlist):
        self.varlist = [Argument(var) for var in varlist]
        self.results = [Argument(var) for var in statlist]
        self.code = {var.text: Argument(var) for var in varlist}
        for var in self.results:
            self.code[var.text] = Argument(var)
        self.node = None

    def __repr__(self):
        return "CODE({})".format(
            ", ".join(repr(assign) for assign in self.code.values())
        )

    @classmethod
    def _processed(cls, vardict, resultdict):
        ret = cls(tuple(), tuple())
        ret.node_vars = vardict
        ret.node_results = resultdict
        return ret

    def add_assign(self, name, rhs, end=False):
        if name.text in self.code:
            raise DuplicateNameError(self.code[name.text].name, name)
        assign = Assignment(name, rhs)
        if end:
            self.results.append(assign)
        self.code[name.text] = assign

    def inner_link(self):
        for result in self.results:
            result.inner_link(self.code, tuple())

    def compute_type(self):
        self.type = FunctionType(
            (var.get_text() for var in self.varlist),
            (var.get_text() for var in self.results)
        )
        for result in self.results:
            if isinstance(result, Argument):
                continue
            self.type.connect(result.find_arguments(), result.get_text())
        self.retfunc = len(self.results) == 1 and\
            self.results[0].get_text() == "return"

    def outer_link(self, functions):
        for result in self.results:
            result.outer_link(functions)

    def find_deps(self):
        context = tuple(val[0].text for val in self.code) +\
                  tuple(name.text for name in self.varlist)
        self.deps = set()
        for name, rhs in self.code:
            rhs.find_deps(self.deps, context)

    def nodisate(self):
        if self.node is None:
            self.node = Node(interpreter.Function.from_function(self))
            self.node.node = self.node
        return self.node


class Program:
    def __init__(self):
        self.functions = {}
        self.main = None

    def __repr__(self):
        return "PROGRAM:\n" + "\n".join(
                "{} = {}".format(name, repr(rhs))
                for name, rhs in self.functions.items())

    def add_func(self, name, body):
        if name.text == "main":
            self.main = body
        self.functions[name.text] = body

    def link(self, built_ins):
        for function in self.functions.values():
            function.inner_link()
            function.compute_type()
        self.functions.update(built_ins)
        for function in self.functions.values():
            function.outer_link(self.functions)

    def nodisate(self):
        return self.main.nodisate()


def expr(it):
    now, new = next(it)
    if check_token_type(now, Number):
        return now
    expect_token_types(now, (Name, Number))
    cur = now
    if check_token_type(new, Literal("(")):
        cur = Application(cur)
        next(it)
        now, new = next(it)
        expect_token_type(now, Name)
        expect_token_type(new, Literal("="))
        name = now
        next(it)
        rhs = expr(it)
        cur.add_param(name, rhs)
        now, new = next(it)
        while check_token_type(now, Literal(",")):
            now, new = next(it)
            expect_token_type(now, Name)
            expect_token_type(new, Literal("="))
            name = now
            next(it)
            rhs = expr(it)
            cur.add_param(name, rhs)
            now, new = next(it)
        expect_token_type(now, Literal(")"))
    if check_token_type(new, Literal(".")):
        next(it)
        now, new = next(it)
        cur = Property(cur, now)
    return cur


def function(it):
    now, new = next(it)
    varlist = []
    statlist = []
    expect_token_types(now, (Literal("("), Literal("[")))
    if check_token_type(now, Literal("(")):
        now, new = next(it)
        expect_token_type(now, Name)
        name = now
        varlist.append(name)
        now, new = next(it)
        while check_token_type(now, Literal(",")):
            now, new = next(it)
            expect_token_type(now, Name)
            name = now
            varlist.append(name)
            now, new = next(it)
        expect_token_type(now, Literal(")"))
        now, new = next(it)
    if check_token_type(now, Literal("[")):
        now, new = next(it)
        expect_token_type(now, Name)
        name = now
        statlist.append(name)
        now, new = next(it)
        while check_token_type(now, Literal(",")):
            now, new = next(it)
            expect_token_type(now, Name)
            varlist.append(name)
            now, new = next(it)
        expect_token_type(now, Literal("]"))
        now, new = next(it)
    cur = Function(varlist, statlist)
    if check_token_type(now, Literal("{")):
        while not check_token_type(now, Literal("}")):
            now, new = next(it)
            if check_token_type(now, Literal("[")):
                result = True
                name, new = next(it)
                expect_token_type(name, Name)
                expect_token_type(new, Literal("]"))
                next(it)
            elif check_token_type(now, Name):
                result = False
                name = now
            else:
                expect_token_types(now, (Literal("["), Name))
            now, new = next(it)
            expect_token_type(now, Literal("="))
            rhs = expr(it)
            cur.add_assign(name, rhs, result)
            now, new = next(it)
            expect_token_types(now, (Literal("}"), Literal(",")))
    return cur


def program(it):
    ret = Program()
    now, new = next(it)
    while now is not END:
        name = now
        expect_token_type(new, Literal("="))
        next(it)
        func = function(it)
        ret.add_func(name, func)
        now, new = next(it)
    return ret
