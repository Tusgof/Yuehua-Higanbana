from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PLAN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "macro_calendar_sources_v1.json"


class MacroCalendarCaptureCommandPlanError(ValueError):
    pass


def plan_capture_commands(
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
    start_year: int = 2022,
    end_year: int = 2025,
) -> dict[str, Any]:
    if start_year > end_year:
        raise MacroCalendarCaptureCommandPlanError("start_year must be less than or equal to end_year")

    source_plan = _load_source_plan(source_plan_path)
    sources = source_plan["sources"]
    commands = []
    for year in range(start_year, end_year + 1):
        as_of_date = f"{year}-12-31"
        for source in sources:
            source_id = source["source_id"]
            source_url = _source_url_for_year(source, year)
            commands.append(
                {
                    "year": year,
                    "as_of_date": as_of_date,
                    "source_id": source_id,
                    "provider": source["provider"],
                    "event_types": source["event_types"],
                    "source_url": source_url,
                    "command": (
                        "python scripts\\capture_macro_calendar_snapshots.py "
                        f"--as-of-date {as_of_date} --source-id {source_id} --execute"
                    ),
                }
            )

    return {
        "mode": "dry_run",
        "source_plan_path": str(source_plan_path),
        "target_years": [start_year, end_year],
        "source_count": len(sources),
        "command_count": len(commands),
        "commands": commands,
        "next_step": "Run commands source-by-source only after approval for multi-file raw archive writes.",
    }


def _load_source_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MacroCalendarCaptureCommandPlanError(f"{path} must contain a JSON object")
    return payload


def _source_url_for_year(source: dict[str, Any], year: int) -> str:
    template = source.get("source_url_template")
    if isinstance(template, str) and template:
        return template.format(year=year)
    return source["source_url"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan source-by-source official macro calendar capture commands.")
    parser.add_argument("--source-plan-path", type=Path, default=DEFAULT_SOURCE_PLAN_PATH)
    parser.add_argument("--start-year", type=int, default=2022)
    parser.add_argument("--end-year", type=int, default=2025)
    args = parser.parse_args(argv)

    result = plan_capture_commands(args.source_plan_path, args.start_year, args.end_year)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
