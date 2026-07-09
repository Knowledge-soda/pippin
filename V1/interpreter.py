class Node:
    counter = 0

    def __init__(self, content):
        self.content = content
        self.cloned = False
        self.number = type(self).counter
        type(self).counter += 1

    def __repr__(self):
        return "{}#{}".format(self.number, self.content)

    def __str__(self):
        return repr(self.content)

    @classmethod
    def from_string(cls, string):
        return cls(Number(int(string)))

    def clone(self, arguments):
        if self.cloned:
            return self
        ret = Node(self.content.clone(arguments))
        ret.cloned = True
        return ret

    def end_cloning_process(self):
        self.cloned = False
        self.content.end_cloning_process()

    def eval(self):
        while isinstance(self.content, (Property, Application)):
            self.content = self.content.eval()


class InterpretedNode:
    pass


class Function(InterpretedNode):
    def __init__(self, results, arguments, changed=False):
        self.results = results
        self.arguments = arguments
        self.changed = changed

    def __repr__(self):
        return "FUNCTION({}; PA: {})".format(
                ", ".join(key for key in self.results.keys()),
                ", ".join(key for key, value in self.arguments)
                )

    @classmethod
    def from_function(cls, function):
        return cls({
            var.get_text(): var.nodisate() for var in function.results
        }, (
            tuple((var.get_text(), None) for var in function.varlist)
        ))

    def _find_arg(self, arg):
        if isinstance(arg, int):
            for i, (name, value) in enumerate(self.arguments):
                if value is None:
                    if not arg:
                        return i, name
                    arg -= 1
        else:
            for i, (name, value) in enumerate(self.arguments):
                if name == arg:
                    return i, name

    def apply(self, applications):
        newargs = list(self.arguments)
        for name, value in applications:
            i, newname = self._find_arg(name)
            newargs[i] = (newname, value)
        return Function(
            self.results.copy(),
            tuple(newargs),
            True
        )

    def get(self, text):
        if self.changed:
            for name, result in self.results.items():
                self.results[name] = result.clone(self.arguments)
            self.changed = False
            for result in self.results.values():
                result.end_cloning_process()
        return self.results[text]

    def clone(self, arguments):
        return self

    def end_cloning_process(self):
        return

    def eval(self):
        return self


class Application(InterpretedNode):
    def __init__(self, func, params):
        self.func = func
        self.params = params

    def __repr__(self):
        return "@({}; {})".format(
                self.func,
                ", ".join(
                    "{}={}".format(key, value) for key, value in self.params
                )
            )

    def clone(self, arguments):
        func = self.func.clone(arguments)
        params = tuple(
                (key, node.clone(arguments)) for key, node in self.params)
        return Application(func, params)

    def end_cloning_process(self):
        self.func.end_cloning_process()
        for _, value in self.params:
            value.end_cloning_process()

    def eval(self):
        self.func.eval()
        return self.func.content.apply(self.params)


class Property(InterpretedNode):
    def __init__(self, left, name):
        self.left = left
        self.name = name

    def __repr__(self):
        return ".({}, {})".format(self.left, self.name)

    def clone(self, arguments):
        return Property(self.left.clone(arguments), self.name)

    def end_cloning_process(self):
        self.left.end_cloning_process()

    def eval(self):
        self.left.eval()
        return self.left.content.get(self.name).content


class Argument(InterpretedNode):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "ARG({})".format(self.name)

    def clone(self, arguments):
        for key, value in arguments:
            if key == self.name and value is not None:
                return value.content
        return self

    def end_cloning_process(self):
        return

    def eval(self):
        # is this even legal???
        return self


class Number(InterpretedNode):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return repr(self.value)

    def clone(self, arguments):
        return self

    def end_cloning_process(self):
        return

    def eval(self):
        return self


def driver(main):
    while True:
        line = input()
        if line[0] == "?":
            ret = main.content.get(line[1:])
            ret.eval()
            print(ret)
        elif line[0] == "!":
            break
        else:
            var, num = line.split("=")
            main.content = main.content.apply(((var, Node(Number(int(num)))),))
