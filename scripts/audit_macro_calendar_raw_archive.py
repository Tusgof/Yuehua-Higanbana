from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PLAN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "macro_calendar_sources_v1.json"
DEFAULT_RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "macro_calendar"


class MacroCalendarRawArchiveAuditError(ValueError):
    pass


def audit_raw_archive(
    raw_root: Path = DEFAULT_RAW_ROOT,
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
    start_year: int = 2022,
    end_year: int = 2025,
    current_as_of_date: date | None = None,
) -> dict[str, Any]:
    if start_year > end_year:
        raise MacroCalendarRawArchiveAuditError("start_year must be less than or equal to end_year")

    current_as_of_date = current_as_of_date or date.today()
    source_plan = _load_source_plan(source_plan_path)
    source_ids = [source["source_id"] for source in source_plan["sources"]]
    years = []
    for year in range(start_year, end_year + 1):
        as_of_date = _as_of_date_for_year(year, current_as_of_date)
        manifest_path = raw_root / as_of_date / "capture_manifest.json"
        manifest = _load_manifest(manifest_path)
        captured_by_source = {item.get("source_id"): item for item in manifest.get("captured", [])} if manifest else {}
        sources = []
        for source_id in source_ids:
            item = captured_by_source.get(source_id)
            sources.append(_audit_source(raw_root, as_of_date, source_id, item))
        missing_sources = [source["source_id"] for source in sources if source["status"] != "present"]
        years.append(
            {
                "year": year,
                "as_of_date": as_of_date,
                "manifest_path": str(manifest_path),
                "manifest_present": manifest is not None,
                "source_count": len(sources),
                "present_count": len(sources) - len(missing_sources),
                "missing_sources": missing_sources,
                "sources": sources,
                "status": "pass" if not missing_sources else "blocked",
            }
        )

    blocked_years = [year["year"] for year in years if year["status"] != "pass"]
    return {
        "status": "pass" if not blocked_years else "blocked",
        "raw_root": str(raw_root),
        "source_plan_path": str(source_plan_path),
        "target_years": [start_year, end_year],
        "required_source_count": len(source_ids),
        "blocked_years": blocked_years,
        "years": years,
        "next_step": _next_step(blocked_years),
    }


def _audit_source(raw_root: Path, as_of_date: str, source_id: str, item: dict[str, Any] | None) -> dict[str, Any]:
    expected_path = raw_root / as_of_date / f"{source_id}.html"
    if item is None:
        return {"source_id": source_id, "expected_path": str(expected_path), "status": "missing_manifest_entry"}

    output_path = Path(str(item.get("output_path", expected_path)))
    if not output_path.exists():
        return {"source_id": source_id, "expected_path": str(expected_path), "output_path": str(output_path), "status": "missing_file"}

    payload = output_path.read_bytes()
    actual_sha256 = hashlib.sha256(payload).hexdigest()
    expected_sha256 = str(item.get("sha256", ""))
    expected_bytes = int(item.get("bytes", -1))
    status = "present"
    if expected_bytes != len(payload):
        status = "bytes_mismatch"
    elif expected_sha256 and expected_sha256 != actual_sha256:
        status = "sha256_mismatch"

    return {
        "source_id": source_id,
        "expected_path": str(expected_path),
        "output_path": str(output_path),
        "bytes": len(payload),
        "sha256": actual_sha256,
        "status": status,
    }


def _load_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MacroCalendarRawArchiveAuditError(f"{path} must contain a JSON object")
    return payload


def _load_source_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MacroCalendarRawArchiveAuditError(f"{path} must contain a JSON object")
    return payload


def _next_step(blocked_years: list[int]) -> str:
    if not blocked_years:
        return "Raw macro calendar archive appears complete for target years; convert/import snapshots and rerun coverage audit."
    return f"Capture missing official macro calendar sources for {min(blocked_years)}-{max(blocked_years)} source-by-source."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit source-by-source raw official macro calendar archive completeness.")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--source-plan-path", type=Path, default=DEFAULT_SOURCE_PLAN_PATH)
    parser.add_argument("--start-year", type=int, default=2022)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--current-as-of-date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args(argv)

    result = audit_raw_archive(args.raw_root, args.source_plan_path, args.start_year, args.end_year, args.current_as_of_date)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _as_of_date_for_year(year: int, current_as_of_date: date) -> str:
    if year == current_as_of_date.year:
        return current_as_of_date.isoformat()
    return f"{year}-12-31"


if __name__ == "__main__":
    raise SystemExit(main())
