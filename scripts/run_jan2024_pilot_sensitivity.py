from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_jan2024_pilot_pnl import ADAPTER_SUMMARY_PATH, QUOTE_PATH, run_pilot_pnl


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = PROJECT_ROOT / "reports" / "pilots" / "jan_2024_pilot_sensitivity_summary.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "pilots" / "jan_2024_pilot_sensitivity_report.md"
SEARCH_LOG_PATH = PROJECT_ROOT / "reports" / "experiments" / "search_logs" / "jan_2024_pilot_sensitivity_search_log.jsonl"


def default_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    for fill_model in ["mid", "half_spread", "full_spread_stress"]:
        for fee_per_contract in [0.0, 0.65, 1.0]:
            scenarios.append(
                {
                    "scenario_id": f"{fill_model}_fee_{str(fee_per_contract).replace('.', '_')}_strict",
                    "fill_model": fill_model,
                    "fee_per_contract": fee_per_contract,
                    "close_fallback": "strict_1545",
                }
            )
    scenarios.append(
        {
            "scenario_id": "mid_fee_0_nearest_close",
            "fill_model": "mid",
            "fee_per_contract": 0.0,
            "close_fallback": "nearest_1545_window",
        }
    )
    return scenarios


def run_sensitivity(
    adapter_summary_path: Path = ADAPTER_SUMMARY_PATH,
    quote_path: Path = QUOTE_PATH,
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
    search_log_path: Path = SEARCH_LOG_PATH,
) -> dict[str, Any]:
    scenario_results = []
    scenarios = default_scenarios()
    for trial_index, scenario in enumerate(scenarios, start=1):
        summary = run_pilot_pnl(
            adapter_summary_path=adapter_summary_path,
            quote_path=quote_path,
            summary_path=summary_path.with_name(f"{scenario['scenario_id']}.tmp.json"),
            report_path=report_path.with_name(f"{scenario['scenario_id']}.tmp.md"),
            fee_per_contract=scenario["fee_per_contract"],
            fill_model=scenario["fill_model"],
            close_fallback=scenario["close_fallback"],
        )
        scenario_results.append(compact_result(scenario, summary, trial_index))
    cleanup_tmp_files(summary_path.parent)
    write_search_log(scenario_results, search_log_path)
    result = {
        "mode": "pilot_sensitivity_only",
        "evidence_warning": "One-month pilot sensitivity; not enough evidence for strategy acceptance.",
        "scenario_count": len(scenario_results),
        "best_scenario": max(scenario_results, key=lambda row: row["total_net_pnl"]),
        "worst_scenario": min(scenario_results, key=lambda row: row["total_net_pnl"]),
        "scenarios": scenario_results,
        "search_log": search_log_metadata(scenario_results, search_log_path),
        "parameter_grid": parameter_grid(scenarios),
        "selection_rule": {
            "selected_metric": "total_net_pnl",
            "selected_best_scenario_id": max(scenario_results, key=lambda row: row["total_net_pnl"])["scenario_id"],
            "acceptance_use": "diagnostic_only_not_oos_tuning",
        },
        "dsr_assessment": dsr_assessment(scenario_results),
        "pilot_decision": pilot_decision(scenario_results),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(result), encoding="utf-8")
    return result


def compact_result(scenario: dict[str, Any], summary: dict[str, Any], trial_index: int = 1) -> dict[str, Any]:
    return {
        "trial_index": trial_index,
        **scenario,
        "candidate_days": summary["candidate_days"],
        "closed_trades": summary["closed_trades"],
        "skipped_trades": summary["skipped_trades"],
        "total_net_pnl": summary["total_net_pnl"],
        "average_net_pnl": summary["average_net_pnl"],
        "win_rate": summary["win_rate"],
        "worst_trade": summary["worst_trade"],
        "best_trade": summary["best_trade"],
        "max_drawdown": summary["max_drawdown"],
        "sharpe_proxy": summary["sharpe_proxy"],
        "status_counts": summary["status_counts"],
    }


def parameter_grid(scenarios: list[dict[str, Any]]) -> dict[str, list[Any]]:
    return {
        "fill_model": sorted({scenario["fill_model"] for scenario in scenarios}),
        "fee_per_contract": sorted({scenario["fee_per_contract"] for scenario in scenarios}),
        "close_fallback": sorted({scenario["close_fallback"] for scenario in scenarios}),
    }


def write_search_log(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(search_log_record(row), ensure_ascii=False, sort_keys=True) + "\n")


def search_log_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "parameter_search_trial",
        "schema_version": "m3_search_log_v1",
        "experiment_id": "jan_2024_pilot_sensitivity",
        "trial_index": row["trial_index"],
        "scenario_id": row["scenario_id"],
        "parameters": {
            "fill_model": row["fill_model"],
            "fee_per_contract": row["fee_per_contract"],
            "close_fallback": row["close_fallback"],
        },
        "metrics": {
            "candidate_days": row["candidate_days"],
            "closed_trades": row["closed_trades"],
            "skipped_trades": row["skipped_trades"],
            "total_net_pnl": row["total_net_pnl"],
            "average_net_pnl": row["average_net_pnl"],
            "win_rate": row["win_rate"],
            "worst_trade": row["worst_trade"],
            "best_trade": row["best_trade"],
            "max_drawdown": row["max_drawdown"],
            "sharpe_proxy": row["sharpe_proxy"],
        },
    }


