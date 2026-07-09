from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import interpreter_metadata
from lib.io import load_json, relative_to_root, write_json


DEFAULT_CONFIG = PROJECT_ROOT / "config" / "new_code_scripts.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "new_script_lib_usage_audit.json"


def _imports_lib(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "lib" or alias.name.startswith("lib.") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module == "lib" or (node.module or "").startswith("lib."):
                return True
    return False


def audit_new_script_lib_usage(
    config_path: Path = DEFAULT_CONFIG,
    output_path: Path = DEFAULT_OUTPUT,
    write_report: bool = True,
) -> dict[str, Any]:
    config = load_json(config_path)
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for relative in config.get("scripts", []):
        path = PROJECT_ROOT / str(relative)
        status = "missing"
        imports_lib = False
        if path.exists():
            imports_lib = _imports_lib(path)
            status = "pass" if imports_lib else "blocked_no_lib_import"
        if status != "pass":
            blockers.append(f"{status}:{relative}")
        rows.append(
            {
                "script_path": relative_to_root(path, PROJECT_ROOT),
                "status": status,
                "imports_lib": imports_lib,
            }
        )

    report: dict[str, Any] = {
        "audit_id": "new_script_lib_usage_audit",
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "script_count": len(rows),
        "bypassing_lib_count": sum(1 for row in rows if row["status"] == "blocked_no_lib_import"),
        "rows": rows,
        "interpreter": interpreter_metadata(),
    }
    if write_report:
        write_json(output_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit whether new scripts use shared lib infrastructure.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = audit_new_script_lib_usage(args.config, args.output, write_report=True)
    print(f"{report['status']}: {report['bypassing_lib_count']} new scripts bypass lib")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
