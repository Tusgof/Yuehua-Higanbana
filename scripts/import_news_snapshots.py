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
DEFAULT_SOURCE_PLAN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "news_sources_v1.json"
DEFAULT_SNAPSHOT_PATH = PROJECT_ROOT / "tests" / "fixtures" / "news_snapshots" / "gdelt_news_sample.csv"
EASTERN = ZoneInfo("America/New_York")


class NewsImportError(ValueError):
    pass


def import_news_snapshot(
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
    output_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    source_plan = _load_source_plan(source_plan_path)
    source_by_id = {source["source_id"]: source for source in source_plan["sources"]}
    records = parse_snapshot(snapshot_path, source_by_id, source_plan)
    coverage_errors = _check_required_topic_coverage(records, source_plan)
    errors = validate_records(records) + quality_check_records(records) + _check_duplicate_urls(records)
    if coverage_errors or errors:
        raise NewsImportError("\n".join(coverage_errors + errors))

    normalized_dir = output_root / "data" / "normalized" / "spy_0dte" / "news"
    registry_dir = output_root / "data" / "registry"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    registry_dir.mkdir(parents=True, exist_ok=True)

    output_path = normalized_dir / "news_item.jsonl"
    _write_jsonl(output_path, sorted(records, key=lambda record: record["published_at_et"]))

    manifest = _build_manifest(snapshot_path, records)
    manifest_errors = validate_record(manifest)
    if manifest_errors:
        raise NewsImportError("\n".join(manifest_errors))

    registry_path = registry_dir / "datasets.jsonl"
    with registry_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n")

    return {
        "record_count": len(records),
        "topics": sorted({record["topic"] for record in records if "topic" in record}),
        "normalized_path": str(output_path),
        "registry_path": str(registry_path),
        "manifest": manifest,
    }


def parse_snapshot(
    snapshot_path: Path,
    source_by_id: dict[str, dict[str, Any]],
    source_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with snapshot_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_columns = {
            "source_id",
            "topic",
            "decision_time_et",
            "fetched_at_utc",
            "published_at_utc",
            "source_name",
            "headline",
            "url",
        }
        missing_columns = required_columns.difference(reader.fieldnames or [])
        if missing_columns:
            raise NewsImportError(f"snapshot missing columns: {sorted(missing_columns)}")
        for index, row in enumerate(reader, start=2):
            records.append(_normalize_row(row, index, snapshot_path, source_by_id, source_plan))
    return records


def _normalize_row(
    row: dict[str, str],
    index: int,
    snapshot_path: Path,
    source_by_id: dict[str, dict[str, Any]],
    source_plan: dict[str, Any],
) -> dict[str, Any]:
    source_id = row["source_id"].strip()
    topic = row["topic"].strip()
    source = source_by_id.get(source_id)
    if not source:
        raise NewsImportError(f"row {index}: unknown source_id {source_id!r}")
    if source.get("archive_status") not in {"candidate", "supplement_only"}:
        raise NewsImportError(f"row {index}: source_id {source_id!r} is not approved for snapshot import")
    if topic not in set(source["allowed_topics"]):
        raise NewsImportError(f"row {index}: topic {topic!r} is not allowed for {source_id!r}")

    decision_time = _parse_timestamp(row["decision_time_et"].strip(), index, "decision_time_et")
    fetched_at = _parse_timestamp(row["fetched_at_utc"].strip(), index, "fetched_at_utc")
    published_at = _parse_timestamp(row["published_at_utc"].strip(), index, "published_at_utc")
    _check_anti_leakage(index, decision_time, fetched_at, published_at, source_plan)

    headline = row["headline"].strip()
    url = row["url"].strip()
    source_name = row["source_name"].strip()
    if not headline:
        raise NewsImportError(f"row {index}: headline is required")
    if not url.startswith("https://"):
        raise NewsImportError(f"row {index}: url must be https")
    if not source_name:
        raise NewsImportError(f"row {index}: source_name is required")

    return {
        "record_type": "news_item",
        "schema_version": "m2.0",
        "news_id": _news_id(source_id, topic, published_at, url),
        "decision_time_et": decision_time.astimezone(EASTERN).isoformat(timespec="seconds"),
        "fetched_at_et": fetched_at.astimezone(EASTERN).isoformat(timespec="seconds"),
        "published_at_et": published_at.astimezone(EASTERN).isoformat(timespec="seconds"),
        "source_name": source_name,
        "headline": headline,
        "url": url,
        "provider": source["provider"],
        "topic": topic,
        "source": f"file://{snapshot_path}#{source_id}",
    }


def _parse_timestamp(value: str, index: int, field: str) -> datetime:
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise NewsImportError(f"row {index}: invalid {field}") from exc
    if parsed.tzinfo is None:
        raise NewsImportError(f"row {index}: {field} must include timezone")
    return parsed


def _check_anti_leakage(
    index: int,
    decision_time: datetime,
    fetched_at: datetime,
    published_at: datetime,
    source_plan: dict[str, Any],
) -> None:
    rules = source_plan.get("anti_leakage_rules", {})
    if rules.get("published_at_must_be_lte_decision_time") is True and published_at > decision_time:
        raise NewsImportError(f"row {index}: published_at_utc is after decision_time_et")
    if rules.get("fetched_at_must_be_lte_decision_time_for_live_replay") is True and fetched_at > decision_time:
        raise NewsImportError(f"row {index}: fetched_at_utc is after decision_time_et")


def _check_required_topic_coverage(records: list[dict[str, Any]], source_plan: dict[str, Any]) -> list[str]:
    required = set(source_plan.get("minimum_required_topics", []))
    present = {record.get("topic") for record in records}
    missing = sorted(required.difference(present))
    if missing:
        return [f"snapshot missing required news topics: {missing}"]
    return []


def _check_duplicate_urls(records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, record in enumerate(records):
        key = (record["provider"], record["url"])
        if key in seen:
            errors.append(f"record[{index}]: duplicate provider/url {key}")
        seen.add(key)
    return errors


def _news_id(source_id: str, topic: str, published_at: datetime, url: str) -> str:
    payload = "|".join([source_id, topic, published_at.isoformat(), url])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"news-{topic}-{digest}"


def _build_manifest(snapshot_path: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    dates = sorted(record["published_at_et"][:10] for record in records)
    raw_hash = _sha256(snapshot_path)
    return {
        "record_type": "data_registry_manifest",
        "schema_version": "m2.0",
        "dataset_id": f"news-snapshot-{raw_hash[:12]}",
        "provider": "news-snapshot",
        "source_url": f"file://{snapshot_path}",
        "ingested_at_et": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "coverage_start": dates[0],
        "coverage_end": dates[-1],
        "raw_sha256": raw_hash,
        "schema_name": "m2_contracts",
        "schema_version_applied": "m2.0",
        "license_notes": "Offline fixture snapshot from news source plan. Use archived source snapshots for real research imports.",
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
    parser = argparse.ArgumentParser(description="Import offline news snapshots into canonical news_item JSONL.")
    parser.add_argument("--snapshot-path", type=Path, default=DEFAULT_SNAPSHOT_PATH)
    parser.add_argument("--source-plan-path", type=Path, default=DEFAULT_SOURCE_PLAN_PATH)
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()

    result = import_news_snapshot(args.snapshot_path, args.source_plan_path, args.output_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
