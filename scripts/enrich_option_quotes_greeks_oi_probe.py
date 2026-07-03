from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_greeks_oi_feasibility as greeks_audit
import probe_databento_opra_statistics as opra_probe


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = PROJECT_ROOT / "reports" / "baselines" / "subsystem_a_orb_baseline_summary.json"
OPRA_OI_REPORT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_opra_statistics_oi_download_probe_2024_01_03.json"
OUTPUT_JSONL = PROJECT_ROOT / "data" / "derived" / "spy_0dte" / "greeks_oi_probe" / "option_quote_enriched_2024-01-03.jsonl"
SUMMARY_OUTPUT = PROJECT_ROOT / "reports" / "greeks_oi_enrichment_probe_summary.json"
REPORT_OUTPUT = PROJECT_ROOT / "reports" / "greeks_oi_enrichment_probe_report.md"
TARGET_DATE = "2024-01-03"
ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")
MARKET_CLOSE = time(16, 0)
RISK_FREE_RATE = 0.05
DIVIDEND_YIELD = 0.0


def run_enrichment_probe(
    summary_path: Path = SUMMARY_PATH,
    opra_report_path: Path = OPRA_OI_REPORT_PATH,
    output_jsonl: Path = OUTPUT_JSONL,
    summary_output: Path = SUMMARY_OUTPUT,
    report_output: Path = REPORT_OUTPUT,
    target_date: str = TARGET_DATE,
) -> dict[str, Any]:
    summary = _load_json(summary_path)
    opra_report = _load_json(opra_report_path)
    quote_rows = greeks_audit._load_quote_rows_for_date(summary, target_date)
    bar_rows = greeks_audit._load_bar_rows_for_date(summary, target_date)
    oi_lookup = _load_oi_lookup(opra_report, {row["databento_symbol"] for row in quote_rows})

    enriched = [
        enrich_quote(row, bar_rows, oi_lookup)
        for row in quote_rows
    ]
    _write_jsonl(output_jsonl, enriched)
    result = summarize_enrichment(enriched, summary_path, opra_report_path, output_jsonl, target_date)
    write_reports(result, summary_output, report_output)
    return result


