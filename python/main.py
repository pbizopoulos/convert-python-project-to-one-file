from __future__ import annotations

import ast
import unittest
from pathlib import Path
from shutil import copy, copyfile
from typing import Any

import isort
import ssort


class Transformer(ast.NodeTransformer):
    def visit(self: Transformer, node: Any) -> Any:  # noqa: ANN401
        self.generic_visit(node)
        if isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Constant):
                return None
            if isinstance(node.value, ast.Call):  # noqa: SIM102
                if hasattr(node.value.func, "id") and node.value.func.id == "print":
                    return None
        if isinstance(node, ast.FunctionDef):
            node.returns = None
            if node.args.args:
                for arg in node.args.args:
                    arg.annotation = None
            return node
        return node


class IndividualizeImportNames(ast.NodeTransformer):
    def __init__(
        self: IndividualizeImportNames,
        attr_usage: dict[str, dict[str, None]],
    ) -> None:
        self.attr_usage = attr_usage

    def visit_Import(self: IndividualizeImportNames, node: Any) -> Any:  # noqa: ANN401,N802
        leftover_imports = []
        if unused_names := [
            alias for alias in node.names if alias.name not in self.attr_usage
        ]:
            leftover_imports.append(ast.Import(names=unused_names))
        return leftover_imports + [
            ast.ImportFrom(
                module=alias.name,
                names=[ast.alias(name=attr) for attr in self.attr_usage[alias.name]],
            )
            for alias in node.names
            if alias.name in self.attr_usage
        ]

    def visit_Attribute(self: IndividualizeImportNames, node: Any) -> Any:  # noqa: ANN401,N802
        self.generic_visit(node)
        if hasattr(node.value, "id") and node.value.id in self.attr_usage:
            return ast.Name(id=node.attr, ctx=ast.Load())
        return node


def convert_python_project_to_one_file(input_file_name: str) -> int:  # noqa: C901,PLR0915
    base_path = Path(input_file_name).resolve().parent
    if (base_path / "__init__.py").is_file():
        base_path = base_path.parent
    output_file_name = base_path / "output.py"
    copy(input_file_name, output_file_name)
    node_modules = []
    done = False
    while not done:
        done = True
        with output_file_name.open() as file:
            tree = ast.parse(file.read())
        attr_usage = {}  # type: ignore[var-annotated]
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and hasattr(node.value, "id"):
                attr_usage.setdefault(node.value.id, set()).add(node.attr)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.append(node.names[0].name)  # noqa: PERF401
        attr_usage = {key: attr_usage[key] for key in imports if key in attr_usage}
        IndividualizeImportNames(attr_usage).visit(tree)
        code_unparsed = ast.unparse(tree)
        with output_file_name.open("w") as file:
            file.write(code_unparsed)
        isort.file(output_file_name, float_to_top=True, quiet=True)
        with output_file_name.open() as file:
            tree = ast.parse(file.read())
        transformer = Transformer()
        ast.fix_missing_locations(transformer.visit(tree))
        code_unparsed = ast.unparse(tree)
        with output_file_name.open("w") as file:
            file.write(code_unparsed)
        with output_file_name.open() as file:
            tree = ast.parse(file.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                node_module: str = node.module  # type: ignore[assignment]
                other_module_file_name = (
                    base_path / f'{node_module.replace(".", "/")}.py'
                )
                if other_module_file_name.is_file():
                    done = False
                    with output_file_name.open(mode="r") as file:
                        lines = file.readlines()
                    with output_file_name.open(mode="w") as file:
                        for i, line in enumerate(lines, 1):
                            if i != node.lineno:
                                file.write(line)
                    if node_module in node_modules:
                        break
                    node_modules.append(node_module)
                    with other_module_file_name.open("r") as f:
                        other_module_code = f.read()
                    new_lines = other_module_code.split("\n")
                    with output_file_name.open(mode="r") as file:
                        lines = file.readlines()
                    lines.insert(0, "\n".join(new_lines) + "\n")
                    with output_file_name.open(mode="w") as file:
                        file.writelines(lines)
                    break
    with output_file_name.open(mode="r") as file:
        code = file.read()
    code = ssort.ssort(code)
    with output_file_name.open(mode="w") as file:
        file.write(code)
    return 0


class Tests(unittest.TestCase):
    def setUp(self: Tests) -> None:
        copyfile("prm/main.py", "tmp/main.py")
        copyfile("prm/library_1.py", "tmp/library_1.py")
        copyfile("prm/library_2.py", "tmp/library_2.py")

    def test_convert_python_project_to_one_file_input(self: Tests) -> None:
        convert_python_project_to_one_file("tmp/main.py")
        with Path("tmp/output.py").open(encoding="utf-8") as file:
            code_output_before_processed = file.read()
        with Path("prm/output.py").open(encoding="utf-8") as file:
            code_output_after = file.read()
        if code_output_before_processed != code_output_after:
            raise AssertionError


def main() -> None:
    import fire

    fire.Fire(convert_python_project_to_one_file)


if __name__ == "__main__":
    unittest.main()
