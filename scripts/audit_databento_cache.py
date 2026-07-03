from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_download_plan.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_cache_audit.md"
DEFAULT_JSON_REPORT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_cache_audit.json"


def audit_cache(plan_path: Path = DEFAULT_PLAN_PATH) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    items = []
    present_count = 0
    missing_count = 0
    invalid_count = 0
    total_present_bytes = 0

    for item in plan.get("items", []):
        output_path = Path(item["output_path"])
        exists = output_path.exists()
        size = output_path.stat().st_size if exists else 0
        valid = exists and size > 0
        row: dict[str, Any] = {
            "window": item["window"],
            "output_path": str(output_path),
            "exists": exists,
            "valid": valid,
            "estimated_cost_usd": item.get("estimated_cost_usd"),
        }
        if valid:
            row["bytes"] = size
            row["sha256"] = _sha256(output_path)
            present_count += 1
            total_present_bytes += size
        else:
            row["bytes"] = size
            row["sha256"] = None
            if exists:
                invalid_count += 1
            else:
                missing_count += 1
        items.append(row)

    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_plan": str(plan_path),
        "scenario": plan.get("scenario"),
        "planned_request_count": len(plan.get("items", [])),
        "present_count": present_count,
        "missing_count": missing_count,
        "invalid_count": invalid_count,
        "total_present_bytes": total_present_bytes,
        "all_present": missing_count == 0 and invalid_count == 0 and len(items) > 0,
        "items": items,
    }


def render_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Databento Cache Audit",
        "",
        f"- **Created at UTC**: `{audit['created_at_utc']}`",
        f"- **Source plan**: `{audit['source_plan']}`",
        f"- **Scenario**: `{audit['scenario']}`",
        f"- **Planned windows**: {audit['planned_request_count']}",
        f"- **Present files**: {audit['present_count']}",
        f"- **Missing files**: {audit['missing_count']}",
        f"- **Invalid files**: {audit['invalid_count']}",
        f"- **Total present bytes**: {audit['total_present_bytes']}",
        f"- **All present**: `{audit['all_present']}`",
        "",
        "## Missing Windows",
        "",
    ]
    missing = [item for item in audit["items"] if not item["exists"]]
    if missing:
        for item in missing:
            lines.append(f"- `{item['window']}` -> `{item['output_path']}`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Use Rule",
            "",
            "- This audit is offline-only and does not call Databento.",
            "- Missing windows need explicit user-approved download before real experiments.",
            "- Present files can be reused by repeated experiments without another Databento request.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(audit: dict[str, Any], report_path: Path, json_report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_markdown(audit), encoding="utf-8")
    json_report_path.parent.mkdir(parents=True, exist_ok=True)
    json_report_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit local Databento raw-cache files without calling Databento.")
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--json-report-path", type=Path, default=DEFAULT_JSON_REPORT_PATH)
    args = parser.parse_args()

    audit = audit_cache(args.plan_path)
    write_outputs(audit, args.report_path, args.json_report_path)
    print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
