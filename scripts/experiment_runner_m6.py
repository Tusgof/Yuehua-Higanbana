from __future__ import annotations

import json
import math
import sys
from datetime import date
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_m2_contracts import load_schema, validate_record


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "experiments" / "experiment_manifests.json"
REPORT_DIR = PROJECT_ROOT / "reports" / "experiments"


class ExperimentRunnerError(ValueError):
    pass


def load_manifests(path: Path = MANIFEST_PATH) -> list[dict[str, Any]]:
    manifests = json.loads(path.read_text(encoding="utf-8"))
    schema = load_schema()
    for manifest in manifests:
        errors = validate_record(manifest, schema)
        if errors:
            raise ExperimentRunnerError("\n".join(errors))
        validate_chronological_split(manifest)
    return manifests


def validate_chronological_split(manifest: dict[str, Any]) -> None:
    train_end = date.fromisoformat(manifest["train_window"]["end"])
    oos_start = date.fromisoformat(manifest["oos_window"]["start"])
    if train_end >= oos_start:
        raise ExperimentRunnerError(f"{manifest['experiment_id']}: train window overlaps OOS")
    if manifest["parameters_locked_before_oos"] is not True:
        raise ExperimentRunnerError(f"{manifest['experiment_id']}: parameters must be locked before OOS")


