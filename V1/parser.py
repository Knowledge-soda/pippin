from .lexer import Number, Name, Literal, END
from .error import UnexpectedTokenError, DuplicateNameError, \
        TypingError, SyntacticError
from .types import FunctionType, NumberType
from .interpreter import Node
from . import interpreter
from .compiler import NumOperand, FuncRef, Instruction


class LL1:
    def __init__(self, stream):
        self._gen = self._look_ahead_iterator(stream)
        self._repeat = False

    def __iter__(self):
        return self

    def __next__(self):
        if self._repeat:
            self._repeat = False
            return (self.now, self.look_ahead)
        return next(self._gen)

    def _look_ahead_iterator(self, it):
        self.now = next(it)
        for look_ahead in it:
            self.look_ahead = look_ahead
            yield self.now, look_ahead
            self.now = look_ahead
        self.look_ahead = END
        yield self.now, look_ahead

    def repeat_last(self):
        self._repeat = True


def check_token_type(token, token_class):
    if token == END:
        return False
    if isinstance(token_class, Literal):
        return isinstance(token, Literal) and token.ch == token_class.ch
    return isinstance(token, token_class)


def check_token_types(token, class_list):
    for token_class in class_list:
        if check_token_type(token, token_class):
            return True
    return False


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


class BinOp:
    TABLE = {
            "+": "plus",
            "-": "minus",
            "*": "mult",
            "/": "div"
    }

    def __init__(self, left, right, op):
        self.left = left
        self.right = right
        self.op = op

    def __repr__(self):
        return "BIN{}({}, {})".format(
                repr(self.op), repr(self.left), repr(self.right))

    def inner_link(self, code, chain):
        ret = Application(Name(self.TABLE[self.op.ch], self.op.debug))
        ret.add_param(Name("l", self.op.debug), self.left)
        ret.add_param(Name("r", self.op.debug), self.right)
        return ret.inner_link(code, chain)


class Application:
    def __init__(self, name):
        self.name = name
        self.params = []
        self.linked = False
        self.retfunc = False
        self.node = None
        self.ccname = None
        self.instruction = None

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

    def inner_link(self, code, chain):
        self.func = self.name.inner_link(code, chain)
        # TODO: accept number specified inputs
        accepting = 0
        new_params = []
        for i, (name, value) in enumerate(self.params):
            right = value.inner_link(code, chain)
            if name is None:
                if accepting:
                    raise SyntacticError("Free argument too late!",
                                         value.debug)
                new_params.append((i, right))
            if isinstance(name, Name):
                new_params.append((name.text, right))
                accepting = 2
        self.params = new_params
        return self

    def find_arguments(self):
        return self.func.find_arguments().union(
            *(value.find_arguments() for _, value in self.params))

    def outer_link(self, functions):
        if self.linked:
            return self.assign_element
        self.linked = True
        self.func = self.func.outer_link(functions)
        for i, (name, value) in enumerate(self.params):
            self.params[i] = (name, value.outer_link(functions))
            if not isinstance(self.params[i][1].type, NumberType):
                raise TypingError(self.name.debug, "int",
                                  self.params[i][1].type)
        self.type = self.func.type.apply((name) for name, _ in self.params)
        if self.func.retfunc:
            ret = Property(self, Name("return", self.name.debug))
            ret.type = NumberType()
            ret.linked = True
            self.assign_element = ret
            return ret
        self.assign_element = self
        return self

    def nodisate(self):
        if self.node is None:
            func = self.func.nodisate()
            params = tuple(
                (key, node.nodisate()) for key, node in self.params)
            self.node = Node(interpreter.Application(func, params))
        return self.node

    def compile(self, compiler):
        if self.ccname is None:
            self.ccname = compiler.get_name("APPL")
            func = self.func.compile(compiler)
            compiler.add_line(
                "Node *{} = create_application({}, {});"
                .format(self.ccname, func, len(self.params)))
            for key, node in self.params:
                node_name = node.compile(compiler)
                if isinstance(key, int):
                    compiler.add_line(
                        "set_appl_arg_num({}, {}, {});"
                        .format(self.ccname, key, node_name)
                    )
                else:
                    compiler.add_line(
                        "set_appl_arg_str({}, \"{}\", {});"
                        .format(self.ccname, key, node_name)
                    )
        return self.ccname

    def ad_compile(self, compiler):
        if self.instruction is None:
            func = self.func.ad_compile(compiler)
            app_ins = []
            for key, node in self.params:
                node_ins = node.ad_compile(compiler)
                if isinstance(key, int):
                    ins = Instruction("SET_NUM_ARG",
                                      NumOperand(key),
                                      node_ins)
                else:
                    key_index = compiler.add_constant(key)
                    ins = Instruction("SET_STR_ARG",
                                      NumOperand(key_index),
                                      node_ins)
                app_ins.append(ins)
            self.instruction = Instruction("APPLY", func,
                                           NumOperand(len(self.params)))
            compiler.add_instruction(self.instruction)
            for ins in app_ins:
                compiler.add_instruction(ins)
        return NumOperand(self.instruction.index)


