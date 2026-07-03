from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_JSONL = PROJECT_ROOT / "data" / "derived" / "spy_0dte" / "greeks_oi_probe" / "option_quote_enriched_2024-01-03.jsonl"
SUMMARY_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "gamma_aggregation_diagnostic_summary.json"
TARGET_DATE = "2024-01-03"
CONTRACT_MULTIPLIER = 100
UTC = ZoneInfo("UTC")


def run_diagnostic(
    input_jsonl: Path = INPUT_JSONL,
    summary_output: Path = SUMMARY_OUTPUT,
    target_date: str = TARGET_DATE,
) -> dict[str, Any]:
    rows = _load_jsonl(input_jsonl)
    result = aggregate_gamma_diagnostic(rows, input_jsonl, target_date)
    write_summary(result, summary_output)
    return result


def aggregate_gamma_diagnostic(rows: list[dict[str, Any]], input_jsonl: Path, target_date: str) -> dict[str, Any]:
    computed_rows = [row for row in rows if row.get("greeks_status") == "computed_with_caveats"]
    blocked_rows = [row for row in rows if row.get("greeks_status") != "computed_with_caveats"]
    quote_count = len(rows)
    underlying_join_count = sum(1 for row in rows if row.get("underlying_price") is not None)
    oi_join_count = sum(1 for row in rows if row.get("open_interest") is not None)
    timestamp_discipline = _timestamp_discipline(rows)
    bucket_summaries = _bucket_summaries(rows)
    blocked_by_bucket_right = _blocked_counts(blocked_rows)
    coverage = _coverage_gate(quote_count, underlying_join_count, oi_join_count, len(computed_rows))
    stability = _stability_gate(rows)
    economic_sign = {
        "status": "blocked",
        "reason": "requires_multiple_dates_for_realized_volatility_and_pnl_split",
    }
    search_log = {
        "status": "pass",
        "reason": "no threshold or best gamma bucket was selected in this diagnostic run",
    }
    gates = {
        "coverage": coverage,
        "timestamp_discipline": timestamp_discipline,
        "stability": stability,
        "economic_sign": economic_sign,
        "search_log": search_log,
    }
    blockers = _gate_blockers(gates)

    return {
        "record_type": "gamma_aggregation_diagnostic",
        "schema_version": "gamma_aggregation_diagnostic_v1",
        "status": "blocked" if blockers else "pass_diagnostic_only",
        "target_date": target_date,
        "input_jsonl": str(input_jsonl),
        "quote_count": quote_count,
        "computed_greeks_count": len(computed_rows),
        "blocked_greeks_count": len(blocked_rows),
        "underlying_join_count": underlying_join_count,
        "open_interest_join_count": oi_join_count,
        "contract_multiplier": CONTRACT_MULTIPLIER,
        "bucket_summaries": bucket_summaries,
        "blocked_rows_by_moneyness_and_right": blocked_by_bucket_right,
        "validation_gates": gates,
        "blockers": blockers,
        "strategy_use_status": "diagnostic_only_blocked_by_policy_gates" if blockers else "diagnostic_only_not_strategy_ready",
        "research_decision": _research_decision(blockers),
    }


def moneyness_bucket(moneyness: float) -> str:
    if moneyness < 0.97:
        return "deep_put"
    if moneyness < 0.995:
        return "otm_put"
    if moneyness <= 1.005:
        return "atm"
    if moneyness <= 1.03:
        return "otm_call"
    return "deep_call"


def local_gamma_exposure(row: dict[str, Any]) -> float:
    return float(row["gamma"]) * float(row["open_interest"]) * CONTRACT_MULTIPLIER * float(row["underlying_price"])


def signed_gamma_proxy(row: dict[str, Any]) -> float:
    exposure = local_gamma_exposure(row)
    right = str(row.get("right", "")).lower()
    if right == "call":
        return exposure
    if right == "put":
        return -exposure
    raise ValueError(f"unsupported option right: {row.get('right')}")


