from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import interpreter_metadata


PLAN_PATH = PROJECT_ROOT / "experiments" / "h_a2_targeted_data_regime_expansion_plan.json"
LOWER_PROXY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_lower_resolution_proxy_summary.json"
NORMAL_CONTROL_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_import_diagnostic.json"
POST_CONTROL_PATH = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_post_stress_normalization_control_import_diagnostic.json"
)
STRESS_REVIEW_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_2022_10_coarse_stress_review.json"
IBKR_READINESS_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "ibkr_spy_bars_readiness_probe_h_a2_2022_10.json"
OUTPUT_JSON = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_targeted_geometry_cache_inventory_and_cost_plan.json"
OUTPUT_MD = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_targeted_geometry_cache_inventory_and_cost_plan.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_non_risk(row: dict[str, Any]) -> bool:
    regimes = row.get("regimes", {})
    return not any(
        [
            regimes.get("prior_high_vix"),
            regimes.get("prior_stress_vix"),
            regimes.get("high_importance_macro"),
        ]
    )


def vix_bucket(row: dict[str, Any]) -> str:
    value = row.get("regimes", {}).get("prior_vix_close")
    if value is None:
        return "missing_vix"
    if value >= 25:
        return "high_vix"
    if value < 15:
        return "low_vix"
    return "normal_vix"


def load_option_summary_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for path in (PROJECT_ROOT / "reports" / "data_cost").glob("databento_normalization_summary*.json"):
        data = load_json(path)
        for item in data.get("files", []):
            raw_file = str(item.get("file", ""))
            name = Path(raw_file).name
            if not name:
                continue
            index[name] = {
                "summary_path": str(path.relative_to(PROJECT_ROOT)),
                "output_rows": item.get("output_rows", 0),
                "input_rows": item.get("input_rows", 0),
                "raw_file": raw_file,
            }
    return index


def load_spy_bar_index(dataset_ids: set[str]) -> dict[str, dict[str, bool]]:
    by_date: dict[str, dict[str, bool]] = defaultdict(lambda: {"has_0935": False, "has_1545": False})
    for dataset_id in sorted(dataset_ids):
        path = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / dataset_id / "spy_bar.jsonl"
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                ts = row.get("timestamp_et", "")
                date = ts[:10]
                if ts[11:19] == "09:35:00":
                    by_date[date]["has_0935"] = True
                if ts[11:19] == "15:45:00":
                    by_date[date]["has_1545"] = True
    return dict(by_date)


def option_window_status(index: dict[str, dict[str, Any]], date: str, window: str) -> dict[str, Any]:
    matches = [
        value
        for name, value in index.items()
        if name.startswith(f"{date}_{window}") and name.endswith(".dbn.zst")
    ]
    row_count = sum(int(item.get("output_rows") or 0) for item in matches)
    return {
        "present": bool(matches),
        "positive_output_rows": row_count > 0,
        "output_rows": row_count,
        "matched_file_count": len(matches),
    }


