from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.databento_dbn import load_option_snapshots, load_spy_ohlcv_bars
from lib.environment import data_root
from lib.io import load_json
from lib.options import replay_vertical
from lib.orb import opening_breakout
from lib.regime_inputs import load_macro_events_by_date, load_vix_vxv, previous_vix_record
from lib.report import render_markdown_report, write_report_pair
from lib.search_log import write_search_log
from lib.statistics import (
    first_order_autocorrelation,
    minimum_track_record_length,
    probabilistic_sharpe_ratio,
    raw_kurtosis_population,
    sharpe_ratio,
    skewness_population,
)
from scripts.validate_h_a2_fresh_oos_timestamp_clean_checkpoint_preregistration import DEFAULT_PATH, validate


DEFAULT_DOWNLOAD_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_h_a2_fresh_oos_2025_2026.json"
DEFAULT_VIX_PATH = data_root() / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl"
DEFAULT_MACRO_PATH = data_root() / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_fresh_oos_timestamp_clean_checkpoint.json"
DEFAULT_MARKDOWN_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_fresh_oos_timestamp_clean_checkpoint.md"
DEFAULT_SEARCH_LOG_PATH = PROJECT_ROOT / "reports" / "experiments" / "search_logs" / "h_a2_fresh_oos_timestamp_clean_checkpoint.jsonl"


