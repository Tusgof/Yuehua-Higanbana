from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_strategy_ablation_preregistration.json"
DEFAULT_SOURCE_REVIEW_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_acceptance_blocker_review.json"
REQUIRED_SCHEMA_VERSION = "h_g1_gamma_strategy_ablation_preregistration_v1"


def validate_h_g1_gamma_strategy_ablation_preregistration(
    prereg_path: Path = DEFAULT_PREREG_PATH,
    source_review_path: Path = DEFAULT_SOURCE_REVIEW_PATH,
) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    source_review = _load_json(source_review_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != REQUIRED_SCHEMA_VERSION:
        blockers.append(f"unsupported_schema_version:{prereg.get('schema_version')}")
    if prereg.get("artifact_type") != "h_g1_gamma_strategy_ablation_preregistration":
        blockers.append(f"unexpected_artifact_type:{prereg.get('artifact_type')}")
    if prereg.get("hypothesis_id") != "H-G1":
        blockers.append(f"unexpected_hypothesis_id:{prereg.get('hypothesis_id')}")
    if prereg.get("status") != "preregistered_strategy_ablation":
        blockers.append(f"unexpected_status:{prereg.get('status')}")
    if prereg.get("evidence_tier") != "E0":
        blockers.append(f"unexpected_evidence_tier:{prereg.get('evidence_tier')}")
    if prereg.get("conclusion") != "ยังสรุปไม่ได้":
        blockers.append("unexpected_conclusion")

    _require_false(blockers, prereg, "network_used")
    _require_false(blockers, prereg, "paid_data_used")
    _require_false(blockers, prereg, "new_data_requested")
    _require_false(blockers, prereg, "strategy_pnl_used")
    _require_false(blockers, prereg, "research_log_required")
    _require_false(blockers, prereg, "strategy_use_allowed_before_results")
    _require_false(blockers, prereg, "paper_trading_allowed_before_results")

    if prereg.get("source_blocker_review") != "reports/diagnostics/h_g1_acceptance_blocker_review.json":
        blockers.append("source_blocker_review_not_locked")
    if source_review.get("status") != "blocked_before_strategy_use":
        blockers.append(f"source_review_status_unexpected:{source_review.get('status')}")
    if source_review.get("strategy_use_allowed") is not False:
        blockers.append("source_review_strategy_use_not_blocked")
    if source_review.get("paper_trading_allowed") is not False:
        blockers.append("source_review_paper_trading_not_blocked")

    split = prereg.get("chronological_split", {})
    if split.get("method") != "fixed_chronological_split":
        blockers.append(f"chronological_split_method_invalid:{split.get('method')}")
    if split.get("train_start") != "2022-05-11" or split.get("train_end") != "2023-12-31":
        blockers.append("train_window_not_locked")
    if split.get("oos_start") != "2024-01-01":
        blockers.append("oos_start_not_locked")
    _require_false(blockers, split, "random_split_allowed")
    _require_false(blockers, split, "oos_tuning_allowed")
    _require_true(blockers, split, "thresholds_frozen_before_oos")

    baseline = prereg.get("baseline_variant", {})
    if baseline.get("variant_id") != "baseline_quant_only":
        blockers.append(f"baseline_variant_not_locked:{baseline.get('variant_id')}")
    if baseline.get("gamma_filter") != "none":
        blockers.append("baseline_uses_gamma_filter")

    gamma_variants = prereg.get("gamma_variants", [])
    if not isinstance(gamma_variants, list) or len(gamma_variants) != 3:
        blockers.append(f"gamma_variant_count_invalid:{len(gamma_variants) if isinstance(gamma_variants, list) else 'not_list'}")
        gamma_variants = []
    variant_ids = [variant.get("variant_id") for variant in gamma_variants if isinstance(variant, dict)]
    expected_ids = {
        "skip_negative_gamma_proxy_days",
        "skip_extreme_negative_gamma_proxy_days",
        "positive_gamma_proxy_only",
    }
    if set(variant_ids) != expected_ids:
        blockers.append(f"gamma_variant_ids_not_locked:{variant_ids}")
    if len(variant_ids) != len(set(variant_ids)):
        blockers.append("duplicate_gamma_variant_ids")

    variant_count_policy = prereg.get("variant_count_policy", {})
    if variant_count_policy.get("total_trial_count") != 4:
        blockers.append(f"trial_count_not_locked:{variant_count_policy.get('total_trial_count')}")
    _require_false(blockers, variant_count_policy, "additional_variants_allowed_without_new_preregistration")

    selection_rule = prereg.get("selection_rule", {})
    _require_false(blockers, selection_rule, "best_sharpe_selection_allowed")
    required_advance_phrases = [
        "MinTRL/PSR",
        "DSR",
        "Big-day dependency",
        "Cost drag",
        "Regime coverage",
    ]
    advance_text = " ".join(selection_rule.get("candidate_can_advance_to_e2_only_if", []))
    for phrase in required_advance_phrases:
        if phrase not in advance_text:
            blockers.append(f"selection_rule_missing:{phrase}")

    search_log = prereg.get("search_log_policy", {})
    _require_true(blockers, search_log, "required")
    _require_true(blockers, search_log, "must_log_every_attempted_variant")
    _require_true(blockers, search_log, "dsr_required_if_selecting_best")
    _require_true(blockers, search_log, "dsr_blocker_required_if_uncomputable")
    if search_log.get("effective_trial_count_floor") != 4:
        blockers.append(f"effective_trial_count_floor_invalid:{search_log.get('effective_trial_count_floor')}")
    if search_log.get("path") != "reports/experiments/search_logs/h_g1_gamma_strategy_ablation_search_log.jsonl":
        blockers.append("search_log_path_not_locked")

    metrics = set(prereg.get("metrics_required", []))
    for metric in {
        "mid_pnl",
        "implementable_pnl",
        "cost_drag",
        "mintrl",
        "psr",
        "under_sampled_label",
        "underpowered_label",
        "dsr_or_dsr_blocker",
        "big_day_dependency_result",
        "regime_trade_counts",
    }:
        if metric not in metrics:
            blockers.append(f"missing_metric:{metric}")

    power = prereg.get("statistical_power_policy", {})
    _require_true(blockers, power, "mintrl_required")
    _require_true(blockers, power, "psr_required")
    if power.get("null_sharpe_thresholds") != [0.0, 0.5]:
        blockers.append(f"null_sharpe_thresholds_not_locked:{power.get('null_sharpe_thresholds')}")
    for key in ["sample_length", "observed_sharpe", "skewness", "kurtosis", "first_order_autocorrelation"]:
        if key not in power.get("distribution_inputs_required", []):
            blockers.append(f"missing_power_input:{key}")

    big_day = prereg.get("big_day_dependency_policy", {})
    _require_true(blockers, big_day, "required")
    _require_true(blockers, big_day, "remove_extreme_winners_and_losers")
    if big_day.get("extreme_fraction_each_side") != 0.05:
        blockers.append(f"big_day_fraction_invalid:{big_day.get('extreme_fraction_each_side')}")

    pnl = prereg.get("implementable_pnl_policy", {})
    _require_true(blockers, pnl, "mid_pnl_required")
    _require_true(blockers, pnl, "implementable_pnl_required")
    _require_true(blockers, pnl, "cost_drag_required")
    _require_true(blockers, pnl, "bid_ask_spread_treatment_required")
    _require_false(blockers, pnl, "entry_market_orders_allowed")
    if pnl.get("per_leg_fee_usd") != 0.64:
        blockers.append(f"per_leg_fee_usd_invalid:{pnl.get('per_leg_fee_usd')}")
    if pnl.get("forced_close_time_et") != "15:45":
        blockers.append(f"forced_close_time_invalid:{pnl.get('forced_close_time_et')}")

    proxy = prereg.get("proxy_wording_policy", {})
    if proxy.get("required_term") != "signed-OI gamma proxy":
        blockers.append("proxy_required_term_not_locked")
    forbidden_terms = set(proxy.get("forbidden_terms_without_inventory_source", []))
    for term in {"true market-maker net gamma", "dealer net gamma", "market-maker inventory"}:
        if term not in forbidden_terms:
            blockers.append(f"missing_forbidden_proxy_term:{term}")
    _require_true(blockers, proxy, "inventory_source_required_for_true_net_gamma_claim")

    forbidden = set(prereg.get("forbidden_before_results", []))
    for item in {
        "strategy use",
        "paper trading approval",
        "new paid data justified solely by this preregistration",
        "OOS threshold tuning after viewing validation results",
        "claiming true market-maker net gamma",
    }:
        if item not in forbidden:
            blockers.append(f"missing_forbidden_before_results:{item}")

    if "results" in prereg or "observed_pnl" in prereg:
        blockers.append("preregistration_contains_results")

    return {
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "preregistration_path": _relative(prereg_path),
        "hypothesis_id": prereg.get("hypothesis_id"),
        "variant_count": 1 + len(gamma_variants),
        "next_allowed_action": prereg.get("next_allowed_action"),
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_true(blockers: list[str], payload: dict[str, Any], key: str) -> None:
    if payload.get(key) is not True:
        blockers.append(f"{key}_not_true")


def _require_false(blockers: list[str], payload: dict[str, Any], key: str) -> None:
    if payload.get(key) is not False:
        blockers.append(f"{key}_not_false")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-G1 gamma strategy-ablation pre-registration.")
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    parser.add_argument("--source-review-path", type=Path, default=DEFAULT_SOURCE_REVIEW_PATH)
    args = parser.parse_args(argv)
    result = validate_h_g1_gamma_strategy_ablation_preregistration(args.prereg_path, args.source_review_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
