from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VIX_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl"
DATA_COST_ROOT = PROJECT_ROOT / "reports" / "data_cost"
PILOT_ROOT = PROJECT_ROOT / "reports" / "pilots"
PAID_COST_AUDIT = DATA_COST_ROOT / "paid_cost_audit.json"
SUMMARY_PATH = DATA_COST_ROOT / "h_a2_2022_h2_stress_purchase_estimate.json"
REPORT_PATH = DATA_COST_ROOT / "h_a2_2022_h2_stress_purchase_estimate.md"

HIGH_VIX_THRESHOLD = 25.0
STRESS_VIX_THRESHOLD = 30.0
STOP_THRESHOLD_USD = 125.0


def build_estimate(
    vix_path: Path = VIX_PATH,
    data_cost_root: Path = DATA_COST_ROOT,
    pilot_root: Path = PILOT_ROOT,
    paid_cost_audit_path: Path = PAID_COST_AUDIT,
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
) -> dict[str, Any]:
    months = _rank_2022_h2_vix_months(vix_path)
    cost_model = _build_cost_model(data_cost_root)
    trade_density = _project_trade_density(pilot_root)
    paid_cost = _load_json(paid_cost_audit_path) if paid_cost_audit_path.exists() else {}
    headroom = float(paid_cost.get("remaining_before_stop_usd", 0.0))

    top2 = _build_plan("top2", months[:2], cost_model, trade_density, headroom)
    top3 = _build_plan("top3", months[:3], cost_model, trade_density, headroom)

    result = {
        "record_type": "data_purchase_estimate",
        "schema_version": "h_a2_2022_h2_stress_purchase_estimate_v1",
        "hypothesis_id": "H-A2",
        "plan_id": "h_a2_2022_h2_stress_purchase_estimate",
        "status": "complete",
        "mode": "projection_no_databento_api_call",
        "no_new_paid_data": True,
        "purpose": "Estimate whether 2022 H2 high-VIX months are worth live cost-checking before any Databento purchase.",
        "cost_guard": {
            "basis": paid_cost.get("cost_guard_basis"),
            "used_usd": paid_cost.get("cost_guard_used_usd"),
            "stop_threshold_usd": paid_cost.get("stop_threshold_usd", STOP_THRESHOLD_USD),
            "remaining_before_stop_usd": headroom,
        },
        "selection_policy": {
            "source": str(vix_path),
            "window": "2022-07-01..2022-12-31",
            "ranking": "descending by high30 days, then high25 days, then average VIX, then max VIX",
            "high_vix_threshold": HIGH_VIX_THRESHOLD,
            "stress_vix_threshold": STRESS_VIX_THRESHOLD,
        },
        "ranked_2022_h2_months": months,
        "cost_model": cost_model,
        "trade_density_model": trade_density,
        "purchase_candidates": [top2, top3],
        "recommendation": _recommend(top2, top3, headroom),
        "next_actions": [
            "If continuing H-A2.5, run a live Databento metadata cost check for top2 only before any download.",
            "Do not buy top3 unless the user tops up or live cost proves top3 remains under the current guard.",
            "After any live cost estimate, re-run paid-cost audit before download.",
        ],
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(result), encoding="utf-8")
    return result


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# H-A2 2022 H2 Stress Purchase Estimate",
        "",
        "## Status",
        f"- Mode: `{result['mode']}`",
        f"- No new paid data: `{result['no_new_paid_data']}`",
        f"- Remaining before stop: `${result['cost_guard']['remaining_before_stop_usd']}`",
        f"- Recommendation: `{result['recommendation']['status']}`",
        f"- Reason: {result['recommendation']['reason']}",
        "",
        "## Ranked 2022 H2 Months",
        "| Rank | Month | Trading days | Avg VIX | Max VIX | High>=25 days | Stress>=30 days |",
        "|--:|:--|--:|--:|--:|--:|--:|",
    ]
    for row in result["ranked_2022_h2_months"]:
        lines.append(
            f"| {row['rank']} | `{row['month']}` | {row['trading_days']} | {row['avg_vix']} | "
            f"{row['max_vix']} | {row['high_vix_days']} | {row['stress_vix_days']} |"
        )
    lines.extend(
        [
            "",
            "## Purchase Candidates",
            "| Candidate | Months | Projected cost low/base/high | Headroom status | Projected candidates base |",
            "|:--|:--|:--|:--|--:|",
        ]
    )
    for plan in result["purchase_candidates"]:
        lines.append(
            f"| `{plan['candidate_id']}` | `{', '.join(plan['months'])}` | "
            f"${plan['cost_projection']['low_usd']} / ${plan['cost_projection']['base_usd']} / ${plan['cost_projection']['high_usd']} | "
            f"`{plan['headroom_status']}` | {plan['trade_density_projection']['base_candidate_ready_days']} |"
        )
    lines.extend(
        [
            "",
            "## Cost Model",
            "```json",
            json.dumps(result["cost_model"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Trade Density Model",
            "```json",
            json.dumps(result["trade_density_model"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _rank_2022_h2_vix_months(path: Path) -> list[dict[str, Any]]:
    by_month: dict[str, list[float]] = {}
    for row in _load_jsonl(path):
        trade_date = row["date"]
        if "2022-07-01" <= trade_date <= "2022-12-31":
            by_month.setdefault(trade_date[:7], []).append(float(row["vix_close"]))

    rows = []
    for month, values in sorted(by_month.items()):
        rows.append(
            {
                "month": month,
                "trading_days": len(values),
                "avg_vix": round(mean(values), 4),
                "max_vix": round(max(values), 4),
                "high_vix_days": sum(value >= HIGH_VIX_THRESHOLD for value in values),
                "stress_vix_days": sum(value >= STRESS_VIX_THRESHOLD for value in values),
            }
        )
    rows.sort(key=lambda row: (row["stress_vix_days"], row["high_vix_days"], row["avg_vix"], row["max_vix"]), reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def _build_cost_model(root: Path) -> dict[str, Any]:
    monthly = _monthly_cost_totals(root)
    comparable = [value for month, value in monthly.items() if month >= "2023-09"]
    if not comparable:
        raise ValueError("No comparable Databento monthly cost artifacts found")
    low = min(comparable)
    base = mean(comparable)
    high = max(comparable)
    return {
        "source": "existing Databento download_result artifacts; projection only, not a live Databento quote",
        "comparable_month_count": len(comparable),
        "comparable_month_costs": {month: monthly[month] for month in sorted(monthly) if month >= "2023-09"},
        "per_month_low_usd": round(low, 6),
        "per_month_base_usd": round(base, 6),
        "per_month_high_usd": round(high, 6),
    }


def _monthly_cost_totals(root: Path) -> dict[str, float]:
    totals: dict[str, float] = {}
    for path in sorted(root.glob("databento_download_result*.json")):
        month = _month_from_cost_path(path)
        if month is None:
            continue
        payload = _load_json(path)
        cost = _cost_from_payload(payload)
        if cost is None:
            continue
        totals[month] = round(totals.get(month, 0.0) + cost, 6)
    return totals


def _month_from_cost_path(path: Path) -> str | None:
    match = re.search(r"(?:insample|oos)_(20\d{2})_(\d{2})", path.name)
    if not match:
        return None
    month = f"{match.group(1)}-{match.group(2)}"
    if month == "2024-07" and "partial" in path.name:
        return None
    return month


def _project_trade_density(root: Path) -> dict[str, Any]:
    month_counts: dict[str, dict[str, int]] = {}
    for path in sorted(root.glob("*_pilot_adapter_summary.json")):
        payload = _load_json(path)
        for day in payload.get("days", []):
            month = str(day["date"])[:7]
            counts = month_counts.setdefault(month, {"trade_days": 0, "candidate_ready_days": 0})
            counts["trade_days"] += 1
            if day.get("status") == "candidate_ready":
                counts["candidate_ready_days"] += 1

    existing = [row for month, row in month_counts.items() if month >= "2023-03"]
    total_days = sum(row["trade_days"] for row in existing)
    total_candidates = sum(row["candidate_ready_days"] for row in existing)
    overall_rate = total_candidates / total_days if total_days else 0.0
    aug_2024 = month_counts.get("2024-08", {"trade_days": 0, "candidate_ready_days": 0})
    aug_rate = aug_2024["candidate_ready_days"] / aug_2024["trade_days"] if aug_2024["trade_days"] else 0.0
    return {
        "source": "existing pilot adapter summaries; projection only",
        "observed_month_count": len(existing),
        "observed_trade_days": total_days,
        "observed_candidate_ready_days": total_candidates,
        "overall_candidate_rate": round(overall_rate, 6),
        "aug_2024_candidate_rate": round(aug_rate, 6),
        "note": "Candidate density is uncertain in 2022 because option data is not downloaded yet; use this only as a pre-purchase density warning.",
    }


def _build_plan(
    candidate_id: str,
    months: list[dict[str, Any]],
    cost_model: dict[str, Any],
    trade_density: dict[str, Any],
    headroom: float,
) -> dict[str, Any]:
    month_count = len(months)
    trading_days = sum(row["trading_days"] for row in months)
    low = round(cost_model["per_month_low_usd"] * month_count, 6)
    base = round(cost_model["per_month_base_usd"] * month_count, 6)
    high = round(cost_model["per_month_high_usd"] * month_count, 6)
    base_candidates = round(trading_days * trade_density["overall_candidate_rate"], 2)
    stress_low_candidates = round(trading_days * trade_density["aug_2024_candidate_rate"], 2)
    headroom_status = "fits_base_projection" if base < headroom else "requires_live_cost_or_topup"
    if high < headroom:
        headroom_status = "fits_high_projection"
    return {
        "candidate_id": candidate_id,
        "months": [row["month"] for row in months],
        "trading_days": trading_days,
        "cost_projection": {"low_usd": low, "base_usd": base, "high_usd": high},
        "trade_density_projection": {
            "base_candidate_ready_days": base_candidates,
            "stress_low_candidate_ready_days": stress_low_candidates,
        },
        "headroom_status": headroom_status,
    }


def _recommend(top2: dict[str, Any], top3: dict[str, Any], headroom: float) -> dict[str, str]:
    if top2["cost_projection"]["base_usd"] < headroom and top3["cost_projection"]["base_usd"] >= headroom:
        return {
            "status": "live_cost_check_top2_only",
            "reason": "Top2 is the only candidate that plausibly fits the current headroom on base projection; top3 likely requires top-up.",
        }
    if top2["cost_projection"]["base_usd"] >= headroom:
        return {
            "status": "pause_until_topup_or_live_cost_lower",
            "reason": "Even top2 base projection is at or above current headroom.",
        }
    return {
        "status": "live_cost_check_top2_then_decide_top3",
        "reason": "Top2 and possibly top3 fit the base projection; use live Databento cost before any download.",
    }


def _cost_from_payload(payload: dict[str, Any]) -> float | None:
    for key in ("total_estimated_cost_usd", "estimated_cost_usd"):
        value = payload.get(key)
        if isinstance(value, int | float):
            return round(float(value), 6)
    request = payload.get("request")
    if isinstance(request, dict) and isinstance(request.get("estimated_cost_usd"), int | float):
        return round(float(request["estimated_cost_usd"]), 6)
    return None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan H-A2 2022 H2 high-VIX stress data purchase before any download.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)

    result = build_estimate(summary_path=args.summary_path, report_path=args.report_path)
    print(json.dumps({key: value for key, value in result.items() if key != "ranked_2022_h2_months"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