def build_train_inventory(lower_proxy: dict[str, Any], option_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = [
        row
        for row in lower_proxy.get("daily_rows", [])
        if row.get("split") == "in_sample" and row.get("existing_trade_count", 0) > 0 and is_non_risk(row)
    ]
    dataset_ids = {str(row.get("dataset")) for row in rows if row.get("dataset")}
    spy_index = load_spy_bar_index(dataset_ids)
    date_rows: list[dict[str, Any]] = []
    missing: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        date = row["date"]
        spy = spy_index.get(date, {"has_0935": False, "has_1545": False})
        entry = option_window_status(option_index, date, "entry_a_0935")
        close = option_window_status(option_index, date, "forced_close_1545")
        if not spy["has_0935"]:
            missing["spy_0935"].append(date)
        if not spy["has_1545"]:
            missing["spy_1545"].append(date)
        if not entry["positive_output_rows"]:
            missing["entry_option_chain"].append(date)
        if not close["positive_output_rows"]:
            missing["forced_close_option_quotes"].append(date)
        date_rows.append(
            {
                "date": date,
                "dataset": row.get("dataset"),
                "vix_bucket": vix_bucket(row),
                "day_ready_for_local_geometry_parser": bool(
                    spy["has_0935"]
                    and spy["has_1545"]
                    and entry["positive_output_rows"]
                    and close["positive_output_rows"]
                ),
                "spy_0935": spy["has_0935"],
                "spy_1545": spy["has_1545"],
                "entry_option_output_rows": entry["output_rows"],
                "forced_close_option_output_rows": close["output_rows"],
            }
        )
    ready_count = sum(1 for row in date_rows if row["day_ready_for_local_geometry_parser"])
    return {
        "target_set_id": "train_candidate_geometry_backfill",
        "target_date_count": len(date_rows),
        "ready_for_local_geometry_parser_count": ready_count,
        "cache_status": "local_cache_complete_for_inventory" if ready_count == len(date_rows) else "local_cache_partial",
        "missing_by_field": {key: values for key, values in sorted(missing.items())},
        "request_count_needed_now": 0 if ready_count == len(date_rows) else len(set().union(*missing.values())),
        "regime_counts": dict(Counter(row["vix_bucket"] for row in date_rows)),
        "date_rows": date_rows,
    }


def summarize_control_pack(path: Path, label: str) -> dict[str, Any]:
    data = load_json(path)
    diagnostics = data.get("date_diagnostics", [])
    ready_dates = data.get("aggregate_diagnostic", {}).get("candidate_trade_data_ready_dates", [])
    spy_pass_count = sum(1 for item in diagnostics if item.get("spy_underlying_import", {}).get("status") == "pass")
    entry_ready = sum(
        1
        for item in diagnostics
        if (item.get("entry_exit_quote_availability", {}).get("entry_window_zero_dte_valid_mid_rows") or 0) > 0
    )
    close_ready = sum(
        1
        for item in diagnostics
        if (item.get("entry_exit_quote_availability", {}).get("forced_close_zero_dte_valid_mid_rows") or 0) > 0
    )
    return {
        "label": label,
        "source_path": str(path.relative_to(PROJECT_ROOT)),
        "date_count": len(diagnostics),
        "candidate_ready_dates": ready_dates,
        "candidate_ready_count": len(ready_dates),
        "spy_bar_pass_count": spy_pass_count,
        "entry_quote_ready_count": entry_ready,
        "forced_close_quote_ready_count": close_ready,
    }


def build_normal_control_inventory() -> dict[str, Any]:
    packs = [
        summarize_control_pack(NORMAL_CONTROL_PATH, "normal_control_low_normal_vix"),
        summarize_control_pack(POST_CONTROL_PATH, "post_stress_normalization_control"),
    ]
    return {
        "target_set_id": "normal_control_geometry_pack",
        "cache_status": "local_cache_complete_for_candidate_ready_dates",
        "pack_count": len(packs),
        "total_dates": sum(item["date_count"] for item in packs),
        "candidate_ready_dates": [date for item in packs for date in item["candidate_ready_dates"]],
        "candidate_ready_count": sum(item["candidate_ready_count"] for item in packs),
        "request_count_needed_now": 0,
        "packs": packs,
    }


def build_stress_inventory() -> dict[str, Any]:
    review = load_json(STRESS_REVIEW_PATH)
    ibkr = load_json(IBKR_READINESS_PATH) if IBKR_READINESS_PATH.exists() else {}
    counts = review.get("counts", {})
    quote_dates = counts.get("quote_available_dates", [])
    return {
        "target_set_id": "stress_regime_geometry_pack",
        "cache_status": "option_quotes_present_underlying_bars_blocked",
        "quote_available_dates": quote_dates,
        "quote_available_day_count": len(quote_dates),
        "missing_underlying_bar_dates": quote_dates,
        "missing_underlying_bar_count": len(quote_dates),
        "request_count_needed_now": 0,
        "blocked_source_status": {
            "databento_equs_mini_2022_unavailable": True,
            "ibkr_readiness_status": ibkr.get("status", "unknown"),
            "ibkr_open_ports": ibkr.get("open_ports", []),
        },
    }


def build_oos_inventory() -> dict[str, Any]:
    return {
        "target_set_id": "oos_locked_rule_evaluation_pack",
        "cache_status": "future_preregistration_only",
        "request_count_needed_now": 0,
        "reason": "OOS data must wait for a train-locked rule and a separate no-OOS-tuning preregistration.",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    targets = {item["target_set_id"]: item for item in payload["target_sets"]}
    train = targets["train_candidate_geometry_backfill"]
    normal = targets["normal_control_geometry_pack"]
    stress = targets["stress_regime_geometry_pack"]
    return "\n".join(
        [
            "# H-A2.64 Targeted Geometry Cache Inventory And Cost Plan",
            "",
            "## Result",
            f"- Status: `{payload['status']}`",
            f"- Evidence tier: `{payload['evidence_tier']}`",
            f"- Network used: `{payload['guardrails']['network_used']}`",
            f"- Paid data used: `{payload['guardrails']['paid_data_used']}`",
            f"- Paid download allowed: `{payload['guardrails']['paid_download_allowed']}`",
            "",
            "## Target-Set Summary",
            "| Target set | Cache status | Ready / count | Requests now |",
            "|:--|:--|:--|--:|",
            f"| `train_candidate_geometry_backfill` | `{train['cache_status']}` | {train['ready_for_local_geometry_parser_count']} / {train['target_date_count']} | {train['request_count_needed_now']} |",
            f"| `normal_control_geometry_pack` | `{normal['cache_status']}` | {normal['candidate_ready_count']} candidate-ready / {normal['total_dates']} dates | {normal['request_count_needed_now']} |",
            f"| `stress_regime_geometry_pack` | `{stress['cache_status']}` | {stress['quote_available_day_count']} quote-available / {stress['missing_underlying_bar_count']} missing underlying bars | {stress['request_count_needed_now']} |",
            "| `oos_locked_rule_evaluation_pack` | `future_preregistration_only` | blocked | 0 |",
            "",
            "## Cost Estimate",
            f"- Status: `{payload['cost_estimate']['status']}`",
            f"- Selected key env: `{payload['cost_estimate']['selected_key_env']}`",
            "- Reason: Workstream 1 remains open, so live metadata cost calls are deferred.",
            "",
            "## Next Safe Action",
            payload["next_safe_action"],
            "",
        ]
    )


def build_report() -> dict[str, Any]:
    plan = load_json(PLAN_PATH)
    lower_proxy = load_json(LOWER_PROXY_PATH)
    option_index = load_option_summary_index()
    target_sets = [
        build_train_inventory(lower_proxy, option_index),
        build_normal_control_inventory(),
        build_stress_inventory(),
        build_oos_inventory(),
    ]
    return {
        "schema_version": "h_a2_targeted_geometry_cache_inventory_v1",
        "artifact_type": "cache_inventory_and_cost_plan",
        "hypothesis_id": "H-A2",
        "experiment_id": "h_a2_targeted_geometry_cache_inventory_and_cost_estimate",
        "step_id": "H-A2.64",
        "status": "complete_no_download_cost_estimate_deferred",
        "evidence_tier": "E0",
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_preregistration": str(PLAN_PATH.relative_to(PROJECT_ROOT)),
        "source_preregistration_status": plan.get("status"),
        "target_sets": target_sets,
        "cost_estimate": {
            "status": "deferred_by_technical_dd_workstream_1_freeze",
            "live_metadata_call_used": False,
            "estimated_cost_usd": None,
            "selected_key_env": None,
            "reason": "Technical DD Workstream 1 remains open; this artifact inventories cache and plans requests only.",
        },
        "grouped_request_plan": {
            "status": "no_download",
            "provider_request_count_now": 0,
            "download_request_count_now": 0,
            "notes": [
                "Train and normal/control geometry should proceed first as local parser work.",
                "Stress-regime geometry is blocked on real 2022 SPY underlying bars, not on local option quote cache.",
                "OOS evaluation remains future-preregistration-only.",
            ],
        },
        "guardrails": {
            "network_used": False,
            "paid_data_used": False,
            "live_metadata_cost_call_used": False,
            "paid_download_allowed": False,
            "new_provider_used": False,
            "broker_request_used": False,
            "ibkr_request_used": False,
            "llm_call_used": False,
            "oos_rule_evaluation_used": False,
            "paper_trading_allowed": False,
            "operational_validation_allowed": False,
            "real_money_allowed": False,
        },
        "allowed_claims": [
            "H-A2.64 inventories existing cache coverage for the H-A2.63 target sets.",
            "Train and normal/control target sets can move to local geometry-parser work without new downloads.",
            "Stress-regime exact geometry remains blocked by missing real 2022 SPY underlying bars.",
        ],
        "forbidden_claims": [
            "Do not claim H-A2 edge is validated.",
            "Do not claim a breakeven-aware rule is selected for trading.",
            "Do not approve paid download, OOS rule evaluation, paper trading, operational validation, or real-money trading.",
            "Do not claim E2 acceptance-grade evidence.",
        ],
        "next_safe_action": (
            "Pre-register or implement a local H-A2 train/control geometry parser using existing cached "
            "SPY bars and OPRA quotes. Keep it local/no-paid/no-OOS-rule-selection until train geometry "
            "fields are computed and validated."
        ),
        "interpreter": interpreter_metadata(),
    }


def main() -> int:
    payload = build_report()
    write_json(OUTPUT_JSON, payload)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "output": str(OUTPUT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

