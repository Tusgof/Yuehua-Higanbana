from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.integrity import sha256_file
from lib.io import load_json, relative_to_root, write_json


DATA_ROOT = PROJECT_ROOT / "data"
TARGETS = [
    "raw/spy_0dte/databento/oos_2024_06_intraday_exit_30m_chunk2/2024-06-13_exit_check_1430.dbn.zst",
    "raw/spy_0dte/databento/oos_2024_06_intraday_exit_30m_chunk2/2024-06-13_exit_check_1500.dbn.zst",
]
SUPPLEMENTAL_REGISTRY = DATA_ROOT / "registry" / "paid_artifact_checksums.jsonl"
DOWNLOAD_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_oos_2024_06_intraday_exit_30m_chunk2.json"
NORMALIZATION_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "databento_normalization_summary_2024_06.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "databento_checksum_mismatch_diagnosis_2026_07_10.json"
DEFAULT_MD_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "databento_checksum_mismatch_diagnosis_2026_07_10.md"


def diagnose_checksum_mismatches() -> dict[str, Any]:
    supplemental = _load_jsonl(SUPPLEMENTAL_REGISTRY)
    expected_by_path = {str(row.get("path")): row for row in supplemental}
    download_payload = load_json(DOWNLOAD_REPORT)
    normalization_payload = load_json(NORMALIZATION_REPORT)
    rows = []
    for relative in TARGETS:
        path = DATA_ROOT / relative
        duplicate = _normalized_duplicate_path(relative)
        expected_row = expected_by_path.get(relative, {})
        download_rows = _matching_dicts(download_payload, Path(relative).name)
        normalization_rows = _matching_dicts(normalization_payload, Path(relative).name)
        actual_sha = sha256_file(path) if path.exists() else None
        duplicate_sha = sha256_file(duplicate) if duplicate.exists() else None
        expected_sha = expected_row.get("sha256")
        rows.append(
            {
                "relative_path": relative,
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else None,
                "actual_sha256": actual_sha,
                "expected_sha256": expected_sha,
                "status": "sha256_mismatch" if actual_sha != expected_sha else "pass",
                "byte_delta_vs_download_report": _byte_delta(path, download_rows),
                "last_write_time_local": _mtime(path),
                "expected_source_report": expected_row.get("source_report"),
                "download_report_rows": download_rows,
                "normalized_duplicate_path": relative_to_root(duplicate, PROJECT_ROOT),
                "normalized_duplicate_exists": duplicate.exists(),
                "normalized_duplicate_sha256": duplicate_sha,
                "normalized_duplicate_same_as_current": duplicate_sha == actual_sha,
                "normalization_rows": normalization_rows,
            }
        )

    blockers = [f"{row['relative_path']}:{row['status']}" for row in rows if row["status"] != "pass"]
    return {
        "schema_version": "databento_checksum_mismatch_diagnosis_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "target_count": len(rows),
        "rows": rows,
        "decision": "No rebaseline performed. The blocker remains open until original files are restored or user/Fable accepts a documented revalidation/rebaseline decision.",
        "source_paths": {
            "supplemental_registry": relative_to_root(SUPPLEMENTAL_REGISTRY, PROJECT_ROOT),
            "download_report": relative_to_root(DOWNLOAD_REPORT, PROJECT_ROOT),
            "normalization_report": relative_to_root(NORMALIZATION_REPORT, PROJECT_ROOT),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Databento Checksum Mismatch Diagnosis - 2026-07-10",
        "",
        f"- **Status**: `{report['status']}`",
        f"- **Target files**: {report['target_count']}",
        f"- **Decision**: {report['decision']}",
        "",
        "## Findings",
        "",
        "| File | Expected bytes delta | Expected SHA-256 | Actual SHA-256 | Duplicate same as current | Status |",
        "|:--|--:|:--|:--|:--:|:--|",
    ]
    for row in report["rows"]:
        lines.append(
            "| `{file}` | {delta} | `{expected}` | `{actual}` | `{duplicate}` | `{status}` |".format(
                file=row["relative_path"],
                delta=row["byte_delta_vs_download_report"],
                expected=row["expected_sha256"],
                actual=row["actual_sha256"],
                duplicate=row["normalized_duplicate_same_as_current"],
                status=row["status"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The committed supplemental checksum registry and the original Databento download report agree on the expected hashes.",
            "- The current local files are larger than the recorded download artifacts and have different bit-level hashes.",
            "- The normalized `oos_2024_06` duplicate copies have the same current hashes as the mismatched files, so they are not independent backups of the expected originals.",
            "- Existing normalization evidence still shows both windows were parsed as 90,700 input rows and 2,380 0DTE output rows, but that does not clear the bit-level integrity blocker.",
            "- No registry hash, download-result hash, or data file was rebaselined by this diagnosis.",
            "",
            "## Required Closure",
            "",
            "Workstream 1 remains open until the original expected files are restored from external backup or the user/Fable approves a documented revalidation/rebaseline decision.",
            "",
        ]
    )
    return "\n".join(lines)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _matching_dicts(payload: Any, filename: str) -> list[dict[str, Any]]:
    rows = []
    for item in _walk(payload):
        if not isinstance(item, dict):
            continue
        if any(filename in str(value) for value in item.values() if not isinstance(value, (dict, list))):
            rows.append(item)
    return rows


def _normalized_duplicate_path(relative: str) -> Path:
    return DATA_ROOT / relative.replace("oos_2024_06_intraday_exit_30m_chunk2/", "oos_2024_06/")


def _byte_delta(path: Path, download_rows: list[dict[str, Any]]) -> int | None:
    if not path.exists():
        return None
    expected_bytes = next((row.get("bytes") for row in download_rows if isinstance(row.get("bytes"), int)), None)
    if expected_bytes is None:
        return None
    return path.stat().st_size - int(expected_bytes)


def _mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose the two known Databento checksum mismatches without rebaselining.")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD_OUTPUT)
    args = parser.parse_args()
    report = diagnose_checksum_mismatches()
    write_json(args.json_output, report)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
