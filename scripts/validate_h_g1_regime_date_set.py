from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration.json"

ALLOWED_SPLITS = {"in_sample", "oos"}
ALLOWED_VOL_BUCKETS = {"low", "normal", "high"}
ALLOWED_SCHEMA_VERSIONS = {
    "h_g1_gamma_regime_date_set_preregistration_v1",
    "h_g1_gamma_regime_date_set_preregistration_v2",
    "h_g1_gamma_regime_date_set_preregistration_v3",
}
ALLOWED_OI_STATUS = {"existing_probe", "needs_metadata_cost_check", "downloaded"}


def validate_h_g1_regime_date_set(manifest_path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    blockers: list[str] = []

    schema_version = manifest.get("schema_version")
    if schema_version not in ALLOWED_SCHEMA_VERSIONS:
        blockers.append(f"unsupported_schema_version:{manifest.get('schema_version')}")
    if manifest.get("hypothesis_id") != "H-G1":
        blockers.append(f"unexpected_hypothesis_id:{manifest.get('hypothesis_id')}")

    dates = manifest.get("selected_dates")
    if not isinstance(dates, list):
        blockers.append("selected_dates_must_be_list")
        dates = []

    min_counts = manifest.get("minimum_regime_counts", {})
    expected_count = min_counts.get("total_dates")
    if schema_version == "h_g1_gamma_regime_date_set_preregistration_v1" and expected_count != 12:
        blockers.append(f"total_dates_not_locked_to_12:{expected_count}")
    if len(dates) != expected_count:
        blockers.append(f"selected_date_count_mismatch:{len(dates)}!={expected_count}")

    seen_dates: set[str] = set()
    split_counts: Counter[str] = Counter()
    vol_counts: Counter[str] = Counter()
    macro_counts: Counter[str] = Counter()
    month_counts: Counter[str] = Counter()
    oi_counts: Counter[str] = Counter()

    for item in dates:
        if not isinstance(item, dict):
            blockers.append("selected_date_entry_not_object")
            continue
        date = item.get("date")
        if not isinstance(date, str) or len(date) != 10:
            blockers.append(f"invalid_date:{date}")
            continue
        if date in seen_dates:
            blockers.append(f"duplicate_date:{date}")
        seen_dates.add(date)
        month_counts[date[:7]] += 1

        split = item.get("split")
        if split not in ALLOWED_SPLITS:
            blockers.append(f"{date}:invalid_split:{split}")
        else:
            split_counts[split] += 1

        vol_bucket = item.get("volatility_bucket")
        if vol_bucket not in ALLOWED_VOL_BUCKETS:
            blockers.append(f"{date}:invalid_volatility_bucket:{vol_bucket}")
        else:
            vol_counts[vol_bucket] += 1

        if item.get("high_importance_macro") is True:
            macro_counts["high_importance_macro"] += 1
        elif item.get("high_importance_macro") is False:
            macro_counts["no_high_importance_macro"] += 1
        else:
            blockers.append(f"{date}:high_importance_macro_must_be_boolean")

        if not isinstance(item.get("macro_events"), list):
            blockers.append(f"{date}:macro_events_must_be_list")
        if not item.get("selection_reason"):
            blockers.append(f"{date}:missing_selection_reason")
        if item.get("local_quote_cache_status") != "present":
            blockers.append(f"{date}:local_quote_cache_not_present")
        if item.get("local_spy_bar_cache_status") != "present":
            blockers.append(f"{date}:local_spy_bar_cache_not_present")

        oi_status = item.get("opra_oi_status")
        if oi_status not in ALLOWED_OI_STATUS:
            blockers.append(f"{date}:invalid_opra_oi_status:{oi_status}")
        else:
            oi_counts[oi_status] += 1

    _require_min(blockers, "low_volatility", vol_counts["low"], min_counts.get("low_volatility"))
    _require_min(blockers, "normal_volatility", vol_counts["normal"], min_counts.get("normal_volatility"))
    _require_min(blockers, "high_volatility", vol_counts["high"], min_counts.get("high_volatility"))
    _require_min(
        blockers,
        "high_importance_macro",
        macro_counts["high_importance_macro"],
        min_counts.get("high_importance_macro"),
    )
    _require_min(
        blockers,
        "no_high_importance_macro",
        macro_counts["no_high_importance_macro"],
        min_counts.get("no_high_importance_macro"),
    )
    _require_min(blockers, "in_sample", split_counts["in_sample"], min_counts.get("in_sample"))
    _require_min(blockers, "oos", split_counts["oos"], min_counts.get("oos"))
    _require_min(blockers, "unique_calendar_months", len(month_counts), min_counts.get("unique_calendar_months"))

    data_policy = manifest.get("data_policy", {})
    if data_policy.get("symbol_universe") != ["SPY"]:
        blockers.append(f"symbol_universe_not_spy_only:{data_policy.get('symbol_universe')}")
    if data_policy.get("paid_action_before_manifest_validation") != "forbidden":
        blockers.append("paid_action_before_manifest_validation_not_forbidden")
    if data_policy.get("broad_calendar_purchase") != "forbidden":
        blockers.append("broad_calendar_purchase_not_forbidden")
    if data_policy.get("existing_oi_probe_date") != "2024-01-03":
        blockers.append(f"unexpected_existing_oi_probe_date:{data_policy.get('existing_oi_probe_date')}")

    if schema_version == "h_g1_gamma_regime_date_set_preregistration_v3":
        _validate_v3_manifest(blockers, manifest, seen_dates, oi_counts)

    return {
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "manifest_path": _relative(manifest_path),
        "hypothesis_id": manifest.get("hypothesis_id"),
        "date_count": len(dates),
        "split_counts": dict(sorted(split_counts.items())),
        "volatility_bucket_counts": dict(sorted(vol_counts.items())),
        "macro_counts": dict(sorted(macro_counts.items())),
        "unique_calendar_months": len(month_counts),
        "opra_oi_status_counts": dict(sorted(oi_counts.items())),
    }


def _validate_v3_manifest(
    blockers: list[str],
    manifest: dict[str, Any],
    seen_dates: set[str],
    oi_counts: Counter[str],
) -> None:
    if "2023-07-12" in seen_dates:
        blockers.append("v3_removed_date_still_present:2023-07-12")
    if "2023-09-13" not in seen_dates:
        blockers.append("v3_expected_replacement_missing:2023-09-13")
    if oi_counts["needs_metadata_cost_check"] != 1:
        blockers.append(f"v3_expected_one_metadata_cost_check:{oi_counts['needs_metadata_cost_check']}")

    replacement_audit = manifest.get("replacement_audit", {})
    if replacement_audit.get("removed_date") != "2023-07-12":
        blockers.append(f"v3_unexpected_removed_date:{replacement_audit.get('removed_date')}")
    if replacement_audit.get("selected_replacement_date") != "2023-09-13":
        blockers.append(f"v3_unexpected_replacement_date:{replacement_audit.get('selected_replacement_date')}")

    candidates = manifest.get("candidate_ranking_table")
    if not isinstance(candidates, list) or not candidates:
        blockers.append("v3_candidate_ranking_table_missing")
        return
    top = candidates[0]
    if top.get("date") != "2023-09-13":
        blockers.append(f"v3_top_rank_candidate_unexpected:{top.get('date')}")
    if top.get("rank") != 1:
        blockers.append(f"v3_top_rank_not_one:{top.get('rank')}")
    if top.get("same_macro_family_as_removed") is not True:
        blockers.append("v3_top_rank_not_same_macro_family")
    if top.get("local_option_quote_cache_present") is not True:
        blockers.append("v3_top_rank_quote_cache_not_present")
    if top.get("local_spy_bar_cache_present") is not True:
        blockers.append("v3_top_rank_spy_bar_cache_not_present")


def _require_min(blockers: list[str], name: str, observed: int, required: Any) -> None:
    if not isinstance(required, int):
        blockers.append(f"missing_minimum_count:{name}")
        return
    if observed < required:
        blockers.append(f"minimum_count_not_met:{name}:{observed}<{required}")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-G1 gamma/OI regime date-set pre-registration manifest.")
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    args = parser.parse_args(argv)
    result = validate_h_g1_regime_date_set(args.manifest_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
