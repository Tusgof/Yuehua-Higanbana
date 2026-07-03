from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = PROJECT_ROOT / "reports" / "baselines" / "subsystem_a_orb_baseline_summary.json"
VIX_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl"
MACRO_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl"
JSON_OUTPUT = PROJECT_ROOT / "reports" / "risk_first_data_audit.json"
MD_OUTPUT = PROJECT_ROOT / "reports" / "risk_first_data_audit.md"
GREEKS_OI_FEASIBILITY_PATH = PROJECT_ROOT / "reports" / "greeks_oi_feasibility_audit.json"
GREEKS_OI_ENRICHMENT_PATH = PROJECT_ROOT / "reports" / "greeks_oi_enrichment_probe_summary.json"

NULL_SHARPE_THRESHOLDS = [0.0, 0.5]
ONE_SIDED_95_Z = 1.6448536269514722
MAJOR_MACRO_TYPES = {"CPI", "NFP", "PCE", "FOMC_DECISION", "FOMC_MINUTES"}
GREEK_FIELDS = {"delta", "gamma", "vega", "theta", "rho", "iv", "implied_volatility"}
OI_FIELDS = {"open_interest", "oi"}


def audit_risk_first_data(
    summary_path: Path = SUMMARY_PATH,
    vix_path: Path = VIX_PATH,
    macro_path: Path = MACRO_PATH,
) -> dict[str, Any]:
    summary = _load_json(summary_path)
    trades = _load_closed_trades_from_components(summary)
    vix_rows = _load_jsonl(vix_path)
    macro_by_date = _load_macro_by_date(macro_path)
    spy_bars_by_date = _load_spy_bars_by_date(summary)

    sample_audit = _sample_inference_audit(trades)
    regime_audit = _regime_coverage_audit(trades, vix_rows, macro_by_date, spy_bars_by_date)
    greeks_probe = _greeks_data_probe(summary)
    blockers = _blockers(sample_audit, regime_audit, greeks_probe)

    return {
        "record_type": "risk_first_data_audit",
        "schema_version": "risk_first_data_audit_v1",
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "input_paths": {
            "baseline_summary": str(summary_path),
            "vix_vxv": str(vix_path),
            "macro_calendar": str(macro_path),
        },
        "sample_inference_audit": sample_audit,
        "regime_coverage_audit": regime_audit,
        "greeks_data_probe": greeks_probe,
        "next_safe_action": _next_safe_action(blockers),
        "note": "Read-only Risk-first audit from existing local artifacts; no live Databento or OpenRouter calls.",
    }


