from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_m3_fixture import quality_check_records
from validate_m2_contracts import validate_record, validate_records


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PLAN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "macro_calendar_sources_v1.json"
DEFAULT_SNAPSHOT_PATH = PROJECT_ROOT / "tests" / "fixtures" / "macro_calendar_snapshots" / "official_macro_calendar_sample.csv"
EASTERN = ZoneInfo("America/New_York")


class MacroCalendarImportError(ValueError):
    pass


def import_macro_calendar_snapshot(
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
    output_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    source_plan = _load_source_plan(source_plan_path)
    source_by_id = {source["source_id"]: source for source in source_plan["sources"]}
    records = parse_snapshot(snapshot_path, source_by_id)
    coverage_errors = _check_required_event_coverage(records, source_plan)
    errors = validate_records(records) + quality_check_records(records)
    if coverage_errors or errors:
        raise MacroCalendarImportError("\n".join(coverage_errors + errors))

    normalized_dir = output_root / "data" / "normalized" / "spy_0dte" / "macro_calendar"
    registry_dir = output_root / "data" / "registry"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    registry_dir.mkdir(parents=True, exist_ok=True)

    output_path = normalized_dir / "macro_event.jsonl"
    _write_jsonl(output_path, sorted(records, key=lambda record: record["event_timestamp_et"]))

    manifest = _build_manifest(snapshot_path, records)
    manifest_errors = validate_record(manifest)
    if manifest_errors:
        raise MacroCalendarImportError("\n".join(manifest_errors))

    registry_path = registry_dir / "datasets.jsonl"
    with registry_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n")

    return {
        "record_count": len(records),
        "event_types": sorted({record["event_type"] for record in records}),
        "normalized_path": str(output_path),
        "registry_path": str(registry_path),
        "manifest": manifest,
    }


def parse_snapshot(snapshot_path: Path, source_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with snapshot_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_columns = {"source_id", "event_type", "event_date", "release_time_et", "title"}
        missing_columns = required_columns.difference(reader.fieldnames or [])
        if missing_columns:
            raise MacroCalendarImportError(f"snapshot missing columns: {sorted(missing_columns)}")
        for index, row in enumerate(reader, start=2):
            records.append(_normalize_row(row, index, snapshot_path, source_by_id))
    return records


def _normalize_row(row: dict[str, str], index: int, snapshot_path: Path, source_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_id = row["source_id"].strip()
    event_type = row["event_type"].strip()
    source = source_by_id.get(source_id)
    if not source:
        raise MacroCalendarImportError(f"row {index}: unknown source_id {source_id!r}")
    if event_type not in set(source["event_types"]):
        raise MacroCalendarImportError(f"row {index}: {event_type!r} is not allowed for {source_id!r}")

    event_date = row["event_date"].strip()
    release_time = row["release_time_et"].strip()
    timestamp = _parse_eastern_timestamp(event_date, release_time, index)
    title = row["title"].strip()
    event_id = _event_id(source_id, event_type, event_date, release_time, title)
    return {
        "record_type": "macro_event",
        "schema_version": "m2.0",
        "event_id": event_id,
        "event_type": event_type,
        "event_timestamp_et": timestamp,
        "importance": source["default_importance"],
        "provider": source["provider"],
        "source": f"file://{snapshot_path}#{source_id}",
    }


def _parse_eastern_timestamp(event_date: str, release_time: str, index: int) -> str:
    try:
        naive = datetime.fromisoformat(f"{event_date}T{release_time}:00")
    except ValueError as exc:
        raise MacroCalendarImportError(f"row {index}: invalid event_date/release_time_et") from exc
    return naive.replace(tzinfo=EASTERN).isoformat(timespec="seconds")


def _check_required_event_coverage(records: list[dict[str, Any]], source_plan: dict[str, Any]) -> list[str]:
    required = set(source_plan.get("minimum_required_event_types", []))
    present = {record["event_type"] for record in records}
    missing = sorted(required.difference(present))
    if missing:
        return [f"snapshot missing required event types: {missing}"]
    return []


def _event_id(source_id: str, event_type: str, event_date: str, release_time: str, title: str) -> str:
    payload = "|".join([source_id, event_type, event_date, release_time, title.lower()])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{event_type.lower()}-{event_date}-{digest}"


def _build_manifest(snapshot_path: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    dates = sorted(record["event_timestamp_et"][:10] for record in records)
    raw_hash = _sha256(snapshot_path)
    return {
        "record_type": "data_registry_manifest",
        "schema_version": "m2.0",
        "dataset_id": f"macro-calendar-snapshot-{raw_hash[:12]}",
        "provider": "official-macro-calendar-snapshot",
        "source_url": f"file://{snapshot_path}",
        "ingested_at_et": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "coverage_start": dates[0],
        "coverage_end": dates[-1],
        "raw_sha256": raw_hash,
        "schema_name": "m2_contracts",
        "schema_version_applied": "m2.0",
        "license_notes": "Offline archived snapshot from official macro-calendar source plan. Preserve raw source files and hashes for real research imports.",
    }


def _load_source_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Import offline official macro calendar snapshots into canonical macro_event JSONL.")
    parser.add_argument("--snapshot-path", type=Path, default=DEFAULT_SNAPSHOT_PATH)
    parser.add_argument("--source-plan-path", type=Path, default=DEFAULT_SOURCE_PLAN_PATH)
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()

    result = import_macro_calendar_snapshot(args.snapshot_path, args.source_plan_path, args.output_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
