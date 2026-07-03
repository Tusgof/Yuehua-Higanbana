from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "strategy_data_readiness_audit.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "strategy_data_readiness_audit.md"
MINIMUM_TRADE_COUNT = 500

DEFAULT_INPUTS = {
    "in_sample_multimonth": PROJECT_ROOT / "reports" / "pilots" / "insample_2023_mar_dec_multimonth_summary.json",
    "jan_2024_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "jan_2024_pilot_adapter_summary.json",
    "jan_2024_oos": PROJECT_ROOT / "reports" / "pilots" / "jan_2024_pilot_pnl_summary.json",
    "feb_2024_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "feb_2024_pilot_adapter_summary.json",
    "feb_2024_oos": PROJECT_ROOT / "reports" / "pilots" / "feb_2024_pilot_pnl_summary.json",
    "mar_2024_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "mar_2024_pilot_adapter_summary.json",
    "mar_2024_oos": PROJECT_ROOT / "reports" / "pilots" / "mar_2024_pilot_pnl_summary.json",
    "apr_2024_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "apr_2024_pilot_adapter_summary.json",
    "apr_2024_oos": PROJECT_ROOT / "reports" / "pilots" / "apr_2024_pilot_pnl_summary.json",
    "may_2024_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "may_2024_pilot_adapter_summary.json",
    "may_2024_oos": PROJECT_ROOT / "reports" / "pilots" / "may_2024_pilot_pnl_summary.json",
    "jun_2024_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "jun_2024_pilot_adapter_summary.json",
    "jun_2024_oos": PROJECT_ROOT / "reports" / "pilots" / "jun_2024_pilot_pnl_summary.json",
    "jul_2024_partial_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "jul_2024_partial_pilot_adapter_summary.json",
    "jul_2024_partial_oos": PROJECT_ROOT / "reports" / "pilots" / "jul_2024_partial_pilot_pnl_summary.json",
    "jul_2024_chunk3_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "jul_2024_chunk3_pilot_adapter_summary.json",
    "jul_2024_chunk3_oos": PROJECT_ROOT / "reports" / "pilots" / "jul_2024_chunk3_pilot_pnl_summary.json",
    "jul_2024_chunk4_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "jul_2024_chunk4_pilot_adapter_summary.json",
    "jul_2024_chunk4_oos": PROJECT_ROOT / "reports" / "pilots" / "jul_2024_chunk4_pilot_pnl_summary.json",
    "jul_2024_chunk5_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "jul_2024_chunk5_pilot_adapter_summary.json",
    "jul_2024_chunk5_oos": PROJECT_ROOT / "reports" / "pilots" / "jul_2024_chunk5_pilot_pnl_summary.json",
    "aug_2024_chunk1_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "aug_2024_chunk1_pilot_adapter_summary.json",
    "aug_2024_chunk1_oos": PROJECT_ROOT / "reports" / "pilots" / "aug_2024_chunk1_pilot_pnl_summary.json",
    "aug_2024_chunk2_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "aug_2024_chunk2_pilot_adapter_summary.json",
    "aug_2024_chunk2_oos": PROJECT_ROOT / "reports" / "pilots" / "aug_2024_chunk2_pilot_pnl_summary.json",
    "aug_2024_chunk3_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "aug_2024_chunk3_pilot_adapter_summary.json",
    "aug_2024_chunk3_oos": PROJECT_ROOT / "reports" / "pilots" / "aug_2024_chunk3_pilot_pnl_summary.json",
    "aug_2024_chunk4_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "aug_2024_chunk4_pilot_adapter_summary.json",
    "aug_2024_chunk4_oos": PROJECT_ROOT / "reports" / "pilots" / "aug_2024_chunk4_pilot_pnl_summary.json",
    "aug_2024_chunk5_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "aug_2024_chunk5_pilot_adapter_summary.json",
    "aug_2024_chunk5_oos": PROJECT_ROOT / "reports" / "pilots" / "aug_2024_chunk5_pilot_pnl_summary.json",
    "sep_2024_chunk1_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "sep_2024_chunk1_pilot_adapter_summary.json",
    "sep_2024_chunk1_oos": PROJECT_ROOT / "reports" / "pilots" / "sep_2024_chunk1_pilot_pnl_summary.json",
    "sep_2024_chunk2_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "sep_2024_chunk2_pilot_adapter_summary.json",
    "sep_2024_chunk2_oos": PROJECT_ROOT / "reports" / "pilots" / "sep_2024_chunk2_pilot_pnl_summary.json",
    "sep_2024_chunk3_oos_adapter": PROJECT_ROOT / "reports" / "pilots" / "sep_2024_chunk3_pilot_adapter_summary.json",
    "sep_2024_chunk3_oos": PROJECT_ROOT / "reports" / "pilots" / "sep_2024_chunk3_pilot_pnl_summary.json",
    "sep_2024_remainder_oos_adapter": PROJECT_ROOT
    / "reports"
    / "pilots"
    / "sep_2024_remainder_daily_union_pilot_adapter_summary.json",
    "sep_2024_remainder_oos": PROJECT_ROOT
    / "reports"
    / "pilots"
    / "sep_2024_remainder_daily_union_pilot_pnl_summary.json",
    "oct_2024_oos_adapter": PROJECT_ROOT
    / "reports"
    / "pilots"
    / "oct_2024_daily_union_pilot_adapter_summary.json",
    "oct_2024_oos": PROJECT_ROOT / "reports" / "pilots" / "oct_2024_daily_union_pilot_pnl_summary.json",
    "nov_2024_oos_adapter": PROJECT_ROOT
    / "reports"
    / "pilots"
    / "nov_2024_daily_union_pilot_adapter_summary.json",
    "nov_2024_oos": PROJECT_ROOT / "reports" / "pilots" / "nov_2024_daily_union_pilot_pnl_summary.json",
    "dec_2024_oos_adapter": PROJECT_ROOT
    / "reports"
    / "pilots"
    / "dec_2024_daily_union_pilot_adapter_summary.json",
    "dec_2024_oos": PROJECT_ROOT / "reports" / "pilots" / "dec_2024_daily_union_pilot_pnl_summary.json",
}


