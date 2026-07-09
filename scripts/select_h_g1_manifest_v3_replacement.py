from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration_v3_plan.json"
V2_MANIFEST_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration_v2.json"
MACRO_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl"
VIX_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl"
DATABENTO_CACHE_ROOT = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento"
OUTPUT_MANIFEST_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration_v3.json"
OUTPUT_REPORT_JSON = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_manifest_v3_candidate_selection.json"
OUTPUT_REPORT_MD = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_manifest_v3_candidate_selection.md"


def build_manifest_v3(
    plan_path: Path = PLAN_PATH,
    v2_manifest_path: Path = V2_MANIFEST_PATH,
    output_manifest_path: Path = OUTPUT_MANIFEST_PATH,
    output_report_json: Path = OUTPUT_REPORT_JSON,
    output_report_md: Path = OUTPUT_REPORT_MD,
) -> dict[str, Any]:
    plan = _read_json(plan_path)
    v2_manifest = _read_json(v2_manifest_path)

    remove_date = plan["replacement_objective"]["remove_date"]
    selected_dates_v2 = v2_manifest["selected_dates"]
    used_dates = {item["date"] for item in selected_dates_v2}
    candidates = _rank_candidates(plan=plan, used_dates=used_dates)
    if not candidates:
        raise RuntimeError("No eligible H-G1 v3 replacement candidates found from local macro/VIX/cache inputs")

    selected = candidates[0]
    replacement = {
        "date": selected["date"],
        "split": plan["replacement_objective"]["target_split"],
        "volatility_bucket": plan["replacement_objective"]["target_volatility_bucket"],
        "vix_close": selected["vix_close"],
        "high_importance_macro": True,
        "macro_events": selected["macro_events"],
        "trend_regime": "low_vol_macro_replacement",
        "selection_reason": (
            "H-G1 v3 replacement for 2023-07-12 selected by locked plan rules: "
            "same preferred CPI family first, then closest same-day VIX close to 13.54, "
            "with local option quote and SPY bar cache present. Gamma/OI/PnL inputs were not used."
        ),
        "local_quote_cache_status": "present",
        "local_spy_bar_cache_status": "present",
        "opra_oi_status": "needs_metadata_cost_check",
    }

    selected_dates = [replacement if item["date"] == remove_date else item for item in selected_dates_v2]
    manifest = {
        "schema_version": "h_g1_gamma_regime_date_set_preregistration_v3",
        "hypothesis_id": "H-G1",
        "created_at": "2026-07-03",
        "supersedes": _relative(v2_manifest_path),
        "source_plan": _relative(plan_path),
        "purpose": (
            "Replace the weak 2023-07-12 otm_put bucket before any new OI purchase, "
            "using only the locked H-G1.10 ranking rules and local macro/VIX/cache evidence."
        ),
        "data_policy": {
            "symbol_universe": ["SPY"],
            "new_paid_data_allowed_after_validation": True,
            "paid_action_before_manifest_validation": "forbidden",
            "purchase_scope": (
                "At most one replacement full UTC day of OPRA statistics/OI for 2023-09-13 "
                "after this manifest validates and metadata cost guard passes."
            ),
            "broad_calendar_purchase": "forbidden",
            "existing_oi_probe_date": "2024-01-03",
            "cost_guard": plan["data_policy"]["cost_guard"],
            "requires_metadata_cost_check_before_download": True,
        },
        "replacement_audit": {
            "removed_date": remove_date,
            "removed_bucket": plan["blocked_bucket_to_repair"]["bucket"],
            "selected_replacement_date": selected["date"],
            "ranking_rules_source": _relative(plan_path),
            "candidate_selection_report": _relative(output_report_json),
            "forbidden_inputs_not_used": plan["candidate_selection_rules"]["forbidden_selection_inputs"],
            "macro_source": _relative(MACRO_PATH),
            "vix_source": _relative(VIX_PATH),
            "local_cache_root": _relative(DATABENTO_CACHE_ROOT),
        },
        "candidate_ranking_table": candidates,
        "minimum_regime_counts": {
            "total_dates": plan["concrete_manifest_requirements"]["total_dates"],
            **plan["concrete_manifest_requirements"]["minimum_regime_counts"],
        },
        "selected_dates": selected_dates,
        "locked_outputs": {
            "candidate_selection_json": _relative(output_report_json),
            "candidate_selection_report": _relative(output_report_md),
            "next_required_step": "Run metadata cost check for one replacement OPRA statistics/OI day only after manifest validation passes.",
        },
    }

    report = {
        "schema_version": "h_g1_manifest_v3_candidate_selection_v1",
        "hypothesis_id": "H-G1",
        "status": "pass",
        "network_used": False,
        "paid_data_used": False,
        "selected_replacement_date": selected["date"],
        "removed_date": remove_date,
        "candidate_count": len(candidates),
        "ranking_rules": plan["candidate_selection_rules"]["ranking_order_before_oi_purchase"],
        "forbidden_selection_inputs_not_used": plan["candidate_selection_rules"]["forbidden_selection_inputs"],
        "candidate_ranking_table": candidates,
        "output_manifest": _relative(output_manifest_path),
    }

    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output_report_json.parent.mkdir(parents=True, exist_ok=True)
    output_manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_report_md.write_text(_render_markdown(report), encoding="utf-8")
    return report


