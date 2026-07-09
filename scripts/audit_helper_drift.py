from __future__ import annotations

import argparse
import ast
import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import interpreter_metadata
from lib.io import relative_to_root, write_json


HELPER_NAMES = {
    "_load_json",
    "_load_jsonl",
    "_relative",
    "_validate_guardrails",
    "_write_search_log",
    "write_reports",
    "_write_reports",
}
DEFAULT_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "helper_drift_audit.json"


def _function_hash(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    cloned = ast.fix_missing_locations(ast.parse(ast.unparse(node)).body[0])
    assert isinstance(cloned, (ast.FunctionDef, ast.AsyncFunctionDef))
    cloned.name = "<helper>"
    normalized = ast.dump(cloned, include_attributes=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _iter_helper_functions(path: Path) -> list[dict[str, str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    helpers: list[dict[str, str]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in HELPER_NAMES:
            helpers.append({"name": node.name, "sha256": _function_hash(node)})
    return helpers


def audit_helper_drift(
    script_root: Path = PROJECT_ROOT / "scripts",
    output_path: Path = DEFAULT_OUTPUT,
    write_report: bool = True,
) -> dict[str, Any]:
    occurrences: dict[str, list[dict[str, str]]] = defaultdict(list)
    for path in sorted(script_root.rglob("*.py")):
        for helper in _iter_helper_functions(path):
            occurrences[helper["name"]].append(
                {
                    "path": relative_to_root(path, PROJECT_ROOT),
                    "sha256": helper["sha256"],
                }
            )

    helper_reports: list[dict[str, Any]] = []
    total_divergent_files = 0
    for helper_name in sorted(HELPER_NAMES):
        rows = occurrences.get(helper_name, [])
        counts = Counter(row["sha256"] for row in rows)
        majority_hash = counts.most_common(1)[0][0] if counts else None
        divergent = [row for row in rows if row["sha256"] != majority_hash]
        total_divergent_files += len(divergent)
        helper_reports.append(
            {
                "helper_name": helper_name,
                "occurrence_count": len(rows),
                "variant_count": len(counts),
                "majority_sha256": majority_hash,
                "divergent_files": divergent,
            }
        )

    report: dict[str, Any] = {
        "audit_id": "helper_drift_audit",
        "status": "pass_with_findings" if total_divergent_files else "pass",
        "purpose": "Measure duplicated helper drift without editing frozen experiment scripts.",
        "script_root": relative_to_root(script_root, PROJECT_ROOT),
        "helper_names": sorted(HELPER_NAMES),
        "helper_reports": helper_reports,
        "total_divergent_files": total_divergent_files,
        "auto_fix_applied": False,
        "interpreter": interpreter_metadata(),
    }
    if write_report:
        write_json(output_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit duplicated helper-body drift across scripts.")
    parser.add_argument("--script-root", type=Path, default=PROJECT_ROOT / "scripts")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = audit_helper_drift(args.script_root, args.output, write_report=True)
    print(
        f"{report['status']}: {report['total_divergent_files']} divergent helper copies "
        f"across {len(report['helper_reports'])} helper names"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
