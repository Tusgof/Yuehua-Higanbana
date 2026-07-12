from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import data_root, interpreter_metadata
from lib.integrity import combined_named_file_hash, dbn_record_body_hashes, sha256_file


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def _data_path(raw: str, root: Path) -> Path:
    normalized = raw.removeprefix("file://").replace("\\", "/")
    marker = "data/"
    if marker in normalized.lower():
        index = normalized.lower().index(marker)
        relative = normalized[index + len(marker) :]
        return root.joinpath(*Path(relative).parts)
    path = Path(normalized)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _registry_check(row: dict[str, Any], root: Path, verify_hashes: bool) -> dict[str, Any]:
    source = _data_path(str(row.get("source_url", "")), root)
    expected = str(row.get("raw_sha256", "")).lower()
    result: dict[str, Any] = {
        "dataset_id": row.get("dataset_id"),
        "source_path": str(source),
        "expected_sha256": expected,
        "exists": source.exists(),
        "hash_valid": bool(SHA256_PATTERN.fullmatch(expected)),
    }
    if not source.exists():
        result["status"] = "missing"
        return result
    if not result["hash_valid"]:
        result["status"] = "invalid_expected_hash"
        return result
    if not verify_hashes:
        result["status"] = "inventory_only"
        return result
    if source.is_file():
        actual = sha256_file(source)
        result["file_count"] = 1
    else:
        files = sorted(source.glob("*.dbn.zst"))
        result["file_count"] = len(files)
        if not files:
            result["status"] = "no_hashable_files"
            return result
        actual = combined_named_file_hash(files)
    result["actual_sha256"] = actual
    result["status"] = "pass" if actual == expected else "sha256_mismatch"
    return result


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _download_report_artifacts(report_root: Path, root: Path) -> list[dict[str, str]]:
    found: dict[str, dict[str, str]] = {}
    for report_path in sorted(report_root.glob("*.json")):
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            continue
        for item in _walk(payload):
            expected = str(item.get("sha256", "")).lower()
            raw_path = item.get("raw_path") or item.get("output_path")
            if not raw_path or not SHA256_PATTERN.fullmatch(expected):
                continue
            if "databento" not in str(raw_path).lower():
                continue
            path = _data_path(str(raw_path), root)
            key = str(path.resolve()).lower()
            try:
                source_report = report_path.relative_to(PROJECT_ROOT).as_posix()
            except ValueError:
                source_report = str(report_path)
            candidate = {
                "path": str(path),
                "sha256": expected,
                "source_report": source_report,
            }
            previous = found.get(key)
            if previous and previous["sha256"] != expected:
                candidate["conflict"] = previous["sha256"]
            found[key] = candidate
    return list(found.values())


def _backfill_canonical_hashes(supplemental_registry_path: Path, root: Path) -> dict[str, int]:
    existing_rows = _jsonl(supplemental_registry_path) if supplemental_registry_path.exists() else []
    existing_by_path = {str(row["path"]): row for row in existing_rows}
    raw_paths = sorted((root / "raw").rglob("*.dbn.zst"))
    for path in raw_paths:
        relative = path.relative_to(root).as_posix()
        row = existing_by_path.setdefault(
            relative,
            {
                "record_type": "paid_artifact_checksum",
                "schema_version": "paid-artifact-checksum-v2",
                "provider": "Databento",
                "path": relative,
                "sha256": sha256_file(path),
                "source_report": "local_raw_tree_canonical_backfill",
            },
        )
        canonical = dbn_record_body_hashes(path)
        row["schema_version"] = "paid-artifact-checksum-v2"
        row["canonical_content_sha256"] = canonical["sha256"]
        row["canonical_content_bytes"] = canonical["bytes"]
        row["canonical_content_format"] = "dbn_record_body_after_metadata_v1"

    supplemental_registry_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [existing_by_path[key] for key in sorted(existing_by_path)]
    supplemental_registry_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return {"canonical_backfilled": len(raw_paths), "supplemental_registry_count": len(rows)}