def calculate_metrics(daily_pnl: list[dict[str, Any]], trades: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [row["net_pnl"] / row["starting_equity"] for row in daily_pnl if row["starting_equity"] > 0]
    pnls = [row["net_pnl"] for row in daily_pnl]
    equity = [row["ending_equity"] for row in daily_pnl]
    trade_pnls = [trade["net_pnl"] for trade in trades]
    downside = [r for r in returns if r < 0]
    wins = [pnl for pnl in trade_pnls if pnl > 0]
    losses = [pnl for pnl in trade_pnls if pnl < 0]
    return {
        "trade_count": len(trades),
        "total_net_pnl": round(sum(trade_pnls), 2),
        "sharpe": _sharpe(returns),
        "sortino": _sortino(returns, downside),
        "max_drawdown": _max_drawdown(equity),
        "es95": _expected_shortfall(pnls, 0.95),
        "es99": _expected_shortfall(pnls, 0.99),
        "worst_day_loss": min(pnls) if pnls else 0.0,
        "win_rate": round(len(wins) / len(trade_pnls), 4) if trade_pnls else 0.0,
        "payoff_ratio": round(mean(wins) / abs(mean(losses)), 4) if wins and losses else None,
        "cost_drag": round(sum(trade.get("gross_pnl", 0) - trade.get("net_pnl", 0) for trade in trades), 2),
        "benchmark_return": round(sum(row["benchmark_return"] for row in daily_pnl), 8),
    }


def conclusion_from_metrics(metrics: dict[str, Any], min_trades: int = 500) -> str:
    if metrics["trade_count"] < min_trades:
        return "ยังสรุปไม่ได้"
    if metrics["sharpe"] > 0 and metrics["max_drawdown"] > -0.2:
        return "ผ่าน"
    return "ไม่ผ่าน"


def generate_experiment_report(
    manifest: dict[str, Any],
    metrics: dict[str, Any],
    output_dir: Path = REPORT_DIR,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    chart_dir = output_dir / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    chart_path = chart_dir / f"{manifest['experiment_id']}_equity.svg"
    write_svg_line_chart([1000, 1000 + metrics["total_net_pnl"]], chart_path)

    conclusion = conclusion_from_metrics(metrics)
    report_path = output_dir / f"{manifest['experiment_id']}.md"
    report_path.write_text(_render_report(manifest, metrics, conclusion, chart_path), encoding="utf-8")

    metadata = {
        "record_type": "report_metadata",
        "schema_version": "m2.0",
        "report_id": f"report-{manifest['experiment_id']}",
        "experiment_id": manifest["experiment_id"],
        "generated_at_et": "2026-06-29T08:00:00-04:00",
        "language": "th",
        "conclusion": conclusion,
        "metrics": metrics,
        "chart_paths": [str(chart_path)],
    }
    errors = validate_record(metadata, load_schema())
    if errors:
        raise ExperimentRunnerError("\n".join(errors))
    return {"report_path": str(report_path), "metadata": metadata}


def generate_all_fixture_reports(output_dir: Path = REPORT_DIR) -> dict[str, Any]:
    manifests = load_manifests()
    daily, trades = fixture_daily_pnl_and_trades()
    metrics = calculate_metrics(daily, trades)
    reports = [generate_experiment_report(manifest, metrics, output_dir) for manifest in manifests]
    gate = acceptance_gate([report["metadata"] for report in reports])
    final_review_path = output_dir.parent / "final_research_review.md"
    final_review_path.parent.mkdir(parents=True, exist_ok=True)
    final_review_path.write_text(_render_final_review(reports, gate), encoding="utf-8")
    return {
        "report_count": len(reports),
        "reports": [report["report_path"] for report in reports],
        "final_review_path": str(final_review_path),
        "gate": gate,
    }


def acceptance_gate(report_metadatas: list[dict[str, Any]], min_trades: int = 500) -> dict[str, Any]:
    reasons: list[str] = []
    if not report_metadatas:
        reasons.append("no experiment reports")
    for metadata in report_metadatas:
        metrics = metadata["metrics"]
        if metadata["conclusion"] != "ผ่าน":
            reasons.append(f"{metadata['experiment_id']}: conclusion={metadata['conclusion']}")
        if metrics.get("trade_count", 0) < min_trades:
            reasons.append(f"{metadata['experiment_id']}: trade_count below {min_trades}")
        for required in ("sharpe", "sortino", "max_drawdown", "es95", "es99", "worst_day_loss"):
            if required not in metrics:
                reasons.append(f"{metadata['experiment_id']}: missing {required}")
    return {"status": "pass" if not reasons else "blocked", "reasons": reasons}


def write_svg_line_chart(values: list[float], path: Path) -> None:
    if not values:
        values = [0.0]
    width, height, pad = 480, 240, 24
    min_v, max_v = min(values), max(values)
    span = max(max_v - min_v, 1)
    points = []
    for i, value in enumerate(values):
        x = pad + (width - 2 * pad) * (i / max(len(values) - 1, 1))
        y = height - pad - ((value - min_v) / span) * (height - 2 * pad)
        points.append(f"{x:.1f},{y:.1f}")
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        '<rect width="100%" height="100%" fill="white"/>\n'
        '<text x="24" y="20" font-size="14" fill="#111">Fixture equity curve</text>\n'
        f'<polyline fill="none" stroke="#2563eb" stroke-width="3" points="{" ".join(points)}"/>\n'
        '</svg>\n',
        encoding="utf-8",
    )


def fixture_daily_pnl_and_trades() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    daily = [
        {"date": "2024-01-03", "starting_equity": 1000.0, "ending_equity": 1010.0, "net_pnl": 10.0, "benchmark_return": 0.001},
        {"date": "2024-01-04", "starting_equity": 1010.0, "ending_equity": 1005.0, "net_pnl": -5.0, "benchmark_return": -0.0005},
    ]
    trades = [
        {"trade_id": "t1", "gross_pnl": 12.0, "net_pnl": 10.0},
        {"trade_id": "t2", "gross_pnl": -4.0, "net_pnl": -5.0},
    ]
    return daily, trades


def _render_report(manifest: dict[str, Any], metrics: dict[str, Any], conclusion: str, chart_path: Path) -> str:
    return f"""# รายงานการทดลอง {manifest['experiment_id']}

## สมมติฐาน
{manifest['hypothesis']}

## หลักฐานที่ใช้
- Evidence type: fixture / synthetic smoke test
- Train window: {manifest['train_window']['start']} to {manifest['train_window']['end']}
- OOS window: {manifest['oos_window']['start']} to {manifest['oos_window']['end']}
- Chart: `{chart_path}`

![equity curve]({chart_path})

## Metrics
```json
{json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True)}
```

## ข้อสรุป
{conclusion}

## เหตุผล
ผลนี้ยังเป็น fixture ถ้า trade_count ต่ำกว่าเกณฑ์ N >= 500 ต้องถือว่ายังสรุปไม่ได้ ไม่ใช่หลักฐานว่า edge ใช้งานได้จริง

## เงื่อนไขที่จะทำให้ข้อสรุปล้ม
- ข้อมูลจริงไม่มี bid/ask ที่ timestamp เข้าและออก
- OOS ถูกใช้ปรับ parameter
- ผลลัพธ์พึ่งพา extreme trades ไม่กี่ครั้ง

## ถ้าล้มเหลวต้องทำอะไรต่อ
ตรวจ data source, execution cost, split policy, และสร้าง hypothesis ใหม่ที่วัดผลได้

## Local Wiki References
- `D:\\Fogust\\Workspace\\LLM Wiki\\LLM Wiki\\wiki\\concepts\\backtest-validation-protocol.md`
- `D:\\Fogust\\Workspace\\LLM Wiki\\LLM Wiki\\wiki\\concepts\\implementable-option-pnl.md`
"""


def _render_final_review(reports: list[dict[str, Any]], gate: dict[str, Any]) -> str:
    lines = [
        "# Final Research Review",
        "",
        "## สถานะ",
        f"- Gate status: `{gate['status']}`",
        "- Evidence type: fixture / synthetic smoke test",
        "- ข้อสรุป: ยังสรุปไม่ได้",
        "",
        "## รายงานการทดลอง",
    ]
    for report in reports:
        metadata = report["metadata"]
        lines.append(f"- `{metadata['experiment_id']}`: {metadata['conclusion']} ({report['report_path']})")
    lines.extend([
        "",
        "## เหตุผลที่ยังไม่ผ่าน",
    ])
    if gate["reasons"]:
        lines.extend(f"- {reason}" for reason in gate["reasons"])
    else:
        lines.append("- ไม่มี blocker จาก gate")
    lines.extend([
        "",
        "## เงื่อนไขก่อนใช้เงินจริง",
        "- ต้องมีข้อมูล SPY 0DTE option bid/ask จริงตาม timestamp ที่ระบบใช้",
        "- ต้องรัน OOS โดยไม่ปรับ parameter หลังเห็นผล",
        "- ต้องผ่านเกณฑ์ N >= 500 trades หรือระบุว่า evidence ยังไม่พอ",
        "- ต้องผ่าน IBKR/options permission และ launch checklist",
        "",
    ])
    return "\n".join(lines)


def _sharpe(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    sd = pstdev(returns)
    return round((mean(returns) / sd) * math.sqrt(252), 4) if sd else 0.0


def _sortino(returns: list[float], downside: list[float]) -> float:
    if not returns or not downside:
        return 0.0
    sd = pstdev(downside)
    return round((mean(returns) / sd) * math.sqrt(252), 4) if sd else 0.0


def _max_drawdown(equity: list[float]) -> float:
    peak = None
    max_dd = 0.0
    for value in equity:
        peak = value if peak is None else max(peak, value)
        max_dd = min(max_dd, (value / peak) - 1)
    return round(max_dd, 6)


def _expected_shortfall(values: list[float], confidence: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    tail_count = max(1, int(math.ceil(len(ordered) * (1 - confidence))))
    return round(mean(ordered[:tail_count]), 4)


if __name__ == "__main__":
    result = generate_all_fixture_reports()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