def write_reports(result: dict[str, Any], json_output: Path = JSON_OUTPUT, md_output: Path = MD_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_output.write_text(_render_markdown(result), encoding="utf-8")


def _sample_inference_audit(trades: list[dict[str, Any]]) -> dict[str, Any]:
    returns = _trade_returns(trades)
    sharpe = _sharpe(returns)
    skewness = _skewness(returns)
    kurtosis = _kurtosis(returns)
    autocorr = _first_order_autocorr(returns)
    psr_rows = [
        _psr_mintrl_row(sharpe, len(returns), skewness, kurtosis, autocorr, threshold)
        for threshold in NULL_SHARPE_THRESHOLDS
    ]
    labels = ["under-sampled", "underpowered"]
    if any(row["mintrl_status"] == "pass" for row in psr_rows):
        labels = ["underpowered"]
    return {
        "status": "blocked",
        "blockers": ["requires_mintrl_psr_sample_adequacy"],
        "return_basis": "per-trade implementable_pnl / starting_equity from closed Sub-System A ORB baseline trades",
        "starting_equity": 1000.0,
        "sample_length": len(returns),
        "observed_sharpe": sharpe,
        "skewness": skewness,
        "kurtosis": kurtosis,
        "first_order_autocorrelation": autocorr,
        "effective_sample_length_autocorr_adjusted": _effective_sample_length(len(returns), autocorr),
        "psr_mintrl_approximation": {
            "formula_policy": "Lopez-de-Prado-style finite-sample Sharpe approximation using skewness/kurtosis; autocorrelation is handled by effective sample length heuristic because the local wiki does not specify the full closed-form AR(1) adjustment.",
            "significance": "one-sided 95pct",
            "rows": psr_rows,
        },
        "labels": labels,
        "interpretation": "Current evidence is diagnostic only. It may help choose the next data target, but it cannot approve the strategy.",
    }


def _psr_mintrl_row(
    observed_sharpe: float | None,
    n: int,
    skewness: float | None,
    kurtosis: float | None,
    autocorr: float | None,
    null_sharpe: float,
) -> dict[str, Any]:
    if observed_sharpe is None or skewness is None or kurtosis is None or n < 3:
        return {
            "null_sharpe": null_sharpe,
            "psr": None,
            "mintrl_required_observations": None,
            "mintrl_status": "blocked_missing_distribution_inputs",
        }

    variance_term = 1.0 - (skewness * observed_sharpe) + (((kurtosis - 1.0) / 4.0) * observed_sharpe * observed_sharpe)
    variance_term = max(variance_term, 1e-12)
    effective_n = _effective_sample_length(n, autocorr)
    denominator = math.sqrt(variance_term)
    statistic = (observed_sharpe - null_sharpe) * math.sqrt(max(effective_n - 1.0, 1.0)) / denominator
    psr = _normal_cdf(statistic)

    if observed_sharpe <= null_sharpe:
        mintrl = None
        status = "blocked_observed_sharpe_not_above_null"
    else:
        mintrl_raw = 1.0 + variance_term * (ONE_SIDED_95_Z / (observed_sharpe - null_sharpe)) ** 2
        autocorr_inflation = _autocorr_inflation(autocorr)
        mintrl = math.ceil(mintrl_raw * autocorr_inflation)
        status = "pass" if n >= mintrl else "under-sampled"

    return {
        "null_sharpe": null_sharpe,
        "psr": round(psr, 6),
        "mintrl_required_observations": mintrl,
        "mintrl_status": status,
        "actual_observations": n,
    }


def _regime_coverage_audit(
    trades: list[dict[str, Any]],
    vix_rows: list[dict[str, Any]],
    macro_by_date: dict[str, list[dict[str, Any]]],
    spy_bars_by_date: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    enriched = []
    for trade in trades:
        trade_date = str(trade["date"])
        vix_record = _previous_vix_record(trade_date, vix_rows)
        macro_events = macro_by_date.get(trade_date, [])
        trend = _trend_bucket(trade_date, spy_bars_by_date)
        enriched.append(
            {
                **trade,
                "vix_bucket": _vix_bucket(vix_record),
                "macro_bucket": _macro_bucket(macro_events),
                "trend_bucket": trend,
                "subperiod_bucket": _subperiod_bucket(trade_date),
            }
        )

    coverage = {
        "vix_bucket": _summarize_bucket(enriched, "vix_bucket"),
        "macro_bucket": _summarize_bucket(enriched, "macro_bucket"),
        "trend_bucket": _summarize_bucket(enriched, "trend_bucket"),
        "subperiod_bucket": _summarize_bucket(enriched, "subperiod_bucket"),
        "split": _summarize_bucket(enriched, "split"),
    }
    missing = _missing_regime_warnings(coverage)
    return {
        "status": "blocked" if missing else "pass",
        "blockers": missing,
        "trade_count": len(enriched),
        "coverage": coverage,
        "methodology": {
            "vix": "Previous available VIX/VIX3M close before trade date.",
            "macro": "Same-day scheduled macro events from canonical macro archive.",
            "trend": "Ex-ante SPY close versus trailing 20 prior trading-day closes when enough prior bar coverage exists.",
            "subperiod": "Reference/pre-break, post-break train, and OOS labels from PROJECT_BRAIN split policy.",
        },
    }


def _greeks_data_probe(summary: dict[str, Any]) -> dict[str, Any]:
    quote_paths = [Path(dataset["quote_path"]) for dataset in summary.get("datasets", []) if dataset.get("quote_path")]
    field_counts: dict[str, int] = defaultdict(int)
    sampled_files = 0
    sampled_rows = 0
    for path in quote_paths:
        if not path.exists():
            continue
        sampled_files += 1
        with path.open("r", encoding="utf-8-sig") as handle:
            for index, line in enumerate(handle):
                if index >= 100:
                    break
                if not line.strip():
                    continue
                sampled_rows += 1
                row = json.loads(line)
                for field in row:
                    field_counts[field] += 1

    present_fields = set(field_counts)
    greek_fields_present = sorted(present_fields & GREEK_FIELDS)
    oi_fields_present = sorted(present_fields & OI_FIELDS)
    required_for_self_computed = {"bid", "ask", "strike", "right", "expiration_date", "quote_timestamp_et", "underlying"}
    self_compute_missing = sorted(required_for_self_computed - present_fields)
    blockers = []
    if not greek_fields_present:
        blockers.append("normalized_option_quotes_missing_vendor_greeks")
    if not oi_fields_present:
        blockers.append("normalized_option_quotes_missing_open_interest")
    if self_compute_missing:
        blockers.append("self_computed_greeks_missing_required_quote_fields:" + ",".join(self_compute_missing))
    feasibility = _load_optional_json(GREEKS_OI_FEASIBILITY_PATH)
    feasibility_status = feasibility.get("status") if feasibility else None
    enrichment = _load_optional_json(GREEKS_OI_ENRICHMENT_PATH)
    enrichment_status = enrichment.get("status") if enrichment else None

    return {
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "sampled_quote_files": sampled_files,
        "sampled_quote_rows": sampled_rows,
        "observed_quote_fields": sorted(present_fields),
        "vendor_greek_fields_present": greek_fields_present,
        "open_interest_fields_present": oi_fields_present,
        "self_computed_greeks_feasibility": (
            "passed_local_iv_delta_gamma_probe_with_caveats"
            if feasibility_status == "pass"
            else "feasible_for_iv_delta_gamma_probe_if_underlying_price_and_rate_assumptions_are_joined"
            if not self_compute_missing
            else "blocked"
        ),
        "oi_greeks_feasibility_report": str(GREEKS_OI_FEASIBILITY_PATH) if feasibility else None,
        "oi_greeks_feasibility_status": feasibility_status,
        "oi_greeks_enrichment_report": str(GREEKS_OI_ENRICHMENT_PATH) if enrichment else None,
        "oi_greeks_enrichment_status": enrichment_status,
        "oi_greeks_enrichment_counts": {
            "quote_count": enrichment.get("quote_count") if enrichment else None,
            "open_interest_join_count": enrichment.get("open_interest_join_count") if enrichment else None,
            "underlying_join_count": enrichment.get("underlying_join_count") if enrichment else None,
            "computed_greeks_count": enrichment.get("computed_greeks_count") if enrichment else None,
            "greeks_status_counts": enrichment.get("greeks_status_counts") if enrichment else None,
        },
        "databento_next_probe": (
            "Current cbbo-1m normalized quotes do not include vendor Greeks or OI, but the local derived enrichment probe passed with caveats. Next define gamma aggregation/scaling and validation policy before any NOVI/net-gamma strategy report."
            if enrichment_status == "pass"
            else
            "Current cbbo-1m normalized quotes do not include vendor Greeks or OI. The OPRA OI timestamp/symbol mapping and self-computed IV/Delta/Gamma feasibility audit passed with caveats; next implement normalized quote enrichment plus rate/dividend and gamma aggregation policy before any gamma-family strategy report."
            if feasibility_status == "pass"
            else "Current cbbo-1m normalized quotes do not include vendor Greeks or OI. The OPRA statistics/OI metadata and one-day download probes are complete; next define timestamp mapping for OI and test self-computed IV/Greeks feasibility before using gamma-family inputs in a strategy report."
        ),
    }


def _load_closed_trades_from_components(summary: dict[str, Any]) -> list[dict[str, Any]]:
    trades = []
    for dataset in summary.get("datasets", []):
        path = Path(dataset["component_summary_path"])
        if not path.exists():
            continue
        component = _load_json(path)
        for trade in component.get("trades", []):
            if str(trade.get("status", "")).startswith("closed_"):
                trades.append({**trade, "dataset": dataset["label"], "split": dataset["split"]})
    return sorted(trades, key=lambda row: (row.get("date", ""), row.get("dataset", "")))


def _load_spy_bars_by_date(summary: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_paths = set()
    for dataset in summary.get("datasets", []):
        path = Path(dataset["bar_path"])
        if path in seen_paths or not path.exists():
            continue
        seen_paths.add(path)
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            trade_date = str(row["timestamp_et"])[:10]
            rows[trade_date].append(row)
    return {key: sorted(value, key=lambda row: row["timestamp_et"]) for key, value in rows.items()}


def _trade_returns(trades: list[dict[str, Any]]) -> list[float]:
    return [round(float(trade.get("implementable_pnl", 0.0)) / 1000.0, 10) for trade in trades]


def _sharpe(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    sd = pstdev(values)
    if sd == 0:
        return None
    return round(mean(values) / sd, 6)


def _skewness(values: list[float]) -> float | None:
    if len(values) < 3:
        return None
    mu = mean(values)
    sd = pstdev(values)
    if sd == 0:
        return None
    return round(sum(((x - mu) / sd) ** 3 for x in values) / len(values), 6)


def _kurtosis(values: list[float]) -> float | None:
    if len(values) < 4:
        return None
    mu = mean(values)
    sd = pstdev(values)
    if sd == 0:
        return None
    return round(sum(((x - mu) / sd) ** 4 for x in values) / len(values), 6)


def _first_order_autocorr(values: list[float]) -> float | None:
    if len(values) < 3:
        return None
    x = values[:-1]
    y = values[1:]
    mx = mean(x)
    my = mean(y)
    numerator = sum((a - mx) * (b - my) for a, b in zip(x, y))
    denominator = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def _effective_sample_length(n: int, autocorr: float | None) -> float:
    if autocorr is None or autocorr <= 0:
        return float(n)
    if autocorr >= 0.99:
        return 1.0
    return max(1.0, n * (1.0 - autocorr) / (1.0 + autocorr))


def _autocorr_inflation(autocorr: float | None) -> float:
    if autocorr is None or autocorr <= 0:
        return 1.0
    if autocorr >= 0.99:
        return 100.0
    return (1.0 + autocorr) / (1.0 - autocorr)


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _load_macro_by_date(path: Path) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _load_jsonl(path):
        if row.get("record_type") == "macro_event":
            rows[str(row["event_timestamp_et"])[:10]].append(row)
    return dict(rows)


def _previous_vix_record(trade_date: str, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    target = date.fromisoformat(trade_date)
    candidates = [row for row in rows if date.fromisoformat(row["date"]) < target]
    return candidates[-1] if candidates else None


def _vix_bucket(record: dict[str, Any] | None) -> str:
    if record is None:
        return "missing_vix"
    vix = float(record["vix_close"])
    vxv = float(record["vxv_close"])
    band = "vix_low_lt15" if vix < 15 else "vix_normal_15_25" if vix <= 25 else "vix_high_gt25"
    term = "term_inverted" if vix >= vxv else "term_normal"
    return f"{band}|{term}"


def _macro_bucket(events: list[dict[str, Any]]) -> str:
    if not events:
        return "no_same_day_macro"
    event_types = {str(event.get("event_type")) for event in events}
    if event_types & MAJOR_MACRO_TYPES:
        return "major_macro_same_day"
    if any(event.get("importance") == "high" for event in events):
        return "high_importance_macro_same_day"
    return "other_macro_same_day"


def _trend_bucket(trade_date: str, bars_by_date: dict[str, list[dict[str, Any]]]) -> str:
    prior_dates = sorted(day for day in bars_by_date if day < trade_date)
    if len(prior_dates) < 20:
        return "trend_insufficient_prior_bars"
    last_20 = prior_dates[-20:]
    closes = [float(bars_by_date[day][-1]["close"]) for day in last_20 if bars_by_date[day]]
    if len(closes) < 20:
        return "trend_insufficient_prior_bars"
    previous_close = closes[-1]
    sma20 = mean(closes)
    if previous_close > sma20 * 1.005:
        return "spy_uptrend_above_sma20"
    if previous_close < sma20 * 0.995:
        return "spy_downtrend_below_sma20"
    return "spy_neutral_near_sma20"


def _subperiod_bucket(trade_date: str) -> str:
    if trade_date < "2022-05-11":
        return "reference_pre_break"
    if trade_date < "2024-01-01":
        return "post_break_train"
    return "oos_2024_plus"


def _summarize_bucket(trades: list[dict[str, Any]], field: str) -> dict[str, Any]:
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {"trade_count": 0, "implementable_pnl": 0.0, "wins": 0})
    for trade in trades:
        bucket = str(trade.get(field, "missing"))
        pnl = float(trade.get("implementable_pnl", 0.0))
        buckets[bucket]["trade_count"] += 1
        buckets[bucket]["implementable_pnl"] += pnl
        if pnl > 0:
            buckets[bucket]["wins"] += 1
    return {
        key: {
            "trade_count": value["trade_count"],
            "implementable_pnl": round(value["implementable_pnl"], 2),
            "win_rate": round(value["wins"] / value["trade_count"], 4) if value["trade_count"] else 0.0,
        }
        for key, value in sorted(buckets.items())
    }


def _missing_regime_warnings(coverage: dict[str, dict[str, Any]]) -> list[str]:
    blockers = []
    if "reference_pre_break" not in coverage["subperiod_bucket"]:
        blockers.append("missing_reference_pre_break_regime_trades")
    if not any(key.startswith("vix_high_gt25") for key in coverage["vix_bucket"]):
        blockers.append("missing_high_vix_trade_coverage")
    if "major_macro_same_day" not in coverage["macro_bucket"]:
        blockers.append("missing_major_macro_same_day_trade_coverage")
    if "trend_insufficient_prior_bars" in coverage["trend_bucket"]:
        blockers.append("trend_bucket_has_insufficient_prior_bar_history")
    return blockers


def _blockers(sample_audit: dict[str, Any], regime_audit: dict[str, Any], greeks_probe: dict[str, Any]) -> list[str]:
    blockers = []
    blockers.extend(sample_audit.get("blockers", []))
    blockers.extend(f"regime_coverage:{item}" for item in regime_audit.get("blockers", []))
    blockers.extend(f"greeks_data_probe:{item}" for item in greeks_probe.get("blockers", []))
    return blockers


def _next_safe_action(blockers: list[str]) -> str:
    if not blockers:
        return "Use this audit as the pre-purchase checkpoint, then choose the next data target by missing regime/sample field rather than by calendar completion."
    if GREEKS_OI_ENRICHMENT_PATH.exists():
        return "Do not buy broad calendar data yet. The local Greeks/OI enrichment probe passed with caveats; next define gamma aggregation/scaling and validation policy, or choose a targeted sample/regime expansion for pre-break, high-VIX, or major-macro coverage."
    if GREEKS_OI_FEASIBILITY_PATH.exists():
        return "Do not buy broad calendar data yet. The OPRA OI plus self-computed IV/Greeks feasibility path passed with caveats; next either enrich normalized quotes for gamma-family research or choose a targeted sample/regime expansion for pre-break, high-VIX, or major-macro coverage."
    return "Do not buy broad calendar data yet. Review risk_first_data_audit and the completed OPRA statistics/OI probe, then choose a targeted next data action: OI timestamp mapping plus self-computed IV/Greeks feasibility, pre-break/high-VIX/major-macro coverage, or a revised higher-density strategy hypothesis."


def _render_markdown(result: dict[str, Any]) -> str:
    sample = result["sample_inference_audit"]
    regimes = result["regime_coverage_audit"]
    greeks = result["greeks_data_probe"]
    lines = [
        "# Risk-First Data Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Trade sample: {sample['sample_length']}",
        f"- Observed Sharpe: `{sample['observed_sharpe']}`",
        f"- Skewness: `{sample['skewness']}`",
        f"- Kurtosis: `{sample['kurtosis']}`",
        f"- First-order autocorrelation: `{sample['first_order_autocorrelation']}`",
        f"- Labels: {', '.join(f'`{label}`' for label in sample['labels'])}",
        f"- Next safe action: {result['next_safe_action']}",
        "",
        "## Blockers",
        "",
    ]
    lines.extend([f"- `{blocker}`" for blocker in result["blockers"]] or ["- None"])
    lines.extend(
        [
            "",
            "## PSR / MinTRL Approximation",
            "",
            "| Null Sharpe | PSR | MinTRL required | Actual N | Status |",
            "|--:|--:|--:|--:|:--|",
        ]
    )
    for row in sample["psr_mintrl_approximation"]["rows"]:
        lines.append(
            f"| {row['null_sharpe']} | {row['psr']} | {row['mintrl_required_observations']} | {row['actual_observations']} | `{row['mintrl_status']}` |"
        )
    lines.extend(["", "## Regime Coverage", ""])
    for name, buckets in regimes["coverage"].items():
        lines.extend([f"### {name}", "", "| Bucket | Trades | PnL | Win rate |", "|:--|--:|--:|--:|"])
        for bucket, row in buckets.items():
            lines.append(f"| `{bucket}` | {row['trade_count']} | {row['implementable_pnl']} | {row['win_rate']} |")
        lines.append("")
    lines.extend(
        [
            "## Greeks / OI Feasibility",
            "",
            f"- Status: `{greeks['status']}`",
            f"- Sampled quote files: {greeks['sampled_quote_files']}",
            f"- Sampled quote rows: {greeks['sampled_quote_rows']}",
            f"- Observed quote fields: {', '.join(f'`{field}`' for field in greeks['observed_quote_fields'])}",
            f"- Vendor Greek fields present: {', '.join(greeks['vendor_greek_fields_present']) or 'none'}",
            f"- Open-interest fields present: {', '.join(greeks['open_interest_fields_present']) or 'none'}",
            f"- Self-computed Greeks feasibility: `{greeks['self_computed_greeks_feasibility']}`",
            f"- OI/Greeks feasibility report: `{greeks.get('oi_greeks_feasibility_report') or 'none'}`",
            f"- OI/Greeks enrichment report: `{greeks.get('oi_greeks_enrichment_report') or 'none'}`",
            "",
            "## Note",
            "",
            result["note"],
        ]
    )
    return "\n".join(lines) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Risk-first sample, regime, and Greeks/OI data readiness.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--vix-path", type=Path, default=VIX_PATH)
    parser.add_argument("--macro-path", type=Path, default=MACRO_PATH)
    parser.add_argument("--json-output", type=Path, default=JSON_OUTPUT)
    parser.add_argument("--md-output", type=Path, default=MD_OUTPUT)
    args = parser.parse_args()

    result = audit_risk_first_data(args.summary_path, args.vix_path, args.macro_path)
    write_reports(result, args.json_output, args.md_output)
    print(json.dumps({"status": result["status"], "blockers": result["blockers"]}, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
