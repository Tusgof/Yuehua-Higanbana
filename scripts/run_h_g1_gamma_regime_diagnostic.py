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
import audit_greeks_oi_feasibility as greeks_audit
import enrich_option_quotes_greeks_oi_probe as enricher
import probe_databento_opra_statistics as opra_probe
import run_gamma_aggregation_diagnostic as gamma_v1


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration.json"
BASELINE_SUMMARY_PATH = PROJECT_ROOT / "reports" / "baselines" / "subsystem_a_orb_baseline_summary.json"
OI_DOWNLOAD_RESULT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "h_g1_gamma_oi_download_result.json"
EXISTING_OI_REPORT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_opra_statistics_oi_download_probe_2024_01_03.json"
OUTPUT_JSONL = PROJECT_ROOT / "data" / "derived" / "spy_0dte" / "h_g1_gamma_regime" / "option_quote_enriched_12_date_snapshot.jsonl"
ENRICHMENT_SUMMARY_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_enrichment_summary.json"
DIAGNOSTIC_SUMMARY_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_diagnostic_summary.json"
DIAGNOSTIC_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_diagnostic_report.md"
SIDE_AWARE_POLICY_ADOPTION_PATH = PROJECT_ROOT / "experiments" / "h_g1_side_aware_bucket_policy_adoption.json"
ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")
DECISION_TIME = time(9, 35)
FORCED_CLOSE_TIME = time(15, 45)
REQUIRED_BUCKETS = ("otm_put", "atm", "otm_call")
MONEYNESS_ONLY_POLICY_ID = "GAMMA_AGGREGATION_VALIDATION_POLICY.md v2"
SIDE_AWARE_POLICY_ID = "h_g1_required_bucket_policy_v3_side_aware"


def run_h_g1_diagnostic(
    manifest_path: Path = MANIFEST_PATH,
    baseline_summary_path: Path = BASELINE_SUMMARY_PATH,
    oi_download_result_path: Path = OI_DOWNLOAD_RESULT_PATH,
    additional_oi_download_result_paths: list[Path] | None = None,
    existing_oi_report_path: Path = EXISTING_OI_REPORT_PATH,
    output_jsonl: Path = OUTPUT_JSONL,
    enrichment_summary_output: Path = ENRICHMENT_SUMMARY_OUTPUT,
    diagnostic_summary_output: Path = DIAGNOSTIC_SUMMARY_OUTPUT,
    diagnostic_report_output: Path = DIAGNOSTIC_REPORT_OUTPUT,
    research_log_slug: str = "higanbana-gamma-oi-regime-diagnostic",
    research_log_path: str = "research_log/013-higanbana-gamma-oi-regime-diagnostic.md",
    policy_adoption_path: Path | None = None,
) -> dict[str, Any]:
    manifest = _load_json(manifest_path)
    policy_context = _policy_context(policy_adoption_path)
    baseline_summary = _load_json(baseline_summary_path)
    oi_paths = _oi_raw_paths_by_date(oi_download_result_path, existing_oi_report_path, additional_oi_download_result_paths)
    date_entries = manifest["selected_dates"]
    enriched_rows: list[dict[str, Any]] = []
    enrichment_dates = []

    for entry in date_entries:
        date = entry["date"]
        quote_rows = _decision_snapshot_quotes(greeks_audit._load_quote_rows_for_date(baseline_summary, date))
        bar_rows = greeks_audit._load_bar_rows_for_date(baseline_summary, date)
        oi_path = oi_paths.get(date)
        oi_lookup = _load_oi_lookup(oi_path, {row["databento_symbol"] for row in quote_rows}) if oi_path else {}
        date_rows = [enricher.enrich_quote(row, bar_rows, oi_lookup) for row in quote_rows]
        for row in date_rows:
            row["schema_version"] = "h_g1_gamma_regime_enriched_snapshot_v1"
            row["hypothesis_id"] = "H-G1"
            row["decision_snapshot_policy"] = {
                "selected_time_et": DECISION_TIME.isoformat(),
                "fallback": "first available quote timestamp for the date when 09:35 ET is absent",
                "reason": "H-G1 policy validates a decision-time gamma proxy, not every intraday quote minute.",
            }
            row["manifest_regime"] = {
                "split": entry["split"],
                "volatility_bucket": entry["volatility_bucket"],
                "high_importance_macro": entry["high_importance_macro"],
                "trend_regime": entry["trend_regime"],
            }
        enriched_rows.extend(date_rows)
        enrichment_dates.append(_date_enrichment_summary(date, entry, quote_rows, bar_rows, oi_path, date_rows))

    _write_jsonl(output_jsonl, enriched_rows)
    enrichment_summary = _enrichment_summary(manifest_path, output_jsonl, enrichment_dates, enriched_rows)
    _write_json(enrichment_summary_output, enrichment_summary)

    diagnostic = aggregate_h_g1_diagnostic(
        enriched_rows,
        manifest,
        output_jsonl,
        enrichment_summary_output,
        research_log_slug=research_log_slug,
        research_log_path=research_log_path,
        policy_context=policy_context,
    )
    _write_json(diagnostic_summary_output, diagnostic)
    diagnostic_report_output.parent.mkdir(parents=True, exist_ok=True)
    diagnostic_report_output.write_text(_render_markdown(diagnostic), encoding="utf-8")
    return diagnostic


