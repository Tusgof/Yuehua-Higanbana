from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import data_root
from lib.io import load_json, load_jsonl
from lib.report import render_markdown_report, write_report_pair
from lib.statistics import minimum_track_record_length


DATE_PATTERN = re.compile(r"20\d{2}-\d{2}-\d{2}")
DEVELOPMENT_OUTCOMES_CUTOFF = "2026-04-24"
DEFAULT_INVENTORY_JSON = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_orb_0936_untouched_inventory.json"
DEFAULT_INVENTORY_MD = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_orb_0936_untouched_inventory.md"
DEFAULT_COST_JSON = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_orb_0936_cost_plan.json"
DEFAULT_COST_MD = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_orb_0936_cost_plan.md"
VIEWED_OUTCOME_ARTIFACTS = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_independent_validation_import_diagnostic.json",
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_import_diagnostic.json",
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_post_stress_normalization_control_import_diagnostic.json",
    PROJECT_ROOT / "reports" / "experiments" / "h_a2_fresh_oos_timestamp_clean_checkpoint.json",
)


def discover_date_named_raw_files(raw_root: Path) -> dict[str, list[Path]]:
    files_by_date: dict[str, list[Path]] = {}
    if not raw_root.exists():
        return files_by_date
    for path in raw_root.rglob("*.dbn.zst"):
        if any(part.startswith("_integrity_") for part in path.parts):
            continue
        match = DATE_PATTERN.search(path.name)
        if match:
            files_by_date.setdefault(match.group(0), []).append(path)
    return {key: sorted(value) for key, value in sorted(files_by_date.items())}


def viewed_dates_from_artifacts(paths: tuple[Path, ...] = VIEWED_OUTCOME_ARTIFACTS) -> set[str]:
    dates: set[str] = set()
    for path in paths:
        if path.exists():
            dates.update(DATE_PATTERN.findall(path.read_text(encoding="utf-8")))
    return dates


def classify_local_dates(local_dates: set[str], viewed_dates: set[str]) -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    for trade_date in sorted(local_dates):
        if trade_date <= "2024-12-31":
            reason = "legacy_2022_stress_or_2023_2024_strategy_development_window"
        elif trade_date in viewed_dates:
            reason = "date_present_in_completed_h_a2_outcome_or_import_diagnostic"
        else:
            reason = "none"
        rows.append(
            {
                "date": trade_date,
                "status": "contaminated_not_fresh" if reason != "none" else "untouched_local_candidate",
                "exclusion_reason": reason,
            }
        )
    untouched = [row["date"] for row in rows if row["status"] == "untouched_local_candidate"]
    return {"rows": rows, "untouched_dates": untouched}


def checksum_metadata_summary(files_by_date: dict[str, list[Path]], root: Path) -> dict[str, Any]:
    registry_path = root / "registry" / "paid_artifact_checksums.jsonl"
    registry_rows = load_jsonl(registry_path) if registry_path.exists() else []
    registry_by_path = {str(row.get("path", "")).replace("\\", "/"): row for row in registry_rows}
    checked = 0
    registered = 0
    dual_hash_metadata = 0
    missing_paths: list[str] = []
    for paths in files_by_date.values():
        for path in paths:
            checked += 1
            relative = path.relative_to(root).as_posix()
            row = registry_by_path.get(relative)
            if row is None:
                missing_paths.append(relative)
                continue
            registered += 1
            if _valid_sha256(row.get("sha256")) and _valid_sha256(row.get("canonical_content_sha256")):
                dual_hash_metadata += 1
    return {
        "registry_path": str(registry_path),
        "date_named_raw_file_count": checked,
        "registered_file_count": registered,
        "dual_hash_metadata_count": dual_hash_metadata,
        "missing_registry_paths": missing_paths,
        "status": "pass" if checked == registered == dual_hash_metadata else "blocked",
        "note": "This inventory checks committed checksum metadata only. The fixture/full integrity verification re-hashes file content.",
    }


