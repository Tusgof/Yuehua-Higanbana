from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = PROJECT_ROOT / "reports" / "pilots"
SUMMARY_PATH = PILOT_DIR / "insample_2023_mar_dec_multimonth_summary.json"
REPORT_PATH = PILOT_DIR / "insample_2023_mar_dec_multimonth_report.md"
DEFAULT_SCENARIOS = [
    {
        "label": "mar_2023",
        "split": "in_sample",
        "adapter": PILOT_DIR / "mar_2023_pilot_adapter_summary.json",
        "pnl": [
            PILOT_DIR / "mar_2023_pilot_pnl_summary.json",
            PILOT_DIR / "mar_2023_pilot_pnl_target_stop_summary.json",
        ],
    },
    {
        "label": "apr_2023",
        "split": "in_sample",
        "adapter": PILOT_DIR / "apr_2023_pilot_adapter_summary.json",
        "pnl": [
            PILOT_DIR / "apr_2023_pilot_pnl_summary.json",
            PILOT_DIR / "apr_2023_pilot_pnl_target_stop_summary.json",
        ],
    },
    {
        "label": "may_2023",
        "split": "in_sample",
        "adapter": PILOT_DIR / "may_2023_pilot_adapter_summary.json",
        "pnl": [
            PILOT_DIR / "may_2023_pilot_pnl_summary.json",
            PILOT_DIR / "may_2023_pilot_pnl_target_stop_summary.json",
        ],
    },
    {
        "label": "jun_2023",
        "split": "in_sample",
        "adapter": PILOT_DIR / "jun_2023_pilot_adapter_summary.json",
        "pnl": [
            PILOT_DIR / "jun_2023_pilot_pnl_summary.json",
            PILOT_DIR / "jun_2023_pilot_pnl_target_stop_summary.json",
        ],
    },
    {
        "label": "jul_2023",
        "split": "in_sample",
        "adapter": PILOT_DIR / "jul_2023_pilot_adapter_summary.json",
        "pnl": [
            PILOT_DIR / "jul_2023_pilot_pnl_summary.json",
            PILOT_DIR / "jul_2023_pilot_pnl_target_stop_summary.json",
        ],
    },
    {
        "label": "aug_2023",
        "split": "in_sample",
        "adapter": PILOT_DIR / "aug_2023_pilot_adapter_summary.json",
        "pnl": [
            PILOT_DIR / "aug_2023_pilot_pnl_summary.json",
            PILOT_DIR / "aug_2023_pilot_pnl_target_stop_summary.json",
        ],
    },
    {
        "label": "sep_2023",
        "split": "in_sample",
        "adapter": PILOT_DIR / "sep_2023_pilot_adapter_summary.json",
        "pnl": [
            PILOT_DIR / "sep_2023_pilot_pnl_summary.json",
            PILOT_DIR / "sep_2023_pilot_pnl_target_stop_summary.json",
        ],
    },
    {
        "label": "oct_2023",
        "split": "in_sample",
        "adapter": PILOT_DIR / "oct_2023_pilot_adapter_summary.json",
        "pnl": [
            PILOT_DIR / "oct_2023_pilot_pnl_summary.json",
            PILOT_DIR / "oct_2023_pilot_pnl_target_stop_summary.json",
        ],
    },
    {
        "label": "nov_2023",
        "split": "in_sample",
        "adapter": PILOT_DIR / "nov_2023_pilot_adapter_summary.json",
        "pnl": [
            PILOT_DIR / "nov_2023_pilot_pnl_summary.json",
            PILOT_DIR / "nov_2023_pilot_pnl_target_stop_summary.json",
        ],
    },
    {
        "label": "dec_2023",
        "split": "in_sample",
        "adapter": PILOT_DIR / "dec_2023_pilot_adapter_summary.json",
        "pnl": [
            PILOT_DIR / "dec_2023_pilot_pnl_summary.json",
            PILOT_DIR / "dec_2023_pilot_pnl_target_stop_summary.json",
        ],
    },
]


def run_multimonth_summary(
    scenarios: list[dict[str, Any]] | None = None,
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
) -> dict[str, Any]:
    summary = build_summary(scenarios or DEFAULT_SCENARIOS)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary), encoding="utf-8")
    return summary


