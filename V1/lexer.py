ADDITIONAL = "_-+*/"
LITERALS = "=()[]{}.,"


class END:
    pass


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
            raise RuntimeError(
                "{}, {}: Variable name starts with invalid character '{}'"
                .format(self.row, self.col, self.now))
        buffer = [self.now]
        while self.look_ahead != END and (self.look_ahead.isalnum()
                                          or self.look_ahead in ADDITIONAL):
            next(self)
            buffer.append(self.now)
        return "".join(buffer)


class Number:
    def __init__(self, text, debug):
        self.n = int(text)
        self.row, self.col = debug

    def __repr__(self):
        return "NUM {}".format(self.n)

    def find_deps(self, *args):
        pass


class Name:
    def __init__(self, text, debug):
        self.text = text
        self.row, self.col = debug

    def __repr__(self):
        return "NAME '{}'".format(self.text)

    def find_deps(self, result, context):
        if self.text not in context:
            result.add(self.text)


class Literal:
    def __init__(self, text, debug):
        self.ch = text
        self.row, self.col = debug

    def __repr__(self):
        return "LIT'{}'".format(self.ch)


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
            raise RuntimeError(
                "Unknown symbol '{}' in row {}!".format(ch, it.row))
    yield END
    yield END
