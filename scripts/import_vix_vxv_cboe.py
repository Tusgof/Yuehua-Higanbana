from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from validate_m2_contracts import load_schema, validate_record, validate_records


DEFAULT_CAPTURE_ROOT = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "vix_vxv" / date.today().isoformat()
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl"
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "data" / "registry" / "datasets.jsonl"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "vix_vxv_import_summary.json"


class VixVxvImportError(ValueError):
    pass


def import_vix_vxv(
    capture_root: Path = DEFAULT_CAPTURE_ROOT,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    start_date: date = date(2022, 1, 1),
    end_date: date = date.today(),
) -> dict[str, Any]:
    manifest_path = capture_root / "capture_manifest.json"
    manifest = _load_manifest(manifest_path)
    files = {item["series"]: Path(item["output_path"]) for item in manifest["captured"]}
    vix_rows = _load_cboe_history(files["VIX"], "VIX")
    vxv_rows = _load_cboe_history(files["VIX3M"], "VIX3M")

    records = []
    for row_date in sorted(set(vix_rows).intersection(vxv_rows)):
        if start_date <= row_date <= end_date:
            records.append(
                {
                    "record_type": "vix_vxv",
                    "schema_version": "m2.0",
                    "date": row_date.isoformat(),
                    "vix_close": vix_rows[row_date],
                    "vxv_close": vxv_rows[row_date],
                    "provider": "Cboe",
                    "source": f"file://{manifest_path}",
                }
            )

    if not records:
        raise VixVxvImportError("no overlapping VIX/VIX3M rows found for requested date window")
    schema = load_schema()
    errors = validate_records(records, schema)
    if errors:
        raise VixVxvImportError("\n".join(errors))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    manifest_record = _build_registry_manifest(manifest, manifest_path, records)
    manifest_errors = validate_record(manifest_record, schema)
    if manifest_errors:
        raise VixVxvImportError("\n".join(manifest_errors))
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    if not _registry_contains(registry_path, manifest_record):
        with registry_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest_record, ensure_ascii=False, sort_keys=True) + "\n")

    result = {
        "record_count": len(records),
        "coverage_start": records[0]["date"],
        "coverage_end": records[-1]["date"],
        "normalized_path": str(output_path),
        "registry_path": str(registry_path),
        "manifest": manifest_record,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise VixVxvImportError(f"capture manifest not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise VixVxvImportError(f"{path} must contain a JSON object")
    captured = payload.get("captured")
    if not isinstance(captured, list):
        raise VixVxvImportError("capture manifest missing captured array")
    return payload


def _load_cboe_history(path: Path, series: str) -> dict[date, float]:
    rows: dict[date, float] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_date = datetime.strptime(row["DATE"], "%m/%d/%Y").date()
            close = row.get("CLOSE") if "CLOSE" in row else row.get(series)
            if close in (None, ""):
                continue
            rows[row_date] = float(close)
    return rows


def _build_registry_manifest(manifest: dict[str, Any], manifest_path: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    raw_sha = _combined_raw_sha256([Path(item["output_path"]) for item in manifest["captured"]])
    return {
        "record_type": "data_registry_manifest",
        "schema_version": "m2.0",
        "dataset_id": f"cboe-vix-vxv-{raw_sha[:12]}",
        "provider": "Cboe",
        "source_url": f"file://{manifest_path}",
        "ingested_at_et": datetime.now().astimezone().isoformat(timespec="seconds"),
        "coverage_start": records[0]["date"],
        "coverage_end": records[-1]["date"],
        "raw_sha256": raw_sha,
        "schema_name": "m2_contracts",
        "schema_version_applied": "m2.0",
        "license_notes": "Official public Cboe VIX and VIX3M history CSVs. VIX3M close is mapped to vxv_close for the project VIX/VXV term-structure field.",
    }


def _combined_raw_sha256(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.name):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import official Cboe VIX/VIX3M CSV captures into canonical vix_vxv JSONL.")
    parser.add_argument("--capture-root", type=Path, default=DEFAULT_CAPTURE_ROOT)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--start-date", type=date.fromisoformat, default=date(2022, 1, 1))
    parser.add_argument("--end-date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args(argv)

    result = import_vix_vxv(args.capture_root, args.output_path, args.registry_path, args.summary_path, args.start_date, args.end_date)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
