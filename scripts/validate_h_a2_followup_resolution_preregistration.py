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
DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_followup_resolution_preregistration.json"


def validate_h_a2_followup_resolution_preregistration(prereg_path: Path = DEFAULT_PREREG_PATH) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != "h_a2_followup_resolution_preregistration_v1":
        blockers.append("unsupported_schema_version")
    if prereg.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if prereg.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if prereg.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if prereg.get("decision") != "lower_resolution_proxy_first":
        blockers.append("decision_must_be_lower_resolution_proxy_first")

    source_artifacts = prereg.get("source_artifacts", {})
    for key in [
        "data_resolution_audit",
        "h_a2_10_summary",
        "h_a2_10_log",
        "spy_bar_unavailable_report",
        "wiki_orb_concept",
        "wiki_backtest_validation_protocol",
        "wiki_orb_source",
    ]:
        value = source_artifacts.get(key)
        if not value:
            blockers.append(f"missing_source_artifact:{key}")
        elif not Path(value).is_absolute() and not (PROJECT_ROOT / value).exists():
            blockers.append(f"source_artifact_does_not_exist:{key}")
        elif Path(value).is_absolute() and not Path(value).exists():
            blockers.append(f"source_artifact_does_not_exist:{key}")

    candidate_paths = prereg.get("candidate_paths", {})
    proxy = candidate_paths.get("lower_resolution_proxy_first", {})
    exact = candidate_paths.get("exact_spy_bar_source_plan", {})
    if proxy.get("selected") is not True:
        blockers.append("proxy_path_must_be_selected")
    if exact.get("selected") is not False:
        blockers.append("exact_source_path_must_not_be_selected")
    if proxy.get("evidence_target") != "E1":
        blockers.append("proxy_evidence_target_must_be_e1")

    allowed_inputs = "\n".join(proxy.get("allowed_inputs", []))
    for phrase in ["existing local SPY intraday bars", "macro calendar", "VIX/VXV", "H-A2.10"]:
        if phrase not in allowed_inputs:
            blockers.append(f"missing_allowed_input:{phrase}")

    forbidden_claims = "\n".join(proxy.get("forbidden_claims", []))
    for phrase in ["exact 2022-10 ORB", "deployable strategy edge", "paper trading", "proxy PnL"]:
        if phrase not in forbidden_claims:
            blockers.append(f"missing_proxy_forbidden_claim:{phrase}")

    exact_forbidden = "\n".join(exact.get("forbidden_now", []))
    for phrase in ["IBKR historical bars", "more 2022 option data", "new paid provider"]:
        if phrase not in exact_forbidden:
            blockers.append(f"missing_exact_forbidden_now:{phrase}")

    requirements = prereg.get("next_preregistration_requirements", {})
    required_true_flags = [
        "must_state_hypothesis_first",
        "must_state_minimum_data_resolution",
        "must_explain_why_1_minute_bars_are_or_are_not_required",
        "must_use_chronological_split",
        "must_forbid_random_split",
        "must_track_all_trials_for_dsr",
        "must_report_mintrl_psr_or_explicit_not_applicable_reason",
        "must_report_big_day_dependency_if_strategy_returns_exist",
        "must_separate_mid_and_implementable_pnl_if_option_pnl_exists",
        "must_preserve_no_paper_trading",
    ]
    for field in required_true_flags:
        if requirements.get(field) is not True:
            blockers.append(f"{field}_must_be_true")

    guardrails = prereg.get("guardrails", {})
    false_flags = [
        "network_allowed",
        "paid_data_allowed",
        "new_provider_allowed",
        "ibkr_request_allowed",
        "llm_call_allowed",
        "strategy_pnl_allowed_in_this_artifact",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "research_log_required_for_this_preregistration",
    ]
    for field in false_flags:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    outputs = prereg.get("planned_outputs", {})
    for key in ["preregistration_json", "preregistration_md", "validator", "next_experiment_log_if_future_proxy_runs"]:
        if not outputs.get(key):
            blockers.append(f"missing_planned_output:{key}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "prereg_path": _relative(prereg_path),
        "hypothesis_id": prereg.get("hypothesis_id"),
        "evidence_tier": prereg.get("evidence_tier"),
        "decision": prereg.get("decision"),
        "proxy_selected": proxy.get("selected"),
        "exact_source_selected": exact.get("selected"),
        "paper_trading_allowed": guardrails.get("paper_trading_allowed"),
    }


def _load_json(path: Path) -> Any:
    return json.loads(expand_configured_tokens(path.read_text(encoding="utf-8")))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 follow-up resolution preregistration.")
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_followup_resolution_preregistration(args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
