from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VIEW_DIR = ROOT / "view"
FORMATTER_FILE = VIEW_DIR / "formatter.py"
REPORTER_FILE = VIEW_DIR / "reporter.py"
INIT_FILE = VIEW_DIR / "__init__.py"


def node_source(lines: list[str], node: ast.AST) -> str:
    start = getattr(node, "lineno", 1)
    if isinstance(node, ast.ClassDef) and node.decorator_list:
        start = min([start] + [d.lineno for d in node.decorator_list])
    end = getattr(node, "end_lineno", start)
    return "".join(lines[start - 1 : end]).rstrip() + "\n"


def main() -> None:
    if not FORMATTER_FILE.exists():
        raise FileNotFoundError(f"Expected {FORMATTER_FILE} to exist.")

    source = FORMATTER_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)

    nodes_by_name: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            nodes_by_name[node.name] = node

    # 1. Write view/formatter.py (Formatter + _truncate)
    formatter_body = [
        '"""Output formatting for the PIM CLI."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Iterable",
        "",
        "from model import PIR, PIRRepository, format_datetime",
        "from model.pir import Contact, Event, PlainText, Task",
        "",
        "",
        node_source(lines, nodes_by_name["Formatter"]).rstrip(),
        "",
        "",
        node_source(lines, nodes_by_name["_truncate"]).rstrip(),
        "",
    ]
    FORMATTER_FILE.write_text("\n".join(formatter_body), encoding="utf-8")

    # 2. Write view/reporter.py (Reporter, PrintReporter, InMemoryReporter)
    reporter_body = [
        '"""Output sinks for the PIM CLI."""',
        "",
        "from __future__ import annotations",
        "",
        "import sys",
        "from typing import IO, List, Optional",
        "",
        "",
        node_source(lines, nodes_by_name["Reporter"]).rstrip(),
        "",
        "",
        node_source(lines, nodes_by_name["PrintReporter"]).rstrip(),
        "",
        "",
        node_source(lines, nodes_by_name["InMemoryReporter"]).rstrip(),
        "",
    ]
    REPORTER_FILE.write_text("\n".join(reporter_body), encoding="utf-8")

    # 3. Update view/__init__.py if present so `from view import ...` keeps working
    if INIT_FILE.exists():
        init_src = INIT_FILE.read_text(encoding="utf-8")
        init_lines = init_src.splitlines(keepends=True)
        init_tree = ast.parse(init_src)

        edits: list[tuple[int, int, str]] = []
        for node in init_tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == "formatter" and node.level == 1:
                names = [a.name for a in node.names]
                new_block = []
                if "Formatter" in names:
                    new_block.append("from .formatter import Formatter\n")
                rep_names = [n for n in names if n != "Formatter"]
                if rep_names:
                    new_block.append(f"from .reporter import {', '.join(rep_names)}\n")
                edits.append((node.lineno, node.end_lineno or node.lineno, "".join(new_block)))

        for start, end, replacement in sorted(edits, key=lambda e: e[0], reverse=True):
            init_lines[start - 1 : end] = [replacement]

        updated_init = "".join(init_lines)
        if "InMemoryReporter" not in updated_init:
            updated_init = updated_init.rstrip() + "\nfrom .reporter import InMemoryReporter\n"
        INIT_FILE.write_text(updated_init, encoding="utf-8")

    print("Split view/formatter.py into view/formatter.py and view/reporter.py")


if __name__ == "__main__":
    main()