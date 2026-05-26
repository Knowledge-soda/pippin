from .error import LexicalError, AssignmentLoopError, UnknownNameError
from .types import NumberType
from .interpreter import Node
from . import interpreter

ADDITIONAL = "_-+*/"
LITERALS = "=()[]{}.,"


class END:
    name = "END"


class LL1Text:
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


class Number:
    name = "NUM"

    def __init__(self, text, debug):
        self.n = int(text)
        self.row, self.col = self.debug = debug
        self.name = "NUM {}".format(self.n)
        self.linked = False
        self.node = None
        self.ccname = None

    def __repr__(self):
        return self.name

    def inner_link(self, *args):
        return self

    def find_arguments(self):
        return frozenset()

    def find_deps(self, *args):
        pass

    def outer_link(self, *args):
        if self.linked:
            return self
        self.linked = True
        self.type = NumberType()
        return self

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


class Name:
    name = "NAME"

    def __init__(self, text, debug):
        self.text = text
        self.row, self.col = self.debug = debug
        self.name = "NAME '{}'".format(text)

    def __repr__(self):
        return self.name

    def inner_link(self, code, chain):
        if self.text in chain:
            raise AssignmentLoopError(chain + (self.text,))
        if self.text in code:
            assign = code[self.text]
            return assign.inner_link(code, chain)
        else:
            return self

    def find_arguments(self):
        return frozenset()

    def get_text(self):
        return self.text

    def outer_link(self, functions):
        if self.text not in functions:
            raise UnknownNameError(self.debug, self.text)
        return functions[self.text]

    def find_deps(self, result, context):
        if self.text not in context:
            result.add(self.text)


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
    for ch, look in it:
        debug = it.get_debug()
        if ch.isdecimal():
            yield Number(it.read_while(str.isdecimal), debug)
        elif ch in LITERALS:
            yield Literal(ch, debug)
        elif ch.isalpha() or ch in ADDITIONAL:
            yield Name(it.read_name(), debug)
        elif not ch.isspace():
            raise LexicalError("Unknown symbol '{}'!".format(ch), debug)
    yield END
    yield END
