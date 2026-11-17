from __future__ import annotations

import ast
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_EXC = ROOT / "model" / "exceptions.py"
PKG_DIR = ROOT / "model" / "exceptions"

CLASS_TO_MODULE = {
    "PIMModelError": "pim_model_error",
    "UnknownFieldError": "unknown_field_error",
    "InvalidFieldValueError": "invalid_field_value_error",
    "PIRNotFoundError": "pir_not_found_error",
    "DuplicatePIRIdError": "duplicate_pir_id_error",
    "InvalidFileExtensionError": "invalid_file_extension_error",
    "StorageCorruptionError": "storage_corruption_error",
    "UnknownPIRTypeError": "unknown_pir_type_error",
    "CriterionSyntaxError": "criterion_syntax_error",
}


def node_source(lines: list[str], node: ast.AST) -> str:
    start = getattr(node, "lineno", 1)
    if isinstance(node, ast.ClassDef) and node.decorator_list:
        start = min([start] + [d.lineno for d in node.decorator_list])
    end = getattr(node, "end_lineno", start)
    return "".join(lines[start - 1 : end]).rstrip() + "\n"


def main() -> None:
    if not SRC_EXC.exists():
        raise FileNotFoundError(f"Expected {SRC_EXC} to exist.")

    source = SRC_EXC.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)

    classes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }

    if PKG_DIR.exists():
        shutil.rmtree(PKG_DIR)
    PKG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Write base class file
    base_src = node_source(lines, classes["PIMModelError"]).rstrip()
    (PKG_DIR / "pim_model_error.py").write_text(
        f"from __future__ import annotations\n\n\n{base_src}\n",
        encoding="utf-8",
    )

    # 2. Write each exception subclass file
    for cls_name, mod_name in CLASS_TO_MODULE.items():
        if cls_name == "PIMModelError":
            continue
        cls_src = node_source(lines, classes[cls_name]).rstrip()
        body = (
            "from __future__ import annotations\n\n"
            "from .pim_model_error import PIMModelError\n\n\n"
            f"{cls_src}\n"
        )
        (PKG_DIR / f"{mod_name}.py").write_text(body, encoding="utf-8")

    # 3. Write __init__.py re-exporting all exceptions
    init_lines = ["from __future__ import annotations", ""]
    for cls_name, mod_name in CLASS_TO_MODULE.items():
        init_lines.append(f"from .{mod_name} import {cls_name}")
    init_lines.extend(["", "__all__ = ["])
    for cls_name in CLASS_TO_MODULE:
        init_lines.append(f'    "{cls_name}",')
    init_lines.append("]")
    (PKG_DIR / "__init__.py").write_text("\n".join(init_lines) + "\n", encoding="utf-8")

    # 4. Remove shadowing model/exceptions.py
    SRC_EXC.unlink()
    print("Successfully created model/exceptions/ and removed model/exceptions.py")


if __name__ == "__main__":
    main()