import zipfile
from pathlib import Path
from typing import Iterator

from js import Blob, document, window
from pyodide.ffi.wrappers import add_event_listener

from main import convert_python_project_to_one_file  # type: ignore[attr-defined]

space = "    "
branch = "│   "
tee = "├── "
last = "└── "


def tree(dir_path: Path, prefix: str = "") -> Iterator[str]:
    contents = list(dir_path.iterdir())
    pointers = [tee] * (len(contents) - 1) + [last]
    for pointer, path in zip(pointers, contents):
        yield prefix + pointer + path.name
        if path.is_dir():
            extension = branch if pointer == tee else space
            yield from tree(path, prefix=prefix + extension)


def on_download_output(content: str) -> None:
    a = document.createElement("a")
    document.body.appendChild(a)
    a.style = "display: none"
    blob = Blob.new([content])
    url = window.URL.createObjectURL(blob)
    a.href = url
    a.download = "main.py"
    a.click()
    window.URL.revokeObjectURL(url)


async def on_click_convert_button(_) -> None:  # type: ignore[no-untyped-def] # noqa: ANN001
    choose_main_file_select_selected_index = (
        document.getElementById("choose-main-file-select").selectedIndex + 1
    )
    with zipfile.ZipFile("tmp.zip", "r") as zip_ref:
        zip_extracted_dir = zip_ref.namelist()
    main_file_name = zip_extracted_dir[choose_main_file_select_selected_index]
    result = convert_python_project_to_one_file(main_file_name)
    if not result:
        output_file_path = Path(main_file_name).parent.parent / "output.py"
        with Path(output_file_path).open() as file:  # noqa: ASYNC101
            content = file.read()
    on_download_output(content)


async def on_change_file_input(e) -> None:  # type: ignore[no-untyped-def] # noqa: ANN001
    file_list = e.target.files
    first_item = file_list.item(0)
    array_buf = await first_item.arrayBuffer()
    my_bytes = array_buf.to_bytes()
    with Path("tmp.zip").open("wb") as file:  # noqa: ASYNC101
        file.write(my_bytes)
    with zipfile.ZipFile("tmp.zip", "r") as zip_ref:
        zip_extracted_dir = zip_ref.namelist()
        zip_ref.extractall()
    choose_main_file_select = document.getElementById("choose-main-file-select")
    choose_main_file_select.innerHTML = ""
    for zip_, line in zip(zip_extracted_dir[1:], tree(Path(zip_extracted_dir[0]))):
        choose_a_file_option = document.createElement("option")
        choose_main_file_select.appendChild(choose_a_file_option)
        choose_a_file_option.textContent += line
        if Path(zip_).is_dir() or not zip_.endswith(".py"):
            choose_a_file_option.disabled = True


def main() -> None:
    add_event_listener(
        document.getElementById("file-input"),
        "change",
        on_change_file_input,
    )
    add_event_listener(
        document.getElementById("convert-button"),
        "click",
        on_click_convert_button,
    )


if __name__ == "__main__":
    main()