def verify_data_integrity(
    registry_path: Path,
    report_root: Path,
    root: Path,
    *,
    verify_hashes: bool = True,
    supplemental_registry_path: Path | None = None,
    write_supplemental_registry: bool = False,
    backfill_canonical_hashes: bool = False,
) -> dict[str, Any]:
    rows = _jsonl(registry_path)
    paid_rows = [
        row
        for row in rows
        if str(row.get("provider", "")).lower() in {"databento", "interactive brokers"}
    ]
    latest_index_by_source: dict[str, int] = {}
    for index, row in enumerate(paid_rows):
        source = _data_path(str(row.get("source_url", "")), root)
        latest_index_by_source[str(source.resolve()).lower()] = index

    registry_checks = []
    for index, row in enumerate(paid_rows):
        source = _data_path(str(row.get("source_url", "")), root)
        source_key = str(source.resolve()).lower()
        latest_index = latest_index_by_source[source_key]
        if index != latest_index:
            registry_checks.append(
                {
                    "dataset_id": row.get("dataset_id"),
                    "source_path": str(source),
                    "expected_sha256": str(row.get("raw_sha256", "")).lower(),
                    "exists": source.exists(),
                    "hash_valid": bool(
                        SHA256_PATTERN.fullmatch(str(row.get("raw_sha256", "")).lower())
                    ),
                    "status": "superseded",
                    "superseded_by": paid_rows[latest_index].get("dataset_id"),
                }
            )
            continue
        registry_checks.append(_registry_check(row, root, verify_hashes))
    registry_sources = [Path(item["source_path"]) for item in registry_checks]

    artifacts = _download_report_artifacts(report_root, root)
    if write_supplemental_registry:
        if supplemental_registry_path is None:
            raise ValueError("supplemental_registry_path is required for backfill")
        supplemental_registry_path.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            {
                "record_type": "paid_artifact_checksum",
                "schema_version": "paid-artifact-checksum-v1",
                "provider": "Databento",
                "path": Path(item["path"]).relative_to(root).as_posix(),
                "sha256": item["sha256"],
                "source_report": item["source_report"],
            }
            for item in sorted(artifacts, key=lambda item: item["path"].lower())
        ]
        supplemental_registry_path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )

    canonical_backfill = None
    if write_supplemental_registry or backfill_canonical_hashes:
        if supplemental_registry_path is None:
            raise ValueError("supplemental_registry_path is required for canonical backfill")
        canonical_backfill = _backfill_canonical_hashes(supplemental_registry_path, root)

    supplemental_rows = (
        _jsonl(supplemental_registry_path)
        if supplemental_registry_path is not None and supplemental_registry_path.exists()
        else []
    )
    supplemental_by_path = {
        str((root / str(row["path"])).resolve()).lower(): row for row in supplemental_rows
    }
    uncovered: list[dict[str, str]] = []
    for artifact in artifacts:
        path = Path(artifact["path"])
        covered = (
            any(path == source or source in path.parents for source in registry_sources)
            or str(path.resolve()).lower() in supplemental_by_path
        )
        if not covered:
            uncovered.append(artifact)

    blockers = [
        f"registry_check_failed:{item['dataset_id']}:{item['status']}"
        for item in registry_checks
        if item["status"] not in {"pass", "inventory_only", "superseded"}
    ]
    blockers.extend(f"download_artifact_not_in_dataset_registry:{item['path']}" for item in uncovered)
    supplemental_checks: list[dict[str, Any]] = []
    if verify_hashes:
        for key, row in supplemental_by_path.items():
            path = root / str(row["path"])
            expected = str(row.get("sha256", "")).lower()
            canonical_expected = str(row.get("canonical_content_sha256", "")).lower()
            canonical_path_raw = row.get("canonical_path")
            canonical = None
            if not path.exists():
                status = "missing"
                actual = None
            else:
                actual = sha256_file(path)
                if canonical_expected:
                    if canonical_path_raw:
                        canonical_path = root / str(canonical_path_raw)
                        canonical = {
                            "sha256": sha256_file(canonical_path) if canonical_path.exists() else None,
                            "path": str(canonical_path),
                        }
                    else:
                        canonical = dbn_record_body_hashes(path)
                canonical_matches = canonical is None or canonical["sha256"] == canonical_expected
                if actual == expected and canonical_matches:
                    status = "pass"
                elif canonical_expected and canonical_matches:
                    status = "content_verified_envelope_variance"
                else:
                    status = "sha256_mismatch"
            check = {
                "path": str(path),
                "expected_sha256": expected,
                "actual_sha256": actual,
                "status": status,
            }
            if canonical is not None:
                check["expected_canonical_content_sha256"] = canonical_expected
                check["actual_canonical_content_sha256"] = canonical["sha256"]
            supplemental_checks.append(check)
            if status not in {"pass", "content_verified_envelope_variance"}:
                blockers.append(f"supplemental_check_failed:{key}:{status}")
    return {
        "status": "pass" if not blockers else "blocked",
        "verify_hashes": verify_hashes,
        "data_root": str(root),
        "registry_path": str(registry_path),
        "registered_paid_dataset_count": len(paid_rows),
        "download_report_artifact_count": len(artifacts),
        "uncovered_download_artifact_count": len(uncovered),
        "supplemental_registry_path": (
            str(supplemental_registry_path) if supplemental_registry_path is not None else None
        ),
        "supplemental_registry_count": len(supplemental_rows),
        "registry_checks": registry_checks,
        "supplemental_checks": supplemental_checks,
        "canonical_backfill": canonical_backfill,
        "uncovered_download_artifacts": uncovered,
        "blockers": blockers,
        "interpreter": interpreter_metadata(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify paid Databento artifacts against registry hashes.")
    parser.add_argument(
        "--registry",
        type=Path,
        default=data_root() / "registry" / "datasets.jsonl",
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=PROJECT_ROOT / "reports" / "data_cost",
    )
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument(
        "--supplemental-registry",
        type=Path,
        default=data_root() / "registry" / "paid_artifact_checksums.jsonl",
    )
    parser.add_argument("--write-supplemental-registry", action="store_true")
    parser.add_argument("--backfill-canonical-hashes", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = verify_data_integrity(
        args.registry,
        args.report_root,
        data_root(),
        verify_hashes=not args.inventory_only,
        supplemental_registry_path=args.supplemental_registry,
        write_supplemental_registry=args.write_supplemental_registry,
        backfill_canonical_hashes=args.backfill_canonical_hashes,
    )
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
