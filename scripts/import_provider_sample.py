from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_m3_fixture import quality_check_records
from provider_adapters import parse_optionsdx_quote_csv, parse_thetadata_quote_csv
from validate_m2_contracts import validate_record


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def import_provider_sample(provider: str, raw_path: Path, output_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    records = parse_provider_sample(provider, raw_path)
    quality_errors = quality_check_records(records)
    if quality_errors:
        raise ValueError("\n".join(quality_errors))

    normalized_dir = output_root / "data" / "normalized" / "spy_0dte"
    registry_dir = output_root / "data" / "registry"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    registry_dir.mkdir(parents=True, exist_ok=True)

    quote_path = normalized_dir / "option_quote.jsonl"
    _write_jsonl(quote_path, sorted(records, key=lambda record: record["quote_timestamp_et"]))

    manifest = _build_manifest(provider, raw_path, records)
    manifest_errors = validate_record(manifest)
    if manifest_errors:
        raise ValueError("\n".join(manifest_errors))

    registry_path = registry_dir / "datasets.jsonl"
    with registry_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n")

    return {
        "provider": manifest["provider"],
        "record_count": len(records),
        "normalized_path": str(quote_path),
        "registry_path": str(registry_path),
        "manifest": manifest,
    }


def parse_provider_sample(provider: str, raw_path: Path) -> list[dict]:
    normalized = provider.strip().lower()
    if normalized == "optionsdx":
        return parse_optionsdx_quote_csv(raw_path)
    if normalized == "thetadata":
        return parse_thetadata_quote_csv(raw_path)
    raise ValueError(f"unsupported provider: {provider}")


def _build_manifest(provider: str, raw_path: Path, records: list[dict]) -> dict[str, Any]:
    dates = sorted({record["expiration_date"] for record in records})
    provider_label = records[0]["provider"] if records else provider
    return {
        "record_type": "data_registry_manifest",
        "schema_version": "m2.0",
        "dataset_id": f"provider-sample-{provider_label.lower()}-{_sha256(raw_path)[:12]}",
        "provider": provider_label,
        "source_url": f"file://{raw_path}",
        "ingested_at_et": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "coverage_start": dates[0],
        "coverage_end": dates[-1],
        "raw_sha256": _sha256(raw_path),
        "schema_name": "m2_contracts",
        "schema_version_applied": "m2.0",
        "license_notes": "Provider sample import. Confirm license terms before using for real research.",
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
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
    parser = argparse.ArgumentParser(description="Import a provider option quote sample into canonical JSONL.")
    parser.add_argument("--provider", required=True, choices=["optionsdx", "thetadata"])
    parser.add_argument("--raw-path", required=True, type=Path)
    parser.add_argument("--output-root", default=PROJECT_ROOT, type=Path)
    args = parser.parse_args()

    result = import_provider_sample(args.provider, args.raw_path, args.output_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
