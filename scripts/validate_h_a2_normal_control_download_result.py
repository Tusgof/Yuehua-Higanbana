from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "databento_download_result_h_a2_normal_control_low_normal_vix_control_pack.json"
)
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_normal_control_paid_download_decision.json"


def validate_h_a2_normal_control_download_result(
    result_path: Path = DEFAULT_RESULT_PATH,
    decision_path: Path = DEFAULT_DECISION_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    result = _load_json(result_path)
    decision = _load_json(decision_path)

    expected_dates = decision.get("selected_batch", {}).get("dates") or []
    downloads = (result.get("execution") or {}).get("downloads") or []

    if result.get("schema_version") != "h_a2_normal_control_download_result_v1":
        blockers.append("unsupported_schema_version")
    if result.get("status") != "pass":
        blockers.append("download_result_must_pass")
    if result.get("mode") != "download_complete":
        blockers.append("mode_must_be_download_complete")
    if result.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if result.get("scenario") != "h_a2_normal_control_low_normal_vix_control_pack":
        blockers.append("scenario_must_be_h_a2_normal_control_low_normal_vix_control_pack")
    if result.get("download_performed") is not True:
        blockers.append("download_performed_must_be_true")
    if _portable_path(result.get("source_decision")) != "experiments/h_a2_normal_control_paid_download_decision.json":
        blockers.append("source_decision_mismatch")
    if _portable_path(result.get("source_cost_report")) != "reports/data_cost/h_a2_normal_control_low_normal_vix_control_pack_cost_estimate.json":
        blockers.append("source_cost_report_mismatch")
    if result.get("download_decision") != "approve_low_normal_vix_control_pack_download_after_paid_cost_audit_pass":
        blockers.append("download_decision_must_match_h_a2_45")
    if result.get("planned_required_request_count") != 150:
        blockers.append("planned_required_request_count_must_be_150")
    if result.get("metadata_grouped_request_count") != 20 or result.get("request_count") != 20:
        blockers.append("grouped_request_count_must_be_20")
    if _round6(result.get("total_estimated_cost_usd")) != 5.398913:
        blockers.append("estimated_cost_mismatch")
    if result.get("paid_cost_audit_before_download", {}).get("status") != "pass":
        blockers.append("paid_cost_audit_before_download_must_pass")

    guard = result.get("cost_guard") or {}
    if guard.get("selected_key_env") != "DATABENTO_API_MO":
        blockers.append("selected_key_env_must_be_databento_api_mo")
    if guard.get("basis") != "selected_key_mo_ai_pool":
        blockers.append("cost_guard_basis_must_be_selected_key_mo_ai_pool")
    if float(guard.get("projected_selected_key_usage_if_downloaded_usd", 999999)) >= float(
        guard.get("selected_key_cap_usd", 0)
    ):
        blockers.append("projected_selected_key_usage_must_remain_below_cap")

    if len(downloads) != 20:
        blockers.append("download_rows_must_equal_20")
    request_dates = {row.get("date") for row in downloads}
    if request_dates != set(expected_dates):
        blockers.append("download_dates_must_match_decision")
    if any(row.get("dataset") not in {"OPRA.PILLAR", "EQUS.MINI"} for row in downloads):
        blockers.append("download_dataset_out_of_scope")
    if any(row.get("schema") not in {"cbbo-1m", "ohlcv-1m"} for row in downloads):
        blockers.append("download_schema_out_of_scope")
    if any(row.get("source") not in {"downloaded", "cache"} for row in downloads):
        blockers.append("download_source_must_be_downloaded_or_cache")
    if any(int(row.get("bytes", 0) or 0) <= 0 for row in downloads):
        blockers.append("download_file_must_be_non_empty")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "result_path": _relative(result_path),
        "scenario": result.get("scenario"),
        "request_count": result.get("request_count"),
        "downloaded_count": (result.get("execution") or {}).get("downloaded_count"),
        "cache_count": (result.get("execution") or {}).get("cache_count"),
        "total_bytes": (result.get("execution") or {}).get("total_bytes"),
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _round6(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def _portable_path(value: Any) -> str:
    return str(value or "").replace("\\", "/")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the H-A2 normal/control download result.")
    parser.add_argument("--result-path", type=Path, default=DEFAULT_RESULT_PATH)
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_normal_control_download_result(args.result_path, args.decision_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