def _bucket_summaries(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    computed = [row for row in rows if row.get("greeks_status") == "computed_with_caveats"]
    total_abs_gamma = sum(abs(local_gamma_exposure(row)) for row in computed)
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        bucket = _row_bucket(row)
        summary = buckets.setdefault(
            bucket,
            {
                "row_count": 0,
                "computed_count": 0,
                "blocked_count": 0,
                "open_interest_sum": 0,
                "underlying_notional_sum": 0.0,
                "raw_local_gamma_exposure_sum": 0.0,
                "signed_oi_gamma_proxy_sum": 0.0,
                "scaled_signed_gamma_proxy": None,
                "bucket_contribution_share": None,
                "percentile_rank": "probe_only",
            },
        )
        summary["row_count"] += 1
        if row.get("greeks_status") != "computed_with_caveats":
            summary["blocked_count"] += 1
            continue
        oi = float(row["open_interest"])
        underlying_price = float(row["underlying_price"])
        notional = oi * CONTRACT_MULTIPLIER * underlying_price
        exposure = local_gamma_exposure(row)
        signed = signed_gamma_proxy(row)
        summary["computed_count"] += 1
        summary["open_interest_sum"] += int(oi)
        summary["underlying_notional_sum"] += notional
        summary["raw_local_gamma_exposure_sum"] += exposure
        summary["signed_oi_gamma_proxy_sum"] += signed

    for summary in buckets.values():
        notional = summary["underlying_notional_sum"]
        raw_gamma = summary["raw_local_gamma_exposure_sum"]
        signed = summary["signed_oi_gamma_proxy_sum"]
        summary["underlying_notional_sum"] = round(notional, 6)
        summary["raw_local_gamma_exposure_sum"] = round(raw_gamma, 6)
        summary["signed_oi_gamma_proxy_sum"] = round(signed, 6)
        summary["scaled_signed_gamma_proxy"] = round(signed / notional, 10) if notional else None
        summary["bucket_contribution_share"] = round(abs(raw_gamma) / total_abs_gamma, 10) if total_abs_gamma else None
    return dict(sorted(buckets.items()))


def _row_bucket(row: dict[str, Any]) -> str:
    if row.get("strike") is None or row.get("underlying_price") is None:
        return "unknown"
    return moneyness_bucket(float(row["strike"]) / float(row["underlying_price"]))


def _blocked_counts(blocked_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in blocked_rows:
        key = f"{_row_bucket(row)}|{row.get('right', 'unknown')}"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _coverage_gate(quote_count: int, underlying_join_count: int, oi_join_count: int, computed_count: int) -> dict[str, Any]:
    if quote_count == 0:
        return {"status": "blocked", "reason": "no_quote_rows"}
    underlying_join_rate = underlying_join_count / quote_count
    oi_join_rate = oi_join_count / quote_count
    computed_greeks_rate = computed_count / quote_count
    blockers = []
    if underlying_join_rate < 0.95:
        blockers.append("underlying_join_rate_below_95pct")
    if oi_join_rate < 0.95:
        blockers.append("open_interest_join_rate_below_95pct")
    if computed_greeks_rate < 0.70:
        blockers.append("computed_greeks_rate_below_70pct")
    return {
        "status": "pass" if not blockers else "blocked",
        "underlying_join_rate": round(underlying_join_rate, 6),
        "open_interest_join_rate": round(oi_join_rate, 6),
        "computed_greeks_rate": round(computed_greeks_rate, 6),
        "blockers": blockers,
    }


def _timestamp_discipline(rows: list[dict[str, Any]]) -> dict[str, Any]:
    future_oi = 0
    future_underlying = 0
    parse_errors = 0
    checked_oi = 0
    checked_underlying = 0
    for row in rows:
        try:
            quote_ts = _parse_dt(row["quote_timestamp_et"])
            oi_ts = row.get("open_interest_timestamp_utc")
            underlying_ts = row.get("underlying_price_timestamp_et")
            if oi_ts:
                checked_oi += 1
                if _parse_dt(oi_ts).astimezone(UTC) > quote_ts.astimezone(UTC):
                    future_oi += 1
            if underlying_ts:
                checked_underlying += 1
                if _parse_dt(underlying_ts) > quote_ts:
                    future_underlying += 1
        except (KeyError, TypeError, ValueError):
            parse_errors += 1
    blockers = []
    if future_oi:
        blockers.append("future_open_interest_detected")
    if future_underlying:
        blockers.append("future_underlying_bar_detected")
    if parse_errors:
        blockers.append("timestamp_parse_errors")
    return {
        "status": "pass" if not blockers else "blocked",
        "checked_open_interest_rows": checked_oi,
        "checked_underlying_rows": checked_underlying,
        "future_open_interest_rows": future_oi,
        "future_underlying_rows": future_underlying,
        "timestamp_parse_errors": parse_errors,
        "blockers": blockers,
    }


def _stability_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    dates = sorted({str(row.get("quote_timestamp_et", ""))[:10] for row in rows if row.get("quote_timestamp_et")})
    if len(dates) < 4:
        return {
            "status": "blocked",
            "available_dates": dates,
            "label": "under-regime-sampled",
            "reason": "policy requires multiple dates/regimes before strategy use",
        }
    return {"status": "pass", "available_dates": dates}


def _gate_blockers(gates: dict[str, dict[str, Any]]) -> list[str]:
    blockers = []
    for name, gate in gates.items():
        if gate["status"] != "pass":
            blockers.append(f"{name}_gate:{gate['status']}")
    return blockers


def _research_decision(blockers: list[str]) -> str:
    if blockers:
        return (
            "ยังสรุปไม่ได้: diagnostic aggregation คำนวณ proxy ได้ แต่ยังไม่ผ่าน policy gates "
            "จึงใช้เป็น NOVI/net-gamma strategy filter ไม่ได้"
        )
    return "ผ่านเฉพาะ diagnostic: aggregation ผ่าน gate เบื้องต้น แต่ยังต้องทดสอบ MinTRL/PSR และ OOS ก่อนใช้เป็น strategy filter"


def _parse_dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_summary(result: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run diagnostic gamma aggregation against the project validation policy.")
    parser.add_argument("--input-jsonl", type=Path, default=INPUT_JSONL)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--target-date", default=TARGET_DATE)
    args = parser.parse_args(argv)

    result = run_diagnostic(args.input_jsonl, args.summary_output, args.target_date)
    print(json.dumps({"status": result["status"], "blockers": result["blockers"]}, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"blocked", "pass_diagnostic_only"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
