from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import data_root, interpreter_metadata
from lib.integrity import sha256_file


DATA_ROOT = data_root()
ORIGINAL_DOWNLOAD_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_oos_2024_06_intraday_exit_30m_chunk2.json"
COST_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "databento_integrity_redownload_cost_2024_06_13.json"
DOWNLOAD_RESULT = PROJECT_ROOT / "reports" / "data_cost" / "databento_integrity_redownload_download_result_2024_06_13.json"
DIAGNOSTIC_JSON = PROJECT_ROOT / "reports" / "diagnostics" / "databento_integrity_mismatch_2024_06_13.json"
DIAGNOSTIC_MD = PROJECT_ROOT / "reports" / "diagnostics" / "databento_integrity_mismatch_2024_06_13.md"
SUPPLEMENTAL_REGISTRY = DATA_ROOT / "registry" / "paid_artifact_checksums.jsonl"
TARGETS = (
    "raw/spy_0dte/databento/oos_2024_06_intraday_exit_30m_chunk2/2024-06-13_exit_check_1430.dbn.zst",
    "raw/spy_0dte/databento/oos_2024_06_intraday_exit_30m_chunk2/2024-06-13_exit_check_1500.dbn.zst",
)


def classify(fresh_sha256: str | None, historical_sha256: str | None, current_sha256: str | None) -> tuple[str, str]:
    if fresh_sha256 and fresh_sha256 == historical_sha256:
        return "case_1", "restored_from_provider"
    if fresh_sha256 and fresh_sha256 == current_sha256:
        return "case_2", "provider_revision_accepted"
    return "case_3", "escalated_unexplained"


def resolve() -> dict[str, Any]:
    original = _read_json(ORIGINAL_DOWNLOAD_REPORT)
    cost = _read_json(COST_REPORT)
    download = _read_json(DOWNLOAD_RESULT)
    original_by_window = {str(item["window"]): item for item in original["downloaded"]}
    fresh_by_window = {str(item["window"]): item for item in download["downloaded"]}
    rows: list[dict[str, Any]] = []

    for relative in TARGETS:
        window = Path(relative).stem.removesuffix(".dbn")
        historical = original_by_window[window]
        fresh = fresh_by_window[window]
        current_path = DATA_ROOT / relative
        fresh_path = Path(fresh["output_path"])
        current_before = _snapshot(current_path)
        fresh_snapshot = _snapshot(fresh_path)
        case, disposition = classify(
            fresh_snapshot["sha256"],
            str(historical["sha256"]),
            current_before["sha256"],
        )
        row: dict[str, Any] = {
            "window": window,
            "relative_path": relative,
            "case": case,
            "disposition": disposition,
            "historical": {
                "availability": "not_available_no_original_backup",
                "bytes": historical["bytes"],
                "sha256": historical["sha256"],
                "parse_probe": {"status": "not_available_no_original_backup"},
            },
            "current_before": current_before,
            "fresh_quarantine": fresh_snapshot,
        }
        if case == "case_1":
            shutil.copy2(fresh_path, current_path)
            row["current_after"] = _snapshot(current_path)
            row["replacement"] = "current_file_replaced_with_fresh_provider_copy;_quarantine_retained"
        elif case == "case_2":
            _append_provider_revision(relative, fresh_snapshot["sha256"], str(historical["sha256"]))
            row["current_after"] = _snapshot(current_path)
            row["registry_append"] = "superseded_by_provider_revision"
        else:
            row["current_after"] = current_before
        rows.append(row)

    unresolved = [row["relative_path"] for row in rows if row["case"] == "case_3"]
    status = "blocked" if unresolved else "resolved"
    comparison = {
        "id": "databento_integrity_redownload_comparison_2024_06_13",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "authorization": cost["authorization"],
        "cost": {
            "estimated_cost_usd": cost["total_estimated_cost_usd"],
            "actual_charge_usd": cost["total_estimated_cost_usd"],
            "actual_charge_basis": "Databento metadata.get_cost quote immediately before both completed downloads; account-usage receipt API is unavailable for independent reconciliation.",
            "selected_api_key_env": cost["selected_api_key_env"],
        },
        "rows": rows,
        "unresolved_files": unresolved,
        "interpreter": interpreter_metadata(),
    }
    _write_cost_record(cost, comparison)
    _append_diagnostic(comparison)
    return comparison


