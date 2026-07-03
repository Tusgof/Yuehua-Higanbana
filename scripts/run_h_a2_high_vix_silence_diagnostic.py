from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from run_m4_subsystem_a_baseline import DATASETS
from run_m5_regime_filter_sensitivity import load_vix_vxv, previous_vix_record


REPORT_ROOT = PROJECT_ROOT / "reports" / "diagnostics"
SUMMARY_PATH = REPORT_ROOT / "h_a2_high_vix_silence_diagnostic_summary.json"
REPORT_PATH = REPORT_ROOT / "h_a2_high_vix_silence_diagnostic_report.md"
VIX_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl"

HIGH_VIX_THRESHOLD = 25.0
STRESS_VIX_THRESHOLD = 30.0


def run_diagnostic(
    vix_path: Path = VIX_PATH,
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
) -> dict[str, Any]:
    vix_rows = load_vix_vxv(vix_path)
    aug_datasets = [row for row in DATASETS if row[0].startswith("oos_2024_08")]
    daily_rows: list[dict[str, Any]] = []

    for label, split, adapter_name, normalized_name in aug_datasets:
        adapter_path = PROJECT_ROOT / "reports" / "pilots" / adapter_name
        quote_path = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name / "option_quote.jsonl"
        bar_path = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name / "spy_bar.jsonl"
        adapter = _load_json(adapter_path)
        quote_counts = _count_option_quotes_by_date(quote_path)
        bar_counts = _count_spy_bars_by_date(bar_path)

        for day in adapter["days"]:
            trade_date = day["date"]
            same_day_vix = _vix_record_for_date(trade_date, vix_rows)
            prior_vix = previous_vix_record(trade_date, vix_rows)
            daily_rows.append(
                {
                    "date": trade_date,
                    "dataset_label": label,
                    "split": split,
                    "adapter_status": day.get("status"),
                    "direction": day.get("direction"),
                    "same_day_vix_close": _close_or_none(same_day_vix),
                    "prior_vix_date": prior_vix.get("date") if prior_vix else None,
                    "prior_vix_close": _close_or_none(prior_vix),
                    "same_day_high_vix": _is_high(same_day_vix, HIGH_VIX_THRESHOLD),
                    "same_day_stress_vix": _is_high(same_day_vix, STRESS_VIX_THRESHOLD),
                    "prior_high_vix": _is_high(prior_vix, HIGH_VIX_THRESHOLD),
                    "prior_stress_vix": _is_high(prior_vix, STRESS_VIX_THRESHOLD),
                    "option_quote_rows": quote_counts.get(trade_date, 0),
                    "spy_bar_rows": bar_counts.get(trade_date, 0),
                    "has_option_quotes": quote_counts.get(trade_date, 0) > 0,
                    "has_spy_bars": bar_counts.get(trade_date, 0) > 0,
                }
            )

    candidate_rows = [row for row in daily_rows if row["adapter_status"] == "candidate_ready"]
    same_day_high_rows = [row for row in daily_rows if row["same_day_high_vix"]]
    prior_high_rows = [row for row in daily_rows if row["prior_high_vix"]]
    same_day_stress_rows = [row for row in daily_rows if row["same_day_stress_vix"]]
    prior_stress_rows = [row for row in daily_rows if row["prior_stress_vix"]]
    missing_vix = [row["date"] for row in daily_rows if row["same_day_vix_close"] is None or row["prior_vix_close"] is None]
    missing_market_data = [
        row["date"]
        for row in daily_rows
        if (row["same_day_high_vix"] or row["prior_high_vix"]) and (not row["has_option_quotes"] or not row["has_spy_bars"])
    ]

    result = {
        "record_type": "diagnostic_summary",
        "schema_version": "h_a2_high_vix_silence_diagnostic_v1",
        "diagnostic_id": "h_a2_high_vix_silence_diagnostic",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E1",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "diagnostic_result": _diagnostic_result(missing_vix, missing_market_data, same_day_high_rows, prior_high_rows),
        "tier_blockers": [
            "diagnostic_only",
            "under-sampled",
            "does_not_validate_h_a2_edge",
            "still_missing_reference_pre_break_coverage",
        ],
        "research_log_required": False,
        "no_new_paid_data": True,
        "methodology": {
            "scope": "Aug 2024 cached OOS data only, used to diagnose high-VIX labeling versus ORB silence.",
            "vix_policy_under_review": "M5.5 uses previous available VIX/VXV close before trade date for ex-ante filtering.",
            "same_day_vix_policy": "Same-day VIX close is diagnostic only and not available before entry.",
            "high_vix_threshold": HIGH_VIX_THRESHOLD,
            "stress_vix_threshold": STRESS_VIX_THRESHOLD,
        },
        "input_paths": {
            "vix_vxv": _relative(vix_path),
            "aug_2024_adapters": [_relative(PROJECT_ROOT / "reports" / "pilots" / item[2]) for item in aug_datasets],
        },
        "counts": {
            "aug_2024_trade_days": len(daily_rows),
            "candidate_ready_days": len(candidate_rows),
            "same_day_high_vix_days": len(same_day_high_rows),
            "prior_high_vix_days": len(prior_high_rows),
            "same_day_stress_vix_days": len(same_day_stress_rows),
            "prior_stress_vix_days": len(prior_stress_rows),
            "candidate_ready_on_same_day_high_vix": _candidate_count(same_day_high_rows),
            "candidate_ready_on_prior_high_vix": _candidate_count(prior_high_rows),
            "candidate_ready_on_same_day_stress_vix": _candidate_count(same_day_stress_rows),
            "candidate_ready_on_prior_stress_vix": _candidate_count(prior_stress_rows),
        },
        "date_sets": {
            "candidate_ready_dates": [row["date"] for row in candidate_rows],
            "same_day_high_vix_dates": [row["date"] for row in same_day_high_rows],
            "prior_high_vix_dates": [row["date"] for row in prior_high_rows],
            "same_day_stress_vix_dates": [row["date"] for row in same_day_stress_rows],
            "prior_stress_vix_dates": [row["date"] for row in prior_stress_rows],
            "missing_vix_dates": missing_vix,
            "missing_market_data_on_high_vix_dates": missing_market_data,
        },
        "interpretation": {
            "labeling_gap": bool(missing_vix or missing_market_data),
            "orb_silence_during_high_vix": bool(same_day_high_rows or prior_high_rows)
            and _candidate_count(same_day_high_rows) == 0
            and _candidate_count(prior_high_rows) == 0,
            "prior_close_shift_note": (
                "The 2024-08-05 VIX spike is visible in same-day close, but M5.5 prior-close policy cannot know it before entry. "
                "The ex-ante high-VIX label shifts to later dates after the spike is already observed."
            ),
            "research_implication": (
                "Aug 2024 does not currently provide high-VIX ORB trade outcomes; it only shows that the ORB trigger produced no "
                "candidate trades during the cached high-VIX stress window."
            ),
        },
        "daily_rows": daily_rows,
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(result), encoding="utf-8")
    return result


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# H-A2 High-VIX Silence Diagnostic",
        "",
        "## Status",
        f"- Hypothesis: `{result['hypothesis_id']}`",
        f"- Evidence tier: `{result['evidence_tier']}`",
        f"- Conclusion: {result['conclusion']}",
        f"- Diagnostic result: `{result['diagnostic_result']}`",
        f"- No new paid data: `{result['no_new_paid_data']}`",
        "",
        "## Counts",
        "```json",
        json.dumps(result["counts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Date Sets",
        "```json",
        json.dumps(result["date_sets"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Interpretation",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in result["interpretation"].items())
    lines.extend(
        [
            "",
            "## Daily Rows",
            "| Date | Adapter status | Same-day VIX | Prior VIX date | Prior VIX | Same-day high | Prior high | Option rows | SPY bars |",
            "|:--|:--|--:|:--|--:|:--:|:--:|--:|--:|",
        ]
    )
    for row in result["daily_rows"]:
        lines.append(
            f"| {row['date']} | `{row['adapter_status']}` | {row['same_day_vix_close']} | {row['prior_vix_date']} | "
            f"{row['prior_vix_close']} | {row['same_day_high_vix']} | {row['prior_high_vix']} | "
            f"{row['option_quote_rows']} | {row['spy_bar_rows']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _count_option_quotes_by_date(path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        counts[str(row["quote_timestamp_et"])[:10]] += 1
    return counts


def _count_spy_bars_by_date(path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        counts[str(row["timestamp_et"])[:10]] += 1
    return counts


def _diagnostic_result(
    missing_vix: list[str],
    missing_market_data: list[str],
    same_day_high_rows: list[dict[str, Any]],
    prior_high_rows: list[dict[str, Any]],
) -> str:
    if missing_vix or missing_market_data:
        return "labeling_or_market_data_gap"
    if same_day_high_rows and prior_high_rows and _candidate_count(same_day_high_rows) == 0 and _candidate_count(prior_high_rows) == 0:
        return "genuine_orb_silence_during_high_vix_window"
    return "mixed_or_inconclusive"


def _candidate_count(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row["adapter_status"] == "candidate_ready")


def _vix_record_for_date(value: str, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    target = date.fromisoformat(value)
    for row in rows:
        if date.fromisoformat(row["date"]) == target:
            return row
    return None


def _close_or_none(row: dict[str, Any] | None) -> float | None:
    return None if row is None else float(row["vix_close"])


def _is_high(row: dict[str, Any] | None, threshold: float) -> bool:
    return row is not None and float(row["vix_close"]) >= threshold


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose Aug 2024 H-A2 high-VIX labeling versus ORB silence.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)

    result = run_diagnostic(summary_path=args.summary_path, report_path=args.report_path)
    print(json.dumps({key: value for key, value in result.items() if key != "daily_rows"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
