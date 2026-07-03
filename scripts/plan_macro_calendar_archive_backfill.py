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

REQUIRED_WINDOWS = {
    "reference_pre_break": ("2019-01-01", "2022-05-10"),
    "train": ("2022-05-11", "2023-12-31"),
    "oos": ("2024-01-01", date.today().isoformat()),
}


class MacroCalendarBackfillPlanError(ValueError):
    pass


def plan_macro_calendar_backfill(
    macro_path: Path = DEFAULT_MACRO_PATH,
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
    start_year: int = 2022,
    end_year: int | None = None,
) -> dict[str, Any]:
    source_plan = _load_source_plan(source_plan_path)
    required_event_types = [str(event_type) for event_type in source_plan["minimum_required_event_types"]]
    source_by_event = _source_by_event_type(source_plan)
    records = _load_macro_events(macro_path)
    end_year = end_year or date.today().year
    if start_year > end_year:
        raise MacroCalendarBackfillPlanError("start_year must be less than or equal to end_year")

    present_by_year: dict[int, set[str]] = defaultdict(set)
    present_by_window: dict[str, set[str]] = {name: set() for name in REQUIRED_WINDOWS}
    for record in records:
        event_date = _event_date(record)
        event_type = record["event_type"]
        present_by_year[event_date.year].add(event_type)
        for name, (start, end) in REQUIRED_WINDOWS.items():
            if date.fromisoformat(start) <= event_date <= date.fromisoformat(end):
                present_by_window[name].add(event_type)

    years = []
    for year in range(start_year, end_year + 1):
        present = sorted(present_by_year.get(year, set()))
        missing = sorted(set(required_event_types).difference(present))
        years.append(
            {
                "year": year,
                "present_event_types": present,
                "missing_event_types": missing,
                "source_requests": _requests_for_missing(year, missing, source_by_event),
            }
        )

    windows = []
    for name, (start, end) in REQUIRED_WINDOWS.items():
        present = sorted(present_by_window[name])
        missing = sorted(set(required_event_types).difference(present))
        windows.append({"window": name, "start": start, "end": end, "present_event_types": present, "missing_event_types": missing})

    missing_years = [item["year"] for item in years if item["missing_event_types"]]
    return {
        "status": "blocked" if missing_years else "pass",
        "macro_path": str(macro_path),
        "source_plan_path": str(source_plan_path),
        "target_years": [start_year, end_year],
        "required_event_types": required_event_types,
        "years": years,
        "windows": windows,
        "next_actions": _next_actions(missing_years),
    }


def _load_source_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MacroCalendarBackfillPlanError(f"{path} must contain a JSON object")
    return payload


def _source_by_event_type(source_plan: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    mapping: dict[str, list[dict[str, str]]] = defaultdict(list)
    for source in source_plan["sources"]:
        for event_type in source["event_types"]:
            mapping[str(event_type)].append(
                {
                    "source_id": str(source["source_id"]),
                    "provider": str(source["provider"]),
                    "source_url": str(source["source_url"]),
                    "parser_status": str(source["parser_status"]),
                }
            )
    return mapping


def _load_macro_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
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
        raise MacroCalendarBackfillPlanError("macro_event missing event_timestamp_et")
    return datetime.fromisoformat(timestamp).date()


def _requests_for_missing(year: int, missing_event_types: list[str], source_by_event: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    requests = []
    for event_type in missing_event_types:
        for source in source_by_event.get(event_type, []):
            requests.append({"year": year, "event_type": event_type, **source})
    return requests


def _next_actions(missing_years: list[int]) -> list[str]:
    if not missing_years:
        return ["Macro calendar archive coverage appears complete for target years; run the coverage auditor to confirm."]
    return [
        f"Backfill official macro calendar archive snapshots for {min(missing_years)}-{max(missing_years)}.",
        "Preserve raw source files and hashes before conversion/import.",
        "Convert archived source pages or official release calendars into importer CSV shape without using OOS outcomes to tune event selection.",
        "Run import_macro_calendar_snapshots.py, then audit_macro_calendar_coverage.py.",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan missing official macro calendar archive coverage by year and source.")
    parser.add_argument("--macro-path", type=Path, default=DEFAULT_MACRO_PATH)
    parser.add_argument("--source-plan-path", type=Path, default=DEFAULT_SOURCE_PLAN_PATH)
    parser.add_argument("--start-year", type=int, default=2022)
    parser.add_argument("--end-year", type=int)
    args = parser.parse_args(argv)

    result = plan_macro_calendar_backfill(args.macro_path, args.source_plan_path, args.start_year, args.end_year)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