def _rank_candidates(plan: dict[str, Any], used_dates: set[str]) -> list[dict[str, Any]]:
    allowed = plan["candidate_selection_rules"]["allowed_window"]
    start_date = allowed["start"]
    end_date = allowed["end"]
    removed_vix = 13.54
    preferred_events = plan["replacement_objective"]["preferred_macro_events"]

    macro_by_date = _load_high_importance_macro_events()
    vix_by_date = _load_vix()
    candidates: list[dict[str, Any]] = []

    for date, macro_events in sorted(macro_by_date.items()):
        if not start_date <= date <= end_date:
            continue
        if date in used_dates:
            continue
        vix_close = vix_by_date.get(date)
        if not isinstance(vix_close, int | float) or vix_close >= 15:
            continue
        preferred_present = [event for event in preferred_events if event in macro_events]
        if not preferred_present:
            continue
        quote_present = _has_local_cache_date(date, "option_quote.jsonl", "quote_timestamp_et")
        spy_bar_present = _has_local_cache_date(date, "spy_bar.jsonl", "timestamp_et")
        if not quote_present or not spy_bar_present:
            continue

        is_same_macro_family = "CPI" in macro_events
        candidates.append(
            {
                "rank": 0,
                "date": date,
                "split": "in_sample",
                "volatility_bucket": "low",
                "vix_close": vix_close,
                "vix_abs_deviation_from_removed": round(abs(vix_close - removed_vix), 6),
                "high_importance_macro": True,
                "macro_events": sorted(macro_events),
                "preferred_macro_events_present": preferred_present,
                "same_macro_family_as_removed": is_same_macro_family,
                "local_option_quote_cache_present": quote_present,
                "local_spy_bar_cache_present": spy_bar_present,
                "selection_inputs": ["macro_event_type", "same_day_vix_close", "local_quote_cache_presence", "local_spy_bar_cache_presence"],
            }
        )

    candidates.sort(
        key=lambda item: (
            0 if item["same_macro_family_as_removed"] else 1,
            item["vix_abs_deviation_from_removed"],
            item["date"],
        )
    )
    for idx, item in enumerate(candidates, start=1):
        item["rank"] = idx
    return candidates


def _load_high_importance_macro_events() -> dict[str, set[str]]:
    events: dict[str, set[str]] = defaultdict(set)
    for obj in _iter_jsonl(MACRO_PATH):
        if obj.get("importance") != "high":
            continue
        timestamp = obj.get("event_timestamp_et")
        event_type = obj.get("event_type")
        if isinstance(timestamp, str) and isinstance(event_type, str):
            events[timestamp[:10]].add(event_type)
    return events


def _load_vix() -> dict[str, float]:
    out: dict[str, float] = {}
    for obj in _iter_jsonl(VIX_PATH):
        date = obj.get("date")
        vix_close = obj.get("vix_close")
        if isinstance(date, str) and isinstance(vix_close, int | float):
            out[date] = float(vix_close)
    return out


def _has_local_cache_date(date: str, filename: str, timestamp_field: str) -> bool:
    folder = DATABENTO_CACHE_ROOT / f"insample_{date[:7].replace('-', '_')}"
    path = folder / filename
    if not path.exists():
        return False
    needle = f'"{timestamp_field}": "{date}'
    with path.open("r", encoding="utf-8") as handle:
        return any(needle in line for line in handle if line.strip())


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# H-G1 Manifest V3 Candidate Selection",
        "",
        "- **Status**: pass",
        "- **Network used**: false",
        "- **Paid data used**: false",
        f"- **Removed date**: `{report['removed_date']}`",
        f"- **Selected replacement**: `{report['selected_replacement_date']}`",
        "",
        "## Ranking Table",
        "",
        "| Rank | Date | VIX | VIX diff | Macro | Quote cache | SPY bar cache |",
        "|:--|:--|--:|--:|:--|:--:|:--:|",
    ]
    for item in report["candidate_ranking_table"]:
        lines.append(
            "| {rank} | {date} | {vix_close:.2f} | {vix_abs_deviation_from_removed:.2f} | {macro} | {quote} | {bar} |".format(
                rank=item["rank"],
                date=item["date"],
                vix_close=item["vix_close"],
                vix_abs_deviation_from_removed=item["vix_abs_deviation_from_removed"],
                macro=", ".join(item["macro_events"]),
                quote="yes" if item["local_option_quote_cache_present"] else "no",
                bar="yes" if item["local_spy_bar_cache_present"] else "no",
            )
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Candidate selection used only macro event type, same-day VIX close, and local cache presence.",
            "- Gamma/OI result, strategy PnL, and post-decision realized volatility were not used.",
            "- The next allowed action is metadata cost check for the one replacement OPRA statistics/OI day after manifest validation passes.",
            "",
        ]
    )
    return "\n".join(lines)


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Select H-G1 manifest v3 replacement and write concrete manifest.")
    parser.add_argument("--plan-path", type=Path, default=PLAN_PATH)
    parser.add_argument("--v2-manifest-path", type=Path, default=V2_MANIFEST_PATH)
    parser.add_argument("--output-manifest-path", type=Path, default=OUTPUT_MANIFEST_PATH)
    parser.add_argument("--output-report-json", type=Path, default=OUTPUT_REPORT_JSON)
    parser.add_argument("--output-report-md", type=Path, default=OUTPUT_REPORT_MD)
    args = parser.parse_args(argv)

    report = build_manifest_v3(
        plan_path=args.plan_path,
        v2_manifest_path=args.v2_manifest_path,
        output_manifest_path=args.output_manifest_path,
        output_report_json=args.output_report_json,
        output_report_md=args.output_report_md,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
