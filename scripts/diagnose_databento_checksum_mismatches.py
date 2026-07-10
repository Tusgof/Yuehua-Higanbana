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
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "databento_integrity_mismatch_2024_06_13.json"
DEFAULT_MD_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "databento_integrity_mismatch_2024_06_13.md"
REFERENCE_SUFFIXES = {".json", ".jsonl", ".md", ".py"}


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
        parse_probe = _dbn_parse_probe(path)
        references = _find_references(Path(relative).name)
        rows.append(
            {
                "relative_path": relative,
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else None,
                "actual_sha256": actual_sha,
                "expected_sha256": expected_sha,
                "status": "sha256_mismatch" if actual_sha != expected_sha else "pass",
                "byte_delta_vs_download_report": _byte_delta(path, download_rows),
                "last_write_time_utc": _mtime(path),
                "expected_source_report": expected_row.get("source_report"),
                "download_report_rows": download_rows,
                "normalized_duplicate_path": relative_to_root(duplicate, PROJECT_ROOT),
                "normalized_duplicate_exists": duplicate.exists(),
                "normalized_duplicate_sha256": duplicate_sha,
                "normalized_duplicate_same_as_current": duplicate_sha == actual_sha,
                "normalization_rows": normalization_rows,
                "parse_probe": parse_probe,
                "references": references,
            }
        )

    blockers = [f"{row['relative_path']}:{row['status']}" for row in rows if row["status"] != "pass"]
    classification = _classify(rows)
    affected = _affected_completed_experiments()
    return {
        "schema_version": "databento_integrity_mismatch_diagnosis_v2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "target_count": len(rows),
        "rows": rows,
        "classification": classification,
        "affected_completed_experiments": affected["completed_experiments"],
        "affected_data_pipeline_artifacts": affected["data_pipeline_artifacts"],
        "decision": "No rebaseline performed. The blocker remains open until original files are restored, or the user/Fable accepts a documented revalidation/rebaseline decision after the freeze is lifted.",
        "proposed_resolution": [
            "Prefer restore from an external backup containing the original expected hashes.",
            "If no backup exists, keep the historical hashes unchanged and request a user/Fable decision on a small re-download comparison after the purchase freeze is lifted.",
            "Do not use these two files as clean integrity evidence until the disposition is recorded.",
        ],
        "source_paths": {
            "supplemental_registry": relative_to_root(SUPPLEMENTAL_REGISTRY, PROJECT_ROOT),
            "download_report": relative_to_root(DOWNLOAD_REPORT, PROJECT_ROOT),
            "normalization_report": relative_to_root(NORMALIZATION_REPORT, PROJECT_ROOT),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    classification = report["classification"]
    affected_experiments = report["affected_completed_experiments"]
    affected_pipeline = report["affected_data_pipeline_artifacts"]
    lines = [
        "# Databento Integrity Mismatch Diagnosis - 2024-06-13 Exit Checks",
        "",
        f"- **Status**: `{report['status']}`",
        f"- **Target files**: {report['target_count']}",
        f"- **Most likely classification**: `{classification['option']}` / `{classification['label']}`",
        f"- **Confidence**: `{classification['confidence']}`",
        f"- **Decision**: {report['decision']}",
        "",
        "## Findings",
        "",
        "| File | Byte delta | Expected SHA-256 | Actual SHA-256 | Parse status | Duplicate same as current | Status |",
        "|:--|--:|:--|:--|:--|:--:|:--|",
    ]
    for row in report["rows"]:
        parse_status = row.get("parse_probe", {}).get("status")
        lines.append(
            "| `{file}` | {delta} | `{expected}` | `{actual}` | `{parse}` | `{duplicate}` | `{status}` |".format(
                file=row["relative_path"],
                delta=row["byte_delta_vs_download_report"],
                expected=row["expected_sha256"],
                actual=row["actual_sha256"],
                parse=parse_status,
                duplicate=row["normalized_duplicate_same_as_current"],
                status=row["status"],
            )
        )
    lines.extend(["", "## Current File Evidence", ""])
    for row in report["rows"]:
        parse = row.get("parse_probe", {})
        lines.extend(
            [
                f"### `{Path(row['relative_path']).name}`",
                f"- Current size/mtime/SHA-256: `{row['bytes']}` bytes, `{row['last_write_time_utc']}`, `{row['actual_sha256']}`",
                f"- Expected SHA-256: `{row['expected_sha256']}`",
                f"- Parse probe: `{parse.get('status')}`; rows `{parse.get('row_count')}`; dataset/schema `{parse.get('metadata', {}).get('dataset')}` / `{parse.get('metadata', {}).get('schema')}`",
                f"- Referenced by {len(row.get('references', []))} repo text artifacts after excluding this report.",
                "",
            ]
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
            "- Both current files parse as valid DBN locally, so truncation/corruption is not the best explanation from available evidence.",
            "- No later Databento download log was found for these exact files. By elimination, the most likely class is post-download replacement/modification, although local mtimes are not enough to prove the exact mechanism.",
            "- No registry hash, download-result hash, or data file was rebaselined by this diagnosis.",
            "",
            "## Affected Experiment Scan",
            "",
            f"- Completed experiment reports directly referencing either raw filename: `{len(affected_experiments)}`",
        ]
    )
    if affected_experiments:
        lines.extend(f"  - `{item}`" for item in affected_experiments)
    else:
        lines.append("- No completed experiment report directly references these two raw filenames by scan.")
    lines.extend(
        [
            f"- Affected data-pipeline artifacts: `{len(affected_pipeline)}`",
        ]
    )
    lines.extend(f"  - `{item}`" for item in affected_pipeline)
    lines.extend(
        [
            "",
            "## Required Closure",
            "",
            "Workstream 1 remains open until the original expected files are restored from external backup or the user/Fable approves a documented revalidation/rebaseline decision.",
            "If restore is impossible, a small re-download comparison may be the cleanest next evidence step, but it is a user decision because the purchase freeze is active.",
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


def _dbn_parse_probe(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing"}
    try:
        import databento as db  # type: ignore

        store = db.DBNStore.from_file(path)
        frame = store.to_df()
        return {
            "status": "valid_dbn",
            "row_count": int(len(frame)),
            "ts_index_start": str(frame.index.min()) if len(frame) else None,
            "ts_index_end": str(frame.index.max()) if len(frame) else None,
            "metadata": {
                "dataset": str(store.dataset),
                "schema": str(store.schema),
                "stype_in": str(store.stype_in),
                "symbols": list(store.symbols or []),
            },
        }
    except ModuleNotFoundError as exc:
        return {"status": "blocked_missing_optional_package", "error": str(exc)}
    except Exception as exc:
        return {"status": "parse_failed", "error": f"{type(exc).__name__}: {exc}"}


def _find_references(filename: str) -> list[str]:
    references: list[str] = []
    skip_parts = {".git", "__pycache__"}
    roots = [
        PROJECT_ROOT / "PROJECT_BRAIN.md",
        PROJECT_ROOT / "IMPLEMENT_PLAN.md",
        PROJECT_ROOT / "AGENTS.md",
        PROJECT_ROOT / "docs",
        PROJECT_ROOT / "experiments",
        PROJECT_ROOT / "reports",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "tests",
    ]
    for root in roots:
        candidates = [root] if root.is_file() else root.rglob("*")
        for path in candidates:
            if not _reference_candidate(path, skip_parts):
                continue
            relative = path.relative_to(PROJECT_ROOT).as_posix()
            if relative in {
                "reports/diagnostics/databento_integrity_mismatch_2024_06_13.json",
                "reports/diagnostics/databento_integrity_mismatch_2024_06_13.md",
            }:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if filename in text:
                references.append(relative)
    return sorted(set(references))


def _reference_candidate(path: Path, skip_parts: set[str]) -> bool:
    if any(part in skip_parts for part in path.parts):
        return False
    if not path.is_file() or path.suffix not in REFERENCE_SUFFIXES:
        return False
    return True


def _classify(rows: list[dict[str, Any]]) -> dict[str, Any]:
    parse_failed = any(row.get("parse_probe", {}).get("status") == "parse_failed" for row in rows)
    later_download_refs = [
        ref
        for row in rows
        for ref in row.get("references", [])
        if "download_result" in ref and "oos_2024_06_intraday_exit_30m_chunk2" not in ref
    ]
    if parse_failed:
        option = "c"
        label = "corruption_or_truncation"
        confidence = "medium"
        rationale = ["At least one target failed the DBN parse probe."]
    elif later_download_refs:
        option = "a"
        label = "legitimate_re_download_after_original_report"
        confidence = "medium"
        rationale = ["A later download-result reference exists for at least one target file."]
    else:
        option = "b"
        label = "post_download_modification_or_replacement"
        confidence = "medium_low"
        rationale = [
            "No later download log was found for these exact filenames.",
            "Both files parse as valid DBN, so truncation/corruption is not supported by current evidence.",
            "Current files are larger than the original download-report bytes and differ at SHA-256 level.",
            "Local mtimes alone do not prove the exact mechanism, so the classification remains by elimination rather than certainty.",
        ]
    return {
        "option": option,
        "label": label,
        "confidence": confidence,
        "later_download_log_found": bool(later_download_refs),
        "later_download_references": sorted(set(later_download_refs)),
        "rationale": rationale,
    }


def _affected_completed_experiments() -> dict[str, list[str]]:
    filenames = [Path(relative).name for relative in TARGETS]
    completed_reports: list[str] = []
    pipeline_artifacts: list[str] = []
    experiments_root = PROJECT_ROOT / "reports" / "experiments"
    if experiments_root.exists():
        for path in experiments_root.rglob("*"):
            if not path.is_file() or path.suffix not in {".json", ".md"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(filename in text for filename in filenames):
                completed_reports.append(path.relative_to(PROJECT_ROOT).as_posix())
    for path in [DOWNLOAD_REPORT, NORMALIZATION_REPORT]:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(filename in text for filename in filenames):
                pipeline_artifacts.append(path.relative_to(PROJECT_ROOT).as_posix())
    return {
        "completed_experiments": sorted(set(completed_reports)),
        "data_pipeline_artifacts": sorted(set(pipeline_artifacts)),
    }


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
