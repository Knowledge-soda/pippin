from pathlib import Path
import struct


class CCompiler:
    HEAD = [
        "\n",
        "int main(void){\n"
    ]
    TAIL = [
        "    return 0;\n",
        "}\n"
    ]

    def __init__(self):
        path = Path(__file__).parent / "const_compile.c"
        with open(path) as file:
            self.lines = file.readlines()
        self.lines.extend(self.HEAD)
        self.varnum = 0

    def add_line(self, line):
        self.lines.append("    {}\n".format(line))

    def get_name(self, hint=""):
        ret = "_PAGUN_{}_{}".format(hint, self.varnum)
        self.varnum += 1
        return ret

    def finish(self, main_name, filename):
        self.lines.append("    driver({});\n".format(main_name))
        self.lines.extend(self.TAIL)
        with open(filename, "w") as file:
            file.writelines(self.lines)


class AHCompiler:
    def __init__(self):
        self.constants = {}
        self.functions = []
        self.code = []
        self.bytesize = 0

    def print_instructions(self):
        for ins in self.code:
            print(ins)

    def set_builtins(self, builtins):
        self.bytesize += len(builtins)

    def add_instruction(self, instruction):
        instruction.set_index(self.bytesize)
        self.code.append(instruction)
        self.bytesize += len(instruction)

    def add_constant(self, const):
        if const in self.constants:
            return self.constants[const]
        index = len(self.constants)
        self.constants[const] = index
        return index

    def add_function(self, func):
        self.functions.append(func)

    def aggregate(self):
        old_len = 0
        while len(self.functions) > old_len:
            older_len = old_len
            old_len = len(self.functions)
            for i in range(older_len, len(self.functions)):
                self.functions[i].ad_hoc_compile(self)

    def finish(self, filename):
        consize = sum(len(s) + 1 for s in self.constants.keys())
        with open(filename, "wb") as file:
            file.write(b'ad_hoc')
            file.write(bytes.fromhex('3004'))
            file.write(struct.pack("!I", consize))
            file.write(struct.pack("!I", self.bytesize))

            # doesn't work if dict is not ordreded
            for const in self.constants.keys():
                file.write(const.encode("utf-8"))
                file.write(bytes(1))
            for instruction in self.code:
                instruction.write(file)


class NumOperand:
    def __init__(self, number):
        self.number = number

    def __len__(self):
        return 4

    def __repr__(self):
        return str(self.number)

    def write(self, file):
        file.write(struct.pack("!i", self.number))


class FuncRef:
    def __init__(self, func):
        self.func = func

    def __len__(self):
        return 4

    def __repr__(self):
        return "FuncRef"

    def write(self, file):
        i = self.func.instruction.index
        file.write(struct.pack("!i", i))


class Instruction:
    CODES = {
            "AD_FUNC": 0,
            "SET_RES": 2,
            "APPLY": 3,
            "SET_STR_ARG": 4,
            "SET_NUM_ARG": 5,
            "PROPERTY": 6,
            "ARG_NAME": 7,
            "NUM_CONST": 8,
    }

    def __init__(self, opcode, *args):
        self.opcode = opcode
        self.args = args

    def __len__(self):
        return 1 + sum(len(arg) for arg in self.args)

    def __repr__(self):
        return "{}: '{}' |{}|".format(self.index, self.opcode,
                                      " ".join(repr(arg) for arg in self.args))

    def set_index(self, index):
        self.index = index

    def write(self, file):
        file.write(struct.pack("!B", self.CODES[self.opcode]))
        for arg in self.args:
            arg.write(file)
