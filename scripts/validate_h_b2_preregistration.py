from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "experiments" / "h_b2_subsystem_b_scale_preregistration.json"


def validate_h_b2_preregistration(manifest_path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    blockers: list[str] = []

    if manifest.get("schema_version") != "h_b2_subsystem_b_scale_preregistration_v1":
        blockers.append(f"unsupported_schema_version:{manifest.get('schema_version')}")
    if manifest.get("hypothesis_id") != "H-B2":
        blockers.append(f"unexpected_hypothesis_id:{manifest.get('hypothesis_id')}")

    account_sizes = manifest.get("account_sizes_usd")
    if account_sizes != [10000.0, 25000.0]:
        blockers.append(f"account_sizes_not_locked:{account_sizes}")

    wing_grid = manifest.get("strategy_template", {}).get("protective_wing_gap_grid_usd")
    if wing_grid != [5.0, 10.0, 15.0, 20.0]:
        blockers.append(f"wing_grid_not_locked:{wing_grid}")

    capital_rule = manifest.get("capital_rule", {})
    if capital_rule.get("account_risk_fraction") != 0.05:
        blockers.append(f"account_risk_fraction_not_locked:{capital_rule.get('account_risk_fraction')}")
    if capital_rule.get("contract_sizing") != "one_1x2x1_spread_per_eligible_day":
        blockers.append(f"unexpected_contract_sizing:{capital_rule.get('contract_sizing')}")
    if capital_rule.get("fractional_contracts") is not False:
        blockers.append("fractional_contracts_not_forbidden")

    search_control = manifest.get("search_control", {})
    expected_trials = len(account_sizes or []) * len(wing_grid or [])
    if search_control.get("independent_trial_count") != expected_trials:
        blockers.append(
            f"trial_count_mismatch:{search_control.get('independent_trial_count')}!=account_sizes*wing_grid:{expected_trials}"
        )
    if search_control.get("selection_for_deployment") != "forbidden":
        blockers.append("deployment_selection_not_forbidden")
    if not str(search_control.get("dsr_status", "")).startswith("blocked"):
        blockers.append(f"dsr_status_not_blocked:{search_control.get('dsr_status')}")

    data_policy = manifest.get("data_policy", {})
    if data_policy.get("new_paid_data_allowed") is not False:
        blockers.append("new_paid_data_not_forbidden")
    if data_policy.get("symbol_universe") != ["SPY"]:
        blockers.append(f"symbol_universe_not_spy_only:{data_policy.get('symbol_universe')}")

    output_paths = manifest.get("output_paths", {})
    for key in ("summary", "report", "search_log"):
        if not output_paths.get(key):
            blockers.append(f"missing_output_path:{key}")

    return {
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "manifest_path": _relative(manifest_path),
        "hypothesis_id": manifest.get("hypothesis_id"),
        "account_sizes_usd": account_sizes,
        "protective_wing_gap_grid_usd": wing_grid,
        "independent_trial_count": search_control.get("independent_trial_count"),
    }


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-B2 Sub-System B scale pre-registration manifest.")
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    args = parser.parse_args(argv)
    result = validate_h_b2_preregistration(args.manifest_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
