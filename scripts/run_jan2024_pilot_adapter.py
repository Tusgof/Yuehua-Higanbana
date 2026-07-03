from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parent))
from strategy_spec_m4 import StrategySpecError, compute_orb_signal, construct_subsystem_a_vertical


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BAR_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / "one_month_pilot" / "spy_bar.jsonl"
QUOTE_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / "one_month_pilot" / "option_quote.jsonl"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "pilots" / "jan_2024_pilot_adapter_summary.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "pilots" / "jan_2024_pilot_adapter_report.md"
RTH_START = "09:30:00"
RTH_END = "16:00:00"


def run_pilot_adapter(
    bar_path: Path = BAR_PATH,
    quote_path: Path = QUOTE_PATH,
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
) -> dict[str, Any]:
    bars = load_jsonl(bar_path)
    quotes = load_jsonl(quote_path)
    bars_by_date = group_by_date(bars, "timestamp_et")
    quotes_by_date = group_by_date(quotes, "quote_timestamp_et")
    dates = sorted(set(bars_by_date) | set(quotes_by_date))

    day_results = []
    for trade_date in dates:
        day_results.append(evaluate_trade_date(trade_date, bars_by_date.get(trade_date, []), quotes_by_date.get(trade_date, [])))

    summary = summarize_results(day_results, bars, quotes)
    summary["days"] = day_results
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary), encoding="utf-8")
    return summary


def evaluate_trade_date(trade_date: str, bars: list[dict[str, Any]], quotes: list[dict[str, Any]]) -> dict[str, Any]:
    rth_bars = [bar for bar in bars if is_rth(bar["timestamp_et"])]
    result: dict[str, Any] = {
        "date": trade_date,
        "bar_count": len(bars),
        "rth_bar_count": len(rth_bars),
        "quote_count": len(quotes),
        "status": "unknown",
        "reasons": [],
    }
    if not rth_bars:
        result["status"] = "missing_bars"
        result["reasons"].append("no RTH SPY bars")
        return result
    if not quotes:
        result["status"] = "missing_quotes"
        result["reasons"].append("no 0DTE option quotes")
        return result

    try:
        signal = compute_orb_signal(rth_bars)
    except StrategySpecError as exc:
        result["status"] = "signal_error"
        result["reasons"].append(str(exc))
        return result

    result["orb_signal"] = signal
    if signal["decision"] == "no_trade":
        result["status"] = "no_trade"
        result["reasons"].append("ORB close did not break opening range")
        return result

    entry_ts = signal["breakout_timestamp_et"]
    entry_quotes = [quote for quote in quotes if quote["quote_timestamp_et"] == entry_ts]
    result["entry_quote_count"] = len(entry_quotes)
    if not entry_quotes:
        result["status"] = "missing_entry_quotes"
        result["reasons"].append(f"no option quotes at {entry_ts}")
        return result

    direction = "call" if signal["decision"] == "call_breakout" else "put"
    try:
        legs = construct_subsystem_a_vertical(entry_quotes, direction=direction, underlying_price=signal["breakout_close"])
    except StrategySpecError as exc:
        result["status"] = "construction_error"
        result["reasons"].append(str(exc))
        return result

    result["status"] = "candidate_ready"
    result["direction"] = direction
    result["legs"] = legs
    result["reasons"].append("ORB signal and entry option quotes are available")
    return result


def summarize_results(day_results: list[dict[str, Any]], bars: list[dict[str, Any]], quotes: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: dict[str, int] = defaultdict(int)
    for result in day_results:
        status_counts[result["status"]] += 1
    return {
        "mode": "pilot_adapter_only",
        "evidence_warning": "This is a one-month data-join pilot, not strategy evidence.",
        "bar_rows": len(bars),
        "quote_rows": len(quotes),
        "calendar_days": len(day_results),
        "status_counts": dict(sorted(status_counts.items())),
        "candidate_ready_days": status_counts["candidate_ready"],
        "coverage_start": day_results[0]["date"] if day_results else None,
        "coverage_end": day_results[-1]["date"] if day_results else None,
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Databento Pilot Adapter Report",
        "",
        "## สถานะ",
        "- ข้อสรุป: ยังสรุปไม่ได้",
        "- ประเภทหลักฐาน: data-join pilot หนึ่งเดือน ไม่ใช่ผล backtest ที่พิสูจน์ edge",
        f"- Coverage: {summary['coverage_start']} to {summary['coverage_end']}",
        f"- SPY bar rows: {summary['bar_rows']}",
        f"- Option quote rows: {summary['quote_rows']}",
        f"- Candidate-ready days: {summary['candidate_ready_days']} / {summary['calendar_days']}",
        "",
        "## Status Counts",
        "```json",
        json.dumps(summary["status_counts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## ความหมาย",
        "- `candidate_ready` หมายถึงมี RTH SPY bars, มี ORB breakout/no-breakout logic, มี option quotes ที่เวลา entry, และประกอบ Sub-System A vertical ได้",
        "- รายงานนี้ยังไม่คำนวณ PnL, fill, slippage, stop, forced close, Sharpe, หรือ drawdown",
        "- ขั้นถัดไปคือใช้ candidate-ready days ไปต่อกับ fill/backtest engine แบบ bid/ask จริง",
        "",
    ]
    return "\n".join(lines)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"missing input file: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def group_by_date(records: list[dict[str, Any]], timestamp_field: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record[timestamp_field][:10]].append(record)
    return dict(grouped)


def is_rth(timestamp_et: str) -> bool:
    time_part = timestamp_et[11:19]
    return RTH_START <= time_part < RTH_END


def main() -> int:
    parser = argparse.ArgumentParser(description="Join Databento SPY bars and 0DTE option quotes for a pilot adapter summary.")
    parser.add_argument("--bar-path", type=Path, default=BAR_PATH)
    parser.add_argument("--quote-path", type=Path, default=QUOTE_PATH)
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    args = parser.parse_args()
    summary = run_pilot_adapter(args.bar_path, args.quote_path, args.summary_path, args.report_path)
    print(json.dumps({key: value for key, value in summary.items() if key != "days"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