class Property:
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.linked = False
        self.node = None
        self.ccname = None
        self.instruction = None
        self.assign_element = self

    def __repr__(self):
        return "PROP({}, {})".format(self.left, self.right)

    def inner_link(self, code, chain):
        self.left = self.left.inner_link(code, chain)
        return self

    def find_arguments(self):
        return self.left.find_arguments()

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

    def compile(self, compiler):
        if self.ccname is None:
            self.ccname = compiler.get_name("PROP")
            leftname = self.left.compile(compiler)
            compiler.add_line(
                "Node *{} = create_property({}, \"{}\");"
                .format(self.ccname, leftname, self.right.get_text())
            )
        return self.ccname

    def ad_compile(self, compiler):
        if self.instruction is None:
            left_ins = self.left.ad_compile(compiler)
            str_index = compiler.add_constant(self.right.get_text())
            self.instruction = Instruction("PROPERTY", left_ins,
                                           NumOperand(str_index))
            compiler.add_instruction(self.instruction)
        return NumOperand(self.instruction.index)


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
        self.right = self.right.outer_link(functions).assign_element

    def nodisate(self):
        return self.right.nodisate()

    def compile(self, compiler):
        return self.right.compile(compiler)

    def ad_compile(self, compiler):
        return self.right.ad_compile(compiler)


class Argument:
    def __init__(self, name):
        self.name = name
        self.linked = True
        self.node = None
        self.ccname = None
        self.instruction = None
        self.assign_element = self

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

    def compile(self, compiler):
        if self.ccname is None:
            self.ccname = compiler.get_name("ARG")
            compiler.add_line(
                "Node *{} = create_name(\"{}\");".
                format(self.ccname, self.name.text)
            )
        return self.ccname

    def ad_compile(self, compiler):
        if self.instruction is None:
            str_index = compiler.add_constant(self.name.text)
            self.instruction = Instruction("ARG_NAME", NumOperand(str_index))
            compiler.add_instruction(self.instruction)
        return NumOperand(self.instruction.index)


class Function:
    def __init__(self, varlist, statlist):
        self.varlist = [Argument(var) for var in varlist]
        self.results = [Argument(var) for var in statlist]
        self.code = {var.text: Argument(var) for var in varlist}
        for var in self.results:
            self.code[var.text] = Argument(var)
        self.node = None
        self.ccname = None
        self.instruction = None

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
        self.assign_element = self
        for result in self.results:
            result.outer_link(functions)

    def nodisate(self):
        if self.node is None:
            self.node = Node(None)
            self.node.content = interpreter.Function.from_function(self)
            self.node.node = self.node
        return self.node

    def compile(self, compiler):
        if self.ccname is None:
            self.ccname = compiler.get_name("FUNC")
            compiler.add_line(
                "Node *{} = create_func({}, {});"
                .format(self.ccname, len(self.varlist), len(self.results))
            )
            for var in self.varlist:
                compiler.add_line(
                    "set_func_arg({}, \"{}\");"
                    .format(self.ccname, var.get_text())
                )
            for assignment in self.results:
                key = assignment.get_text()
                node = assignment.compile(compiler)
                compiler.add_line(
                    "set_func_res({}, \"{}\", {});"
                    .format(self.ccname, key, node)
                )
        return self.ccname

    def ad_hoc_compile(self, compiler):
        if self.instruction is None or isinstance(self.instruction, FuncRef):
            args = []
            for var in self.varlist:
                args.append(NumOperand(compiler.add_constant(var.get_text())))
            self.instruction = Instruction("AD_FUNC",
                                           NumOperand(len(self.results)),
                                           NumOperand(len(self.varlist)),
                                           *args)
            compiler.add_instruction(self.instruction)
            for assignment in self.results:
                key = NumOperand(compiler.add_constant(assignment.get_text()))
                ins = assignment.ad_compile(compiler)
                compiler.add_instruction(Instruction("SET_RES", key, ins))

    def ad_compile(self, compiler):
        if self.instruction is None:
            compiler.add_function(self)
            self.instruction = FuncRef(self)
        if isinstance(self.instruction, FuncRef):
            return self.instruction
        else:
            return NumOperand(self.instruction.index)


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

    def compile(self, compiler):
        return self.main.compile(compiler)

    def ad_hoc_compile(self, compiler):
        compiler.add_function(self.main)
        compiler.aggregate()


def expression(it):
    ret = expression2(it)
    now, new = next(it)
    while check_token_types(now, (Literal("+"), Literal("-"))):
        right = expression2(it)
        ret = BinOp(ret, right, now)
        now, new = next(it)
    it.repeat_last()
    return ret


def expression2(it):
    ret = expr(it)
    now, new = next(it)
    while check_token_types(now, (Literal("*"), Literal("/"))):
        right = expr(it)
        ret = BinOp(ret, right, now)
        now, new = next(it)
    it.repeat_last()
    return ret


def expr(it):
    now, new = next(it)
    if check_token_type(now, Number):
        return now
    expect_token_types(now, (Name, Number))
    cur = now
    while check_token_types(new, (Literal("("), Literal("."))):
        if check_token_type(new, (Literal("("))):
            cur = Application(cur)
            next(it)
            now, new = next(it)
            if check_token_type(new, Literal("=")):
                expect_token_type(now, Name)
                name = now
                next(it)
            else:
                name = None
                it.repeat_last()
            rhs = expression(it)
            cur.add_param(name, rhs)
            now, new = next(it)
            while check_token_type(now, Literal(",")):
                now, new = next(it)
                if check_token_type(new, Literal("=")):
                    expect_token_type(now, Name)
                    name = now
                    next(it)
                else:
                    name = None
                    it.repeat_last()
                rhs = expression(it)
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
            rhs = expression(it)
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