def _snapshot(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": _relative(path), "exists": path.exists()}
    if not path.exists():
        result.update({"bytes": None, "sha256": None, "parse_probe": {"status": "missing"}})
        return result
    result["bytes"] = path.stat().st_size
    result["sha256"] = sha256_file(path)
    result["parse_probe"] = _parse_probe(path)
    return result


def _parse_probe(path: Path) -> dict[str, Any]:
    try:
        import databento as db  # type: ignore

        store = db.DBNStore.from_file(path)
        frame = store.to_df()
        return {
            "status": "valid_dbn",
            "row_count": int(len(frame)),
            "ts_index_start": str(frame.index.min()) if len(frame) else None,
            "ts_index_end": str(frame.index.max()) if len(frame) else None,
            "dataset": str(store.dataset),
            "schema": str(store.schema),
        }
    except Exception as exc:
        return {"status": "parse_failed", "error": f"{type(exc).__name__}: {exc}"}


def _append_provider_revision(relative: str, fresh_sha256: str, historical_sha256: str) -> None:
    entry = {
        "record_type": "paid_artifact_checksum",
        "schema_version": "paid-artifact-checksum-v1",
        "provider": "Databento",
        "path": relative,
        "sha256": fresh_sha256,
        "source_report": _relative(DIAGNOSTIC_JSON),
        "status": "superseded_by_provider_revision",
        "supersedes_sha256": historical_sha256,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    existing = SUPPLEMENTAL_REGISTRY.read_text(encoding="utf-8-sig") if SUPPLEMENTAL_REGISTRY.exists() else ""
    if json.dumps(entry, sort_keys=True) in {json.dumps(json.loads(line), sort_keys=True) for line in existing.splitlines() if line.strip()}:
        return
    with SUPPLEMENTAL_REGISTRY.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def _write_cost_record(cost: dict[str, Any], comparison: dict[str, Any]) -> None:
    cost["download_execution"] = {
        "completed_at_utc": comparison["completed_at_utc"],
        "status": comparison["status"],
        "download_result": _relative(DOWNLOAD_RESULT),
        "actual_charge_usd": comparison["cost"]["actual_charge_usd"],
        "actual_charge_basis": comparison["cost"]["actual_charge_basis"],
    }
    COST_REPORT.write_text(json.dumps(cost, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Databento Integrity Re-download Cost - 2024-06-13",
        "",
        "- Scope: exactly two user-approved integrity-comparison windows.",
        f"- Cost gate: `${cost['total_estimated_cost_usd']}` estimated against a `${cost['authorization']['hard_cap_usd']}` cap.",
        f"- Recorded charge: `${comparison['cost']['actual_charge_usd']}`.",
        f"- Charge basis: {comparison['cost']['actual_charge_basis']}",
        f"- Result: `{comparison['status']}`.",
        "",
    ]
    COST_REPORT.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")


def _append_diagnostic(comparison: dict[str, Any]) -> None:
    report = _read_json(DIAGNOSTIC_JSON)
    addenda = [item for item in report.get("addenda", []) if item.get("id") != comparison["id"]]
    addenda.append(comparison)
    report["addenda"] = addenda
    report["status"] = comparison["status"]
    report["blockers"] = comparison["unresolved_files"]
    report["decision"] = (
        "Provider re-download comparison resolved the checksum disposition; physical restore rehearsal remains required for Workstream 1 closure."
        if comparison["status"] == "resolved"
        else "Provider re-download comparison is unexplained for the listed files; retain the Workstream 1 integrity blocker for user/Fable review."
    )
    DIAGNOSTIC_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    previous = DIAGNOSTIC_MD.read_text(encoding="utf-8") if DIAGNOSTIC_MD.exists() else ""
    marker = "## Addendum: User-Approved Re-download Comparison"
    if marker in previous:
        previous = previous.split(marker, 1)[0].rstrip() + "\n\n"
    lines = [marker, "", f"- Status: `{comparison['status']}`", f"- Cost: `${comparison['cost']['actual_charge_usd']}`", ""]
    for row in comparison["rows"]:
        lines.extend(
            [
                f"### `{row['window']}`",
                f"- Case/disposition: `{row['case']}` / `{row['disposition']}`",
                f"- Historical hash: `{row['historical']['sha256']}` (raw original unavailable).",
                f"- Current-before hash: `{row['current_before']['sha256']}`; fresh hash: `{row['fresh_quarantine']['sha256']}`.",
                f"- Parse rows current/fresh: `{row['current_before']['parse_probe'].get('row_count')}` / `{row['fresh_quarantine']['parse_probe'].get('row_count')}`.",
                "",
            ]
        )
    DIAGNOSTIC_MD.write_text(previous + "\n".join(lines), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve the approved Databento integrity re-download comparison.")
    parser.parse_args()
    result = resolve()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "resolved" else 1


if __name__ == "__main__":
    raise SystemExit(main())