def build_summary(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    if not scenarios:
        raise ValueError("at least one scenario is required")
    splits = {scenario["split"] for scenario in scenarios}
    if len(splits) != 1:
        raise ValueError("mixed train/OOS splits are not allowed in one multimonth summary")

    monthly = []
    pnl_by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for scenario in scenarios:
        adapter = load_json(Path(scenario["adapter"]))
        monthly.append(month_adapter_summary(scenario["label"], scenario["split"], adapter))
        for pnl_path in scenario["pnl"]:
            pnl = load_json(Path(pnl_path))
            model = pnl["exit_model"]
            pnl_by_model[model].append(month_pnl_summary(scenario["label"], pnl))

    return {
        "mode": "multimonth_pilot_summary",
        "split": next(iter(splits)),
        "month_count": len(scenarios),
        "evidence_warning": "This combines completed pilot summaries only. Trade count is still far below N >= 500, so it is not strategy acceptance evidence.",
        "conclusion": "ยังสรุปไม่ได้",
        "coverage_start": min(row["coverage_start"] for row in monthly),
        "coverage_end": max(row["coverage_end"] for row in monthly),
        "adapter_totals": combine_adapter_months(monthly),
        "pnl_models": {
            model: combine_pnl_months(rows)
            for model, rows in sorted(pnl_by_model.items())
        },
        "monthly": monthly,
    }


def month_adapter_summary(label: str, split: str, adapter: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": label,
        "split": split,
        "coverage_start": adapter["coverage_start"],
        "coverage_end": adapter["coverage_end"],
        "calendar_days": adapter["calendar_days"],
        "candidate_ready_days": adapter["candidate_ready_days"],
        "bar_rows": adapter.get("bar_rows", 0),
        "quote_rows": adapter.get("quote_rows", 0),
        "status_counts": adapter.get("status_counts", {}),
    }


def month_pnl_summary(label: str, pnl: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": label,
        "exit_model": pnl["exit_model"],
        "candidate_days": pnl["candidate_days"],
        "closed_trades": pnl["closed_trades"],
        "skipped_trades": pnl["skipped_trades"],
        "total_net_pnl": pnl["total_net_pnl"],
        "trades": pnl.get("trades", []),
        "status_counts": pnl.get("status_counts", {}),
    }


def combine_adapter_months(monthly: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "calendar_days": sum(row["calendar_days"] for row in monthly),
        "candidate_ready_days": sum(row["candidate_ready_days"] for row in monthly),
        "bar_rows": sum(row["bar_rows"] for row in monthly),
        "quote_rows": sum(row["quote_rows"] for row in monthly),
        "status_counts": sum_counts(row["status_counts"] for row in monthly),
    }


def combine_pnl_months(months: list[dict[str, Any]]) -> dict[str, Any]:
    trades = sorted(
        [
            {**trade, "month_label": month["label"]}
            for month in months
            for trade in month["trades"]
        ],
        key=lambda row: row.get("date", ""),
    )
    closed = [trade for trade in trades if trade["status"].startswith("closed_")]
    skipped = [trade for trade in trades if not trade["status"].startswith("closed_")]
    pnls = [float(trade["net_pnl"]) for trade in closed]
    return {
        "exit_model": months[0]["exit_model"],
        "candidate_days": sum(month["candidate_days"] for month in months),
        "closed_trades": len(closed),
        "skipped_trades": len(skipped),
        "total_net_pnl": round(sum(pnls), 2),
        "average_net_pnl": round(mean(pnls), 4) if pnls else 0.0,
        "win_rate": round(sum(1 for pnl in pnls if pnl > 0) / len(pnls), 4) if pnls else 0.0,
        "worst_trade": min(pnls) if pnls else 0.0,
        "best_trade": max(pnls) if pnls else 0.0,
        "sharpe_proxy": sharpe_proxy(pnls),
        "max_drawdown": max_drawdown([1000.0, *equity_curve(pnls)]),
        "status_counts": sum_counts(month["status_counts"] for month in months),
        "monthly": [
            {key: value for key, value in month.items() if key != "trades"}
            for month in months
        ],
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Higanbana Multimonth Pilot Summary",
        "",
        "## สถานะ",
        f"- Split: `{summary['split']}`",
        f"- ช่วงข้อมูล: `{summary['coverage_start']}` ถึง `{summary['coverage_end']}`",
        f"- ข้อสรุป: {summary['conclusion']}",
        "- ความหมาย: นี่เป็นการรวมผล pilot หลายเดือนเพื่อดูภาพรวมก่อนโหลดข้อมูลเพิ่ม ยังไม่ใช่หลักฐานยืนยัน edge",
        "",
        "## Adapter Totals",
        "```json",
        json.dumps(summary["adapter_totals"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## PnL Models",
    ]
    for model, metrics in summary["pnl_models"].items():
        compact = {key: value for key, value in metrics.items() if key != "monthly"}
        lines.extend(
            [
                f"### `{model}`",
                "```json",
                json.dumps(compact, ensure_ascii=False, indent=2, sort_keys=True),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## ข้อจำกัด",
            "- จำนวน trade ยังต่ำกว่าเกณฑ์ N >= 500 มาก จึงยังสรุประบบไม่ได้",
            "- ผลนี้รวมเฉพาะ Sub-System A pilot ที่มีข้อมูล Databento ครบแล้ว",
            "- ยังไม่รวม VIX/VXV, macro, news/LLM gate, Sub-System B, และ fill retry แบบ production",
            "- ห้ามใช้ผล OOS เพื่อ tune parameter; report นี้ตั้งใจแยก split ต่อหนึ่งไฟล์",
            "",
        ]
    )
    return "\n".join(lines)


def equity_curve(pnls: list[float], starting_equity: float = 1000.0) -> list[float]:
    equity = starting_equity
    curve = []
    for pnl in pnls:
        equity = round(equity + pnl, 2)
        curve.append(equity)
    return curve


def max_drawdown(equity: list[float]) -> float:
    peak = equity[0] if equity else 0.0
    max_dd = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            max_dd = min(max_dd, (value / peak) - 1)
    return round(max_dd, 6)


def sharpe_proxy(pnls: list[float]) -> float | None:
    if len(pnls) < 2:
        return None
    sd = pstdev(pnls)
    if sd == 0:
        return None
    return round(mean(pnls) / sd, 6)


def sum_counts(counts: Any) -> dict[str, int]:
    summed: dict[str, int] = defaultdict(int)
    for count_map in counts:
        for key, value in count_map.items():
            summed[key] += int(value)
    return dict(sorted(summed.items()))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"missing input file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Combine completed monthly Higanbana pilot summaries.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    args = parser.parse_args()
    summary = run_multimonth_summary(summary_path=args.summary_path, report_path=args.report_path)
    print(json.dumps({key: value for key, value in summary.items() if key != "monthly"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
