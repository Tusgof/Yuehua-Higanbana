from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from lib.integrity import dbn_record_body_hashes, sha256_file
from lib.io import load_jsonl, write_jsonl


def estimate_requests(
    requests: list[dict[str, Any]],
    provider: Callable[[dict[str, Any]], float],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for request in requests:
        row = dict(request)
        try:
            row["estimated_cost_usd"] = float(provider(request))
        except Exception as exc:
            row["estimated_cost_usd"] = None
            row["error"] = str(exc)
            errors.append({"window": str(request["window"]), "error": str(exc)})
        rows.append(row)
    return rows, errors


def download_requests(
    requests: list[dict[str, Any]],
    provider: Callable[[dict[str, Any]], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for request in requests:
        try:
            rows.append(provider(request))
        except Exception as exc:
            rows.append({**request, "source": "error", "error": str(exc)})
            errors.append({"window": str(request["window"]), "error": str(exc)})
    return rows, errors


def metadata_cost_provider(api_key_env: str) -> Callable[[dict[str, Any]], float]:
    api_key = _require_api_key(api_key_env)
    import databento as db  # type: ignore[import-not-found]

    client = db.Historical(api_key)

    def provider(request: dict[str, Any]) -> float:
        return float(client.metadata.get_cost(**provider_args(request)))

    return provider


def file_download_provider(api_key_env: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    api_key = _require_api_key(api_key_env)
    import databento as db  # type: ignore[import-not-found]

    client = db.Historical(api_key)

    def provider(request: dict[str, Any]) -> dict[str, Any]:
        raw_path = Path(request["raw_path"])
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        source = "cache"
        if raw_path.exists() and raw_path.stat().st_size == 0:
            raw_path.unlink()
        if not raw_path.exists():
            temp_path = raw_path.with_name(f"{raw_path.name}.download")
            if temp_path.exists():
                temp_path.unlink()
            client.timeseries.get_range(path=temp_path, **provider_args(request))
            temp_path.replace(raw_path)
            source = "downloaded"
        return {
            **request,
            "source": source,
            "bytes": raw_path.stat().st_size,
            "sha256": sha256_file(raw_path),
        }

    return provider


def append_paid_artifact_checksums(
    downloads: list[dict[str, Any]],
    *,
    data_root: Path,
    registry_path: Path,
    source_report: str,
) -> dict[str, Any]:
    existing = load_jsonl(registry_path) if registry_path.exists() else []
    by_path = {str(row["path"]): row for row in existing}
    added = 0
    for row in downloads:
        path = Path(row["raw_path"])
        relative = path.relative_to(data_root).as_posix()
        canonical = dbn_record_body_hashes(path)
        candidate = {
            "record_type": "paid_artifact_checksum",
            "schema_version": "paid-artifact-checksum-v2",
            "provider": "Databento",
            "path": relative,
            "sha256": row["sha256"],
            "canonical_content_sha256": canonical["sha256"],
            "canonical_content_bytes": canonical["bytes"],
            "canonical_content_format": "dbn_record_body_after_metadata_v1",
            "source_report": source_report,
        }
        previous = by_path.get(relative)
        if previous and (
            previous.get("sha256") != candidate["sha256"]
            or previous.get("canonical_content_sha256") != candidate["canonical_content_sha256"]
        ):
            raise RuntimeError(f"checksum registry conflict: {relative}")
        if not previous:
            by_path[relative] = candidate
            added += 1
    write_jsonl(registry_path, [by_path[key] for key in sorted(by_path)])
    return {"status": "pass", "registry_path": str(registry_path), "added_count": added}


def provider_args(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset": request["dataset"],
        "symbols": request["symbols"],
        "schema": request["schema"],
        "stype_in": request["stype_in"],
        "start": request["start"],
        "end": request["end"],
    }


def _require_api_key(api_key_env: str) -> str:
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RuntimeError(f"missing Databento API key environment variable: {api_key_env}")
    return api_key