def audit_strategy_data_readiness(
    input_paths: dict[str, Path] | None = None,
    minimum_trade_count: int = MINIMUM_TRADE_COUNT,
) -> dict[str, Any]:
    paths = input_paths or DEFAULT_INPUTS
    loaded = {name: _load_json(path) for name, path in paths.items()}

    datasets = _dataset_summaries(loaded, paths)
    totals = _totals(datasets)
    blockers = _blockers(datasets, totals, minimum_trade_count)
    sample_adequacy = _sample_adequacy(totals, minimum_trade_count)

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "minimum_trade_count": minimum_trade_count,
        "sample_adequacy": sample_adequacy,
        "totals": totals,
        "datasets": datasets,
        "note": "Read-only audit from existing Databento pilot artifacts; no live API calls.",
    }


def write_reports(
    result: dict[str, Any],
    json_output: Path = DEFAULT_JSON_OUTPUT,
    report_output: Path = DEFAULT_REPORT_OUTPUT,
) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    totals = result["totals"]
    lines = [
        "# Strategy Data Readiness Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Minimum trade count: {result['minimum_trade_count']}",
        f"- Total closed trades: {totals['closed_trades']}",
        f"- Total candidate days: {totals['candidate_days']}",
        f"- Total quote rows: {totals['quote_rows']}",
        f"- Total SPY bar rows: {totals['bar_rows']}",
        f"- Evidence labels: {', '.join(f'`{label}`' for label in result['sample_adequacy']['evidence_labels'])}",
        f"- MinTRL status: `{result['sample_adequacy']['mintrl_status']}`",
        f"- PSR status: `{result['sample_adequacy']['psr_status']}`",
        f"- Power status: `{result['sample_adequacy']['power_status']}`",
        "",
        "## Blockers",
        "",
    ]
    if result["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in result["blockers"])
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Datasets",
            "",
            "| Dataset | Split | Status | Candidate days | Closed trades | Quote rows | SPY bar rows | Source |",
            "|:--|:--|:--|--:|--:|--:|--:|:--|",
        ]
    )
    for dataset in result["datasets"]:
        lines.append(
            "| {label} | {split} | `{status}` | {candidate_days} | {closed_trades} | {quote_rows} | {bar_rows} | `{source}` |".format(
                **dataset
            )
        )

    lines.extend(["", "## Note", "", result["note"]])
    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _dataset_summaries(
    loaded: dict[str, dict[str, Any] | None],
    paths: dict[str, Path],
) -> list[dict[str, Any]]:
    datasets: list[dict[str, Any]] = []
    in_sample = loaded.get("in_sample_multimonth")
    if in_sample is None:
        datasets.append(_missing_dataset("in_sample_multimonth", "in_sample", paths["in_sample_multimonth"]))
    else:
        pnl = in_sample.get("pnl_models", {}).get("forced_close_only", {})
        adapter = in_sample.get("adapter_totals", {})
        datasets.append(
            {
                "label": "in_sample_2023_mar_dec",
                "split": "in_sample",
                "status": "present",
                "source": str(paths["in_sample_multimonth"]),
                "candidate_days": int(pnl.get("candidate_days", adapter.get("candidate_ready_days", 0))),
                "closed_trades": int(pnl.get("closed_trades", 0)),
                "skipped_trades": int(pnl.get("skipped_trades", 0)),
                "quote_rows": int(adapter.get("quote_rows", 0)),
                "bar_rows": int(adapter.get("bar_rows", 0)),
                "coverage_start": in_sample.get("coverage_start"),
                "coverage_end": in_sample.get("coverage_end"),
            }
        )

    for name, adapter_name, label in [
        ("jan_2024_oos", "jan_2024_oos_adapter", "oos_2024_01"),
        ("feb_2024_oos", "feb_2024_oos_adapter", "oos_2024_02"),
        ("mar_2024_oos", "mar_2024_oos_adapter", "oos_2024_03"),
        ("apr_2024_oos", "apr_2024_oos_adapter", "oos_2024_04"),
        ("may_2024_oos", "may_2024_oos_adapter", "oos_2024_05"),
        ("jun_2024_oos", "jun_2024_oos_adapter", "oos_2024_06"),
        ("jul_2024_partial_oos", "jul_2024_partial_oos_adapter", "oos_2024_07_partial"),
        ("jul_2024_chunk3_oos", "jul_2024_chunk3_oos_adapter", "oos_2024_07_chunk3"),
        ("jul_2024_chunk4_oos", "jul_2024_chunk4_oos_adapter", "oos_2024_07_chunk4"),
        ("jul_2024_chunk5_oos", "jul_2024_chunk5_oos_adapter", "oos_2024_07_chunk5"),
        ("aug_2024_chunk1_oos", "aug_2024_chunk1_oos_adapter", "oos_2024_08_chunk1"),
        ("aug_2024_chunk2_oos", "aug_2024_chunk2_oos_adapter", "oos_2024_08_chunk2"),
        ("aug_2024_chunk3_oos", "aug_2024_chunk3_oos_adapter", "oos_2024_08_chunk3"),
        ("aug_2024_chunk4_oos", "aug_2024_chunk4_oos_adapter", "oos_2024_08_chunk4"),
        ("aug_2024_chunk5_oos", "aug_2024_chunk5_oos_adapter", "oos_2024_08_chunk5"),
        ("sep_2024_chunk1_oos", "sep_2024_chunk1_oos_adapter", "oos_2024_09_chunk1"),
        ("sep_2024_chunk2_oos", "sep_2024_chunk2_oos_adapter", "oos_2024_09_chunk2"),
        ("sep_2024_chunk3_oos", "sep_2024_chunk3_oos_adapter", "oos_2024_09_chunk3"),
        ("sep_2024_remainder_oos", "sep_2024_remainder_oos_adapter", "oos_2024_09_remainder"),
        ("oct_2024_oos", "oct_2024_oos_adapter", "oos_2024_10"),
        ("nov_2024_oos", "nov_2024_oos_adapter", "oos_2024_11"),
        ("dec_2024_oos", "dec_2024_oos_adapter", "oos_2024_12"),
    ]:
        if name not in paths or adapter_name not in paths:
            continue
        report = loaded.get(name)
        adapter = loaded.get(adapter_name)
        if report is None or adapter is None:
            datasets.append(_missing_dataset(label, "oos", paths[name]))
        else:
            datasets.append(
                {
                    "label": label,
                    "split": "oos",
                    "status": "present",
                    "source": str(paths[name]),
                    "candidate_days": int(report.get("candidate_days", adapter.get("candidate_ready_days", 0))),
                    "closed_trades": int(report.get("closed_trades", 0)),
                    "skipped_trades": int(report.get("skipped_trades", 0)),
                    "quote_rows": int(adapter.get("quote_rows", 0)),
                    "bar_rows": int(adapter.get("bar_rows", 0)),
                    "coverage_start": adapter.get("coverage_start", _trade_date(report, first=True)),
                    "coverage_end": adapter.get("coverage_end", _trade_date(report, first=False)),
                }
            )
    return datasets


