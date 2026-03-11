from .error import SemanticError


class NumberType:
    def __repr__(self):
        return "int"


class FunctionType:
    def __init__(self, ins, outs):
        self.ins = set(ins)
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
        varset = set(variables)
        if not varset.issubset(self.ins):
            raise SemanticError(
                "Application of nonexistant arguments {} "
                "to function of type {}"
                .format(varset - self.ins, self)
            )
        for var in self.outs:
            self.needed[var] -= varset
        self.ins -= varset

    def apply(self, variables):
        ret = FunctionType(self.ins, self.outs)
        ret.needed = self.needed.copy()
        ret._apply(variables)
        return ret
