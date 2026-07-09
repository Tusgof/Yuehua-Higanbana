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
    / "databento_download_result_h_a2_independent_validation_2025_04_08.json"
)
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_independent_validation_paid_download_decision.json"


def validate_h_a2_independent_validation_download_result(
    result_path: Path = DEFAULT_RESULT_PATH,
    decision_path: Path = DEFAULT_DECISION_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    result = _load_json(result_path)
    decision = _load_json(decision_path)

    if result.get("schema_version") != "h_a2_independent_validation_download_result_v1":
        blockers.append("unsupported_schema_version")
    if result.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if result.get("status") != "pass":
        blockers.append("status_must_be_pass")
    if result.get("mode") != "download_complete":
        blockers.append("mode_must_be_download_complete")
    if result.get("download_performed") is not True:
        blockers.append("download_performed_must_be_true")
    if result.get("scenario") != "h_a2_independent_validation_2025_04_08":
        blockers.append("scenario_mismatch")
    if result.get("request_count") != 15:
        blockers.append("request_count_must_be_15")
    if _round6(result.get("total_estimated_cost_usd")) != 0.504662:
        blockers.append("total_estimated_cost_mismatch")
    if result.get("source_decision") != "experiments\\h_a2_independent_validation_paid_download_decision.json":
        blockers.append("source_decision_mismatch")
    if result.get("source_cost_report") != "reports\\data_cost\\h_a2_independent_validation_paid_cost_estimate.json":
        blockers.append("source_cost_report_mismatch")

    if decision.get("decision") != result.get("download_decision"):
        blockers.append("download_decision_must_match_source_decision")

    selected_batch = result.get("selected_batch", {})
    if selected_batch.get("batch_id") != "sample_cost_probe_high_vix_one_day":
        blockers.append("selected_batch_must_be_sample_cost_probe")
    if selected_batch.get("dates") != ["2025-04-08"]:
        blockers.append("selected_dates_must_be_2025_04_08_only")

    locked = result.get("locked_signal_under_validation", {})
    if locked.get("candidate_decision_time_et") != "09:35:00":
        blockers.append("candidate_decision_time_must_remain_0935")
    if locked.get("entry_time_et") != "09:35:00":
        blockers.append("entry_time_must_remain_0935")
    if _round6(locked.get("opening_followthrough_threshold")) != 0.001:
        blockers.append("threshold_must_remain_0_001")
    for field in [
        "threshold_search_allowed",
        "oos_tuning_allowed",
        "new_oos_selected_filter_allowed",
        "fifteen_minute_conflict_component_allowed",
        "delayed_entry_component_allowed",
    ]:
        if locked.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    execution = result.get("execution", {})
    downloads = execution.get("downloads", [])
    if execution.get("downloaded_count") + execution.get("cache_count") != 15:
        blockers.append("download_or_cache_count_must_total_15")
    if execution.get("errors") != []:
        blockers.append("execution_errors_must_be_empty")
    if not isinstance(execution.get("total_bytes"), int) or execution["total_bytes"] <= 0:
        blockers.append("total_bytes_must_be_positive")
    if len(downloads) != 15:
        blockers.append("downloads_length_must_be_15")

    field_groups = {item.get("field_group") for item in downloads if isinstance(item, dict)}
    if "option_entry_quote" not in field_groups:
        blockers.append("missing_option_entry_quote_download")
    if "option_exit_quotes" not in field_groups:
        blockers.append("missing_option_exit_quotes_downloads")
    if "spy_underlying_bars" not in field_groups:
        blockers.append("missing_spy_underlying_bars_download")

    for index, item in enumerate(downloads):
        if not isinstance(item, dict):
            blockers.append(f"download_{index}_must_be_object")
            continue
        raw_path = Path(str(item.get("raw_path", "")))
        if not raw_path.exists():
            blockers.append(f"download_{index}_raw_path_missing")
        if not isinstance(item.get("bytes"), int) or item["bytes"] <= 0:
            blockers.append(f"download_{index}_bytes_must_be_positive")
        if not item.get("sha256"):
            blockers.append(f"download_{index}_sha256_required")
        if item.get("date") != "2025-04-08":
            blockers.append(f"download_{index}_date_must_be_2025_04_08")

    allowed_claims = "\n".join(result.get("allowed_claims", []))
    if "does not validate H-A2 edge" not in allowed_claims:
        blockers.append("allowed_claims_must_preserve_no_edge_validation")
    forbidden_claims = "\n".join(result.get("forbidden_claims", []))
    for phrase in [
        "Do not claim H-A2 edge is validated.",
        "Do not claim E2 acceptance-grade evidence.",
        "Do not approve paper trading.",
        "Do not run exact replay directly from this download result.",
        "Do not change threshold 0.001 or add an OOS-selected filter.",
    ]:
        if phrase not in forbidden_claims:
            blockers.append(f"missing_forbidden_claim:{phrase}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "result_path": _relative(result_path),
        "scenario": result.get("scenario"),
        "request_count": result.get("request_count"),
        "total_bytes": execution.get("total_bytes"),
        "total_estimated_cost_usd": result.get("total_estimated_cost_usd"),
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the H-A2 independent-validation one-day download result.")
    parser.add_argument("--result-path", type=Path, default=DEFAULT_RESULT_PATH)
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_independent_validation_download_result(args.result_path, args.decision_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