def run_checkpoint(
    prereg_path: Path = DEFAULT_PATH,
    download_report_path: Path = DEFAULT_DOWNLOAD_REPORT,
    vix_path: Path = DEFAULT_VIX_PATH,
    macro_path: Path = DEFAULT_MACRO_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    markdown_path: Path = DEFAULT_MARKDOWN_PATH,
    search_log_path: Path = DEFAULT_SEARCH_LOG_PATH,
) -> dict[str, Any]:
    validation = validate(prereg_path)
    if validation["status"] != "pass":
        raise RuntimeError(f"preregistration blocked: {validation['blockers']}")
    prereg = load_json(prereg_path)
    download = load_json(download_report_path)
    if download.get("status") != "pass" or download.get("request_count") != 40:
        raise RuntimeError("fresh OOS download report is not complete")

    target_dates = {
        date_text: bucket
        for bucket, values in prereg["target_dates"].items()
        for date_text in values
    }
    files = _download_files_by_date(download["downloads"], set(target_dates))
    vix_rows = load_vix_vxv(vix_path)
    macro_by_date = load_macro_events_by_date(macro_path)
    warning_dates = set(prereg["provider_quality_warning_dates"])
    date_results = []

    for date_text in sorted(target_dates):
        bars, bar_coverage = load_spy_ohlcv_bars(files[date_text]["spy"], date_text)
        snapshots, quote_coverage = load_option_snapshots(files[date_text]["options"], date_text)
        signal = opening_breakout(bars, decision_time="09:35:00")
        regime = _regime(date_text, vix_rows, macro_by_date)
        candidate = signal.get("direction") in {"call", "put"} and regime["clean_scope"]
        replay = None
        blockers: list[str] = []
        if candidate:
            direction = str(signal["direction"])
            entry = [row for row in snapshots["09:35:00"] if row["right"] == direction]
            forced = [row for row in snapshots["15:45:00"] if row["right"] == direction]
            try:
                replay = replay_vertical(
                    entry,
                    forced,
                    direction=direction,
                    underlying_price=float(signal["decision_close"]),
                    target_gap=float(prereg["option_replay_rule"]["target_gap_points"]),
                    width=float(prereg["option_replay_rule"]["width_points"]),
                    fee_per_leg_usd=float(prereg["option_replay_rule"]["fee_per_leg_usd"]),
                )
            except Exception as exc:  # noqa: BLE001 - blocker is preserved in the experiment report.
                blockers.append(str(exc))
        date_results.append(
            {
                "date": date_text,
                "vix_bucket": target_dates[date_text],
                "provider_quality_warning": date_text in warning_dates,
                "bar_coverage": bar_coverage,
                "quote_coverage": quote_coverage,
                "regime": regime,
                "timestamp_clean_signal": signal,
                "candidate": candidate,
                "replay_status": "complete" if replay is not None else "blocked" if blockers else "not_candidate",
                "replay": replay,
                "blockers": blockers,
            }
        )

    aggregate = _aggregate(date_results, float(download["total_estimated_cost_usd"]), prereg)
    aggregate["checkpoint_decision"]["stop_expansion"] = True
    aggregate["checkpoint_decision"]["stop_reasons"].append("exact_0935_timestamp_semantics_not_satisfied")
    aggregate["checkpoint_decision"]["next_action"] = (
        "Stop expansion. Treat this as a 09:36 proxy only; pre-register an actually observable 09:35 rule "
        "or an explicit 09:36 rule on data whose outcomes have not been viewed."
    )
    conclusion, reason = _conclusion(aggregate)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    summary = {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_fresh_oos_timestamp_clean_checkpoint_v1",
        "experiment_id": "h_a2_fresh_oos_timestamp_clean_checkpoint",
        "hypothesis_id": "H-A2",
        "status": "complete_methodology_failure",
        "evidence_tier": "E1",
        "conclusion": conclusion,
        "conclusion_reason": reason,
        "generated_at_utc": generated_at,
        "research_question": prereg["research_question"],
        "scope": prereg["scope"],
        "hypothesis": prereg["hypothesis"],
        "source_preregistration": _relative(prereg_path),
        "source_download_report": _relative(download_report_path),
        "lookahead_correction": prereg["lookahead_correction"],
        "methodology": {
            "candidate_rule": prereg["candidate_rule"],
            "option_replay_rule": prereg["option_replay_rule"],
            "trial_policy": prereg["trial_policy"],
            "fresh_outcomes_viewed_before_preregistration": False,
            "bar_timestamp_semantics": "Databento OHLCV-1m ts_event identifies the minute interval start.",
            "configured_decision_bar_timestamp_et": "09:35:00",
            "actual_signal_availability_et": "approximately 09:36:00 after the 09:35 minute bar closes",
            "entry_quote_timestamp_et": "09:35:00",
            "execution_timestamp_alignment_pass": False,
            "exact_0935_question_answered": False,
            "post_0935_feature_used_for_candidate_selection": True,
            "preregistration_deviation": "The preregistration treated the 09:35 bar close as observable at 09:35. That assumption failed after the run and the result is downgraded to a 09:36 proxy.",
        },
        "date_results": date_results,
        "aggregate": aggregate,
        "network_used": False,
        "additional_paid_data_used": False,
        "ibkr_request_used": False,
        "llm_call_used": False,
        "paper_trading_allowed": False,
        "operational_validation_allowed": False,
        "real_money_allowed": False,
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-fresh-oos-timestamp-clean-checkpoint",
        "research_log_path": "research_log/001-higanbana-h-a2-fresh-oos-timestamp-clean-checkpoint.md",
        "tier_blockers": _tier_blockers(aggregate),
        "forbidden_claims": prereg["forbidden_claims"],
        "next_safe_action": aggregate["checkpoint_decision"]["next_action"],
    }
    search_record = {
        "record_type": "h_a2_fresh_oos_timestamp_clean_checkpoint_trial",
        "experiment_id": summary["experiment_id"],
        "trial_id": "fixed_timestamp_clean_orb_v1",
        "trial_count": 1,
        "parameter_search_used": False,
        "threshold_search_used": False,
        "oos_tuning_used": False,
        "candidate_count": aggregate["candidate_count"],
        "completed_trade_count": aggregate["completed_trade_count"],
        "mean_implementable_pnl": aggregate["pnl"]["mean_implementable_pnl"],
        "pnl_valid_for_inference": False,
        "conclusion": conclusion,
    }
    write_search_log(search_log_path, [search_record])
    summary["search_log"] = _relative(search_log_path)
    markdown = _render_markdown(summary)
    return write_report_pair(summary, summary_path, markdown_path, markdown)


def _download_files_by_date(downloads: list[dict[str, Any]], expected_dates: set[str]) -> dict[str, dict[str, Path]]:
    grouped: dict[str, dict[str, Path]] = {}
    for row in downloads:
        date_text = str(row["date"])
        if date_text not in expected_dates:
            continue
        grouped.setdefault(date_text, {})
        key = "options" if row["dataset"] == "OPRA.PILLAR" else "spy" if row["dataset"] == "EQUS.MINI" else ""
        if key:
            grouped[date_text][key] = Path(row["raw_path"])
    missing = [date_text for date_text in sorted(expected_dates) if set(grouped.get(date_text, {})) != {"options", "spy"}]
    if missing:
        raise RuntimeError(f"missing raw inputs for dates: {missing}")
    return grouped


