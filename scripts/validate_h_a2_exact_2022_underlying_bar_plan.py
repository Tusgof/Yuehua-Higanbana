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
DEFAULT_PLAN_PATH = PROJECT_ROOT / "experiments" / "h_a2_exact_2022_underlying_bar_plan.json"
DEFAULT_DOC_PATH = PROJECT_ROOT / "docs" / "H_A2_EXACT_2022_UNDERLYING_BAR_PLAN.md"


def validate_h_a2_exact_2022_underlying_bar_plan(
    plan_path: Path = DEFAULT_PLAN_PATH,
    doc_path: Path = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    plan = _load_json(plan_path)
    doc_text = doc_path.read_text(encoding="utf-8") if doc_path.exists() else ""
    blockers: list[str] = []

    if plan.get("schema_version") != "h_a2_exact_2022_underlying_bar_plan_v1":
        blockers.append("unsupported_schema_version")
    if plan.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if plan.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if plan.get("status") != "plan_complete":
        blockers.append("status_must_be_plan_complete")
    if plan.get("decision") != "build_bounded_acquisition_import_tool_before_any_source_execution":
        blockers.append("decision_must_build_tool_before_execution")

    for key, value in plan.get("source_artifacts", {}).items():
        if not value:
            blockers.append(f"missing_source_artifact:{key}")
        elif not _path_exists(value):
            blockers.append(f"source_artifact_does_not_exist:{key}")

    hypothesis = plan.get("hypothesis_first_statement", "")
    if "SPY 1-minute bars are required only" not in hypothesis:
        blockers.append("hypothesis_first_statement_must_not_make_bars_the_hypothesis")

    gap = plan.get("exact_inference_gap", "")
    if "2022-10 0DTE option quotes" not in gap or "SPY 1-minute underlying bars" not in gap:
        blockers.append("exact_inference_gap_must_name_quotes_and_underlying_bars")

    scope = plan.get("planned_scope", {})
    if scope.get("symbol") != "SPY":
        blockers.append("scope_symbol_must_be_spy")
    if scope.get("data_type") != "underlying_bars":
        blockers.append("scope_data_type_must_be_underlying_bars")
    if scope.get("bar_size") != "1 minute":
        blockers.append("scope_bar_size_must_be_1_minute")
    if scope.get("window_start") != "2022-10-03" or scope.get("window_end") != "2022-10-31":
        blockers.append("scope_window_must_be_october_2022")
    if scope.get("trading_day_count") != 21:
        blockers.append("scope_trading_day_count_must_be_21")
    quote_dates = scope.get("quote_available_dates", [])
    if scope.get("quote_available_day_count") != 13 or len(quote_dates) != 13:
        blockers.append("quote_available_dates_must_have_13_days")
    if "2022-10-03" not in quote_dates or "2022-10-31" not in quote_dates:
        blockers.append("quote_available_dates_must_cover_first_and_last_target")

    required_fields = set(scope.get("minimum_fields", []))
    for field in ["timestamp", "open", "high", "low", "close", "volume"]:
        if field not in required_fields:
            blockers.append(f"missing_required_field:{field}")

    reasons = "\n".join(plan.get("why_1_minute_bars_are_required", []))
    for phrase in ["9:30-9:35 ET opening range", "Stop/target path", "underlying decision timestamp"]:
        if phrase not in reasons:
            blockers.append(f"missing_one_minute_reason:{phrase}")

    steps = {item.get("step_id"): item for item in plan.get("source_execution_order", [])}
    for step_id in [
        "local_cache_rescan",
        "build_bounded_data_only_tool",
        "ibkr_data_only_probe_if_ready",
        "new_provider_source_decision_if_ibkr_unavailable",
    ]:
        if step_id not in steps:
            blockers.append(f"missing_execution_step:{step_id}")

    build_step = steps.get("build_bounded_data_only_tool", {})
    if build_step.get("network_allowed") is not False or build_step.get("must_pass_before_next_step") is not True:
        blockers.append("bounded_tool_step_must_be_no_network_and_required")

    ibkr_step = steps.get("ibkr_data_only_probe_if_ready", {})
    if ibkr_step.get("network_allowed_after_gate") is not True:
        blockers.append("ibkr_step_must_require_gate_before_network")
    if ibkr_step.get("orders_allowed") is not False:
        blockers.append("ibkr_step_must_forbid_orders")
    if "ready_for_manual_data_probe" not in ibkr_step.get("required_gate", ""):
        blockers.append("ibkr_step_must_reference_readiness_gate")

    provider_step = steps.get("new_provider_source_decision_if_ibkr_unavailable", {})
    if provider_step.get("approval_required_before_execute") is not True:
        blockers.append("new_provider_step_must_require_user_approval")

    gates = plan.get("validation_gates_before_exact_rerun", {})
    for field in [
        "provenance_required",
        "raw_hash_or_request_manifest_required",
        "license_notes_required",
        "coverage_audit_required",
        "timestamp_conversion_to_et_required",
        "canonical_import_required",
        "orb_timestamp_coverage_required",
        "full_session_coverage_required",
        "join_to_existing_2022_10_option_quotes_required",
        "no_lookahead_timestamp_rule_required",
        "rerun_allowed_only_after_all_gates_pass",
    ]:
        if gates.get(field) is not True:
            blockers.append(f"{field}_must_be_true")

    forbidden_text = "\n".join(plan.get("forbidden_actions", []))
    for phrase in [
        "Do not request IBKR historical bars",
        "Do not buy 2022-09 option data",
        "Do not buy or use a new provider",
        "Do not transmit orders",
        "Do not run exact H-A2 stress diagnostics",
        "Do not approve paper trading",
    ]:
        if phrase not in forbidden_text:
            blockers.append(f"missing_forbidden_action:{phrase}")

    guardrails = plan.get("guardrails", {})
    for field in [
        "network_used_by_this_artifact",
        "paid_data_used_by_this_artifact",
        "new_provider_used_by_this_artifact",
        "ibkr_request_used_by_this_artifact",
        "llm_call_used_by_this_artifact",
        "strategy_pnl_used_by_this_artifact",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "research_log_required_for_this_plan",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    for phrase in ["Hypothesis First", "Validation Gates Before Exact Rerun", "Forbidden"]:
        if phrase not in doc_text:
            blockers.append(f"plan_doc_missing:{phrase}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "plan_path": _relative(plan_path),
        "hypothesis_id": plan.get("hypothesis_id"),
        "evidence_tier": plan.get("evidence_tier"),
        "decision": plan.get("decision"),
        "allowed_next_action": plan.get("allowed_next_action"),
        "paper_trading_allowed": guardrails.get("paper_trading_allowed"),
        "real_money_allowed": guardrails.get("real_money_allowed"),
    }


def _load_json(path: Path) -> Any:
    return json.loads(expand_configured_tokens(path.read_text(encoding="utf-8")))


def _path_exists(value: str) -> bool:
    path = Path(value)
    if path.is_absolute():
        return path.exists()
    return (PROJECT_ROOT / path).exists()


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 exact 2022 underlying-bar plan.")
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_exact_2022_underlying_bar_plan(args.plan_path, args.doc_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
