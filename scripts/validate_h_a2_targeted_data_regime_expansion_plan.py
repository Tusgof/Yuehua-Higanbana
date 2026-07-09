from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import expand_configured_tokens
DEFAULT_PLAN_PATH = PROJECT_ROOT / "experiments" / "h_a2_targeted_data_regime_expansion_plan.json"
DEFAULT_DOC_PATH = PROJECT_ROOT / "docs" / "H_A2_TARGETED_DATA_REGIME_EXPANSION_PLAN.md"
H_A2_62_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_breakeven_aware_rule_train_diagnostic.json"


def validate_h_a2_targeted_data_regime_expansion_plan(
    plan_path: Path = DEFAULT_PLAN_PATH,
    doc_path: Path = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    plan = _load_json(plan_path)
    doc_text = doc_path.read_text(encoding="utf-8") if doc_path.exists() else ""
    blockers: list[str] = []

    if plan.get("schema_version") != "h_a2_targeted_data_regime_expansion_plan_v1":
        blockers.append("unsupported_schema_version")
    if plan.get("artifact_type") != "preregistration":
        blockers.append("artifact_type_must_be_preregistration")
    if plan.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if plan.get("experiment_id") != "h_a2_targeted_data_regime_expansion_plan":
        blockers.append("experiment_id_must_match")
    if plan.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if plan.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")

    _validate_sources(plan, blockers)
    _validate_h_a2_62(blockers)
    _validate_minimum_fields(plan, blockers)
    _validate_target_sets(plan, blockers)
    _validate_statistics(plan, blockers)
    _validate_cost_policy(plan, blockers)
    _validate_guardrails_claims_and_doc(plan, doc_text, blockers)

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "plan_path": _relative(plan_path),
        "hypothesis_id": plan.get("hypothesis_id"),
        "evidence_tier": plan.get("evidence_tier"),
        "experiment_id": plan.get("experiment_id"),
        "next_safe_action": plan.get("next_safe_action"),
        "planned_next_artifact": (plan.get("planned_next_artifact") or {}).get("step_id"),
        "paid_download_allowed": (plan.get("guardrails") or {}).get("paid_download_allowed"),
        "paper_trading_allowed": (plan.get("guardrails") or {}).get("paper_trading_allowed"),
    }


def _validate_sources(plan: dict[str, Any], blockers: list[str]) -> None:
    for source in plan.get("source_artifacts", []):
        if not (PROJECT_ROOT / source).exists():
            blockers.append(f"source_artifact_missing:{source}")
    for item in plan.get("wiki_basis", []):
        path = Path(str(item.get("path", "")))
        if not path.exists():
            blockers.append(f"wiki_basis_missing:{path}")
        if not item.get("use"):
            blockers.append(f"wiki_basis_missing_use:{path}")


def _validate_h_a2_62(blockers: list[str]) -> None:
    summary = _load_json(H_A2_62_PATH)
    if summary.get("status") != "complete":
        blockers.append("h_a2_62_must_be_complete")
    if summary.get("experiment_id") != "h_a2_breakeven_aware_rule_train_diagnostic":
        blockers.append("h_a2_62_experiment_id_must_match")
    if summary.get("decision", {}).get("decision") != "write_targeted_data_regime_expansion_plan":
        blockers.append("h_a2_62_must_select_targeted_data_plan")
    if summary.get("decision_time_feature_audit", {}).get("can_lock_true_breakeven_aware_rule_from_current_artifacts") is not False:
        blockers.append("h_a2_62_must_block_true_rule_lock")