def aggregate_h_g1_diagnostic(
    rows: list[dict[str, Any]],
    manifest: dict[str, Any],
    input_jsonl: Path,
    enrichment_summary_path: Path,
    research_log_slug: str = "higanbana-gamma-oi-regime-diagnostic",
    research_log_path: str = "research_log/013-higanbana-gamma-oi-regime-diagnostic.md",
    policy_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy_context = policy_context or _policy_context(None)
    rows_by_date = _rows_by_date(rows)
    per_date = {
        date: _per_date_diagnostic(date, date_rows, policy_context)
        for date, date_rows in sorted(rows_by_date.items())
    }
    coverage = _coverage_gate_v2(rows, per_date, policy_context)
    timestamp = gamma_v1._timestamp_discipline(rows)
    stability = _stability_gate_v2(manifest, rows_by_date)
    economic = _economic_sign_check(rows_by_date)
    search_log = {
        "status": "pass",
        "reason": "No gamma threshold, quartile, or best bucket was selected in this diagnostic.",
    }
    gates = {
        "coverage": coverage,
        "timestamp_discipline": timestamp,
        "stability": stability,
        "economic_sign": economic,
        "search_log": search_log,
    }
    blockers = _gate_blockers(gates)
    status = "blocked" if blockers else "pass_diagnostic_only"
    return {
        "record_type": "h_g1_gamma_regime_diagnostic",
        "schema_version": "h_g1_gamma_regime_diagnostic_v1",
        "hypothesis_id": "H-G1",
        "evidence_tier": "E1",
        "research_log_required": True,
        "research_log_slug": research_log_slug,
        "research_log_path": research_log_path,
        "status": status,
        "conclusion": "ยังสรุปไม่ได้" if blockers else "ผ่าน",
        "conclusion_reason": _conclusion_reason(blockers),
        "input_jsonl": str(input_jsonl),
        "enrichment_summary": str(enrichment_summary_path),
        "policy_version": policy_context["policy_id"],
        "required_bucket_policy": policy_context,
        "network_used": False,
        "paid_data_used": False,
        "strategy_pnl_used": False,
        "strategy_use_allowed": False,
        "decision_time_et": DECISION_TIME.isoformat(),
        "date_count": len(rows_by_date),
        "quote_count": len(rows),
        "computed_greeks_count": sum(1 for row in rows if row.get("greeks_status") == "computed_with_caveats"),
        "per_date": per_date,
        "validation_gates": gates,
        "blockers": blockers,
        "strategy_use_status": "diagnostic_only_blocked_by_policy_gates" if blockers else "diagnostic_only_not_strategy_ready",
        "forbidden_claims_preserved": policy_context["forbidden_claims"],
        "tier_blockers": [
            "E1 diagnostic only",
            "H-G1 is a data-validity proxy test, not a strategy acceptance test",
            "No MinTRL/PSR acceptance evidence for a trading rule",
        ],
        "research_decision": _research_decision(blockers),
    }


def _decision_snapshot_quotes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    target_suffix = f"T{DECISION_TIME.isoformat()}"
    selected = [row for row in rows if target_suffix in row.get("quote_timestamp_et", "")]
    if selected:
        return selected
    first_ts = min(row["quote_timestamp_et"] for row in rows)
    return [row for row in rows if row["quote_timestamp_et"] == first_ts]


def _load_oi_lookup(raw_path: Path | None, target_symbols: set[str]) -> dict[str, list[dict[str, Any]]]:
    if not raw_path or not raw_path.exists() or not target_symbols:
        return {}
    import databento as db  # type: ignore

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


def _per_date_diagnostic(date: str, rows: list[dict[str, Any]], policy_context: dict[str, Any] | None = None) -> dict[str, Any]:
    policy_context = policy_context or _policy_context(None)
    computed = [row for row in rows if row.get("greeks_status") == "computed_with_caveats"]
    bucket_stats = _bucket_stats(rows)
    required_bucket_stats = _required_bucket_stats(rows, policy_context)
    aggregate = _aggregate_gamma(computed)
    return {
        "quote_count": len(rows),
        "computed_greeks_count": len(computed),
        "underlying_join_count": sum(1 for row in rows if row.get("underlying_price") is not None),
        "open_interest_join_count": sum(1 for row in rows if row.get("open_interest") is not None),
        "computed_greeks_rate": _safe_rate(len(computed), len(rows)),
        "bucket_stats": bucket_stats,
        "required_bucket_policy_id": policy_context["policy_id"],
        "required_bucket_stats": required_bucket_stats,
        "reported_opposite_right_itm_rows": _opposite_right_counts(rows),
        "required_bucket_blockers": _required_bucket_blockers(required_bucket_stats, policy_context),
        "gamma_aggregate": aggregate,
        "realized_volatility": _realized_volatility_for_date(date),
    }


def _coverage_gate_v2(
    rows: list[dict[str, Any]],
    per_date: dict[str, dict[str, Any]],
    policy_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy_context = policy_context or _policy_context(None)
    quote_count = len(rows)
    computed_count = sum(item["computed_greeks_count"] for item in per_date.values())
    underlying_count = sum(item["underlying_join_count"] for item in per_date.values())
    oi_count = sum(item["open_interest_join_count"] for item in per_date.values())
    raw = gamma_v1._coverage_gate(quote_count, underlying_count, oi_count, computed_count)
    required_bucket_failures = {
        date: item["required_bucket_blockers"]
        for date, item in per_date.items()
        if item["required_bucket_blockers"]
    }
    required_bucket_stats = _required_bucket_stats(rows, policy_context)
    computed_notional = sum(item["computed_oi_notional_sum"] for item in required_bucket_stats.values())
    total_required_notional = sum(item["oi_notional_sum"] for item in required_bucket_stats.values())
    retained_gamma_sum = sum(item["observable_abs_gamma_proxy_sum"] for item in required_bucket_stats.values())
    bucket_weighted = {
        "status": "pass" if not required_bucket_failures and _safe_rate(computed_notional, total_required_notional) >= 0.80 else "blocked",
        "required_buckets": list(REQUIRED_BUCKETS),
        "policy_id": policy_context["policy_id"],
        "required_bucket_failures": required_bucket_failures,
        "computed_required_bucket_oi_notional_share": round(_safe_rate(computed_notional, total_required_notional), 6),
        "retained_abs_gamma_proxy_share": 1.0 if retained_gamma_sum > 0 else 0.0,
        "reported_opposite_right_itm_rows": _opposite_right_counts(rows),
        "note": "OI-notional share is reported because gamma exposure is not observable for rows where IV/Gamma cannot be computed.",
    }
    blockers = []
    if raw["status"] != "pass":
        blockers.append("raw_row_coverage_gate_failed")
    if bucket_weighted["status"] != "pass":
        blockers.append("bucket_weighted_coverage_gate_failed")
    return {
        "status": "pass" if not blockers else "blocked",
        "raw_row_coverage": raw,
        "bucket_weighted_coverage": bucket_weighted,
        "blockers": blockers,
    }


def _bucket_stats(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for row in rows:
        bucket = gamma_v1._row_bucket(row)
        item = stats.setdefault(
            bucket,
            {
                "row_count": 0,
                "computed_count": 0,
                "blocked_count": 0,
                "oi_notional_sum": 0.0,
                "computed_oi_notional_sum": 0.0,
                "observable_abs_gamma_proxy_sum": 0.0,
            },
        )
        item["row_count"] += 1
        notional = _oi_notional(row)
        item["oi_notional_sum"] += notional
        if row.get("greeks_status") == "computed_with_caveats":
            item["computed_count"] += 1
            item["computed_oi_notional_sum"] += notional
            if _has_gamma_inputs(row):
                item["observable_abs_gamma_proxy_sum"] += abs(gamma_v1.local_gamma_exposure(row))
        else:
            item["blocked_count"] += 1
    total_notional = sum(item["oi_notional_sum"] for item in stats.values())
    for item in stats.values():
        item["computed_rate"] = round(_safe_rate(item["computed_count"], item["row_count"]), 6)
        item["oi_notional_share"] = round(_safe_rate(item["oi_notional_sum"], total_notional), 6)
        item["computed_oi_notional_share"] = round(_safe_rate(item["computed_oi_notional_sum"], item["oi_notional_sum"]), 6)
        item["retained_abs_gamma_proxy_share"] = 1.0 if item["observable_abs_gamma_proxy_sum"] > 0 else 0.0
        item["oi_notional_sum"] = round(item["oi_notional_sum"], 6)
        item["computed_oi_notional_sum"] = round(item["computed_oi_notional_sum"], 6)
        item["observable_abs_gamma_proxy_sum"] = round(item["observable_abs_gamma_proxy_sum"], 6)
    return dict(sorted(stats.items()))


def _required_bucket_stats(rows: list[dict[str, Any]], policy_context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if policy_context["policy_id"] != SIDE_AWARE_POLICY_ID:
        return {bucket: _bucket_stats([row for row in rows if gamma_v1._row_bucket(row) == bucket]).get(bucket, _empty_bucket_stats()) for bucket in REQUIRED_BUCKETS}
    bucket_rows = {
        "otm_put": [
            row for row in rows
            if gamma_v1._row_bucket(row) == "otm_put" and str(row.get("right", "")).lower() == "put"
        ],
        "atm": [row for row in rows if gamma_v1._row_bucket(row) == "atm"],
        "otm_call": [
            row for row in rows
            if gamma_v1._row_bucket(row) == "otm_call" and str(row.get("right", "")).lower() == "call"
        ],
    }
    return {bucket: _bucket_stats(items).get(bucket, _empty_bucket_stats()) for bucket, items in bucket_rows.items()}


def _empty_bucket_stats() -> dict[str, Any]:
    return {
        "row_count": 0,
        "computed_count": 0,
        "blocked_count": 0,
        "oi_notional_sum": 0.0,
        "computed_oi_notional_sum": 0.0,
        "observable_abs_gamma_proxy_sum": 0.0,
        "computed_rate": 0.0,
        "oi_notional_share": 0.0,
        "computed_oi_notional_share": 0.0,
        "retained_abs_gamma_proxy_share": 0.0,
    }


def _required_bucket_blockers(bucket_stats: dict[str, dict[str, Any]], policy_context: dict[str, Any] | None = None) -> list[str]:
    policy_context = policy_context or _policy_context(None)
    row_floor = policy_context["thresholds"]["computed_row_rate_floor"]
    notional_floor = policy_context["thresholds"]["computed_oi_notional_share_floor"]
    gamma_floor = policy_context["thresholds"]["retained_abs_gamma_proxy_share_floor"]
    blockers = []
    for bucket in REQUIRED_BUCKETS:
        item = bucket_stats.get(bucket)
        if not item:
            blockers.append(f"{bucket}_missing")
            continue
        if item.get("row_count", 1) == 0:
            blockers.append(f"{bucket}_missing")
        if item["computed_rate"] < row_floor:
            suffix = "side_aware_computed_rate_below_floor" if policy_context["policy_id"] == SIDE_AWARE_POLICY_ID else "computed_rate_below_60pct"
            blockers.append(f"{bucket}_{suffix}")
        if policy_context["policy_id"] == SIDE_AWARE_POLICY_ID:
            if item.get("computed_oi_notional_share", 0.0) < notional_floor:
                blockers.append(f"{bucket}_side_aware_oi_notional_share_below_floor")
            if item.get("retained_abs_gamma_proxy_share", 0.0) < gamma_floor:
                blockers.append(f"{bucket}_side_aware_gamma_proxy_share_below_floor")
    return blockers


def _opposite_right_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        bucket = gamma_v1._row_bucket(row)
        right = str(row.get("right", "")).lower()
        if bucket == "otm_put" and right == "call":
            counts["otm_put_opposite_right_call_rows"] = counts.get("otm_put_opposite_right_call_rows", 0) + 1
        if bucket == "otm_call" and right == "put":
            counts["otm_call_opposite_right_put_rows"] = counts.get("otm_call_opposite_right_put_rows", 0) + 1
    return dict(sorted(counts.items()))


def _stability_gate_v2(manifest: dict[str, Any], rows_by_date: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    selected = manifest["selected_dates"]
    available_dates = sorted(rows_by_date)
    counts = {
        "low_volatility": sum(1 for item in selected if item["date"] in rows_by_date and item["volatility_bucket"] == "low"),
        "normal_volatility": sum(1 for item in selected if item["date"] in rows_by_date and item["volatility_bucket"] == "normal"),
        "high_volatility": sum(1 for item in selected if item["date"] in rows_by_date and item["volatility_bucket"] == "high"),
        "high_importance_macro": sum(1 for item in selected if item["date"] in rows_by_date and item["high_importance_macro"]),
        "no_high_importance_macro": sum(1 for item in selected if item["date"] in rows_by_date and not item["high_importance_macro"]),
        "in_sample": sum(1 for item in selected if item["date"] in rows_by_date and item["split"] == "in_sample"),
        "oos": sum(1 for item in selected if item["date"] in rows_by_date and item["split"] == "oos"),
    }
    minimum = manifest["minimum_regime_counts"]
    blockers = [name for name, count in counts.items() if count < minimum[name]]
    if len(available_dates) < minimum["total_dates"]:
        blockers.append("total_dates_below_manifest_minimum")
    return {
        "status": "pass" if not blockers else "blocked",
        "available_dates": available_dates,
        "regime_counts": counts,
        "minimum_regime_counts": minimum,
        "blockers": blockers,
        "label": "under-regime-sampled" if blockers else "pre_registered_regime_set_covered",
    }


def _economic_sign_check(rows_by_date: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    observations = []
    for date, rows in sorted(rows_by_date.items()):
        computed = [row for row in rows if row.get("greeks_status") == "computed_with_caveats"]
        aggregate = _aggregate_gamma(computed)
        realized = _realized_volatility_for_date(date)
        if aggregate["net_oi_gamma_proxy"] is None or realized["full_day_realized_volatility"] is None:
            continue
        observations.append(
            {
                "date": date,
                "net_oi_gamma_proxy": aggregate["net_oi_gamma_proxy"],
                "next_10m_realized_volatility": realized["next_10m_realized_volatility"],
                "full_day_realized_volatility": realized["full_day_realized_volatility"],
            }
        )
    corr = _pearson(
        [row["net_oi_gamma_proxy"] for row in observations],
        [row["full_day_realized_volatility"] for row in observations],
    )
    blockers = []
    if len(observations) < 6:
        blockers.append("economic_sign_observations_below_6")
    if corr is None:
        blockers.append("economic_sign_correlation_unavailable")
    elif corr > 0:
        blockers.append("positive_gamma_proxy_does_not_show_lower_volatility")
    return {
        "status": "pass" if not blockers else "blocked",
        "method": "Pearson correlation between decision-time net OI gamma proxy and same-day realized volatility after decision time.",
        "expected_sign": "negative_or_zero",
        "observation_count": len(observations),
        "full_day_volatility_correlation": corr,
        "observations": observations,
        "blockers": blockers,
    }


def _aggregate_gamma(computed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gamma_rows = [row for row in computed_rows if row.get("open_interest") is not None and row.get("underlying_price") is not None]
    if not gamma_rows:
        return {"net_oi_gamma_proxy": None, "abs_local_gamma_exposure_sum": 0.0, "underlying_notional_sum": 0.0, "scaled_net_oi_gamma_proxy": None}
    net = sum(gamma_v1.signed_gamma_proxy(row) for row in gamma_rows)
    abs_exposure = sum(abs(gamma_v1.local_gamma_exposure(row)) for row in gamma_rows)
    notional = sum(_oi_notional(row) for row in gamma_rows)
    return {
        "net_oi_gamma_proxy": round(net, 6),
        "abs_local_gamma_exposure_sum": round(abs_exposure, 6),
        "underlying_notional_sum": round(notional, 6),
        "scaled_net_oi_gamma_proxy": round(net / notional, 10) if notional else None,
        "gamma_proxy_row_count": len(gamma_rows),
    }


def _realized_volatility_for_date(date: str) -> dict[str, Any]:
    summary = _load_json(BASELINE_SUMMARY_PATH)
    bars = greeks_audit._load_bar_rows_for_date(summary, date)
    if not bars:
        return {"status": "blocked", "reason": "missing_spy_bars", "next_10m_realized_volatility": None, "full_day_realized_volatility": None}
    decision_prefix = f"{date}T{DECISION_TIME.isoformat()}"
    close_prefix = f"{date}T{FORCED_CLOSE_TIME.isoformat()}"
    post = [row for row in bars if row["timestamp_et"] >= decision_prefix and row["timestamp_et"] <= close_prefix]
    next_10 = post[:10]
    return {
        "status": "pass" if len(post) >= 10 else "blocked",
        "bar_count_after_decision": len(post),
        "next_10m_realized_volatility": _realized_vol(next_10),
        "full_day_realized_volatility": _realized_vol(post),
    }


def _realized_vol(bars: list[dict[str, Any]]) -> float | None:
    closes = [float(row["close"]) for row in bars if float(row.get("close", 0)) > 0]
    if len(closes) < 2:
        return None
    returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / len(returns)
    return round(math.sqrt(variance), 10)


def _date_enrichment_summary(
    date: str,
    manifest_entry: dict[str, Any],
    quote_rows: list[dict[str, Any]],
    bar_rows: list[dict[str, Any]],
    oi_path: Path | None,
    enriched_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "date": date,
        "split": manifest_entry["split"],
        "volatility_bucket": manifest_entry["volatility_bucket"],
        "high_importance_macro": manifest_entry["high_importance_macro"],
        "quote_snapshot_rows": len(quote_rows),
        "bar_rows": len(bar_rows),
        "oi_raw_path": str(oi_path) if oi_path else None,
        "underlying_join_count": sum(1 for row in enriched_rows if row.get("underlying_price") is not None),
        "open_interest_join_count": sum(1 for row in enriched_rows if row.get("open_interest") is not None),
        "computed_greeks_count": sum(1 for row in enriched_rows if row.get("greeks_status") == "computed_with_caveats"),
    }


def _enrichment_summary(manifest_path: Path, output_jsonl: Path, date_summaries: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "record_type": "h_g1_gamma_regime_enrichment_summary",
        "schema_version": "h_g1_gamma_regime_enrichment_v1",
        "hypothesis_id": "H-G1",
        "status": "pass" if rows else "blocked",
        "manifest": str(manifest_path),
        "output_jsonl": str(output_jsonl),
        "decision_time_et": DECISION_TIME.isoformat(),
        "date_count": len(date_summaries),
        "quote_count": len(rows),
        "computed_greeks_count": sum(1 for row in rows if row.get("greeks_status") == "computed_with_caveats"),
        "date_summaries": date_summaries,
    }


def _oi_raw_paths_by_date(
    download_result_path: Path,
    existing_oi_report_path: Path,
    additional_download_result_paths: list[Path] | None = None,
) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    download_paths = [download_result_path, *(additional_download_result_paths or [])]
    for path in download_paths:
        if not path.exists():
            continue
        result = _load_json(path)
        for item in result.get("execution", {}).get("downloads", []):
            paths[item["date"]] = Path(item["raw_path"])
    if existing_oi_report_path.exists():
        existing = _load_json(existing_oi_report_path)
        paths["2024-01-03"] = Path(existing["download"]["raw_path"])
    return paths


def _rows_by_date(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        date = str(row.get("quote_timestamp_et", ""))[:10]
        if date:
            grouped.setdefault(date, []).append(row)
    return grouped


def _gate_blockers(gates: dict[str, dict[str, Any]]) -> list[str]:
    return [f"{name}_gate:{gate['status']}" for name, gate in gates.items() if gate["status"] != "pass"]


def _oi_notional(row: dict[str, Any]) -> float:
    if row.get("open_interest") is None or row.get("underlying_price") is None:
        return 0.0
    return float(row["open_interest"]) * gamma_v1.CONTRACT_MULTIPLIER * float(row["underlying_price"])


def _has_gamma_inputs(row: dict[str, Any]) -> bool:
    return row.get("gamma") is not None and row.get("open_interest") is not None and row.get("underlying_price") is not None


def _policy_context(policy_adoption_path: Path | None) -> dict[str, Any]:
    if policy_adoption_path is None:
        return {
            "policy_id": MONEYNESS_ONLY_POLICY_ID,
            "source": "docs/GAMMA_AGGREGATION_VALIDATION_POLICY.md",
            "required_bucket_gate": "moneyness_only",
            "thresholds": {
                "computed_row_rate_floor": 0.60,
                "computed_oi_notional_share_floor": 0.80,
                "retained_abs_gamma_proxy_share_floor": 0.80,
            },
            "forbidden_claims": [
                "NOVI/net-gamma strategy filter readiness before policy gates pass",
                "true market-maker net gamma",
                "strategy validation from coverage policy",
            ],
        }
    adoption = _load_json(policy_adoption_path)
    if adoption.get("status") != "adopted_for_next_diagnostic_only":
        raise ValueError(f"unsupported H-G1 policy adoption status: {adoption.get('status')}")
    if adoption.get("policy_id") != SIDE_AWARE_POLICY_ID:
        raise ValueError(f"unsupported H-G1 policy id: {adoption.get('policy_id')}")
    scope = adoption.get("adoption_scope", {})
    for key in [
        "strategy_use_allowed",
        "network_allowed",
        "paid_data_allowed",
        "new_dates_allowed",
        "new_option_quotes_allowed",
        "new_oi_files_allowed",
        "strategy_pnl_selection_allowed",
    ]:
        if scope.get(key) is not False:
            raise ValueError(f"H-G1 side-aware policy adoption violates scope guard: {key}")
    return {
        "policy_id": adoption["policy_id"],
        "source": str(policy_adoption_path),
        "required_bucket_gate": "side_aware",
        "adopted_candidate": adoption.get("adopted_candidate"),
        "thresholds": adoption["thresholds"],
        "forbidden_claims": adoption.get("forbidden_claims", []),
    }


def _safe_rate(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_den = math.sqrt(sum((x - x_mean) ** 2 for x in xs))
    y_den = math.sqrt(sum((y - y_mean) ** 2 for y in ys))
    if not x_den or not y_den:
        return None
    return round(numerator / (x_den * y_den), 6)


def _research_decision(blockers: list[str]) -> str:
    if blockers:
        return "ยังสรุปไม่ได้: H-G1 ยังไม่ผ่าน policy v2 จึงห้ามใช้ signed-OI gamma proxy เป็น NOVI/net-gamma strategy filter"
    return "ผ่านเฉพาะ data-validity diagnostic: ยังไม่ใช่ strategy acceptance และยังต้องมี backtest/MinTRL/PSR ก่อนใช้เป็น trading gate"


def _conclusion_reason(blockers: list[str]) -> str:
    if not blockers:
        return "The pre-registered gamma proxy diagnostic passed v2 data-validity gates, but this is not a strategy acceptance result."
    return "The pre-registered gamma proxy diagnostic still has policy blockers: " + ", ".join(blockers)


def _render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# H-G1 Gamma/OI Regime Diagnostic",
        "",
        f"- Status: `{result['status']}`",
        f"- Conclusion: {result['conclusion']}",
        f"- Evidence tier: `{result['evidence_tier']}`",
        f"- Required bucket policy: `{result['policy_version']}`",
        f"- Strategy use: `{result['strategy_use_status']}`",
        f"- Network used: `{result['network_used']}`",
        f"- Paid data used: `{result['paid_data_used']}`",
        f"- Strategy PnL used: `{result['strategy_pnl_used']}`",
        f"- Decision time ET: `{result['decision_time_et']}`",
        f"- Dates: {result['date_count']}",
        f"- Quote rows: {result['quote_count']}",
        f"- Computed Greeks rows: {result['computed_greeks_count']}",
        "",
        "## Gates",
        "",
        "| Gate | Status | Notes |",
        "|:--|:--|:--|",
    ]
    for name, gate in result["validation_gates"].items():
        notes = ", ".join(gate.get("blockers", [])) or gate.get("reason", "")
        lines.append(f"| `{name}` | `{gate['status']}` | {notes} |")
    lines.extend(["", "## Per-Date Summary", "", "| Date | Quotes | Greeks | Underlying | OI | Required bucket blockers |", "|:--|--:|--:|--:|--:|:--|"])
    for date, item in result["per_date"].items():
        blockers = ", ".join(item["required_bucket_blockers"]) or "None"
        lines.append(
            f"| {date} | {item['quote_count']} | {item['computed_greeks_count']} | "
            f"{item['underlying_join_count']} | {item['open_interest_join_count']} | {blockers} |"
        )
    lines.extend(["", "## Decision", "", result["research_decision"], ""])
    return "\n".join(lines)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run H-G1 12-date gamma/OI enrichment and v2 diagnostic.")
    parser.add_argument("--manifest-path", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--baseline-summary-path", type=Path, default=BASELINE_SUMMARY_PATH)
    parser.add_argument("--oi-download-result-path", type=Path, default=OI_DOWNLOAD_RESULT_PATH)
    parser.add_argument("--additional-oi-download-result-path", type=Path, action="append", default=[])
    parser.add_argument("--existing-oi-report-path", type=Path, default=EXISTING_OI_REPORT_PATH)
    parser.add_argument("--output-jsonl", type=Path, default=OUTPUT_JSONL)
    parser.add_argument("--enrichment-summary-output", type=Path, default=ENRICHMENT_SUMMARY_OUTPUT)
    parser.add_argument("--diagnostic-summary-output", type=Path, default=DIAGNOSTIC_SUMMARY_OUTPUT)
    parser.add_argument("--diagnostic-report-output", type=Path, default=DIAGNOSTIC_REPORT_OUTPUT)
    parser.add_argument("--research-log-slug", default="higanbana-gamma-oi-regime-diagnostic")
    parser.add_argument("--research-log-path", default="research_log/013-higanbana-gamma-oi-regime-diagnostic.md")
    parser.add_argument("--policy-adoption-path", type=Path, default=None)
    args = parser.parse_args(argv)

    result = run_h_g1_diagnostic(
        manifest_path=args.manifest_path,
        baseline_summary_path=args.baseline_summary_path,
        oi_download_result_path=args.oi_download_result_path,
        additional_oi_download_result_paths=args.additional_oi_download_result_path,
        existing_oi_report_path=args.existing_oi_report_path,
        output_jsonl=args.output_jsonl,
        enrichment_summary_output=args.enrichment_summary_output,
        diagnostic_summary_output=args.diagnostic_summary_output,
        diagnostic_report_output=args.diagnostic_report_output,
        research_log_slug=args.research_log_slug,
        research_log_path=args.research_log_path,
        policy_adoption_path=args.policy_adoption_path,
    )
    print(json.dumps({"status": result["status"], "blockers": result["blockers"]}, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"blocked", "pass_diagnostic_only"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
