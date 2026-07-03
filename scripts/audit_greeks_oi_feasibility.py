from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_databento_opra_statistics as opra_probe


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = PROJECT_ROOT / "reports" / "baselines" / "subsystem_a_orb_baseline_summary.json"
OPRA_OI_REPORT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_opra_statistics_oi_download_probe_2024_01_03.json"
JSON_OUTPUT = PROJECT_ROOT / "reports" / "greeks_oi_feasibility_audit.json"
MD_OUTPUT = PROJECT_ROOT / "reports" / "greeks_oi_feasibility_audit.md"
ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")
TARGET_DATE = "2024-01-03"
MARKET_CLOSE = time(16, 0)


def audit_greeks_oi_feasibility(
    summary_path: Path = SUMMARY_PATH,
    opra_report_path: Path = OPRA_OI_REPORT_PATH,
) -> dict[str, Any]:
    summary = _load_json(summary_path)
    opra_report = _load_json(opra_report_path)
    quote_rows = _load_quote_rows_for_date(summary, TARGET_DATE)
    bar_rows = _load_bar_rows_for_date(summary, TARGET_DATE)

    quote_field_audit = _quote_field_audit(quote_rows)
    underlying_join = _underlying_join_audit(quote_rows, bar_rows)
    oi_mapping = _opra_oi_mapping_audit(opra_report, quote_rows)
    greek_probe = _greek_calculation_probe(quote_rows, bar_rows)

    blockers = []
    if quote_field_audit["missing_required_fields"]:
        blockers.append("missing_required_quote_fields")
    if underlying_join["status"] != "pass":
        blockers.append("requires_underlying_join")
    if oi_mapping["status"] != "pass":
        blockers.append("requires_oi_timestamp_symbol_mapping")
    if greek_probe["status"] != "pass_with_caveats":
        blockers.append("requires_iv_delta_gamma_probe")

    return {
        "record_type": "greeks_oi_feasibility_audit",
        "schema_version": "greeks_oi_feasibility_v1",
        "target_date": TARGET_DATE,
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "strategy_use_status": "blocked_until_normalized_quote_enrichment_and_gamma_aggregation_policy",
        "input_paths": {
            "baseline_summary": str(summary_path),
            "opra_oi_report": str(opra_report_path),
        },
        "quote_field_audit": quote_field_audit,
        "underlying_join_audit": underlying_join,
        "opra_oi_mapping_audit": oi_mapping,
        "greek_calculation_probe": greek_probe,
        "research_decision": _research_decision(blockers),
    }