def search_log_metadata(rows: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "record_type": "parameter_search_trial",
        "trial_count": len(rows),
        "all_trials_recorded": True,
        "selection_bias_warning": "Diagnostic pilot grid; do not select production parameters from this output.",
    }


def dsr_assessment(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "blocked",
        "reason": "DSR is not computed for this pilot sensitivity output because it is under-sampled, uses a one-month diagnostic window, and does not provide a full acceptance-grade return distribution.",
        "trial_count": len(rows),
        "selected_metric": "total_net_pnl",
        "required_before_acceptance": [
            "full search log for the target experiment family",
            "trial return series or Sharpe estimates across all trials",
            "effective number of trials",
            "null Sharpe threshold",
            "skew/kurtosis/autocorrelation diagnostics",
        ],
    }


def pilot_decision(results: list[dict[str, Any]]) -> dict[str, Any]:
    strict_results = [row for row in results if row["close_fallback"] == "strict_1545"]
    worst_stress = min((row for row in strict_results if row["fill_model"] == "full_spread_stress"), key=lambda row: row["total_net_pnl"])
    missing_close = max(row["skipped_trades"] for row in strict_results)
    reasons = [
        f"worst full-spread stress total_net_pnl={worst_stress['total_net_pnl']}",
        f"strict close skipped_trades={missing_close}",
        "trade_count is far below N >= 500",
    ]
    if worst_stress["total_net_pnl"] > 0 and missing_close <= 2:
        status = "healthy_enough_for_wider_data_pilot"
        reasons.append("pilot remains positive under stress, but this is not strategy acceptance")
    else:
        status = "needs_design_review_before_wider_data"
        reasons.append("pilot is fragile under stress or close data coverage is weak")
    return {"status": status, "reasons": reasons}


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Databento Pilot Sensitivity Report",
        "",
        "## สถานะ",
        "- ข้อสรุป: ยังสรุปไม่ได้",
        f"- Pilot decision: `{result['pilot_decision']['status']}`",
        "- รายงานนี้ใช้เพื่อดูความไวของ pilot เท่านั้น ไม่ใช่หลักฐานว่า strategy มี edge",
        "",
        "## Decision Reasons",
    ]
    lines.extend(f"- {reason}" for reason in result["pilot_decision"]["reasons"])
    lines.extend(
        [
            "",
            "## Search Log And DSR",
            f"- Search log: `{result['search_log']['path']}`",
            f"- Trial count: {result['search_log']['trial_count']}",
            f"- Selected metric: `{result['selection_rule']['selected_metric']}`",
            f"- DSR status: `{result['dsr_assessment']['status']}`",
            f"- DSR reason: {result['dsr_assessment']['reason']}",
            "",
            "## Scenario Summary",
            "| Scenario | Fill | Fee/Contract | Close | Closed | Skipped | Net PnL | Worst | MDD |",
            "|:--|:--|--:|:--|--:|--:|--:|--:|--:|",
        ]
    )
    for row in result["scenarios"]:
        lines.append(
            f"| `{row['scenario_id']}` | `{row['fill_model']}` | {row['fee_per_contract']} | `{row['close_fallback']}` | "
            f"{row['closed_trades']} | {row['skipped_trades']} | {row['total_net_pnl']} | {row['worst_trade']} | {row['max_drawdown']} |"
        )
    lines.extend(
        [
            "",
            "## ข้อจำกัด",
            "- ใช้เฉพาะ pilot window และมี closed trades น้อยมาก",
            "- ยังไม่รวม VIX/VXV, macro, LLM gate, target/stop intraday, fill retry และ Sub-System B",
            "- `nearest_1545_window` เป็น diagnostic เท่านั้น ไม่ควรใช้แทน forced-close exact quote โดยไม่ทดสอบเพิ่ม",
            "",
        ]
    )
    return "\n".join(lines)


def cleanup_tmp_files(folder: Path) -> None:
    if not folder.exists():
        return
    for path in folder.glob("*.tmp.*"):
        path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Databento pilot sensitivity scenarios.")
    parser.add_argument("--adapter-summary-path", type=Path, default=ADAPTER_SUMMARY_PATH)
    parser.add_argument("--quote-path", type=Path, default=QUOTE_PATH)
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    parser.add_argument("--search-log-path", type=Path, default=SEARCH_LOG_PATH)
    args = parser.parse_args()
    result = run_sensitivity(args.adapter_summary_path, args.quote_path, args.summary_path, args.report_path, args.search_log_path)
    print(json.dumps({key: value for key, value in result.items() if key != "scenarios"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