def _missing_dataset(label: str, split: str, path: Path) -> dict[str, Any]:
    return {
        "label": label,
        "split": split,
        "status": "missing",
        "source": str(path),
        "candidate_days": 0,
        "closed_trades": 0,
        "skipped_trades": 0,
        "quote_rows": 0,
        "bar_rows": 0,
        "coverage_start": None,
        "coverage_end": None,
    }


def _totals(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    by_split: dict[str, dict[str, int]] = {}
    for dataset in datasets:
        split = dataset["split"]
        by_split.setdefault(split, {"candidate_days": 0, "closed_trades": 0, "quote_rows": 0, "bar_rows": 0})
        for field in ["candidate_days", "closed_trades", "quote_rows", "bar_rows"]:
            by_split[split][field] += int(dataset[field])

    return {
        "candidate_days": sum(int(dataset["candidate_days"]) for dataset in datasets),
        "closed_trades": sum(int(dataset["closed_trades"]) for dataset in datasets),
        "quote_rows": sum(int(dataset["quote_rows"]) for dataset in datasets),
        "bar_rows": sum(int(dataset["bar_rows"]) for dataset in datasets),
        "dataset_count": sum(1 for dataset in datasets if dataset["status"] == "present"),
        "splits": by_split,
    }


def _blockers(
    datasets: list[dict[str, Any]],
    totals: dict[str, Any],
    minimum_trade_count: int,
) -> list[str]:
    blockers = []
    if any(dataset["status"] == "missing" for dataset in datasets):
        blockers.append("requires_strategy_data_pilot_artifacts")
    if totals["splits"].get("in_sample", {}).get("closed_trades", 0) == 0:
        blockers.append("requires_in_sample_strategy_trades")
    if totals["splits"].get("oos", {}).get("closed_trades", 0) == 0:
        blockers.append("requires_oos_strategy_trades")
    if totals["closed_trades"] < minimum_trade_count:
        blockers.append("requires_minimum_trade_count_500")
    if totals["quote_rows"] <= 0:
        blockers.append("requires_bid_ask_quotes")
    if totals["bar_rows"] <= 0:
        blockers.append("requires_spy_bar_data")
    return sorted(blockers)


def _sample_adequacy(totals: dict[str, Any], minimum_trade_count: int) -> dict[str, Any]:
    closed_trades = int(totals["closed_trades"])
    trade_count_floor_met = closed_trades >= minimum_trade_count
    if trade_count_floor_met:
        evidence_labels = ["sample_count_floor_met", "psr_mintrl_pending"]
        power_status = "pending_experiment_return_distribution"
        power_note = (
            "Closed-trade count meets the rough prior floor, but PSR, MinTRL, and power still require "
            "experiment return distribution metrics before acceptance-grade Sharpe evidence."
        )
    else:
        evidence_labels = ["under-sampled", "underpowered"]
        power_status = "underpowered"
        power_note = (
            "Closed-trade count is below the rough prior floor. Treat any Sharpe or PnL result from this "
            "coverage as diagnostic only until wider data or computed MinTRL/PSR evidence supports it."
        )

    return {
        "actual_closed_trades": closed_trades,
        "rough_minimum_trade_count": minimum_trade_count,
        "trade_count_floor_met": trade_count_floor_met,
        "evidence_labels": evidence_labels,
        "mintrl_required_observations": None,
        "mintrl_status": "pending_experiment_return_distribution",
        "psr_status": "pending_experiment_return_distribution",
        "power_status": power_status,
        "note": power_note,
    }


def _trade_date(report: dict[str, Any], first: bool) -> str | None:
    trades = [trade.get("date") for trade in report.get("trades", []) if trade.get("date")]
    if not trades:
        return None
    return sorted(trades)[0 if first else -1]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit real strategy-data readiness from local pilot artifacts only.")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--minimum-trade-count", type=int, default=MINIMUM_TRADE_COUNT)
    args = parser.parse_args(argv)

    result = audit_strategy_data_readiness(minimum_trade_count=args.minimum_trade_count)
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
