from .error import SemanticError


class NumberType:
    def __repr__(self):
        return "int"


class FunctionType:
    def __init__(self, ins, outs):
        self.ins = list(ins)
        self.outs = set(outs)
        self.needed = {
            var: set() for var in self.outs}
        for var in self.outs:
            if var in self.ins:
                self.needed[var].add(var)

    def __repr__(self):
        return "{{{}}}".format(
            ";\n".join("{} -> {}".format(
                ", ".join(self.needed[var]), var)
                for var in self.outs)
        )

    def connect(self, in_vars, out_var):
        if out_var in self.ins:
            raise SemanticError(
                "Input argument {} has dependencies!"
                .format(out_var)
            )
        self.needed[out_var] |= in_vars

    def free(self, var):
        return not self.needed[var]

    def _apply(self, variables):
        varset = set()
        for var in variables:
            if isinstance(var, int):
                if var >= len(self.ins):
                    raise SemanticError(
                        "Application of too high index {} "
                        "to function with {} arguments"
                        .format(var, len(self.ins))
                    )
                varset.add(self.ins[var])
            else:
                if var not in self.ins:
                    raise SemanticError(
                        "Application of nonexistant argument {} "
                        "to function of type {}"
                        .format(var, self)
                    )
                varset.add(var)
        for var in self.outs:
            self.needed[var] -= varset
        self.ins = list(filter(lambda var: var not in varset, self.ins))

    def apply(self, variables):
        ret = FunctionType(self.ins, self.outs)
        ret.needed = self.needed.copy()
        ret._apply(variables)
        return ret

    def get_input_list(self):
        return tuple((name, None) for name in self.ins)


class AnyType:
    def __repr__(self):
        return "T"

    def connect(self):
        pass

    def free(self, var):
        return True

    def apply(self, vars):
        return AnyType()