def select_chronological_cost_dates(
    vix_rows: list[dict[str, Any]],
    high_macro_dates: set[str],
    local_dates: set[str],
    *,
    after_date: str,
    limit: int,
) -> list[dict[str, Any]]:
    ordered = sorted(vix_rows, key=lambda row: row["date"])
    selected: list[dict[str, Any]] = []
    for index in range(1, len(ordered)):
        trade_date = str(ordered[index]["date"])
        prior_vix = float(ordered[index - 1]["vix_close"])
        if trade_date <= after_date or trade_date in high_macro_dates or trade_date in local_dates or prior_vix >= 25:
            continue
        selected.append(
            {
                "date": trade_date,
                "prior_close_vix": round(prior_vix, 4),
                "vix_bucket": "low" if prior_vix < 15 else "normal",
                "macro_regime": "control_no_high_importance_event",
                "trend_regime": "pending_prior_only_spy_daily_history",
            }
        )
        if len(selected) == limit:
            break
    return selected


def mintrl_planning_scenarios() -> list[dict[str, Any]]:
    scenarios = []
    for observed_sharpe, null_sharpe in ((0.25, 0.0), (0.5, 0.0), (0.75, 0.0), (1.0, 0.0), (0.75, 0.5), (1.0, 0.5)):
        scenarios.append(
            {
                "observed_sharpe": observed_sharpe,
                "null_sharpe": null_sharpe,
                "idealized_mintrl": minimum_track_record_length(
                    observed_sharpe=observed_sharpe,
                    skewness=0.0,
                    raw_kurtosis=3.0,
                    null_sharpe=null_sharpe,
                    autocorrelation=0.0,
                ),
            }
        )
    return scenarios


