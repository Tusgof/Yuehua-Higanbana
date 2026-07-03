from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VIX_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "vix_vxv_coverage_audit.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "vix_vxv_coverage_audit.md"

REQUIRED_WINDOWS = {
    "reference_pre_break": ("2019-01-01", "2022-05-10"),
    "train": ("2022-05-11", "2023-12-31"),
    "oos": ("2024-01-01", date.today().isoformat()),
}


class VixVxvCoverageError(ValueError):
    pass


def audit_vix_vxv_coverage(
    vix_path: Path = DEFAULT_VIX_PATH,
    as_of_date: date | None = None,
    max_staleness_days: int = 7,
) -> dict[str, Any]:
    as_of_date = as_of_date or date.today()
    records = _load_records(vix_path)
    record_dates = [_record_date(record) for record in records]
    coverage_start = min(record_dates).isoformat() if record_dates else None
    coverage_end = max(record_dates).isoformat() if record_dates else None

    years = []
    for year in range(2022, as_of_date.year + 1):
        count = sum(1 for item in record_dates if item.year == year)
        years.append({"year": year, "record_count": count, "status": "pass" if count else "blocked"})

    windows = []
    for name, (start, end) in REQUIRED_WINDOWS.items():
        effective_end = min(date.fromisoformat(end), as_of_date)
        count = sum(1 for item in record_dates if date.fromisoformat(start) <= item <= effective_end)
        windows.append({"window": name, "start": start, "end": effective_end.isoformat(), "record_count": count, "status": "pass" if count else "blocked"})

    blockers = _blockers(records, coverage_start, coverage_end, years, windows, as_of_date, max_staleness_days)
    return {
        "status": "pass" if not blockers else "blocked",
        "vix_path": str(vix_path),
        "record_count": len(records),
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "as_of_date": as_of_date.isoformat(),
        "max_staleness_days": max_staleness_days,
        "years": years,
        "windows": windows,
        "blockers": blockers,
    }


def write_reports(result: dict[str, Any], json_output: Path = DEFAULT_JSON_OUTPUT, report_output: Path = DEFAULT_REPORT_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# VIX/VXV Coverage Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Record count: {result['record_count']}",
        f"- Coverage start: `{result['coverage_start']}`",
        f"- Coverage end: `{result['coverage_end']}`",
        "",
        "## Blockers",
        "",
    ]
    for blocker in result["blockers"]:
        lines.append(f"- `{blocker}`")
    lines.extend(["", "## Year Coverage", "", "| Year | Records | Status |", "|:--|--:|:--|"])
    for item in result["years"]:
        lines.append(f"| {item['year']} | {item['record_count']} | `{item['status']}` |")
    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _record_date(record: dict[str, Any]) -> date:
    if record.get("record_type") != "vix_vxv":
        raise VixVxvCoverageError("non-vix_vxv record found in VIX/VXV file")
    return datetime.fromisoformat(str(record["date"])).date()


def _blockers(
    records: list[dict[str, Any]],
    coverage_start: str | None,
    coverage_end: str | None,
    years: list[dict[str, Any]],
    windows: list[dict[str, Any]],
    as_of_date: date,
    max_staleness_days: int,
) -> list[str]:
    blockers: set[str] = set()
    if not records:
        blockers.add("requires_real_vix_vxv_archive")
    if not coverage_start or coverage_start > "2022-05-11":
        blockers.add("requires_vix_vxv_start_by_2022_05_11")
    if not coverage_end or date.fromisoformat(coverage_end) < as_of_date - timedelta(days=max_staleness_days):
        blockers.add("requires_recent_vix_vxv_close")
    for item in years:
        if item["status"] != "pass":
            blockers.add(f"requires_vix_vxv_coverage_{item['year']}")
    for item in windows:
        if item["status"] != "pass":
            blockers.add(f"requires_vix_vxv_window_coverage_{item['window']}")
    return sorted(blockers)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit canonical VIX/VXV coverage for Higanbana train/OOS windows.")
    parser.add_argument("--vix-path", type=Path, default=DEFAULT_VIX_PATH)
    parser.add_argument("--as-of-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--max-staleness-days", type=int, default=7)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = audit_vix_vxv_coverage(args.vix_path, args.as_of_date, args.max_staleness_days)
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
