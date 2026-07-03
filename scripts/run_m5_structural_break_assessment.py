from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = PROJECT_ROOT / "reports" / "experiments"
SUMMARY_PATH = REPORT_ROOT / "m5_structural_break_assessment_summary.json"
REPORT_PATH = REPORT_ROOT / "m5_structural_break_assessment_report.md"
STRATEGY_READINESS_PATH = PROJECT_ROOT / "reports" / "strategy_data_readiness_audit.json"

REFERENCE_PRE_BREAK_START = "2019-01-01"
BREAK_DATE = "2022-05-11"
REFERENCE_PRE_BREAK_END = "2022-05-10"
PRIMARY_TRAIN_END = "2023-12-31"
OOS_START = "2024-01-01"


def run_assessment(
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
    readiness_path: Path = STRATEGY_READINESS_PATH,
) -> dict[str, Any]:
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    datasets = readiness.get("datasets", [])
    period_summary = summarize_periods(datasets)
    blockers = structural_break_blockers(period_summary, readiness)
    status = "deferred" if blockers else "complete"
    result = {
        "record_type": "experiment_summary",
        "schema_version": "m5_structural_break_assessment_v1",
        "experiment_id": "m5_structural_break_assessment",
        "status": status,
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "Structural-break testing around 2022-05-11 is deferred because current local SPY 0DTE option "
            "coverage has no reference/pre-break observations before 2022-05-11."
        )
        if blockers
        else "Reference/pre-break, post-break train, and OOS coverage are present.",
        "research_log_required": True,
        "research_log_slug": "higanbana-structural-break-deferred-real-data",
        "methodology": {
            "scope": "Assess whether the May 11 2022 structural-break test can be run from existing local real-data artifacts.",
            "data_policy": "Read-only coverage audit from existing strategy-data readiness artifact; no paid API calls and no new data download.",
            "split_policy": {
                "reference_pre_break": {"start": REFERENCE_PRE_BREAK_START, "end": REFERENCE_PRE_BREAK_END},
                "post_break_train": {"start": BREAK_DATE, "end": PRIMARY_TRAIN_END},
                "oos": {"start": OOS_START, "end": "current_available"},
                "forbid_random_split": True,
                "forbid_oos_tuning": True,
            },
            "decision_rule": "Run structural-break statistics only if all three chronological periods have real option coverage and closed trades.",
        },
        "input_paths": {"strategy_data_readiness": str(readiness_path)},
        "blockers": blockers,
        "periods": period_summary,
        "sample_adequacy": readiness.get("sample_adequacy", {}),
        "readiness_totals": readiness.get("totals", {}),
        "next_requirements": next_requirements(blockers),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(result), encoding="utf-8")
    return result


