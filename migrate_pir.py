from __future__ import annotations

import ast
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_PIR = ROOT / "model" / "pir.py"
PKG_DIR = ROOT / "model" / "pir"

CLASS_TO_MODULE = {
    "PIR": "base",
    "PlainText": "plaintext",
    "Task": "task",
    "Event": "event",
    "Contact": "contact",
}

SUBCLASS_NAMES = ["PlainText", "Task", "Event", "Contact"]
DATETIME_NAMES = ["_DATETIME_FORMAT", "parse_datetime", "format_datetime"]


def node_source(lines: list[str], node: ast.AST) -> str:
    start = getattr(node, "lineno", 1)
    if isinstance(node, ast.ClassDef) and node.decorator_list:
        start = min([start] + [d.lineno for d in node.decorator_list])
    end = getattr(node, "end_lineno", start)
    return "".join(lines[start - 1 : end]).rstrip() + "\n"


def main() -> None:
    if not SRC_PIR.exists():
        raise FileNotFoundError(f"Expected {SRC_PIR} to exist in your working baseline.")

    source = SRC_PIR.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)

    nodes_by_name: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            nodes_by_name[node.name] = node
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    nodes_by_name[target.id] = node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            nodes_by_name[node.target.id] = node

    if PKG_DIR.exists():
        shutil.rmtree(PKG_DIR)
    PKG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. datetime_utils.py
    dt_body = [
        "from __future__ import annotations",
        "",
        "import datetime",
        "from ..exceptions import InvalidFieldValueError",
        "",
    ]
    for name in DATETIME_NAMES:
        dt_body.append(node_source(lines, nodes_by_name[name]).rstrip())
    (PKG_DIR / "datetime_utils.py").write_text("\n".join(dt_body) + "\n", encoding="utf-8")

    # 2. base.py (PIR + registry)
    base_body = [
        "from __future__ import annotations",
        "",
        "from abc import ABC, abstractmethod",
        "from typing import Any, Dict, Optional",
        "from ..exceptions import UnknownPIRTypeError",
        "",
        node_source(lines, nodes_by_name["PIR"]).rstrip(),
        "",
        node_source(lines, nodes_by_name["_PIR_REGISTRY"]).rstrip(),
        "",
        node_source(lines, nodes_by_name["_register_pir_class"]).rstrip(),
    ]
    (PKG_DIR / "base.py").write_text("\n".join(base_body) + "\n", encoding="utf-8")

    # 3. One file per subclass
    for cls_name in SUBCLASS_NAMES:
        mod_name = CLASS_TO_MODULE[cls_name]
        cls_src = node_source(lines, nodes_by_name[cls_name]).rstrip()
        needs_dt = "parse_datetime" in cls_src or "format_datetime" in cls_src

        cls_body = [
            "from __future__ import annotations",
            "",
            "import datetime",
            "from typing import Any, Dict, Optional",
            "from ..exceptions import InvalidFieldValueError, UnknownFieldError",
            "from .base import PIR, _register_pir_class",
        ]
        if needs_dt:
            cls_body.append("from .datetime_utils import format_datetime, parse_datetime")
        cls_body.extend(["", cls_src])
        (PKG_DIR / f"{mod_name}.py").write_text("\n".join(cls_body) + "\n", encoding="utf-8")

    # 4. __init__.py (exports + eager subclass import so _PIR_REGISTRY is populated)
    init_body = [
        "from __future__ import annotations",
        "",
        "from typing import Dict",
        "from .base import PIR, _PIR_REGISTRY, _register_pir_class",
        "from .datetime_utils import format_datetime, parse_datetime",
        "from .plaintext import PlainText",
        "from .task import Task",
        "from .event import Event",
        "from .contact import Contact",
        "",
        node_source(lines, nodes_by_name["all_pir_types"]).rstrip(),
        "",
        node_source(lines, nodes_by_name["known_type_names"]).rstrip(),
        "",
        "__all__ = [",
        '    "PIR",',
        '    "PlainText",',
        '    "Task",',
        '    "Event",',
        '    "Contact",',
        '    "parse_datetime",',
        '    "format_datetime",',
        '    "all_pir_types",',
        '    "known_type_names",',
        "]",
    ]
    (PKG_DIR / "__init__.py").write_text("\n".join(init_body) + "\n", encoding="utf-8")

    # 5. Remove shadowing model/pir.py now that model/pir/ is complete
    SRC_PIR.unlink()
    print("Successfully created model/pir/ and removed model/pir.py")


if __name__ == "__main__":
    main()