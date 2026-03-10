from .lexer import Number, Name, Literal, END


class Application:
    def __init__(self, name):
        self.name = name
        self.params = []

    def __repr__(self):
        return "APPL({}, ({}))".format(
            repr(self.name),
            ", ".join(
                "{}={}".format(repr(name), repr(rhs))
                for name, rhs in self.params
            )
        )

    def add_param(self, name, rhs):
        self.params.append((name, rhs))

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

    def find_deps(self, result, context):
        self.left.find_deps(result, context)


class Function:
    def __init__(self, varlist, statlist):
        self.varlist = varlist
        self.results = statlist
        self.code = []

    def __repr__(self):
        return "CODE({})".format(
            ", ".join(
                "{}={}".format(repr(name), repr(rhs))
                for name, rhs in self.code
            )
        )

    def add_node(self, name, rhs, end=False):
        if end:
            self.results.append(name)
        self.code.append((name, rhs))

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
    if isinstance(now, Number):
        return now
    if not isinstance(now, Name):
        raise RuntimeError("{}, {}: Unexpected token {}.".format(
            now.row, now.col, repr(now)))
    cur = now
    if isinstance(new, Literal) and new.ch == "(":
        cur = Application(cur)
        next(it)
        now, new = next(it)
        if not isinstance(now, Name):
            raise RuntimeError("{}, {}: Unexpected token {}.".format(
                now.row, now.col, repr(now)))
        if not (isinstance(new, Literal) and new.ch == "="):
            raise RuntimeError("{}, {}: Unexpected token {}.".format(
                new.row, new.col, repr(new)))
        name = now
        next(it)
        rhs = expr(it)
        cur.add_param(name, rhs)
        now, new = next(it)
        while isinstance(now, Literal) and now.ch == ",":
            now, new = next(it)
            if not isinstance(now, Name):
                raise RuntimeError("{}, {}: Unexpected token {}.".format(
                    now.row, now.col, repr(now)))
            if not (isinstance(new, Literal) and new.ch == "="):
                raise RuntimeError("{}, {}: Unexpected token {}.".format(
                    new.row, new.col, repr(new)))
            name = now
            next(it)
            rhs = expr(it)
            cur.add_param(name, rhs)
            now, new = next(it)
        if not (isinstance(now, Literal) and now.ch == ")"):
            raise RuntimeError("{}, {}: Unexpected token {}.".format(
                now.row, now.col, repr(now)))
    if isinstance(new, Literal) and new.ch == ".":
        next(it)
        now, new = next(it)
        cur = Property(cur, now)
    return cur


def function(it):
    now, new = next(it)
    varlist = []
    statlist = []
    if not isinstance(now, Literal) or now.ch not in "([":
        raise RuntimeError("{}, {}: Unexpected token {}.".format(
            now.row, now.col, repr(now)))
    if isinstance(now, Literal) and now.ch == "(":
        now, new = next(it)
        if not isinstance(now, Name):
            raise RuntimeError("{}, {}: Unexpected token {}.".format(
                now.row, now.col, repr(now)))
        name = now
        varlist.append(name)
        now, new = next(it)
        while isinstance(now, Literal) and now.ch == ",":
            now, new = next(it)
            if not isinstance(now, Name):
                raise RuntimeError("{}, {}: Unexpected token {}.".format(
                    now.row, now.col, repr(now)))
            name = now
            varlist.append(name)
            now, new = next(it)
        if not (isinstance(now, Literal) and now.ch == ")"):
            raise RuntimeError("{}, {}: Unexpected token {}.".format(
                now.row, now.col, repr(now)))
        now, new = next(it)
    if isinstance(now, Literal) and now.ch == "[":
        now, new = next(it)
        if not isinstance(now, Name):
            raise RuntimeError("{}, {}: Unexpected token {}.".format(
                now.row, now.col, repr(now)))
        name = now
        statlist.append(name)
        now, new = next(it)
        while isinstance(now, Literal) and now.ch == ",":
            now, new = next(it)
            if not isinstance(now, Name):
                raise RuntimeError("{}, {}: Unexpected token {}.".format(
                    now.row, now.col, repr(now)))
            varlist.append(name)
            now, new = next(it)
        if not (isinstance(now, Literal) and now.ch == "]"):
            raise RuntimeError("{}, {}: Unexpected token {}.".format(
                now.row, now.col, repr(now)))
        now, new = next(it)
    cur = Function(varlist, statlist)
    if isinstance(now, Literal) and now.ch == "{":
        while not (isinstance(now, Literal) and now.ch == "}"):
            now, new = next(it)
            if isinstance(now, Literal) and now.ch == "[":
                result = True
                name, new = next(it)
                if not isinstance(name, Name):
                    raise RuntimeError("{}, {}: Unexpected token {}.".format(
                        name.row, name.col, repr(name)))
                if not (isinstance(new, Literal) and new.ch == "]"):
                    raise RuntimeError("{}, {}: Unexpected token {}.".format(
                        new.row, new.col, repr(new)))
                next(it)
            elif isinstance(now, Name):
                result = False
                name = now
            else:
                raise RuntimeError("{}, {}: Unexpected token {}.".format(
                    now.row, now.col, repr(now)))
            now, new = next(it)
            if not (isinstance(now, Literal) and now.ch == "="):
                raise RuntimeError("{}, {}: Unexpected token {}.".format(
                    now.row, now.col, repr(now)))
            rhs = expr(it)
            cur.add_node(name, rhs, result)
            now, new = next(it)
            if not (isinstance(now, Literal) and now.ch in "},"):
                raise RuntimeError("{}, {}: Unexpected token {}.".format(
                    now.row, now.col, repr(now)))
    return cur


def program(it):
    ret = Program()
    now, new = next(it)
    while now is not END:
        name = now
        if not (isinstance(new, Literal) and new.ch == "="):
            raise RuntimeError("{}, {}: Unexpected token {}.".format(
                new.row, new.col, repr(new)))
        next(it)
        func = function(it)
        ret.add_func(name, func)
        now, new = next(it)
    return ret
