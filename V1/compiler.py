from pathlib import Path


class Compiler:
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
