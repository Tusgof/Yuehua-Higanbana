from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREG_PATH = (
    PROJECT_ROOT / "experiments" / "h_a2_independent_validation_import_diagnostic_preregistration.json"
)


def validate_h_a2_independent_validation_import_diagnostic_preregistration(
    prereg_path: Path = DEFAULT_PREREG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != "h_a2_independent_validation_import_diagnostic_preregistration_v1":
        blockers.append("unsupported_schema_version")
    if prereg.get("artifact_type") != "preregistration":
        blockers.append("artifact_type_must_be_preregistration")
    if prereg.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if prereg.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if prereg.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if prereg.get("experiment_id") != "h_a2_independent_validation_import_diagnostic":
        blockers.append("experiment_id_must_match")
    if (
        prereg.get("source_download_result")
        != "reports/data_cost/databento_download_result_h_a2_independent_validation_2025_04_08.json"
    ):
        blockers.append("source_download_result_mismatch")

    _validate_source_download(prereg, blockers)
    _validate_target_sample(prereg, blockers)
    _validate_locked_signal(prereg, blockers)
    _validate_inputs(prereg, blockers)
    _validate_planned_steps(prereg, blockers)
    _validate_claims_and_guardrails(prereg, blockers)

    target = prereg.get("target_sample", {})
    guardrails = prereg.get("guardrails", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "prereg_path": _relative(prereg_path),
        "hypothesis_id": prereg.get("hypothesis_id"),
        "evidence_tier": prereg.get("evidence_tier"),
        "experiment_id": prereg.get("experiment_id"),
        "target_date": target.get("date"),
        "expected_request_count": target.get("expected_request_count"),
        "local_raw_dbn_parse_allowed_after_preregistration": guardrails.get(
            "local_raw_dbn_parse_allowed_after_preregistration"
        ),
        "network_allowed": guardrails.get("network_allowed"),
        "paid_data_allowed": guardrails.get("paid_data_allowed"),
        "exact_replay_allowed": guardrails.get("exact_replay_allowed"),
        "paper_trading_allowed": guardrails.get("paper_trading_allowed"),
    }


def _validate_source_download(prereg: dict[str, Any], blockers: list[str]) -> None:
    source = PROJECT_ROOT / prereg.get("source_download_result", "")
    if not source.exists():
        blockers.append("source_download_result_missing")
        return
    result = _load_json(source)
    if result.get("schema_version") != "h_a2_independent_validation_download_result_v1":
        blockers.append("source_download_result_schema_mismatch")
    if result.get("status") != "pass":
        blockers.append("source_download_result_must_pass")
    if result.get("mode") != "download_complete":
        blockers.append("source_download_result_must_be_download_complete")
    if result.get("download_performed") is not True:
        blockers.append("source_download_performed_must_be_true")
    if result.get("scenario") != "h_a2_independent_validation_2025_04_08":
        blockers.append("source_download_scenario_mismatch")
    if result.get("request_count") != 15:
        blockers.append("source_request_count_must_be_15")
    if result.get("execution", {}).get("total_bytes") != 54014593:
        blockers.append("source_total_bytes_must_match_h_a2_40")


def _validate_target_sample(prereg: dict[str, Any], blockers: list[str]) -> None:
    target = prereg.get("target_sample", {})
    if target.get("batch_id") != "sample_cost_probe_high_vix_one_day":
        blockers.append("target_batch_id_must_be_sample_cost_probe")
    if target.get("date") != "2025-04-08":
        blockers.append("target_date_must_be_2025_04_08")
    if target.get("scenario") != "h_a2_independent_validation_2025_04_08":
        blockers.append("target_scenario_mismatch")
    if target.get("vix_bucket") != "vix_above_25":
        blockers.append("target_vix_bucket_must_be_high_vix")
    if _round6(target.get("vix_close")) != 52.33:
        blockers.append("target_vix_close_must_be_52_33")
    if target.get("expected_request_count") != 15:
        blockers.append("expected_request_count_must_be_15")
    if target.get("expected_total_bytes") != 54014593:
        blockers.append("expected_total_bytes_must_match_h_a2_40")
    raw_root = PROJECT_ROOT / target.get("raw_root", "")
    if not raw_root.exists() or not raw_root.is_dir():
        blockers.append("target_raw_root_missing")
    elif len(list(raw_root.glob("*.dbn.zst"))) != 15:
        blockers.append("target_raw_root_must_contain_15_dbn_zst_files")


def _validate_locked_signal(prereg: dict[str, Any], blockers: list[str]) -> None:
    signal = prereg.get("locked_signal_under_validation", {})
    if signal.get("candidate_decision_time_et") != "09:35:00":
        blockers.append("candidate_decision_time_must_be_0935")
    if signal.get("entry_time_et") != "09:35:00":
        blockers.append("entry_time_must_be_0935")
    if signal.get("features") != ["clean_macro_vix_condition", "proxy_5m_followthrough"]:
        blockers.append("features_must_match_locked_original_entry_signal")
    if _round6(signal.get("opening_followthrough_threshold")) != 0.001:
        blockers.append("locked_threshold_must_be_0_001")
    if signal.get("threshold_must_remain_locked") is not True:
        blockers.append("threshold_must_remain_locked_must_be_true")
    for field in [
        "threshold_search_allowed",
        "oos_tuning_allowed",
        "new_oos_selected_filter_allowed",
        "fifteen_minute_conflict_component_allowed",
        "delayed_entry_component_allowed",
    ]:
        if signal.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_inputs(prereg: dict[str, Any], blockers: list[str]) -> None:
    for item in prereg.get("allowed_inputs", []):
        path = item.get("path")
        if not path:
            blockers.append(f"allowed_input_missing_path:{item.get('input')}")
            continue
        if not (PROJECT_ROOT / path).exists():
            blockers.append(f"allowed_input_path_missing:{item.get('input')}")

    forbidden_inputs = {item.get("input") for item in prereg.get("forbidden_inputs", [])}
    for required in [
        "additional_databento_download",
        "new_paid_provider",
        "ibkr_historical_bars",
        "live_llm_outputs",
        "gdelt_live_retry",
        "new_oos_selected_filter",
    ]:
        if required not in forbidden_inputs:
            blockers.append(f"missing_forbidden_input:{required}")


def _validate_planned_steps(prereg: dict[str, Any], blockers: list[str]) -> None:
    step_ids = [step.get("step_id") for step in prereg.get("planned_steps", [])]
    required_order = [
        "raw_file_inventory",
        "spy_underlying_import",
        "opra_quote_import",
        "timestamp_alignment_check",
        "candidate_signal_reconstruction",
        "entry_exit_quote_availability",
        "diagnostic_report",
    ]
    if step_ids != required_order:
        blockers.append("planned_steps_must_follow_required_order")
    for step in prereg.get("planned_steps", []):
        if not step.get("description"):
            blockers.append(f"planned_step_missing_description:{step.get('step_id')}")
        if not step.get("verification"):
            blockers.append(f"planned_step_missing_verification:{step.get('step_id')}")

    outputs = prereg.get("planned_outputs", {})
    for key in ["future_summary_json", "future_summary_md", "future_search_log", "future_normalized_root"]:
        if not outputs.get(key):
            blockers.append(f"missing_planned_output:{key}")


def _validate_claims_and_guardrails(prereg: dict[str, Any], blockers: list[str]) -> None:
    allowed = "\n".join(prereg.get("allowed_claims", []))
    for phrase in ["pre-registered", "already-downloaded raw DBN", "quote availability", "09:35-only", "0.001"]:
        if phrase not in allowed:
            blockers.append(f"missing_allowed_claim_phrase:{phrase}")

    forbidden = "\n".join(prereg.get("forbidden_claims", []))
    for phrase in [
        "edge is validated",
        "E2",
        "paper trading",
        "exact replay",
        "strategy PnL",
        "download more validation packs",
        "IBKR",
        "LLMs",
        "GDELT",
        "0.001",
        "OOS-selected",
        "import diagnostics",
    ]:
        if phrase not in forbidden:
            blockers.append(f"missing_forbidden_claim_phrase:{phrase}")

    guardrails = prereg.get("guardrails", {})
    for field in [
        "network_allowed",
        "paid_data_allowed",
        "additional_download_allowed",
        "new_provider_allowed",
        "broker_request_allowed",
        "ibkr_request_allowed",
        "gdelt_live_retry_allowed",
        "llm_call_allowed",
        "exact_replay_allowed",
        "strategy_pnl_acceptance_allowed",
        "threshold_search_allowed",
        "new_filter_allowed",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "research_log_required_for_this_preregistration",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    for field in ["local_raw_dbn_parse_allowed_after_preregistration", "normalization_diagnostic_allowed_after_preregistration"]:
        if guardrails.get(field) is not True:
            blockers.append(f"{field}_must_be_true")

    completion = "\n".join(prereg.get("completion_criteria", []))
    for phrase in ["2025-04-08", "SPY bar import", "OPRA quote import", "09:35-only", "0.001", "validator passes"]:
        if phrase not in completion:
            blockers.append(f"missing_completion_criterion_phrase:{phrase}")


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
    parser = argparse.ArgumentParser(
        description="Validate H-A2 independent-validation import diagnostic preregistration."
    )
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_independent_validation_import_diagnostic_preregistration(args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