def summarize_periods(datasets: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    periods = {
        "reference_pre_break": empty_period(REFERENCE_PRE_BREAK_START, REFERENCE_PRE_BREAK_END),
        "post_break_train": empty_period(BREAK_DATE, PRIMARY_TRAIN_END),
        "oos": empty_period(OOS_START, "current_available"),
    }
    for dataset in datasets:
        if dataset.get("status") != "present":
            continue
        start = dataset.get("coverage_start")
        end = dataset.get("coverage_end")
        if not start or not end:
            continue
        period_key = period_for_dataset(str(start), str(end))
        if period_key is None:
            continue
        period = periods[period_key]
        period["datasets"].append(dataset["label"])
        period["dataset_count"] += 1
        period["candidate_days"] += int(dataset.get("candidate_days", 0))
        period["closed_trades"] += int(dataset.get("closed_trades", 0))
        period["quote_rows"] += int(dataset.get("quote_rows", 0))
        period["bar_rows"] += int(dataset.get("bar_rows", 0))
        period["coverage_start_actual"] = min_non_null(period["coverage_start_actual"], str(start))
        period["coverage_end_actual"] = max_non_null(period["coverage_end_actual"], str(end))
    for period in periods.values():
        period["coverage_present"] = period["dataset_count"] > 0
        period["closed_trades_present"] = period["closed_trades"] > 0
    return periods


def empty_period(required_start: str, required_end: str) -> dict[str, Any]:
    return {
        "required_start": required_start,
        "required_end": required_end,
        "coverage_start_actual": None,
        "coverage_end_actual": None,
        "coverage_present": False,
        "closed_trades_present": False,
        "dataset_count": 0,
        "candidate_days": 0,
        "closed_trades": 0,
        "quote_rows": 0,
        "bar_rows": 0,
        "datasets": [],
    }


def period_for_dataset(start: str, end: str) -> str | None:
    if end < BREAK_DATE:
        return "reference_pre_break"
    if start >= BREAK_DATE and end < OOS_START:
        return "post_break_train"
    if start >= OOS_START:
        return "oos"
    return None


def min_non_null(current: str | None, candidate: str) -> str:
    return candidate if current is None else min(current, candidate)


def max_non_null(current: str | None, candidate: str) -> str:
    return candidate if current is None else max(current, candidate)


def structural_break_blockers(periods: dict[str, dict[str, Any]], readiness: dict[str, Any]) -> list[str]:
    blockers = []
    required_periods = ["reference_pre_break", "post_break_train", "oos"]
    for key in required_periods:
        if not periods[key]["coverage_present"]:
            blockers.append(f"requires_{key}_option_coverage")
        if not periods[key]["closed_trades_present"]:
            blockers.append(f"requires_{key}_closed_trades")
    if "requires_minimum_trade_count_500" in readiness.get("blockers", []):
        blockers.append("requires_minimum_trade_count_500")
    return sorted(set(blockers))


def next_requirements(blockers: list[str]) -> list[str]:
    if not blockers:
        return ["Run chronological structural-break comparison with pre-registered metrics."]
    return [
        "Add or acquire SPY 0DTE option coverage for 2019-01-01 to 2022-05-10 before running a structural-break claim.",
        "Backfill the missing post-break training window from 2022-05-11 to 2023-02-28 if the test requires full post-break coverage.",
        "Re-run strategy-data readiness and this M5.7 assessment after coverage changes.",
        "Keep Jan-Dec 2024 OOS untouched for final evaluation; do not tune M5.7 rules on OOS diagnostics.",
    ]


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# M5.7 Structural-Break Assessment",
        "",
        "## Status",
        f"- Status: `{result['status']}`",
        f"- Conclusion: {result['conclusion']}",
        f"- Reason: {result['conclusion_reason']}",
        "- Evidence type: real-data coverage assessment, not a structural-break performance test.",
        "- No paid API call or data download was performed.",
        "",
        "## Methodology",
        "```json",
        json.dumps(result["methodology"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Period Coverage",
        "| Period | Required window | Actual window | Datasets | Candidate days | Closed trades | Quote rows | SPY bar rows |",
        "|:--|:--|:--|--:|--:|--:|--:|--:|",
    ]
    for key, period in result["periods"].items():
        actual = actual_window(period)
        required = f"{period['required_start']} to {period['required_end']}"
        lines.append(
            f"| `{key}` | {required} | {actual} | {period['dataset_count']} | {period['candidate_days']} | "
            f"{period['closed_trades']} | {period['quote_rows']} | {period['bar_rows']} |"
        )
    lines.extend(["", "## Blockers", ""])
    if result["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in result["blockers"])
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Interpretation",
            "- The May 11 2022 structural-break question cannot be answered from current local option artifacts because the reference/pre-break period has zero local SPY 0DTE option datasets and zero closed trades.",
            "- Running a comparison with only post-2022 data would not test the stated structural-break hypothesis.",
            "- The correct action is to defer M5.7 until pre-break coverage exists, or explicitly revise the hypothesis away from a pre/post 2022 break test.",
            "",
            "## Next Requirements",
            "",
        ]
    )
    lines.extend(f"{index}. {item}" for index, item in enumerate(result["next_requirements"], start=1))
    lines.append("")
    return "\n".join(lines)


def actual_window(period: dict[str, Any]) -> str:
    if not period["coverage_present"]:
        return "none"
    return f"{period['coverage_start_actual']} to {period['coverage_end_actual']}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assess whether M5.7 structural-break testing can run from current local data.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    parser.add_argument("--readiness-path", type=Path, default=STRATEGY_READINESS_PATH)
    args = parser.parse_args(argv)
    result = run_assessment(args.summary_path, args.report_path, args.readiness_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