def enrich_quote(
    quote: dict[str, Any],
    bar_rows: list[dict[str, Any]],
    oi_lookup: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    record = dict(quote)
    record["record_type"] = "option_quote_greeks_oi_probe"
    record["schema_version"] = "greeks_oi_probe_v1"
    record["enrichment_policy"] = {
        "underlying_join": "latest SPY 1-minute bar with timestamp_et <= quote_timestamp_et",
        "open_interest_join": "latest exact-symbol OPRA OPEN_INTEREST with ts_recv <= quote_timestamp_utc",
        "pricing_model": "European Black-Scholes probe",
        "risk_free_rate": RISK_FREE_RATE,
        "dividend_yield": DIVIDEND_YIELD,
        "expiration_time_et": "16:00:00",
        "caveat": "SPY options are American-style; this is a research probe, not production-grade Greeks.",
    }

    bar = greeks_audit._previous_bar(quote["quote_timestamp_et"], bar_rows)
    if bar:
        record["underlying_price"] = float(bar["close"])
        record["underlying_price_timestamp_et"] = bar["timestamp_et"]
    else:
        record["underlying_join_status"] = "missing_prior_spy_bar"

    oi = latest_oi_before(oi_lookup.get(quote["databento_symbol"], []), greeks_audit._parse_dt(quote["quote_timestamp_et"]).astimezone(UTC))
    if oi:
        record["open_interest"] = int(oi["quantity"])
        record["open_interest_timestamp_utc"] = oi["ts_recv_utc"]
    else:
        record["open_interest_join_status"] = "missing_prior_exact_symbol_oi"

    greeks = compute_quote_greeks(record)
    record.update(greeks)
    return record


def compute_quote_greeks(record: dict[str, Any]) -> dict[str, Any]:
    if "underlying_price" not in record:
        return {"greeks_status": "blocked_missing_underlying_price"}
    mid = (float(record["bid"]) + float(record["ask"])) / 2.0
    quote_ts = greeks_audit._parse_dt(record["quote_timestamp_et"])
    expiry = datetime.combine(datetime.fromisoformat(record["expiration_date"]).date(), MARKET_CLOSE, tzinfo=ET)
    years_to_expiry = max((expiry - quote_ts).total_seconds() / (365.0 * 24.0 * 60.0 * 60.0), 1e-8)
    iv = greeks_audit.implied_volatility_bisection(
        target_price=mid,
        spot=float(record["underlying_price"]),
        strike=float(record["strike"]),
        years_to_expiry=years_to_expiry,
        rate=RISK_FREE_RATE,
        dividend_yield=DIVIDEND_YIELD,
        right=str(record["right"]),
    )
    if iv is None:
        return {
            "mid": round(mid, 6),
            "years_to_expiry": years_to_expiry,
            "greeks_status": "blocked_mid_outside_black_scholes_bracket",
        }
    greeks = greeks_audit.black_scholes_price_delta_gamma(
        spot=float(record["underlying_price"]),
        strike=float(record["strike"]),
        years_to_expiry=years_to_expiry,
        rate=RISK_FREE_RATE,
        dividend_yield=DIVIDEND_YIELD,
        volatility=iv,
        right=str(record["right"]),
    )
    return {
        "mid": round(mid, 6),
        "years_to_expiry": years_to_expiry,
        "implied_volatility": round(iv, 6),
        "delta": round(greeks["delta"], 6),
        "gamma": round(greeks["gamma"], 8),
        "greeks_status": "computed_with_caveats",
    }


def latest_oi_before(rows: list[dict[str, Any]], timestamp_utc: datetime) -> dict[str, Any] | None:
    candidates = [row for row in rows if row["ts_recv_dt"] <= timestamp_utc]
    return candidates[-1] if candidates else None


def summarize_enrichment(
    enriched: list[dict[str, Any]],
    summary_path: Path,
    opra_report_path: Path,
    output_jsonl: Path,
    target_date: str,
) -> dict[str, Any]:
    greeks_status_counts = _counts(row.get("greeks_status", "missing") for row in enriched)
    oi_join_count = sum(1 for row in enriched if "open_interest" in row)
    underlying_join_count = sum(1 for row in enriched if "underlying_price" in row)
    computed_rows = [row for row in enriched if row.get("greeks_status") == "computed_with_caveats"]
    return {
        "record_type": "greeks_oi_enrichment_probe_summary",
        "schema_version": "greeks_oi_enrichment_probe_v1",
        "status": "pass" if enriched and computed_rows and oi_join_count else "blocked",
        "target_date": target_date,
        "input_paths": {
            "baseline_summary": str(summary_path),
            "opra_oi_report": str(opra_report_path),
        },
        "output_jsonl": str(output_jsonl),
        "quote_count": len(enriched),
        "underlying_join_count": underlying_join_count,
        "open_interest_join_count": oi_join_count,
        "greeks_status_counts": greeks_status_counts,
        "computed_greeks_count": len(computed_rows),
        "sample_enriched_records": [_sample_record(row) for row in computed_rows[:3]],
        "strategy_use_status": "blocked_until_gamma_aggregation_policy_and_validation",
        "research_decision": (
            "Enrichment probe passed with caveats: target-date quotes can be enriched with prior SPY bar price, exact-symbol prior OPRA OI, and self-computed IV/Delta/Gamma. "
            "This is still not a strategy experiment and must not be used for production gamma/NOVI filtering until aggregation, validation, and report rules are defined."
        ),
    }


def write_reports(result: dict[str, Any], summary_output: Path = SUMMARY_OUTPUT, report_output: Path = REPORT_OUTPUT) -> None:
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_output.write_text(_render_report(result), encoding="utf-8")


def _load_oi_lookup(opra_report: dict[str, Any], target_symbols: set[str]) -> dict[str, list[dict[str, Any]]]:
    import databento as db  # type: ignore

    raw_path = Path(opra_report["download"]["raw_path"])
    frame = db.DBNStore.from_file(raw_path).to_df()
    oi_rows = opra_probe._rows_matching_stat_type(frame, "OPEN_INTEREST")
    if len(oi_rows) == 0:
        return {}
    subset = oi_rows[oi_rows["symbol"].astype(str).str.strip().isin(target_symbols)]
    lookup: dict[str, list[dict[str, Any]]] = {}
    for row in subset.sort_index().itertuples():
        symbol = str(row.symbol).strip()
        ts_recv = row.Index.to_pydatetime() if hasattr(row.Index, "to_pydatetime") else row.Index
        if ts_recv.tzinfo is None:
            ts_recv = ts_recv.replace(tzinfo=UTC)
        lookup.setdefault(symbol, []).append(
            {
                "ts_recv_dt": ts_recv.astimezone(UTC),
                "ts_recv_utc": ts_recv.astimezone(UTC).isoformat(),
                "quantity": int(row.quantity),
            }
        )
    return lookup


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _sample_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "quote_timestamp_et": row["quote_timestamp_et"],
        "databento_symbol": row["databento_symbol"],
        "underlying_price": row.get("underlying_price"),
        "open_interest": row.get("open_interest"),
        "implied_volatility": row.get("implied_volatility"),
        "delta": row.get("delta"),
        "gamma": row.get("gamma"),
        "greeks_status": row.get("greeks_status"),
    }


def _render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Greeks/OI Enrichment Probe",
        "",
        f"- Status: `{result['status']}`",
        f"- Target date: `{result['target_date']}`",
        f"- Output JSONL: `{result['output_jsonl']}`",
        f"- Quote rows: {result['quote_count']}",
        f"- Underlying joined: {result['underlying_join_count']}",
        f"- Open interest joined: {result['open_interest_join_count']}",
        f"- Computed Greeks: {result['computed_greeks_count']}",
        f"- Strategy use status: `{result['strategy_use_status']}`",
        "",
        "## Greek Status Counts",
        "",
        "| Status | Count |",
        "|:--|--:|",
    ]
    for status, count in result["greeks_status_counts"].items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "## Sample Records",
            "",
            "```json",
            json.dumps(result["sample_enriched_records"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Decision",
            "",
            result["research_decision"],
            "",
            "This is a data enrichment probe, not a completed strategy experiment. Do not write a research log for it.",
            "",
        ]
    )
    return "\n".join(lines)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich one target-date quote set with timestamp-safe OI, underlying price, and probe Greeks.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--opra-report-path", type=Path, default=OPRA_OI_REPORT_PATH)
    parser.add_argument("--output-jsonl", type=Path, default=OUTPUT_JSONL)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=REPORT_OUTPUT)
    parser.add_argument("--target-date", default=TARGET_DATE)
    args = parser.parse_args()

    result = run_enrichment_probe(
        summary_path=args.summary_path,
        opra_report_path=args.opra_report_path,
        output_jsonl=args.output_jsonl,
        summary_output=args.summary_output,
        report_output=args.report_output,
        target_date=args.target_date,
    )
    print(json.dumps({"status": result["status"], "quote_count": result["quote_count"], "computed_greeks_count": result["computed_greeks_count"]}, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