def write_reports(result: dict[str, Any], json_output: Path = JSON_OUTPUT, md_output: Path = MD_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_output.write_text(_render_markdown(result), encoding="utf-8")


def parse_databento_option_symbol(symbol: str) -> dict[str, Any]:
    compact = " ".join(symbol.split())
    parts = compact.split(" ")
    if len(parts) != 2 or len(parts[1]) != 15:
        raise ValueError(f"unsupported Databento option symbol: {symbol}")
    root = parts[0]
    encoded = parts[1]
    yymmdd = encoded[:6]
    cp = encoded[6]
    strike = int(encoded[7:]) / 1000.0
    if cp not in {"C", "P"}:
        raise ValueError(f"unsupported option right in symbol: {symbol}")
    return {
        "underlying": root,
        "expiration_date": f"20{yymmdd[:2]}-{yymmdd[2:4]}-{yymmdd[4:6]}",
        "right": "call" if cp == "C" else "put",
        "strike": strike,
    }


def black_scholes_price_delta_gamma(
    *,
    spot: float,
    strike: float,
    years_to_expiry: float,
    rate: float,
    dividend_yield: float,
    volatility: float,
    right: str,
) -> dict[str, float]:
    if spot <= 0 or strike <= 0 or years_to_expiry <= 0 or volatility <= 0:
        raise ValueError("spot, strike, years_to_expiry, and volatility must be positive")
    sqrt_t = math.sqrt(years_to_expiry)
    d1 = (math.log(spot / strike) + (rate - dividend_yield + 0.5 * volatility * volatility) * years_to_expiry) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t
    df_r = math.exp(-rate * years_to_expiry)
    df_q = math.exp(-dividend_yield * years_to_expiry)
    if right == "call":
        price = spot * df_q * _normal_cdf(d1) - strike * df_r * _normal_cdf(d2)
        delta = df_q * _normal_cdf(d1)
    elif right == "put":
        price = strike * df_r * _normal_cdf(-d2) - spot * df_q * _normal_cdf(-d1)
        delta = -df_q * _normal_cdf(-d1)
    else:
        raise ValueError(f"unsupported right: {right}")
    gamma = df_q * _normal_pdf(d1) / (spot * volatility * sqrt_t)
    return {"price": price, "delta": delta, "gamma": gamma}


def implied_volatility_bisection(
    *,
    target_price: float,
    spot: float,
    strike: float,
    years_to_expiry: float,
    rate: float,
    dividend_yield: float,
    right: str,
    low: float = 0.0001,
    high: float = 5.0,
    tolerance: float = 1e-5,
    max_iterations: int = 100,
) -> float | None:
    low_price = black_scholes_price_delta_gamma(
        spot=spot,
        strike=strike,
        years_to_expiry=years_to_expiry,
        rate=rate,
        dividend_yield=dividend_yield,
        volatility=low,
        right=right,
    )["price"]
    high_price = black_scholes_price_delta_gamma(
        spot=spot,
        strike=strike,
        years_to_expiry=years_to_expiry,
        rate=rate,
        dividend_yield=dividend_yield,
        volatility=high,
        right=right,
    )["price"]
    if target_price < low_price - tolerance or target_price > high_price + tolerance:
        return None
    for _ in range(max_iterations):
        mid = (low + high) / 2.0
        mid_price = black_scholes_price_delta_gamma(
            spot=spot,
            strike=strike,
            years_to_expiry=years_to_expiry,
            rate=rate,
            dividend_yield=dividend_yield,
            volatility=mid,
            right=right,
        )["price"]
        if abs(mid_price - target_price) <= tolerance:
            return mid
        if mid_price < target_price:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def _quote_field_audit(quote_rows: list[dict[str, Any]]) -> dict[str, Any]:
    required = {"bid", "ask", "strike", "right", "expiration_date", "quote_timestamp_et", "databento_symbol"}
    observed = set()
    for row in quote_rows[:500]:
        observed.update(row)
    return {
        "status": "pass" if required <= observed else "blocked",
        "quote_count_for_target_date": len(quote_rows),
        "observed_fields": sorted(observed),
        "required_fields": sorted(required),
        "missing_required_fields": sorted(required - observed),
    }


def _underlying_join_audit(quote_rows: list[dict[str, Any]], bar_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not quote_rows or not bar_rows:
        return {"status": "blocked", "matched_sample_quotes": 0, "bar_count_for_target_date": len(bar_rows)}
    matched = 0
    for quote in quote_rows[:100]:
        if _previous_bar(quote["quote_timestamp_et"], bar_rows):
            matched += 1
    return {
        "status": "pass" if matched > 0 else "blocked",
        "matched_sample_quotes": matched,
        "sample_quotes_checked": min(len(quote_rows), 100),
        "bar_count_for_target_date": len(bar_rows),
        "join_rule": "Use the latest SPY 1-minute bar with timestamp_et <= option quote timestamp_et.",
    }


def _opra_oi_mapping_audit(opra_report: dict[str, Any], quote_rows: list[dict[str, Any]]) -> dict[str, Any]:
    raw_path = Path(opra_report["download"]["raw_path"])
    if not raw_path.exists() or not quote_rows:
        return {"status": "blocked", "reason": "missing raw OPRA statistics file or target-date quote rows"}

    import databento as db  # type: ignore

    frame = db.DBNStore.from_file(raw_path).to_df()
    oi_rows = opra_probe._rows_matching_stat_type(frame, "OPEN_INTEREST")
    quote_symbols = sorted({row["databento_symbol"] for row in quote_rows})
    sample_symbols = quote_symbols[:50]
    oi_symbols = set(str(value).strip() for value in oi_rows["symbol"].dropna().unique()) if len(oi_rows) else set()
    symbol_matches = [symbol for symbol in sample_symbols if symbol in oi_symbols]

    first_quote_ts_utc = _parse_dt(min(row["quote_timestamp_et"] for row in quote_rows)).astimezone(UTC)
    available_before_decision = 0
    latest_by_symbol: dict[str, dict[str, Any]] = {}
    if len(oi_rows) and symbol_matches:
        subset = oi_rows[oi_rows["symbol"].astype(str).str.strip().isin(symbol_matches)]
        subset = subset[subset.index <= first_quote_ts_utc]
        available_before_decision = int(len(subset))
        for symbol in symbol_matches:
            rows = subset[subset["symbol"].astype(str).str.strip() == symbol]
            if len(rows) == 0:
                continue
            latest = rows.sort_index().iloc[-1]
            latest_by_symbol[symbol] = {
                "ts_recv_utc": str(rows.sort_index().index[-1]),
                "quantity": int(latest["quantity"]),
            }

    return {
        "status": "pass" if symbol_matches and latest_by_symbol else "blocked",
        "raw_path": str(raw_path),
        "reported_open_interest_records": opra_report["inspection"]["open_interest_record_count"],
        "loaded_open_interest_records": int(len(oi_rows)),
        "first_quote_timestamp_et": min(row["quote_timestamp_et"] for row in quote_rows),
        "first_quote_timestamp_utc": first_quote_ts_utc.isoformat(),
        "sample_quote_symbols_checked": len(sample_symbols),
        "sample_symbol_match_count": len(symbol_matches),
        "sample_symbol_matches": symbol_matches[:10],
        "oi_records_available_before_first_quote_for_sample_symbols": available_before_decision,
        "latest_oi_before_first_quote_examples": latest_by_symbol,
        "mapping_rule": "For a decision timestamp, use only OPEN_INTEREST records for the exact Databento option symbol with ts_recv <= decision timestamp UTC. If no such record exists, treat OI as missing for that decision.",
    }


def _greek_calculation_probe(quote_rows: list[dict[str, Any]], bar_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not quote_rows or not bar_rows:
        return {"status": "blocked", "reason": "missing quote or bar rows"}
    quote = _select_atm_like_quote(quote_rows, bar_rows)
    if quote is None:
        return {"status": "blocked", "reason": "could not select quote with underlying bar"}
    bar = _previous_bar(quote["quote_timestamp_et"], bar_rows)
    if not bar:
        return {"status": "blocked", "reason": "could not join underlying bar"}

    spot = float(bar["close"])
    mid = (float(quote["bid"]) + float(quote["ask"])) / 2.0
    expiry = datetime.combine(datetime.fromisoformat(quote["expiration_date"]).date(), MARKET_CLOSE, tzinfo=ET)
    quote_ts = _parse_dt(quote["quote_timestamp_et"])
    years_to_expiry = max((expiry - quote_ts).total_seconds() / (365.0 * 24.0 * 60.0 * 60.0), 1e-8)
    rate = 0.05
    dividend_yield = 0.0
    iv = implied_volatility_bisection(
        target_price=mid,
        spot=spot,
        strike=float(quote["strike"]),
        years_to_expiry=years_to_expiry,
        rate=rate,
        dividend_yield=dividend_yield,
        right=str(quote["right"]),
    )
    if iv is None:
        return {
            "status": "blocked",
            "reason": "sample quote mid price is outside Black-Scholes bracket",
            "quote": _public_quote_sample(quote),
            "underlying_price": spot,
            "mid_price": round(mid, 6),
        }
    greeks = black_scholes_price_delta_gamma(
        spot=spot,
        strike=float(quote["strike"]),
        years_to_expiry=years_to_expiry,
        rate=rate,
        dividend_yield=dividend_yield,
        volatility=iv,
        right=str(quote["right"]),
    )
    return {
        "status": "pass_with_caveats",
        "quote": _public_quote_sample(quote),
        "underlying_joined_from_bar": {
            "timestamp_et": bar["timestamp_et"],
            "close": spot,
        },
        "mid_price": round(mid, 6),
        "years_to_expiry": years_to_expiry,
        "assumptions": {
            "pricing_model": "European Black-Scholes feasibility probe",
            "risk_free_rate": rate,
            "dividend_yield": dividend_yield,
            "expiration_time_et": "16:00:00",
            "caveat": "SPY options are American-style and can be affected by dividends/early exercise; this probe is only to prove field feasibility, not production-grade Greeks.",
        },
        "implied_volatility": round(iv, 6),
        "delta": round(greeks["delta"], 6),
        "gamma": round(greeks["gamma"], 8),
    }


def _select_atm_like_quote(quote_rows: list[dict[str, Any]], bar_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = []
    for quote in quote_rows[:5000]:
        bar = _previous_bar(quote["quote_timestamp_et"], bar_rows)
        if not bar:
            continue
        mid = (float(quote["bid"]) + float(quote["ask"])) / 2.0
        if mid <= 0:
            continue
        distance = abs(float(quote["strike"]) - float(bar["close"]))
        scored.append((distance, quote))
    return sorted(scored, key=lambda item: item[0])[0][1] if scored else None


def _load_quote_rows_for_date(summary: dict[str, Any], target_date: str) -> list[dict[str, Any]]:
    rows = []
    for dataset in summary.get("datasets", []):
        if not _dataset_covers_date(dataset, target_date):
            continue
        path = Path(dataset.get("quote_path", ""))
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("expiration_date") == target_date:
                    rows.append(row)
    return sorted(rows, key=lambda row: (row["quote_timestamp_et"], row["databento_symbol"]))


def _load_bar_rows_for_date(summary: dict[str, Any], target_date: str) -> list[dict[str, Any]]:
    rows = []
    seen_paths = set()
    for dataset in summary.get("datasets", []):
        if not _dataset_covers_date(dataset, target_date):
            continue
        path = Path(dataset.get("bar_path", ""))
        if path in seen_paths or not path.exists():
            continue
        seen_paths.add(path)
        with path.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if str(row.get("timestamp_et", "")).startswith(target_date):
                    rows.append(row)
    return sorted(rows, key=lambda row: row["timestamp_et"])


def _dataset_covers_date(dataset: dict[str, Any], target_date: str) -> bool:
    start = dataset.get("coverage_start")
    end = dataset.get("coverage_end")
    if start and end:
        return str(start) <= target_date <= str(end)
    label = str(dataset.get("label", ""))
    return target_date[:7].replace("-", "_") in label or target_date[:4] in label


def _previous_bar(timestamp_et: str, bar_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [row for row in bar_rows if row["timestamp_et"] <= timestamp_et]
    return candidates[-1] if candidates else None


def _parse_dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ET)
    return parsed


def _public_quote_sample(quote: dict[str, Any]) -> dict[str, Any]:
    return {
        "quote_timestamp_et": quote["quote_timestamp_et"],
        "databento_symbol": quote["databento_symbol"],
        "right": quote["right"],
        "strike": quote["strike"],
        "bid": quote["bid"],
        "ask": quote["ask"],
    }


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _normal_pdf(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def _research_decision(blockers: list[str]) -> str:
    if blockers:
        return "Blocked: current artifacts do not yet prove an OI/Greeks path for gamma-family research."
    return (
        "Feasible with caveats: Databento OPRA statistics can provide exact-symbol reference OI before the target decision timestamp, "
        "and current bid/ask quotes plus SPY bars can support a self-computed IV/Delta/Gamma probe. This is not strategy-ready until "
        "normalized quote enrichment, rate/dividend policy, American-option caveat handling, and gamma aggregation rules are implemented."
    )


def _render_markdown(result: dict[str, Any]) -> str:
    oi = result["opra_oi_mapping_audit"]
    greek = result["greek_calculation_probe"]
    fields = result["quote_field_audit"]
    underlying = result["underlying_join_audit"]
    blockers = result["blockers"] or ["None"]
    lines = [
        "# Greeks/OI Feasibility Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Strategy use status: `{result['strategy_use_status']}`",
        f"- Target date: `{result['target_date']}`",
        f"- Research decision: {result['research_decision']}",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- `{blocker}`" for blocker in blockers)
    lines.extend(
        [
            "",
            "## Quote Fields",
            "",
            f"- Quote count: {fields['quote_count_for_target_date']}",
            f"- Missing required fields: {', '.join(fields['missing_required_fields']) or 'none'}",
            "",
            "## Underlying Join",
            "",
            f"- Status: `{underlying['status']}`",
            f"- Sample matched: {underlying['matched_sample_quotes']} / {underlying.get('sample_quotes_checked', 0)}",
            f"- Rule: {underlying.get('join_rule', '-')}",
            "",
            "## OPRA OI Mapping",
            "",
            f"- Status: `{oi['status']}`",
            f"- Loaded OI records: {oi.get('loaded_open_interest_records')}",
            f"- First quote timestamp UTC: `{oi.get('first_quote_timestamp_utc')}`",
            f"- Sample symbol matches: {oi.get('sample_symbol_match_count')} / {oi.get('sample_quote_symbols_checked')}",
            f"- OI records before first quote for matched sample: {oi.get('oi_records_available_before_first_quote_for_sample_symbols')}",
            f"- Mapping rule: {oi.get('mapping_rule')}",
            "",
            "## IV/Delta/Gamma Probe",
            "",
            f"- Status: `{greek['status']}`",
            f"- Implied volatility: `{greek.get('implied_volatility')}`",
            f"- Delta: `{greek.get('delta')}`",
            f"- Gamma: `{greek.get('gamma')}`",
            f"- Caveat: `{(greek.get('assumptions') or {}).get('caveat', greek.get('reason', '-'))}`",
            "",
            "## Note",
            "",
            "This is a data-source and model-input feasibility audit, not a completed strategy experiment. Do not write a research log for it.",
            "",
        ]
    )
    return "\n".join(lines)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit whether OPRA OI plus self-computed IV/Greeks can support gamma-family research.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--opra-report-path", type=Path, default=OPRA_OI_REPORT_PATH)
    parser.add_argument("--json-output", type=Path, default=JSON_OUTPUT)
    parser.add_argument("--md-output", type=Path, default=MD_OUTPUT)
    args = parser.parse_args()

    result = audit_greeks_oi_feasibility(args.summary_path, args.opra_report_path)
    write_reports(result, args.json_output, args.md_output)
    print(json.dumps({"status": result["status"], "blockers": result["blockers"]}, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
