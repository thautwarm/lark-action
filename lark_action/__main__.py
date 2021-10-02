from lark.tools.standalone import main as _main
from lark_action.lark_action_raw import Lark, Transformer, Token, Tree, Lark_StandAlone
from textwrap import indent
from io import StringIO
from wisepy2 import wise

import os
import re
import sys


def keep_only_space(s: str):
    return re.sub(r"\S", " ", s)


def dump(x, file=sys.stdout, col_ref: list = [0]):
    if isinstance(x, Token):
        if col_ref[0] < x.column:
            print(" " * (x.column - col_ref[0]), end="", file=file)
        if x.type != "COMMENT:":
            print(str(x), end="", file=file)
        else:
            print(keep_only_space(str(x)), end="", file=file)
        col_ref[0] = x.end_column
    else:
        assert isinstance(x, Tree), type(x)
        for e in x.children:
            dump(e, file, col_ref)


class Modify(Transformer):
    def __init__(self):
        self.python_file = StringIO()
        self.inline_codes = []
        self.current_rule = ""
        self.action_id = 0
        self.repl_support = False

    def mkrepl(self, args):
        self.repl_support = True
        return Token("", "", column=args[-1].column, end_column=args[-1].end_column)

    def inlinecode(self, args):
        code = str(args[0])
        self.inline_codes.append(code[2:-2])
        value = keep_only_space(code)
        token = Token("", value, column=args[-1].column, end_column=args[-1].end_column)
        return Tree("", [token])

    def get_component(self, args):
        i = int(str(args[-1]))
        value = f"__args[{i}-1]"
        return Token("", value, column=args[0].column, end_column=args[1].end_column)

    def get_location(self, args):
        i = int(str(args[-1]))
        value = f"_get_location(__args[{i}-1])"
        return Token("", value, column=args[0].column, end_column=args[1].end_column)

    def get_value(self, args):
        i = int(str(args[-1]))
        value = f"_get_value(__args[{i}-1])"
        return Token("", value, column=args[0].column, end_column=args[1].end_column)

    def rule(self, args):
        current_rule = str(args[0])
        while not current_rule.isidentifier():
            current_rule = current_rule[1:]
        if not current_rule:
            raise NameError(str(args[0]))
        self.current_rule = current_rule
        self.action_id = 0
        return Tree("", args)

    def noaction(self, args):
        return Tree("", args)

    def action(self, args):
        code = args[1]
        func = f"{self.current_rule}_{self.action_id}"
        print(file=self.python_file)
        print(f"def {func}(self, __args):", file=self.python_file)
        head = f"    return "
        print(head, file=self.python_file, end="")
        dump(code, self.python_file, [args[0].end_column])
        self.action_id += 1
        args.clear()
        args.extend([Token("", f" -> {func}", column=0, end_column=0)])
        return Tree("", args)


def main(filename: str, package: str = "", module: str = "mylang"):
    modifier = Modify()
    parser = Lark_StandAlone(transformer=modifier)
    with open(filename, encoding="utf8") as f:
        tree = parser.parse(f.read())
    package_path = os.path.join(".", *package.split("."))
    lark_grammar_path = os.path.join(package_path, module + ".lark")
    with open(lark_grammar_path, "w", encoding="utf-8") as f:
        dump(tree, file=f)

    old_args = sys.argv.copy()
    sys.argv.clear()
    sys.argv.extend(
        [
            "",
            lark_grammar_path,
            "-c",
            "--keep_all_tokens",
            "-o",
            os.path.join(package_path, module + "_raw.py"),
        ]
    )
    _main()
    sys.argv.clear()
    sys.argv.extend(old_args)
    transformer_src_code = modifier.python_file.getvalue()
    with open(os.path.join(package_path, module + ".py"), "w", encoding="utf-8") as f:
        print("# Generated from lark-action.", file=f)
        print("def _get_location(token):", file=f)
        print("    return (token.line, token.column)", file=f)
        print(file=f)
        print("def _get_value(token):", file=f)
        print("    return token.value", file=f)
        print(file=f)
        for each in modifier.inline_codes:
            print(each, file=f)

        full_module = ".".join([*filter(None, package.split(".")), module])
        print(file=f)
        print(f"from {full_module}_raw import Transformer, Lark_StandAlone, Tree", file=f)
        print(f"class {module}_Transformer(Transformer):", file=f)
        print(indent(transformer_src_code, " " * 4), file=f)
        print(file=f)
        print(file=f)
        print(f"parser = Lark_StandAlone(transformer={module}_Transformer())", file=f)

        if not modifier.repl_support:
            return

        print()
        repl_code = r"""
        import prettyprinter
        prettyprinter.install_extras(["dataclasses"])
        while True:
            print("input q and exit.")
            source = input("> ")
            if source.strip() == "q":
                break
            if not source.strip():
                continue
            res = parser.parse(source)
            if not isinstance(res, Tree):
                prettyprinter.pprint(res)
            else:
                print(res)
            """
        print(f"if __name__ == {'__main__'!r}:", file=f)
        print(repl_code, file=f)


if __name__ == "__main__":
    wise(main)()
