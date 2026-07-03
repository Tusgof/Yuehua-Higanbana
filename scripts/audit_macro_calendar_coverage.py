from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MACRO_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl"
DEFAULT_SOURCE_PLAN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "macro_calendar_sources_v1.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "macro_calendar_coverage_audit.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "macro_calendar_coverage_audit.md"

REQUIRED_WINDOWS = {
    "reference_pre_break": ("2019-01-01", "2022-05-10"),
    "train": ("2022-05-11", "2023-12-31"),
    "oos": ("2024-01-01", date.today().isoformat()),
}


class MacroCalendarCoverageError(ValueError):
    pass


def audit_macro_calendar_coverage(
    macro_path: Path = DEFAULT_MACRO_PATH,
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
) -> dict[str, Any]:
    required_event_types = _load_required_event_types(source_plan_path)
    records = _load_macro_events(macro_path)
    event_dates = [_event_date(record) for record in records]
    coverage_start = min(event_dates).isoformat() if event_dates else None
    coverage_end = max(event_dates).isoformat() if event_dates else None

    by_year: dict[int, set[str]] = defaultdict(set)
    by_window: dict[str, set[str]] = {name: set() for name in REQUIRED_WINDOWS}
    for record, event_date in zip(records, event_dates):
        event_type = record["event_type"]
        by_year[event_date.year].add(event_type)
        for name, (start, end) in REQUIRED_WINDOWS.items():
            if date.fromisoformat(start) <= event_date <= date.fromisoformat(end):
                by_window[name].add(event_type)

    target_years = list(range(2022, date.today().year + 1))
    year_results = []
    for year in target_years:
        present = sorted(by_year.get(year, set()))
        missing = sorted(set(required_event_types).difference(present))
        year_results.append({"year": year, "present_event_types": present, "missing_event_types": missing})

    window_results = []
    for name, (start, end) in REQUIRED_WINDOWS.items():
        present = sorted(by_window[name])
        missing = sorted(set(required_event_types).difference(present))
        window_results.append(
            {
                "window": name,
                "start": start,
                "end": end,
                "present_event_types": present,
                "missing_event_types": missing,
            }
        )

    all_missing = sorted({event for item in year_results + window_results for event in item["missing_event_types"]})
    status = "pass" if not all_missing and coverage_start and coverage_start <= "2022-05-11" else "blocked"
    return {
        "status": status,
        "macro_path": str(macro_path),
        "record_count": len(records),
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "required_event_types": required_event_types,
        "years": year_results,
        "windows": window_results,
        "blockers": _blockers(status, coverage_start, year_results, window_results),
    }


def write_reports(result: dict[str, Any], json_output: Path = DEFAULT_JSON_OUTPUT, report_output: Path = DEFAULT_REPORT_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Macro Calendar Coverage Audit",
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
    lines.extend(["", "## Year Coverage", "", "| Year | Present | Missing |", "|:--|:--|:--|"])
    for item in result["years"]:
        lines.append(
            f"| {item['year']} | {', '.join(item['present_event_types']) or '-'} | {', '.join(item['missing_event_types']) or '-'} |"
        )
    lines.extend(["", "## Window Coverage", "", "| Window | Start | End | Missing |", "|:--|:--|:--|:--|"])
    for item in result["windows"]:
        lines.append(f"| {item['window']} | {item['start']} | {item['end']} | {', '.join(item['missing_event_types']) or '-'} |")
    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_required_event_types(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    event_types = payload.get("minimum_required_event_types")
    if not isinstance(event_types, list) or not event_types:
        raise MacroCalendarCoverageError("minimum_required_event_types must be a non-empty array")
    return [str(event_type) for event_type in event_types]


def _load_macro_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise MacroCalendarCoverageError(f"macro calendar file not found: {path}")
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            if record.get("record_type") == "macro_event":
                records.append(record)
    return records


def _event_date(record: dict[str, Any]) -> date:
    timestamp = str(record.get("event_timestamp_et", ""))
    if not timestamp:
        raise MacroCalendarCoverageError("macro_event missing event_timestamp_et")
    return datetime.fromisoformat(timestamp).date()


def _blockers(status: str, coverage_start: str | None, years: list[dict[str, Any]], windows: list[dict[str, Any]]) -> list[str]:
    blockers: set[str] = set()
    if status == "pass":
        return []
    if not coverage_start or coverage_start > "2022-05-11":
        blockers.add("requires_macro_archive_start_by_2022_05_11")
    for item in years:
        if item["missing_event_types"]:
            blockers.add(f"requires_macro_event_coverage_{item['year']}")
    for item in windows:
        if item["missing_event_types"]:
            blockers.add(f"requires_macro_window_coverage_{item['window']}")
    return sorted(blockers)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit canonical macro calendar coverage for Higanbana train/OOS windows.")
    parser.add_argument("--macro-path", type=Path, default=DEFAULT_MACRO_PATH)
    parser.add_argument("--source-plan-path", type=Path, default=DEFAULT_SOURCE_PLAN_PATH)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = audit_macro_calendar_coverage(args.macro_path, args.source_plan_path)
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
