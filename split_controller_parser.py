from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CTRL_DIR = ROOT / "controller"
PARSER_FILE = CTRL_DIR / "parser.py"
PARSED_CMD_FILE = CTRL_DIR / "parsed_command.py"
INIT_FILE = CTRL_DIR / "__init__.py"


def node_source(lines: list[str], node: ast.AST) -> str:
    start = getattr(node, "lineno", 1)
    if isinstance(node, ast.ClassDef) and node.decorator_list:
        start = min([start] + [d.lineno for d in node.decorator_list])
    end = getattr(node, "end_lineno", start)
    return "".join(lines[start - 1 : end]).rstrip() + "\n"


def main() -> None:
    if not PARSER_FILE.exists():
        raise FileNotFoundError(f"Expected {PARSER_FILE} to exist.")

    source = PARSER_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)

    classes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }

    # 1. Write controller/parsed_command.py
    parsed_cmd_body = [
        '"""Structured representation of a tokenized PIM command."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Dict, List",
        "",
        "",
        node_source(lines, classes["ParsedCommand"]).rstrip(),
        "",
    ]
    PARSED_CMD_FILE.write_text("\n".join(parsed_cmd_body), encoding="utf-8")

    # 2. Rewrite controller/parser.py with TokenizerError + CommandTokenizer
    parser_body = [
        source.split("from __future__ import annotations", 1)[0].rstrip(),
        "",
        "from __future__ import annotations",
        "",
        "from typing import Dict, List, Tuple",
        "",
        "from .parsed_command import ParsedCommand",
        "",
        "",
        node_source(lines, classes["TokenizerError"]).rstrip(),
        "",
        "",
        node_source(lines, classes["CommandTokenizer"]).rstrip(),
        "",
    ]
    PARSER_FILE.write_text("\n".join(parser_body), encoding="utf-8")

    # 3. Update controller/__init__.py if it imports ParsedCommand from .parser
    if INIT_FILE.exists():
        init_src = INIT_FILE.read_text(encoding="utf-8")
        if "ParsedCommand" in init_src and "from .parsed_command import ParsedCommand" not in init_src:
            init_src = init_src.replace(
                "from .parser import",
                "from .parsed_command import ParsedCommand\nfrom .parser import",
            )
            INIT_FILE.write_text(init_src, encoding="utf-8")

    print("Extracted ParsedCommand to controller/parsed_command.py")


if __name__ == "__main__":
    main()