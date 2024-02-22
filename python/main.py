from __future__ import annotations

import shutil
import tarfile
import unittest
from pathlib import Path

import networkx as nx
import requests
from pydeps.pydeps import call_pydeps


def find_main_files_recursively(directory='.'):
    directory_path = Path(directory)
    main_files = []
    for filepath in directory_path.rglob('*.py'):
        if not filepath.name.startswith('__'):
            with filepath.open('r', encoding='utf-8') as file:
                content = file.read()
                if '__main__' in content:
                    main_files.append(filepath)
    return main_files


def convert_to_one_file(input_file_name: str) -> str | int | None:
    input_file_name = find_main_files_recursively(input_file_name)
    dot_file_path = "output.dot"
    call_pydeps(
        input_file_name,
        no_show=True,
        no_output=True,
        show_dot=True,
        dot_out=dot_file_path,
    )
    shutil.move(dot_file_path, f"tmp/{dot_file_path}")
    graph = nx.nx_agraph.read_dot(f"tmp/{dot_file_path}")
    if nx.find_cycle(graph):
        return 1
    num_parents_min = float("inf")
    for node in graph.nodes:
        num_parents = graph.out_degree(node)
        if (graph.in_degree(node) == 1) and (num_parents < num_parents_min):
            num_parents_min = num_parents
    return None


class Tests(unittest.TestCase):
    def test_convert_to_one_file_input(self: Tests) -> None:
        tar_file_path = Path("tmp/downloaded-file.tar")
        if not tar_file_path.exists():
            with tar_file_path.open("wb") as tar_file:
                tar_file.write(
                    requests.get(
                        "https://github.com/imartinez/privateGPT/tarball/main",
                        timeout=60,
                    ).content,
                )
            with tarfile.open(tar_file_path, "r") as tar:
                tar.extractall("tmp/")
            extracted_dir = next(Path("tmp/").iterdir())
        tar_file_path.unlink()
        result = convert_to_one_file(extracted_dir.as_posix())
        if result != 1:
            raise AssertionError


def main() -> None:
    import fire

    fire.Fire(convert_to_one_file)


if __name__ == "__main__":
    unittest.main()
