from __future__ import annotations

import ast
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_CRIT = ROOT / "model" / "criterion.py"
PKG_DIR = ROOT / "model" / "criterion"


def node_source(lines: list[str], node: ast.AST) -> str:
    start = getattr(node, "lineno", 1)
    if isinstance(node, ast.ClassDef) and node.decorator_list:
        start = min([start] + [d.lineno for d in node.decorator_list])
    end = getattr(node, "end_lineno", start)
    return "".join(lines[start - 1 : end]).rstrip() + "\n"


def main() -> None:
    if not SRC_CRIT.exists():
        raise FileNotFoundError(f"Expected {SRC_CRIT} to exist.")

    source = SRC_CRIT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)

    nodes_by_name: dict[str, ast.AST] = {}
    ordered_nodes: list[tuple[str, ast.AST]] = []

    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            nodes_by_name[node.name] = node
            ordered_nodes.append((node.name, node))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    nodes_by_name[target.id] = node
                    ordered_nodes.append((target.id, node))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            nodes_by_name[node.target.id] = node
            ordered_nodes.append((node.target.id, node))

    if PKG_DIR.exists():
        shutil.rmtree(PKG_DIR)
    PKG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. field_index.py
    field_index_names = [
        "_build_field_index",
        "_TEXT_FIELDS",
        "_TIME_FIELDS",
        "_refresh_field_index",
        "known_text_fields",
        "known_time_fields",
        "known_fields",
    ]
    field_index_body = [
        "from __future__ import annotations",
        "",
        "from ..pir import all_pir_types",
        "",
    ]
    for name in field_index_names:
        field_index_body.append(node_source(lines, nodes_by_name[name]).rstrip())
        field_index_body.append("")
    (PKG_DIR / "field_index.py").write_text("\n".join(field_index_body).rstrip() + "\n", encoding="utf-8")

    # 2. tokenizer.py
    tok_names = [
        name
        for name, _ in ordered_nodes
        if name.startswith("_TOK_") or name in {"_Token", "_tokenize"}
    ]
    tok_body = [
        "from __future__ import annotations",
        "",
        "from typing import List",
        "from ..exceptions import CriterionSyntaxError",
        "",
    ]
    for name in tok_names:
        tok_body.append(node_source(lines, nodes_by_name[name]).rstrip())
        tok_body.append("")
    (PKG_DIR / "tokenizer.py").write_text("\n".join(tok_body).rstrip() + "\n", encoding="utf-8")

    # 3. base.py (Criterion defined first; parser/tokenizer imported at bottom to avoid cycles)
    base_body = [
        "from __future__ import annotations",
        "",
        "from ..exceptions import CriterionSyntaxError",
        "from ..pir import PIR",
        "",
        node_source(lines, nodes_by_name["Criterion"]).rstrip(),
        "",
        "from .parser import _CriterionParser",
        "from .tokenizer import _tokenize",
    ]
    (PKG_DIR / "base.py").write_text("\n".join(base_body) + "\n", encoding="utf-8")

    # 4. Leaf & composite criterion modules
    leaf_specs = {
        "type_criterion.py": (
            [
                "from __future__ import annotations",
                "",
                "from ..exceptions import CriterionSyntaxError",
                "from ..pir import PIR, known_type_names",
                "from .base import Criterion",
                "",
            ],
            ["TypeCriterion"],
        ),
        "text_criterion.py": (
            [
                "from __future__ import annotations",
                "",
                "from ..exceptions import CriterionSyntaxError",
                "from ..pir import PIR",
                "from .base import Criterion",
                "from .field_index import _TEXT_FIELDS",
                "",
            ],
            ["TextContainsCriterion"],
        ),
        "time_criterion.py": (
            [
                "from __future__ import annotations",
                "",
                "import datetime",
                "from ..exceptions import CriterionSyntaxError",
                "from ..pir import PIR, format_datetime",
                "from .base import Criterion",
                "from .field_index import _TIME_FIELDS",
                "",
            ],
            ["TimeCompareCriterion"],
        ),
        "composite.py": (
            [
                "from __future__ import annotations",
                "",
                "from ..pir import PIR",
                "from .base import Criterion",
                "",
            ],
            ["AndCriterion", "OrCriterion", "NotCriterion"],
        ),
    }
    for filename, (header, names) in leaf_specs.items():
        body = list(header)
        for name in names:
            body.append(node_source(lines, nodes_by_name[name]).rstrip())
            body.append("")
        (PKG_DIR / filename).write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")

    # 5. parser.py
    parser_body = [
        "from __future__ import annotations",
        "",
        "from typing import List",
        "from ..exceptions import CriterionSyntaxError, InvalidFieldValueError",
        "from ..pir import parse_datetime",
        "from .base import Criterion",
        "from .composite import AndCriterion, NotCriterion, OrCriterion",
        "from .field_index import _TEXT_FIELDS, _TIME_FIELDS, known_fields",
        "from .text_criterion import TextContainsCriterion",
        "from .time_criterion import TimeCompareCriterion",
        "from .tokenizer import _TOK_BARE, _TOK_END, _TOK_EQ, _TOK_GT, _TOK_IDENT, _TOK_LPAREN, _TOK_LT, _TOK_NOT, _TOK_OR, _TOK_RPAREN, _TOK_STRING, _TOK_TILDE, _Token",
        "from .type_criterion import TypeCriterion",
        "",
        node_source(lines, nodes_by_name["_CriterionParser"]).rstrip(),
    ]
    (PKG_DIR / "parser.py").write_text("\n".join(parser_body) + "\n", encoding="utf-8")

    # 6. __init__.py
    init_body = [
        "from __future__ import annotations",
        "",
        "from .base import Criterion",
        "from .composite import AndCriterion, NotCriterion, OrCriterion",
        "from .text_criterion import TextContainsCriterion",
        "from .time_criterion import TimeCompareCriterion",
        "from .type_criterion import TypeCriterion",
        "",
        "__all__ = [",
        '    "Criterion",',
        '    "TypeCriterion",',
        '    "TextContainsCriterion",',
        '    "TimeCompareCriterion",',
        '    "AndCriterion",',
        '    "OrCriterion",',
        '    "NotCriterion",',
        "]",
    ]
    (PKG_DIR / "__init__.py").write_text("\n".join(init_body) + "\n", encoding="utf-8")

    # 7. Remove shadowing model/criterion.py
    SRC_CRIT.unlink()
    print("Successfully created model/criterion/ and removed model/criterion.py")


if __name__ == "__main__":
    main()