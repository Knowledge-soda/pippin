from .error import LexicalError, AssignmentLoopError, UnknownNameError
from .types import NumberType
from .interpreter import Node
from . import interpreter
from .compiler import NumOperand, Instruction

ADDITIONAL = "_"
LITERALS = "=()[]{}.\\,+-*/<>"


class END:
    name = "END"


class LL1Text:
    STRING_TABLE = {
        "n": "\n",
        "\"": "\"",
        "\\": "\\"
    }

    def __init__(self, text):
        self._gen = self._look_ahead_iterator(iter(text))
        self.row = 1
        self.col = 1

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._gen)

    def _look_ahead_iterator(self, it):
        self.now = next(it)
        for look_ahead in it:
            self.look_ahead = look_ahead
            yield self.now, look_ahead
            if self.now == '\n':
                self.row += 1
                self.col = 1
            else:
                self.col += 1
            self.now = look_ahead
        self.look_ahead = END
        yield self.now, look_ahead

    def get_debug(self):
        return self.row, self.col

    def read_while(self, condition):
        buffer = [self.now]
        while self.look_ahead != END and condition(self.look_ahead):
            next(self)
            buffer.append(self.now)
        return "".join(buffer)

    def read_name(self):
        if not (self.now.isalpha() or self.now in ADDITIONAL):
            raise LexicalError(
                "Variable name starts with invalid character '{}'!"
                .format(self.now), self.get_debug())
        buffer = [self.now]
        while self.look_ahead != END and (self.look_ahead.isalnum()
                                          or self.look_ahead in ADDITIONAL):
            next(self)
            buffer.append(self.now)
        return "".join(buffer)

    def read_string(self):
        next(self)
        buffer = []
        while self.now != '"':
            if self.look_ahead == END:
                raise LexicalError(
                    "String does not terminate!",
                    self.get_debug())
            if not self.now.isprintable():
                next(self)
                continue
            if self.now == "\\":
                if self.look_ahead in self.STRING_TABLE:
                    buffer.append(self.STRING_TABLE[self.look_ahead])
                    next(self)
                else:
                    raise LexicalError(
                        "Unknown escape character '\\{}'"
                        .format(self.now), self.get_debug())
            else:
                buffer.append(self.now)
            next(self)
        return "".join(buffer)


class Number:
    name = "NUM"

    def __init__(self, text, debug):
        self.n = int(text)
        self.row, self.col = self.debug = debug
        self.name = "NUM {}".format(self.n)
        self.linked = False
        self.node = None
        self.ccname = None
        self.instruction = None

    def __repr__(self):
        return self.name

    def inner_link(self, *args):
        return self

    def find_arguments(self):
        return frozenset()

    def outer_link(self, *args):
        if self.linked:
            return self
        self.linked = True
        self.assign_element = self
        self.type = NumberType()
        return self

    def re_link(self, *args):
        return self

    def apply_replace(self, *args):
        return self

    def link(self, parent):
        return self

    def accumulate_closure(self, *args):
        pass

    def nodisate(self):
        if self.node is None:
            self.node = Node(interpreter.Number(self.n))
        return self.node

    def compile(self, compiler):
        if self.ccname is None:
            self.ccname = compiler.get_name("num")
            compiler.add_line(
                "Node *{} = create_number({});".format(self.ccname, self.n))
        return self.ccname

    def ad_compile(self, compiler):
        if self.instruction is None:
            self.instruction = Instruction("NUM_CONST", NumOperand(self.n))
            compiler.add_instruction(self.instruction)
        return NumOperand(self.instruction.index)


class Name:
    name = "NAME"

    def __init__(self, text, debug):
        self.text = text
        self.row, self.col = self.debug = debug
        self.name = "NAME '{}'".format(text)

    def __repr__(self):
        return self.name

    def inner_link(self, func, chain):
        if self.text in chain:
            raise AssignmentLoopError(chain + (self.text,))
        if self.text in func.code:
            assign = func.code[self.text]
            return assign.inner_link(func, chain)
        else:
            func.unknowns.add(self.text)
            return self

    def re_link(self, closure):
        if self.text in closure:
            return closure[self.text]
        else:
            return self

    def apply_replace(self):
        return self

    def find_arguments(self):
        return frozenset()

    def get_text(self):
        return self.text

    def outer_link(self, functions):
        if self.text not in functions:
            raise UnknownNameError(self.debug, self.text)
        return functions[self.text]

    def link(self, parent):
        return self

    def accumulate_closure(self, code, closure):
        if self.text in code.keys():
            closure.add(self.text)

    def find_deps(self, result, context):
        if self.text not in context:
            result.add(self.text)


class String:
    name = "STRING"

    def __init__(self, text, debug):
        self.text = text
        self.row, self.col = self.debug = debug
        self.name = "STRING '{}'".format(text)
        self.linked = False
        self.node = None
        self.ccname = None
        self.instruction = None

    def __repr__(self):
        return self.name

    def inner_link(self, *args):
        return self

    def find_arguments(self):
        return frozenset()

    def outer_link(self, *args):
        if self.linked:
            return self
        self.linked = True
        self.assign_element = self
        return self

    def re_link(self, *args):
        return self

    def apply_replace(self, *args):
        return self

    def link(self, parent):
        return self

    def accumulate_closure(self, *args):
        pass

    def nodisate(self):
        if self.node is None:
            self.node = Node(interpreter.String(self.text))
        return self.node

    def compile(self, compiler):
        if self.ccname is None:
            self.ccname = compiler.get_name("ARG")
            compiler.add_line(
                "Node *{} = create_string(\"{}\");".
                format(self.ccname, self.text)
            )
        return self.ccname

    def ad_compile(self, compiler):
        if self.instruction is None:
            str_index = compiler.add_constant(self.text)
            self.instruction = Instruction("STR_CONST", NumOperand(str_index))
            compiler.add_instruction(self.instruction)
        return NumOperand(self.instruction.index)


class Pragma:
    name = "PRAGMA"

    def __init__(self, text, debug):
        self.text = text
        self.row, self.col = self.debug = debug
        self.name = "PRAGMA '{}'".format(text)

    def __repr__(self):
        return self.name


class Literal:
    name = "LIT"

    def __init__(self, text, debug=(0, 0)):
        self.ch = text
        self.row, self.col = self.debug = debug
        self.name = "LIT'{}'".format(text)

    def __repr__(self):
        return self.name


def tokenize(text):
    it = LL1Text(text)
    line_comment = False
    nested_comment = 0
    for ch, look in it:
        if line_comment:
            if ch == "\n":
                line_comment = False
            continue
        if nested_comment:
            if ch == "}" and look == "#":
                nested_comment -= 1
            if ch == "#" and look == "{":
                nested_comment += 1
            continue

        debug = it.get_debug()
        if ch.isdecimal():
            yield Number(it.read_while(str.isdecimal), debug)
        elif ch in "<=>" and look == "=":
            next(it)
            yield Literal(ch + look, debug)
        elif ch in LITERALS:
            yield Literal(ch, debug)
        elif ch.isalpha() or ch in ADDITIONAL:
            yield Name(it.read_name(), debug)
        elif ch == "\"":
            yield String(it.read_string(), debug)
        elif ch == "#":
            if look == "#":
                next(it)
                next(it)
                yield Pragma(it.read_name(), debug)
            elif look == "{":
                nested_comment += 1
            else:
                line_comment = True
        elif not ch.isspace():
            raise LexicalError("Unknown symbol '{}'!".format(ch), debug)
    yield END
    yield END
