from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_lower_resolution_proxy_preregistration.json"


def validate_h_a2_lower_resolution_proxy_preregistration(prereg_path: Path = DEFAULT_PREREG_PATH) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != "h_a2_lower_resolution_proxy_preregistration_v1":
        blockers.append("unsupported_schema_version")
    if prereg.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if prereg.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if prereg.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if prereg.get("experiment_id") != "h_a2_lower_resolution_proxy":
        blockers.append("experiment_id_must_be_h_a2_lower_resolution_proxy")
    if "hypothesis" not in prereg or "1-minute" not in prereg["hypothesis"]:
        blockers.append("hypothesis_must_state_data_resolution_tradeoff")

    _validate_source_artifacts(prereg, blockers)
    _validate_resolution_policy(prereg, blockers)
    _validate_proxy_tests(prereg, blockers)
    _validate_split_trial_and_stats(prereg, blockers)
    _validate_claims_and_guardrails(prereg, blockers)

    guardrails = prereg.get("guardrails", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "prereg_path": _relative(prereg_path),
        "hypothesis_id": prereg.get("hypothesis_id"),
        "evidence_tier": prereg.get("evidence_tier"),
        "experiment_id": prereg.get("experiment_id"),
        "network_allowed": guardrails.get("network_allowed"),
        "paid_data_allowed": guardrails.get("paid_data_allowed"),
        "paper_trading_allowed": guardrails.get("paper_trading_allowed"),
        "planned_proxy_test_count": len(prereg.get("planned_proxy_tests", [])),
    }


def _validate_source_artifacts(prereg: dict[str, Any], blockers: list[str]) -> None:
    source_artifacts = prereg.get("source_artifacts", {})
    required = [
        "parent_decision",
        "parent_decision_doc",
        "data_resolution_audit",
        "h_a2_reanalysis",
        "h_a2_high_vix_diagnostic",
        "h_a2_2022_10_coarse_review",
        "baseline_summary",
        "macro_events",
        "vix_vxv",
        "spy_bars",
        "option_quotes",
        "wiki_orb_concept",
        "wiki_backtest_validation_protocol",
    ]
    for key in required:
        value = source_artifacts.get(key)
        if not value:
            blockers.append(f"missing_source_artifact:{key}")
            continue
        path = Path(value)
        if path.is_absolute():
            if not path.exists():
                blockers.append(f"source_artifact_does_not_exist:{key}")
        elif not (PROJECT_ROOT / path).exists():
            blockers.append(f"source_artifact_does_not_exist:{key}")


def _validate_resolution_policy(prereg: dict[str, Any], blockers: list[str]) -> None:
    policy = prereg.get("minimum_data_resolution", {})
    mechanism = policy.get("mechanism_proxy", {})
    exact = policy.get("exact_backtest", {})

    if mechanism.get("one_minute_required") is not False:
        blockers.append("mechanism_proxy_must_not_require_1_minute")
    if exact.get("one_minute_required") is not True:
        blockers.append("exact_backtest_must_require_1_minute")

    allowed = "\n".join(mechanism.get("allowed_resolutions", []))
    for phrase in ["5-minute bars", "15-minute bars", "daily macro/VIX labels", "existing exact-quote"]:
        if phrase not in allowed:
            blockers.append(f"missing_proxy_resolution:{phrase}")

    exact_required = "\n".join(exact.get("required_resolutions", []))
    for phrase in ["SPY 1-minute bars", "SPY 0DTE option bid/ask quotes"]:
        if phrase not in exact_required:
            blockers.append(f"missing_exact_resolution:{phrase}")


def _validate_proxy_tests(prereg: dict[str, Any], blockers: list[str]) -> None:
    tests = prereg.get("planned_proxy_tests", [])
    test_ids = {test.get("test_id") for test in tests}
    required_ids = {
        "proxy_opening_followthrough_5m",
        "proxy_opening_followthrough_15m",
        "existing_trade_outcome_by_regime",
    }
    missing = sorted(required_ids - test_ids)
    for test_id in missing:
        blockers.append(f"missing_proxy_test:{test_id}")

    for test in tests:
        if "decision_timestamp_policy" not in test:
            blockers.append(f"missing_decision_timestamp_policy:{test.get('test_id')}")
        if "allowed_claim" not in test:
            blockers.append(f"missing_allowed_claim:{test.get('test_id')}")


def _validate_split_trial_and_stats(prereg: dict[str, Any], blockers: list[str]) -> None:
    split = prereg.get("split_policy", {})
    if split.get("chronological_split_required") is not True:
        blockers.append("chronological_split_required_must_be_true")
    if split.get("random_split_forbidden") is not True:
        blockers.append("random_split_forbidden_must_be_true")
    if split.get("oos_tuning_forbidden") is not True:
        blockers.append("oos_tuning_forbidden_must_be_true")

    trials = prereg.get("trial_policy", {})
    if len(trials.get("pre_registered_resolution_trials", [])) < 2:
        blockers.append("must_preregister_resolution_trials")
    if len(trials.get("pre_registered_regime_trials", [])) < 3:
        blockers.append("must_preregister_regime_trials")
    for field in ["trial_count_must_be_reported", "search_log_required", "dsr_required_if_sharpe_or_best_trial_is_reported"]:
        if trials.get(field) is not True:
            blockers.append(f"{field}_must_be_true")

    stats = prereg.get("statistical_policy", {})
    for field in [
        "mintrl_psr_required_if_trade_or_return_series_exists",
        "under_sampled_label_required_below_mintrl",
        "underpowered_label_required_when_power_is_insufficient",
        "big_day_dependency_required_if_strategy_returns_exist",
        "mid_vs_implementable_required_if_option_pnl_exists",
    ]:
        if stats.get(field) is not True:
            blockers.append(f"{field}_must_be_true")


def _validate_claims_and_guardrails(prereg: dict[str, Any], blockers: list[str]) -> None:
    allowed_claims = "\n".join(prereg.get("allowed_claims", []))
    for phrase in ["weakened at proxy level", "falsified at proxy level", "exact-data prioritization"]:
        if phrase not in allowed_claims:
            blockers.append(f"missing_allowed_claim_phrase:{phrase}")

    forbidden_claims = "\n".join(prereg.get("forbidden_claims", []))
    for phrase in ["exact 2022-10 ORB", "E2 acceptance-grade", "paper trading", "IBKR bars", "new data"]:
        if phrase not in forbidden_claims:
            blockers.append(f"missing_forbidden_claim_phrase:{phrase}")

    guardrails = prereg.get("guardrails", {})
    for field in [
        "network_allowed",
        "paid_data_allowed",
        "new_provider_allowed",
        "ibkr_request_allowed",
        "llm_call_allowed",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "research_log_required_for_this_preregistration",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    outputs = prereg.get("allowed_outputs", {})
    for key in ["summary_json", "summary_md", "search_log", "research_log_if_run"]:
        if not outputs.get(key):
            blockers.append(f"missing_allowed_output:{key}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 lower-resolution proxy preregistration.")
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_lower_resolution_proxy_preregistration(args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
