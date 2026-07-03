from __future__ import annotations

import json
import sys
from datetime import datetime, time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = PROJECT_ROOT / "reports" / "baselines"
SUMMARY_PATH = REPORT_ROOT / "m4_execution_rule_compliance_audit.json"
REPORT_PATH = REPORT_ROOT / "m4_execution_rule_compliance_audit.md"

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import run_jan2024_pilot_pnl as pnl
import run_m4_subsystem_b_feasibility as subsystem_b


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_component_summaries() -> list[Path]:
    roots = [
        REPORT_ROOT / "subsystem_a_components",
        REPORT_ROOT / "m4_exit_behavior_components",
    ]
    paths: list[Path] = []
    for root in roots:
        if root.exists():
            paths.extend(sorted(root.glob("**/*_summary.json")))
    return paths


def audit_component_trades(paths: list[Path]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    counts = {
        "component_summary_files": 0,
        "candidate_days": 0,
        "closed_trades": 0,
        "skipped_trades": 0,
        "skipped_missing_entry_quote": 0,
        "skipped_missing_close_quote": 0,
        "entry_fill_rows_checked": 0,
        "close_timestamp_rows_checked": 0,
    }
    exit_reason_counts: dict[str, int] = {}
    close_time_counts: dict[str, int] = {}

    for path in paths:
        summary = load_json(path)
        counts["component_summary_files"] += 1
        counts["candidate_days"] += int(summary.get("candidate_days", 0))
        counts["closed_trades"] += int(summary.get("closed_trades", 0))
        counts["skipped_trades"] += int(summary.get("skipped_trades", 0))
        for status, value in summary.get("status_counts", {}).items():
            exit_reason_counts[status] = exit_reason_counts.get(status, 0) + int(value)

        for trade in summary.get("trades", []):
            status = str(trade.get("status", ""))
            reasons = " ".join(str(reason) for reason in trade.get("reasons", [])).lower()
            if not status.startswith("closed_"):
                if "entry" in reasons:
                    counts["skipped_missing_entry_quote"] += 1
                if "close" in reasons:
                    counts["skipped_missing_close_quote"] += 1
                continue

            entry_fills = trade.get("entry_fills", [])
            if not entry_fills:
                blockers.append(f"{path}: closed trade {trade.get('date')} has no entry_fills evidence")
            for fill in entry_fills:
                counts["entry_fill_rows_checked"] += 1
                order_type = str(fill.get("order_type", "")).upper()
                fill_model = str(fill.get("fill_model", "")).lower()
                if order_type == "MARKET" or fill_model == "market":
                    blockers.append(f"{path}: market entry evidence on {trade.get('date')} fill {fill.get('fill_id')}")

            close_timestamps = trade.get("close_timestamps_by_leg_id", {})
            if not close_timestamps:
                blockers.append(f"{path}: closed trade {trade.get('date')} has no close_timestamps_by_leg_id evidence")
            for timestamp in close_timestamps.values():
                counts["close_timestamp_rows_checked"] += 1
                time_text = str(timestamp)[11:19]
                close_time_counts[time_text] = close_time_counts.get(time_text, 0) + 1
                if datetime.fromisoformat(str(timestamp)).time() > time(15, 45):
                    blockers.append(f"{path}: close timestamp after 15:45 ET on {trade.get('date')}: {timestamp}")

    if counts["skipped_missing_entry_quote"] == 0:
        warnings.append("No real M4 artifact currently contains a missing-entry-quote skipped trade; skip behavior is verified by synthetic probe.")

    return {
        "blockers": blockers,
        "warnings": warnings,
        "counts": counts,
        "status_counts": exit_reason_counts,
        "close_time_counts": dict(sorted(close_time_counts.items())),
    }


def synthetic_subsystem_a_probe() -> dict[str, Any]:
    day = {
        "date": "2024-01-08",
        "direction": "call",
        "orb_signal": {"breakout_timestamp_et": "2024-01-08T09:35:00-05:00"},
        "legs": [
            {"leg_id": "long", "right": "call", "strike": 470.0, "expiration_date": "2024-01-08", "side": "buy", "quantity": 1},
            {"leg_id": "short", "right": "call", "strike": 472.0, "expiration_date": "2024-01-08", "side": "sell", "quantity": 1},
        ],
    }
    quotes = pnl.index_quotes(
        [
            quote("2024-01-08T09:35:00-05:00", "call", 470.0, 1.0, 1.2),
            quote("2024-01-08T15:45:00-05:00", "call", 470.0, 2.0, 2.2),
            quote("2024-01-08T15:45:00-05:00", "call", 472.0, 0.9, 1.1),
        ]
    )
    missing_entry = pnl.evaluate_candidate_day(day, quotes, fee_per_contract=0.0)

    future_close_quotes = pnl.index_quotes(
        [
            quote("2024-01-08T09:35:00-05:00", "call", 470.0, 1.0, 1.2),
            quote("2024-01-08T09:35:00-05:00", "call", 472.0, 0.4, 0.6),
            quote("2024-01-08T15:46:00-05:00", "call", 470.0, 2.0, 2.2),
            quote("2024-01-08T15:46:00-05:00", "call", 472.0, 0.9, 1.1),
        ]
    )
    future_close = pnl.evaluate_candidate_day(day, future_close_quotes, fee_per_contract=0.0, close_fallback="nearest_1545_window")

    return {
        "missing_entry_quote_status": missing_entry["status"],
        "missing_entry_quote_reasons": missing_entry.get("reasons", []),
        "future_close_quote_status": future_close["status"],
        "future_close_quote_reasons": future_close.get("reasons", []),
    }


def audit_subsystem_b_policy(summary_path: Path = REPORT_ROOT / "subsystem_b_put_ratio_feasibility_summary.json") -> dict[str, Any]:
    summary = load_json(summary_path)
    close_probe = subsystem_b.choose_close_timestamp(
        {
            "2024-01-08T15:46:00-05:00": {},
            "2024-01-08T15:44:00-05:00": {},
        }
    )
    blockers = []
    methodology = summary.get("methodology", {})
    if methodology.get("exit_model") != "forced_close_1545":
        blockers.append("Sub-System B summary does not declare forced_close_1545 exit_model.")
    if close_probe != "2024-01-08T15:44:00-05:00":
        blockers.append("Sub-System B close timestamp selector can choose a timestamp after 15:45 ET.")
    return {
        "blockers": blockers,
        "methodology": {
            "entry_time": methodology.get("entry_time"),
            "exit_model": methodology.get("exit_model"),
        },
        "status_counts": summary.get("status_counts", {}),
        "close_selector_probe": close_probe,
    }


def quote(timestamp: str, right: str, strike: float, bid: float, ask: float) -> dict[str, Any]:
    return {
        "quote_timestamp_et": timestamp,
        "right": right,
        "strike": strike,
        "expiration_date": timestamp[:10],
        "bid": bid,
        "ask": ask,
    }


def run_audit(summary_path: Path = SUMMARY_PATH, report_path: Path = REPORT_PATH) -> dict[str, Any]:
    component_audit = audit_component_trades(iter_component_summaries())
    synthetic_probe = synthetic_subsystem_a_probe()
    subsystem_b_audit = audit_subsystem_b_policy()

    blockers = [*component_audit["blockers"], *subsystem_b_audit["blockers"]]
    warnings = list(component_audit["warnings"])
    if synthetic_probe["missing_entry_quote_status"] != "missing_quotes" or not any(
        "entry" in reason for reason in synthetic_probe["missing_entry_quote_reasons"]
    ):
        blockers.append("Sub-System A missing-entry-quote probe did not skip the trade.")
    if synthetic_probe["future_close_quote_status"] != "missing_quotes":
        blockers.append("Sub-System A nearest close fallback accepted a quote after 15:45 ET.")

    result = {
        "record_type": "m4_execution_rule_compliance_audit",
        "schema_version": "m4_execution_rule_compliance_audit_v1",
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "warnings": warnings,
        "rules": {
            "entry_market_orders": "Entry market orders are prohibited.",
            "unfilled_entry_skip": "If entry quotes/fills are unavailable, the candidate is skipped.",
            "latest_close": "No modeled position may close after 15:45:00 ET.",
        },
        "component_trade_audit": component_audit,
        "subsystem_a_synthetic_probe": synthetic_probe,
        "subsystem_b_policy_audit": subsystem_b_audit,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(result), encoding="utf-8")
    return result


def render_report(result: dict[str, Any]) -> str:
    counts = result["component_trade_audit"]["counts"]
    return "\n".join(
        [
            "# M4 Execution Rule Compliance Audit",
            "",
            f"- Status: `{result['status']}`",
            f"- Blockers: `{len(result['blockers'])}`",
            f"- Warnings: `{len(result['warnings'])}`",
            "",
            "## Rules Checked",
            "- Entry market orders are prohibited.",
            "- Missing entry quote/fill evidence must skip the trade.",
            "- No modeled close timestamp may be after 15:45:00 ET.",
            "",
            "## Evidence Summary",
            f"- Component summary files checked: `{counts['component_summary_files']}`",
            f"- Candidate days checked: `{counts['candidate_days']}`",
            f"- Closed trades checked: `{counts['closed_trades']}`",
            f"- Skipped trades checked: `{counts['skipped_trades']}`",
            f"- Entry fill rows checked: `{counts['entry_fill_rows_checked']}`",
            f"- Close timestamp rows checked: `{counts['close_timestamp_rows_checked']}`",
            "",
            "## Close Time Counts",
            "```json",
            json.dumps(result["component_trade_audit"]["close_time_counts"], indent=2, sort_keys=True),
            "```",
            "",
            "## Sub-System A Probe",
            "```json",
            json.dumps(result["subsystem_a_synthetic_probe"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Sub-System B Policy Audit",
            "```json",
            json.dumps(result["subsystem_b_policy_audit"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Warnings",
            *[f"- {warning}" for warning in result["warnings"]],
            "",
            "## Blockers",
            *([f"- {blocker}" for blocker in result["blockers"]] if result["blockers"] else ["- None"]),
            "",
        ]
    )


def main() -> int:
    result = run_audit()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
