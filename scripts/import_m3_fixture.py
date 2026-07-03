from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_m2_contracts import load_schema, validate_record, validate_records


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_PATH = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "m3_fixture_raw.json"


class ImportErrorWithContext(ValueError):
    pass


def import_raw_dataset(raw_path: Path = DEFAULT_RAW_PATH, output_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list):
        raise ImportErrorWithContext("raw payload must contain a records array")

    schema = load_schema()
    contract_errors = validate_records(records, schema)
    quality_errors = quality_check_records(records)
    if contract_errors or quality_errors:
        errors = contract_errors + quality_errors
        raise ImportErrorWithContext("\n".join(errors))

    normalized_dir = output_root / "data" / "normalized" / "spy_0dte"
    registry_dir = output_root / "data" / "registry"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    registry_dir.mkdir(parents=True, exist_ok=True)

    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_type[record["record_type"]].append(record)

    written_files: list[str] = []
    for record_type, type_records in sorted(by_type.items()):
        path = normalized_dir / f"{record_type}.jsonl"
        _write_jsonl(path, sorted(type_records, key=_sort_key))
        written_files.append(str(path))

    manifest = _build_registry_manifest(payload, raw_path)
    manifest_errors = validate_record(manifest, schema)
    if manifest_errors:
        raise ImportErrorWithContext("\n".join(manifest_errors))

    registry_path = registry_dir / "datasets.jsonl"
    if not _registry_contains(registry_path, manifest):
        with registry_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n")

    return {
        "record_count": len(records),
        "record_types": sorted(by_type),
        "written_files": written_files,
        "registry_path": str(registry_path),
        "manifest": manifest
    }


def quality_check_records(records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen_keys: set[tuple[Any, ...]] = set()
    for index, record in enumerate(records):
        timestamp_error = _check_timestamp_fields(index, record)
        if timestamp_error:
            errors.append(timestamp_error)
        key = _unique_key(record)
        if key:
            if key in seen_keys:
                errors.append(f"record[{index}]: duplicate logical key {key}")
            seen_keys.add(key)
    return errors


def _check_timestamp_fields(index: int, record: dict[str, Any]) -> str | None:
    for field, value in record.items():
        if field.endswith("_et") and isinstance(value, str):
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is None:
                return f"record[{index}]: {field} must include timezone offset"
    return None


def _unique_key(record: dict[str, Any]) -> tuple[Any, ...] | None:
    record_type = record.get("record_type")
    if record_type == "spy_bar":
        return (record_type, record.get("symbol"), record.get("timestamp_et"))
    if record_type == "option_quote":
        return (
            record_type,
            record.get("underlying"),
            record.get("quote_timestamp_et"),
            record.get("expiration_date"),
            record.get("right"),
            record.get("strike"),
        )
    if record_type == "vix_vxv":
        return (record_type, record.get("date"))
    if record_type == "macro_event":
        return (record_type, record.get("event_id"))
    if record_type == "news_item":
        return (record_type, record.get("news_id"))
    if record_type == "llm_assessment":
        return (record_type, record.get("assessment_id"))
    return None


def _sort_key(record: dict[str, Any]) -> str:
    for field in ("timestamp_et", "quote_timestamp_et", "event_timestamp_et", "fetched_at_et", "created_at_et", "date"):
        if field in record:
            return str(record[field])
    return json.dumps(record, sort_keys=True)


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _registry_contains(path: Path, manifest: dict[str, Any]) -> bool:
    if not path.exists():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        existing = json.loads(line)
        if (
            existing.get("dataset_id") == manifest["dataset_id"]
            and existing.get("raw_sha256") == manifest["raw_sha256"]
            and existing.get("schema_version_applied") == manifest["schema_version_applied"]
        ):
            return True
    return False


def _build_registry_manifest(payload: dict[str, Any], raw_path: Path) -> dict[str, Any]:
    return {
        "record_type": "data_registry_manifest",
        "schema_version": "m2.0",
        "dataset_id": payload["dataset_id"],
        "provider": payload["provider"],
        "source_url": payload["source_url"],
        "ingested_at_et": payload["ingested_at_et"],
        "coverage_start": payload["coverage_start"],
        "coverage_end": payload["coverage_end"],
        "raw_sha256": _sha256(raw_path),
        "schema_name": payload["schema_name"],
        "schema_version_applied": payload["schema_version_applied"],
        "license_notes": payload["license_notes"],
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    result = import_raw_dataset()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
