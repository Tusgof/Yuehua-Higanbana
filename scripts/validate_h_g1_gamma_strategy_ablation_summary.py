from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_g1_gamma_strategy_ablation_summary.json"
PREREG_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_strategy_ablation_preregistration.json"


def validate_summary(summary_path: Path = SUMMARY_PATH, prereg_path: Path = PREREG_PATH) -> dict[str, Any]:
    summary = _read_json(summary_path)
    prereg = _read_json(prereg_path)
    blockers: list[str] = []

    _expect(blockers, summary.get("schema_version") == "h_g1_gamma_strategy_ablation_v1", "invalid_schema_version")
    _expect(blockers, summary.get("hypothesis_id") == "H-G1", "invalid_hypothesis_id")
    _expect(blockers, summary.get("evidence_tier") == "E1", "evidence_tier_must_remain_E1")
    _expect(blockers, summary.get("status") == "complete_underpowered", "status_must_be_complete_underpowered")
    _expect(blockers, summary.get("conclusion") == "ยังสรุปไม่ได้", "conclusion_must_not_claim_pass")
    for flag in ("network_used", "paid_data_used", "new_data_requested", "strategy_use_allowed", "paper_trading_allowed"):
        _expect(blockers, summary.get(flag) is False, f"{flag}_must_be_false")
    _expect(blockers, summary.get("strategy_pnl_used") is True, "strategy_pnl_used_must_be_true")
    _expect(blockers, summary.get("no_oos_tuning") is True, "no_oos_tuning_must_be_true")
    _expect(blockers, summary.get("random_split_used") is False, "random_split_used_must_be_false")

    expected_variants = _expected_variants(prereg)
    actual_variants = [item.get("variant_id") for item in summary.get("variant_results", [])]
    _expect(blockers, actual_variants == expected_variants, "variant_set_or_order_mismatch")
    _expect(blockers, summary.get("variant_count_policy", {}).get("total_trial_count") == len(expected_variants), "trial_count_policy_mismatch")

    search_log = summary.get("search_log", {})
    search_log_path = PROJECT_ROOT / search_log.get("path", "")
    rows = _read_jsonl(search_log_path) if search_log_path.exists() else []
    _expect(blockers, search_log_path.exists(), "search_log_missing")
    _expect(blockers, [row.get("variant_id") for row in rows] == expected_variants, "search_log_variant_mismatch")
    _expect(blockers, search_log.get("trial_count") == len(expected_variants), "search_log_trial_count_mismatch")
    _expect(blockers, search_log.get("selected_for_deployment") is False, "search_log_must_not_select_deployment")

    required_metrics = set(prereg.get("metrics_required", []))
    for variant in summary.get("variant_results", []):
        missing = _missing_metric_fields(variant, required_metrics)
        if missing:
            blockers.append(f"missing_required_metrics:{variant.get('variant_id')}:{','.join(sorted(missing))}")
        _expect(blockers, variant.get("under_sampled_label") is True, f"{variant.get('variant_id')}:under_sampled_label_required")
        _expect(blockers, variant.get("underpowered_label") is True, f"{variant.get('variant_id')}:underpowered_label_required")
        _expect(blockers, variant.get("mintrl", {}).get("status") == "blocked_insufficient_observations", f"{variant.get('variant_id')}:mintrl_status_required")
        _expect(blockers, variant.get("psr", {}).get("status") == "blocked_insufficient_observations", f"{variant.get('variant_id')}:psr_status_required")

    _expect(blockers, isinstance(summary.get("dsr_or_dsr_blocker"), dict), "dsr_or_dsr_blocker_missing")
    _expect(blockers, isinstance(summary.get("big_day_dependency_result"), dict), "big_day_dependency_result_missing")
    _expect(blockers, "true market-maker net gamma" in summary.get("forbidden_claims_preserved", []), "true_net_gamma_forbidden_claim_not_preserved")
    _expect(blockers, "signed_oi_gamma_proxy_is_not_true_market_maker_net_gamma" in summary.get("tier_blockers", []), "proxy_semantics_blocker_missing")

    return {
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "summary_path": _relative(summary_path),
        "preregistration_path": _relative(prereg_path),
        "variant_count": len(actual_variants),
        "search_log_rows": len(rows),
    }


def _missing_metric_fields(variant: dict[str, Any], required: set[str]) -> set[str]:
    metrics = variant.get("metrics", {})
    present = set(metrics) | set(variant)
    present.add("dsr_or_dsr_blocker")
    present.add("benchmark_comparison")
    missing = set()
    for field in required:
        if field == "dsr_or_dsr_blocker":
            continue
        if field not in present:
            missing.add(field)
    return missing


def _expected_variants(prereg: dict[str, Any]) -> list[str]:
    return [
        prereg["baseline_variant"]["variant_id"],
        *[item["variant_id"] for item in prereg["gamma_variants"]],
    ]


def _expect(blockers: list[str], condition: bool, blocker: str) -> None:
    if not condition:
        blockers.append(blocker)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-G1 gamma strategy-ablation summary.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--prereg-path", type=Path, default=PREREG_PATH)
    args = parser.parse_args(argv)
    result = validate_summary(args.summary_path, args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