def _validate_minimum_fields(plan: dict[str, Any], blockers: list[str]) -> None:
    fields = plan.get("minimum_required_fields", {})
    underlying = fields.get("underlying_bars", {})
    for field in ["timestamp_utc", "timestamp_et", "open", "high", "low", "close", "volume"]:
        if field not in underlying.get("minimum_fields", []):
            blockers.append(f"underlying_field_missing:{field}")
    windows = "\n".join(underlying.get("required_windows_et", []))
    for phrase in ["09:30-09:35", "09:35", "15:45"]:
        if phrase not in windows:
            blockers.append(f"underlying_window_missing:{phrase}")

    entry = fields.get("option_chain_entry", {})
    for field in ["raw_symbol", "expiration", "right", "strike", "bid_px", "ask_px", "bid_sz", "ask_sz"]:
        if field not in entry.get("minimum_fields", []):
            blockers.append(f"entry_option_field_missing:{field}")
    if "09:34-09:36" not in "\n".join(entry.get("required_windows_et", [])):
        blockers.append("entry_window_must_cover_0934_0936")
    if "0.97x to 1.03x" not in entry.get("strike_scope", ""):
        blockers.append("strike_scope_must_be_explicit")

    close = fields.get("option_chain_forced_close", {})
    if "15:44-15:46" not in "\n".join(close.get("required_windows_et", [])):
        blockers.append("forced_close_window_must_cover_1544_1546")
    regime = fields.get("regime_labels", {})
    for field in [
        "vix_bucket",
        "macro_event_flag",
        "macro_event_type",
        "day_of_week",
        "trend_proxy_bucket",
        "stress_subperiod_label",
        "liquidity_bucket_from_entry_quotes",
    ]:
        if field not in regime.get("minimum_fields", []):
            blockers.append(f"regime_field_missing:{field}")


def _validate_target_sets(plan: dict[str, Any], blockers: list[str]) -> None:
    sets = {item.get("target_set_id"): item for item in plan.get("planned_target_sets", [])}
    expected = [
        "train_candidate_geometry_backfill",
        "normal_control_geometry_pack",
        "stress_regime_geometry_pack",
        "oos_locked_rule_evaluation_pack",
    ]
    for target_set_id in expected:
        if target_set_id not in sets:
            blockers.append(f"target_set_missing:{target_set_id}")
    train = sets.get("train_candidate_geometry_backfill", {})
    if train.get("priority") != 1:
        blockers.append("train_geometry_backfill_must_be_priority_1")
    if train.get("expected_current_count_from_h_a2_62") != 30:
        blockers.append("train_expected_count_must_match_h_a2_62")
    if train.get("paid_download_allowed_now") is not False:
        blockers.append("train_paid_download_allowed_now_must_be_false")
    if "metadata_or_cache_inventory_then_cost_estimate" != train.get("allowed_next_step"):
        blockers.append("train_allowed_next_step_must_be_inventory_cost_estimate")
    for target_set_id, item in sets.items():
        if item.get("paid_download_allowed_now") is not False:
            blockers.append(f"paid_download_allowed_now_must_be_false:{target_set_id}")
        if not item.get("regime_coverage_required"):
            blockers.append(f"regime_coverage_required_missing:{target_set_id}")
        if not item.get("minimum_windows"):
            blockers.append(f"minimum_windows_missing:{target_set_id}")


def _validate_statistics(plan: dict[str, Any], blockers: list[str]) -> None:
    stats = plan.get("statistical_requirements_before_acceptance", {})
    for field in [
        "mintrl_required",
        "psr_required",
        "dsr_required_if_any_trial_selection",
        "big_day_dependency_required",
        "active_trade_count_after_each_filter_required",
        "under_sampled_label_required_if_n_below_mintrl",
        "underpowered_label_required_if_power_too_low",
    ]:
        if stats.get(field) is not True:
            blockers.append(f"{field}_must_be_true")
    inputs = set(stats.get("mintrl_inputs", []))
    for field in [
        "sample_length",
        "observed_sharpe",
        "null_sharpe_threshold",
        "return_skewness",
        "return_kurtosis",
        "first_order_autocorrelation",
    ]:
        if field not in inputs:
            blockers.append(f"mintrl_input_missing:{field}")


