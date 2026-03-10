from .lexer import Number, Name, Literal, END
from .error import UnexpectedTokenError, DuplicateNameError


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

    def find_deps(self, result, context):
        self.name.find_deps(result, context)
        for _, value in self.params:
            value.find_deps(result, context)


class Property:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return "PROP({}, {})".format(self.left, self.right)

    def inner_link(self, code, chain):
        self.left.inner_link(code, chain)
        return self

    def find_deps(self, result, context):
        self.left.find_deps(result, context)


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


class Argument:
    def __init__(self, name):
        self.name = name
        self.linked = True

    def __repr__(self):
        return "({})".format(self.name)

    def inner_link(self, code, chain):
        return self


class Function:
    def __init__(self, varlist, statlist):
        self.varlist = [Argument(var) for var in varlist]
        self.results = [Argument(var) for var in statlist]
        self.code = {var.text: Argument(var) for var in varlist}
        for var in self.results:
            self.code[var.text] = Argument(var)

    def __repr__(self):
        return "CODE({})".format(
            ", ".join(repr(assign) for assign in self.code.values())
        )

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

    def find_deps(self):
        context = tuple(val[0].text for val in self.code) +\
                  tuple(name.text for name in self.varlist)
        self.deps = set()
        for name, rhs in self.code:
            rhs.find_deps(self.deps, context)


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