def _regime(date_text: str, vix_rows: list[dict[str, Any]], macro_by_date: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    prior = previous_vix_record(date_text, vix_rows)
    events = macro_by_date.get(date_text, [])
    high_events = [event for event in events if event.get("importance") == "high"]
    prior_vix = float(prior["vix_close"]) if prior else None
    return {
        "prior_vix_date": prior.get("date") if prior else None,
        "prior_vix_close": prior_vix,
        "high_importance_macro": bool(high_events),
        "high_importance_macro_event_types": sorted({str(event["event_type"]) for event in high_events}),
        "clean_scope": prior_vix is not None and prior_vix < 25.0 and not high_events,
    }


def _aggregate(rows: list[dict[str, Any]], purchase_cost: float, prereg: dict[str, Any]) -> dict[str, Any]:
    candidates = [row for row in rows if row["candidate"]]
    completed = [row for row in candidates if row["replay_status"] == "complete"]
    values = [float(row["replay"]["pnl"]["implementable_pnl"]) for row in completed]
    mid_values = [float(row["replay"]["pnl"]["mid_pnl"]) for row in completed]
    stats = _sample_statistics(values)
    warning_values = [float(row["replay"]["pnl"]["implementable_pnl"]) for row in completed if row["provider_quality_warning"]]
    clean_values = [float(row["replay"]["pnl"]["implementable_pnl"]) for row in completed if not row["provider_quality_warning"]]
    cost_per_candidate = purchase_cost / len(candidates) if candidates else None
    mintrl_zero = stats["null_0"]["mintrl"]
    projected_cost = cost_per_candidate * mintrl_zero if cost_per_candidate is not None and mintrl_zero is not None else None
    authorization_headroom = 50.0 - purchase_cost
    warning_dependency = bool(values and warning_values and clean_values and _sign(mean(values)) != _sign(mean(clean_values)))
    stop_reasons = []
    if len(candidates) < 2:
        stop_reasons.append("candidate_count_below_2")
    if stats["observed_sharpe"] is None or stats["observed_sharpe"] <= 0:
        stop_reasons.append("mintrl_falsify_undefined_observed_sharpe_not_positive")
    if projected_cost is not None and projected_cost > authorization_headroom:
        stop_reasons.append("projected_mintrl_cost_exceeds_key_authorization_headroom")
    if warning_dependency:
        stop_reasons.append("provider_warning_dates_determine_pnl_sign")
    bucket_counts = {
        bucket: sum(row["candidate"] and row["vix_bucket"] == bucket for row in rows)
        for bucket in prereg["target_dates"]
    }
    return {
        "target_date_count": len(rows),
        "clean_scope_date_count": sum(row["regime"]["clean_scope"] for row in rows),
        "bar_coverage_pass_count": sum(row["bar_coverage"]["has_0935_bar"] and row["bar_coverage"]["has_1545_bar"] for row in rows),
        "candidate_count": len(candidates),
        "candidate_count_by_vix_bucket": bucket_counts,
        "completed_trade_count": len(completed),
        "blocked_candidate_count": len(candidates) - len(completed),
        "purchase_cost_usd": purchase_cost,
        "cost_per_candidate_usd": round(cost_per_candidate, 6) if cost_per_candidate is not None else None,
        "pnl": {
            "total_mid_pnl": round(sum(mid_values), 2),
            "total_implementable_pnl": round(sum(values), 2),
            "mean_implementable_pnl": round(mean(values), 6) if values else None,
            "winning_trade_count": sum(value > 0 for value in values),
            "losing_trade_count": sum(value < 0 for value in values),
            "cost_drag_total": round(sum(mid_values) - sum(values), 2),
            "valid_for_inference": False,
            "invalid_reason": "Entry option quotes are timestamped 09:35, before the 09:35 underlying bar close makes the signal available around 09:36.",
        },
        "statistics": {
            **stats,
            "valid_for_inference": False,
            "invalid_reason": "Statistics are mechanically computed from a return series with entry-before-signal timestamp mismatch.",
        },
        "big_day_dependency": _big_day_dependency(values),
        "provider_warning_sensitivity": {
            "warning_candidate_count": len(warning_values),
            "non_warning_candidate_count": len(clean_values),
            "mean_all": round(mean(values), 6) if values else None,
            "mean_excluding_warning_dates": round(mean(clean_values), 6) if clean_values else None,
            "pnl_sign_depends_on_warning_dates": warning_dependency,
        },
        "mintrl_cost_projection": {
            "null_sharpe_0_mintrl": mintrl_zero,
            "projected_cost_to_mintrl_usd": round(projected_cost, 6) if projected_cost is not None else None,
            "selected_key_authorization_headroom_usd": round(authorization_headroom, 6),
        },
        "checkpoint_decision": {
            "stop_expansion": bool(stop_reasons),
            "stop_reasons": stop_reasons,
            "next_action": (
                "Stop additional data expansion and revise H-A2 from the timestamp-clean result before any purchase."
                if stop_reasons
                else "Keep H-A2 active at E1 only and write a new decision-tree artifact before any additional data."
            ),
        },
    }


def _sample_statistics(values: list[float]) -> dict[str, Any]:
    observed = sharpe_ratio(values)
    skew = skewness_population(values)
    kurtosis = raw_kurtosis_population(values)
    autocorrelation = first_order_autocorrelation(values)
    result: dict[str, Any] = {
        "sample_count": len(values),
        "observed_sharpe": observed,
        "skewness": skew,
        "raw_kurtosis": kurtosis,
        "first_order_autocorrelation": autocorrelation,
    }
    for label, null in (("null_0", 0.0), ("null_0_5", 0.5)):
        if observed is None or skew is None or kurtosis is None:
            result[label] = {"null_sharpe": null, "psr": None, "mintrl": None}
            continue
        result[label] = {
            "null_sharpe": null,
            "psr": probabilistic_sharpe_ratio(
                observed_sharpe=observed,
                sample_length=len(values),
                skewness=skew,
                raw_kurtosis=kurtosis,
                null_sharpe=null,
                autocorrelation=autocorrelation,
            ),
            "mintrl": minimum_track_record_length(
                observed_sharpe=observed,
                skewness=skew,
                raw_kurtosis=kurtosis,
                null_sharpe=null,
                autocorrelation=autocorrelation,
            ),
        }
    mintrl = result["null_0"]["mintrl"]
    psr = result["null_0"]["psr"]
    result["under_sampled"] = mintrl is None or len(values) < mintrl
    result["underpowered"] = psr is None or psr < 0.95
    return result


def _big_day_dependency(values: list[float]) -> dict[str, Any]:
    if len(values) < 2:
        return {"status": "insufficient_candidates", "trimmed_mean_implementable_pnl": None}
    largest = max(values, key=abs)
    trimmed = list(values)
    trimmed.remove(largest)
    return {
        "status": "measured",
        "removed_largest_absolute_pnl": largest,
        "trimmed_count": len(trimmed),
        "trimmed_mean_implementable_pnl": round(mean(trimmed), 6),
        "mean_sign_survives": _sign(mean(values)) == _sign(mean(trimmed)),
    }


def _conclusion(aggregate: dict[str, Any]) -> tuple[str, str]:
    if "exact_0935_timestamp_semantics_not_satisfied" in aggregate["checkpoint_decision"]["stop_reasons"]:
        return "ยังสรุปไม่ได้", "การทดลองใช้ราคาปิดของแท่งที่ประทับเวลา 09:35 ซึ่งรู้ได้ประมาณ 09:36 แต่ใช้ราคาออปชันเวลา 09:35 เป็นราคาเข้า จึงเกิด entry-before-signal mismatch และ PnL ใช้อ้างอิงสมมติฐานไม่ได้"
    if aggregate["candidate_count"] < 2 or aggregate["completed_trade_count"] < 2:
        return "ยังสรุปไม่ได้", "ข้อมูล OOS ใหม่ให้ candidate ที่ replay สำเร็จน้อยกว่า 2 รายการ จึงยังตอบสมมติฐานไม่ได้และต้องหยุดขยายข้อมูลอัตโนมัติ"
    mean_pnl = aggregate["pnl"]["mean_implementable_pnl"]
    if mean_pnl is not None and mean_pnl <= 0:
        return "ไม่ผ่าน", "กฎ ORB ที่สะอาดจากข้อมูลอนาคตไม่ให้ค่าเฉลี่ย implementable PnL เป็นบวกในชุด OOS ที่ลงทะเบียนไว้"
    return "ยังสรุปไม่ได้", "ค่าเฉลี่ย implementable PnL เป็นบวก แต่จำนวนตัวอย่างยังต่ำกว่า MinTRL หรือกำลังทดสอบยังไม่ถึงเกณฑ์ จึงยังยืนยัน edge ไม่ได้"


def _tier_blockers(aggregate: dict[str, Any]) -> list[str]:
    blockers = [
        "E1 fresh OOS checkpoint only",
        "Prior H-A2 threshold branch is lookahead-contaminated",
        "09:35 bar close is only available around 09:36",
        "Entry quote precedes signal availability",
        "PnL, PSR, and MinTRL invalid for inference",
        "Exact 09:35 research question not answered",
        "No E2 claim",
    ]
    if aggregate["statistics"]["under_sampled"]:
        blockers.append("under-sampled")
    if aggregate["statistics"]["underpowered"]:
        blockers.append("underpowered")
    return blockers


def _render_markdown(summary: dict[str, Any]) -> str:
    aggregate = summary["aggregate"]
    rows = []
    for item in summary["date_results"]:
        pnl = (item.get("replay") or {}).get("pnl", {})
        rows.append(
            f"| {item['date']} | {item['vix_bucket']} | {item['provider_quality_warning']} | "
            f"{item['timestamp_clean_signal'].get('direction')} | {item['candidate']} | {item['replay_status']} | "
            f"{pnl.get('implementable_pnl', '')} |"
        )
    table = "\n".join(
        [
            "| Date | VIX bucket | Quality warning | ORB direction | Candidate | Replay | Implementable PnL |",
            "|:--|:--|:--:|:--:|:--:|:--:|--:|",
            *rows,
        ]
    )
    return render_markdown_report(
        "H-A2 Fresh OOS Timestamp-Clean Checkpoint",
        [
            ("คำถามและข้อสรุป", f"- คำถาม: {summary['research_question']}\n- ข้อสรุป: `{summary['conclusion']}`\n- เหตุผล: {summary['conclusion_reason']}"),
            ("การแก้ Lookahead และข้อจำกัดเวลา", "กฎเดิมใช้ราคา 15:45 คัดเลือกสถานะย้อนหลัง จึงถูกตัดออกก่อนอ่านผลชุดนี้ อย่างไรก็ตาม ราคาปิดของแท่งที่ประทับเวลา 09:35 จะรู้ได้ประมาณ 09:36 ผลรอบนี้จึงเป็น 09:36 proxy ไม่ใช่ exact 09:35"),
            ("ผลรวม", f"- Candidate ที่พบย้อนหลัง: `{aggregate['candidate_count']}`\n- Replay ที่คำนวณได้: `{aggregate['completed_trade_count']}`\n- Mechanical PnL (invalid for inference): `{aggregate['pnl']['total_implementable_pnl']}`\n- PnL valid for inference: `{aggregate['pnl']['valid_for_inference']}`\n- Under-sampled: `{aggregate['statistics']['under_sampled']}`\n- Underpowered: `{aggregate['statistics']['underpowered']}`"),
            ("รายวัน", table),
            ("Checkpoint", f"- Stop expansion: `{aggregate['checkpoint_decision']['stop_expansion']}`\n- Reasons: `{aggregate['checkpoint_decision']['stop_reasons']}`\n- Next: {aggregate['checkpoint_decision']['next_action']}"),
        ],
    )


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the preregistered timestamp-clean H-A2 fresh OOS checkpoint.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--markdown-path", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--search-log-path", type=Path, default=DEFAULT_SEARCH_LOG_PATH)
    args = parser.parse_args(argv)
    result = run_checkpoint(summary_path=args.summary_path, markdown_path=args.markdown_path, search_log_path=args.search_log_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