def build_reports(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    raw_root = root / "raw" / "spy_0dte" / "databento"
    files_by_date = discover_date_named_raw_files(raw_root)
    local_dates = set(files_by_date)
    viewed_dates = viewed_dates_from_artifacts()
    classification = classify_local_dates(local_dates, viewed_dates)
    untouched = classification["untouched_dates"]
    integrity = checksum_metadata_summary(files_by_date, root)

    inventory = {
        "schema_version": "h_a2_orb_0936_untouched_inventory_v1",
        "artifact_type": "data_inventory",
        "status": "blocked_no_local_untouched_dates" if not untouched else "local_untouched_dates_available",
        "generated_date": "2026-07-15",
        "hypothesis_id": "H-A2",
        "experiment_id": "h_a2_orb_0936_validation",
        "mode": "local_metadata_only_no_target_outcome_parse",
        "development_outcomes_cutoff": DEVELOPMENT_OUTCOMES_CUTOFF,
        "local_date_count": len(local_dates),
        "contaminated_local_date_count": len(local_dates) - len(untouched),
        "untouched_local_date_count": len(untouched),
        "untouched_dates": untouched,
        "untouched_regime_counts": {
            "vix": {"low": 0, "normal": 0, "out_of_scope": 0, "unavailable": 0},
            "trend": {"uptrend": 0, "downtrend": 0, "unclassified": 0},
            "macro": {"high_importance": 0, "control": 0, "unavailable": 0},
        },
        "coverage_policy": {
            "availability": "A date must have SPY bars, complete two-leg 0DTE quotes at or after 09:37, and 15:45 close quotes.",
            "timestamp": "Signal 09:36 <= decision 09:36 <= first eligible entry quote 09:37.",
            "integrity": "Every paid raw artifact must have container and canonical-content SHA-256 metadata and pass full verification before a future run.",
            "current_coverage_result": "not_evaluated_because_no_date_survives_untouched_gate",
        },
        "integrity_metadata": integrity,
        "contamination_sources": {
            "legacy_window": "Every local date through 2024-12-31 was available during 2022 stress review or 2023-2024 strategy development.",
            "explicit_completed_artifacts": [str(path.relative_to(PROJECT_ROOT)) for path in VIEWED_OUTCOME_ARTIFACTS],
            "classification_rows": classification["rows"],
        },
        "sample_adequacy": {
            "exact_mintrl_status": "unknown_until_valid_timestamp_correct_returns_exist",
            "idealized_planning_scenarios": mintrl_planning_scenarios(),
            "local_data_sufficient": False,
            "reason": "There are zero local untouched dates before signal, quote, and integrity qualification.",
        },
        "guardrails": {
            "target_outcomes_parsed": False,
            "option_pnl_read": False,
            "experiment_run": False,
            "network_calls": 0,
            "paid_cost_usd": 0.0,
            "research_log_required": False,
        },
        "decision": "create_cost_plan_only_no_purchase",
    }

    vix_rows = load_jsonl(root / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl")
    macro_rows = load_jsonl(root / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl")
    high_macro_dates = {
        str(row["event_timestamp_et"])[:10]
        for row in macro_rows
        if row.get("importance") == "high"
    }
    target_dates = select_chronological_cost_dates(
        vix_rows,
        high_macro_dates,
        local_dates,
        after_date=DEVELOPMENT_OUTCOMES_CUTOFF,
        limit=20,
    )
    prior_download = load_json(PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_h_a2_fresh_oos_2025_2026.json")
    base_projection = round(float(prior_download["total_estimated_cost_usd"]), 6)
    approval_ceiling = round(base_projection * 1.15, 6)
    cost_plan = {
        "schema_version": "h_a2_orb_0936_cost_plan_v1",
        "artifact_type": "data_acquisition_cost_plan",
        "status": "awaiting_user_approval",
        "mode": "plan_only_no_network_no_purchase",
        "generated_date": "2026-07-15",
        "hypothesis_id": "H-A2",
        "named_gap": "No local untouched dates remain for timestamp-correct 09:36 ORB validation.",
        "decision_tree": {
            "q0_named_hypothesis_gap": "pass",
            "q1_cached_data_can_fill_gap": "no_zero_untouched_local_dates",
            "q2_initial_information_cohort": "20 chronological dates after the last viewed outcome date",
            "q3_acceptance": "not_approved_exact_MinTRL_and_candidate_density_unknown",
            "result": "present_cost_plan_for_user_approval_before_live_metadata_or_purchase",
        },
        "target_dates": target_dates,
        "target_date_count": len(target_dates),
        "target_regime_counts": {
            "vix": {
                "low": sum(row["vix_bucket"] == "low" for row in target_dates),
                "normal": sum(row["vix_bucket"] == "normal" for row in target_dates),
            },
            "macro": {"control": len(target_dates), "high_importance": 0},
            "trend": {"pending_prior_only_spy_daily_history": len(target_dates)},
        },
        "required_components": [
            {"dataset": "OPRA.PILLAR", "schema": "cbbo-1m", "symbol": "SPY.OPT", "window": "09:30-15:50 ET per target date"},
            {"dataset": "EQUS.MINI", "schema": "ohlcv-1m", "symbol": "SPY", "window": "regular session per target date"},
            {"dataset": "EQUS.MINI", "schema": "ohlcv-1d", "symbol": "SPY", "window": "2026-03-01 through final target date for prior-only SMA20 trend labels"},
        ],
        "cost_basis": {
            "method": "latest completed 20-date H-A2 actual estimate basis plus 15 percent contingency",
            "source": "reports/data_cost/databento_download_result_h_a2_fresh_oos_2025_2026.json",
            "source_date_count": 20,
            "source_estimated_cost_usd": base_projection,
            "base_projected_cost_usd": base_projection,
            "contingency_rate": 0.15,
            "user_approval_ceiling_usd": approval_ceiling,
            "daily_history_cost_status": "must_be_included_in_live_metadata_refresh_and_fit_inside_ceiling",
        },
        "budget_guard": {
            "selected_key_env": "DATABENTO_API_01",
            "account_provenance": "primary_existing_databento_account",
            "authorization_limit_usd": 50.0,
            "known_committed_usage_usd": 12.361983,
            "projected_usage_at_ceiling_usd": round(12.361983 + approval_ceiling, 6),
            "status": "pass_projection_only",
        },
        "sample_adequacy": {
            "exact_mintrl_status": "unknown_until_valid_returns_exist",
            "idealized_planning_scenarios": mintrl_planning_scenarios(),
            "cohort_role": "initial fixed-rule information cohort; not automatically E2 or sufficient",
            "expansion_rule": "No automatic expansion. Recompute MinTRL from valid returns and require a separate decision-tree cost artifact before more data.",
        },
        "authorization": {
            "user_approval_recorded": False,
            "live_metadata_call_performed": False,
            "download_performed": False,
            "purchase_allowed_by_this_artifact": False,
            "next_action": "User reviews this plan. A separate approved session must refresh live metadata cost and stop if total exceeds the ceiling.",
        },
        "guardrails": {
            "target_outcomes_parsed": False,
            "experiment_run": False,
            "network_calls": 0,
            "paid_cost_usd": 0.0,
            "paper_trading_allowed": False,
            "e2_claim_allowed": False,
        },
    }
    return inventory, cost_plan


def write_outputs(
    inventory: dict[str, Any],
    cost_plan: dict[str, Any],
    inventory_json: Path,
    inventory_md: Path,
    cost_json: Path,
    cost_md: Path,
) -> None:
    inventory_markdown = render_markdown_report(
        "H-A2 ORB 09:36 Untouched Data Inventory",
        [
            ("ผลสรุป", f"- สถานะ: `{inventory['status']}`\n- วันที่ local ทั้งหมด: `{inventory['local_date_count']}`\n- วันที่ untouched: `{inventory['untouched_local_date_count']}`\n- คำตัดสิน: `{inventory['decision']}`"),
            ("Regime ของข้อมูล Untouched", _json_block(inventory["untouched_regime_counts"])),
            ("ความเพียงพอของข้อมูล", _json_block(inventory["sample_adequacy"])),
            ("Timestamp และ Integrity", _json_block({"coverage_policy": inventory["coverage_policy"], "integrity_metadata": inventory["integrity_metadata"]})),
            ("ข้อห้าม", "รายงานนี้อ่านเฉพาะ metadata/provenance และไม่ parse target-day PnL หรือ option outcomes จึงไม่ใช่ผลทดลองและไม่ต้องเขียน research log"),
        ],
    )
    cost_markdown = render_markdown_report(
        "H-A2 ORB 09:36 Cost Plan",
        [
            ("สถานะ", f"- `{cost_plan['status']}`\n- Mode: `{cost_plan['mode']}`\n- ยังไม่อนุญาตให้ซื้อข้อมูล"),
            ("ขอบเขต", f"- วันที่เป้าหมาย: `{cost_plan['target_date_count']}`\n- หลัง cutoff: `{DEVELOPMENT_OUTCOMES_CUTOFF}`\n- Regime: `{json.dumps(cost_plan['target_regime_counts'], ensure_ascii=False)}`"),
            ("วันที่เป้าหมาย", "\n".join(f"- `{row['date']}`: prior VIX `{row['prior_close_vix']}`, `{row['vix_bucket']}`, `{row['macro_regime']}`" for row in cost_plan["target_dates"])),
            ("ประมาณการต้นทุน", _json_block(cost_plan["cost_basis"])),
            ("MinTRL", "ค่า MinTRL ที่แม่นยำยังไม่ทราบเพราะยังไม่มี valid timestamp-correct returns ตารางใน JSON เป็นเพียง idealized scenarios สำหรับวางแผน ห้ามใช้อนุมัติ E2"),
            ("ขั้นต่อไป", cost_plan["authorization"]["next_action"]),
        ],
    )
    write_report_pair(inventory, inventory_json, inventory_md, inventory_markdown)
    write_report_pair(cost_plan, cost_json, cost_md, cost_markdown)


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n```"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inventory untouched H-A2 09:36 data without reading outcomes.")
    parser.add_argument("--data-root", type=Path, default=data_root())
    parser.add_argument("--inventory-json", type=Path, default=DEFAULT_INVENTORY_JSON)
    parser.add_argument("--inventory-md", type=Path, default=DEFAULT_INVENTORY_MD)
    parser.add_argument("--cost-json", type=Path, default=DEFAULT_COST_JSON)
    parser.add_argument("--cost-md", type=Path, default=DEFAULT_COST_MD)
    args = parser.parse_args(argv)
    inventory, cost_plan = build_reports(args.data_root)
    write_outputs(inventory, cost_plan, args.inventory_json, args.inventory_md, args.cost_json, args.cost_md)
    print(json.dumps({"inventory": inventory, "cost_plan": cost_plan}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if inventory["integrity_metadata"]["status"] == "pass" and len(cost_plan["target_dates"]) == 20 else 1


if __name__ == "__main__":
    raise SystemExit(main())