def _validate_cost_policy(plan: dict[str, Any], blockers: list[str]) -> None:
    principles = plan.get("data_expansion_principles", {})
    for field in [
        "hypothesis_first",
        "field_first_before_date_first",
        "batch_grouped_requests_preferred",
        "reuse_cache_before_download",
        "cost_estimate_allowed_next",
        "no_single_day_drip_downloads_without_reason",
    ]:
        if principles.get(field) is not True:
            blockers.append(f"{field}_must_be_true")
    for field in [
        "broad_calendar_buying_allowed",
        "paid_download_allowed_by_this_artifact",
        "oos_rule_evaluation_allowed_by_this_artifact",
    ]:
        if principles.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    policy = plan.get("cost_and_execution_policy", {})
    keys = set(policy.get("approved_key_pool", []))
    if {"DATABENTO_API_MO", "DATABENTO_API_AI"} - keys:
        blockers.append("approved_key_pool_must_include_mo_and_ai")
    if policy.get("selected_key_must_be_logged_before_paid_action") is not True:
        blockers.append("selected_key_logging_required")
    if policy.get("paid_download_allowed_by_this_plan") is not False:
        blockers.append("paid_download_allowed_by_this_plan_must_be_false")
    if policy.get("new_provider_allowed_by_this_plan") is not False:
        blockers.append("new_provider_allowed_by_this_plan_must_be_false")
    if policy.get("batch_grouping_required_where_possible") is not True:
        blockers.append("batch_grouping_required")

    next_artifact = plan.get("planned_next_artifact", {})
    if next_artifact.get("step_id") != "H-A2.64":
        blockers.append("planned_next_artifact_must_be_h_a2_64")
    outputs = "\n".join(next_artifact.get("required_outputs", []))
    for phrase in ["cache coverage", "missing field/window", "candidate date count", "grouped request plan", "estimated cost", "no-download"]:
        if phrase not in outputs:
            blockers.append(f"next_artifact_output_missing:{phrase}")
    forbidden = "\n".join(next_artifact.get("forbidden_outputs", []))
    for phrase in ["no paid download", "no OOS rule evaluation", "no threshold selection", "no paper trading"]:
        if phrase not in forbidden:
            blockers.append(f"next_artifact_forbidden_missing:{phrase}")


def _validate_guardrails_claims_and_doc(plan: dict[str, Any], doc_text: str, blockers: list[str]) -> None:
    guardrails = plan.get("guardrails", {})
    for field in [
        "network_used_by_this_artifact",
        "paid_data_used_by_this_artifact",
        "paid_download_allowed",
        "new_provider_allowed",
        "broker_request_allowed",
        "ibkr_request_allowed",
        "gdelt_live_retry_allowed",
        "llm_call_allowed",
        "oos_rule_evaluation_allowed",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "research_log_required_for_this_preregistration",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    allowed = "\n".join(plan.get("allowed_claims", []))
    for phrase in ["targeted data/regime expansion plan", "not paid download", "forbids broad calendar buying"]:
        if phrase not in allowed:
            blockers.append(f"allowed_claim_missing:{phrase}")
    forbidden = "\n".join(plan.get("forbidden_claims", []))
    for phrase in ["edge is validated", "selected for trading", "paid download", "OOS evaluation", "paper trading", "E2"]:
        if phrase not in forbidden:
            blockers.append(f"forbidden_claim_missing:{phrase}")
    completion = "\n".join(plan.get("completion_criteria", []))
    for phrase in ["H-A2.62", "minimum missing option-chain", "Target sets", "MinTRL", "cache inventory", "validator passes"]:
        if phrase not in completion:
            blockers.append(f"completion_criterion_missing:{phrase}")
    if not plan.get("next_safe_action", "").startswith("Run H-A2.64"):
        blockers.append("next_safe_action_must_start_h_a2_64")
    for phrase in ["Hypothesis-First Data Rule", "Minimum Fields", "Target Sets", "Statistical Requirements", "Forbidden"]:
        if phrase not in doc_text:
            blockers.append(f"doc_missing:{phrase}")


def _load_json(path: Path) -> Any:
    return json.loads(expand_configured_tokens(path.read_text(encoding="utf-8-sig")))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 targeted data/regime expansion plan.")
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_targeted_data_regime_expansion_plan(args.plan_path, args.doc_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
