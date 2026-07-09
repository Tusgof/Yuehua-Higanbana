from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_h_a2_normal_control_exact_replay as base
from validate_h_a2_post_stress_normalization_control_exact_replay_preregistration import (
    validate_h_a2_post_stress_normalization_control_exact_replay_preregistration,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_DATE = "2025-05-05"
CANDIDATE_DIRECTION = "call"

DEFAULT_PREREG_PATH = (
    PROJECT_ROOT / "experiments" / "h_a2_post_stress_normalization_control_exact_replay_preregistration.json"
)
DEFAULT_SOURCE_IMPORT_PATH = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_post_stress_normalization_control_import_diagnostic.json"
)
DEFAULT_RAW_QUOTE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "spy_0dte"
    / "databento"
    / "h_a2_post_stress_normalization_control_pack"
    / "2025-05-05_opra_grouped_0930_1550.dbn.zst"
)
DEFAULT_SUMMARY_PATH = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_post_stress_normalization_control_exact_replay.json"
)
DEFAULT_REPORT_PATH = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_post_stress_normalization_control_exact_replay.md"
)
DEFAULT_SEARCH_LOG_PATH = (
    PROJECT_ROOT
    / "reports"
    / "diagnostics"
    / "search_logs"
    / "h_a2_post_stress_normalization_control_exact_replay_search_log.jsonl"
)


def run_h_a2_post_stress_normalization_control_exact_replay(
    prereg_path: Path = DEFAULT_PREREG_PATH,
    source_import_path: Path = DEFAULT_SOURCE_IMPORT_PATH,
    raw_quote_path: Path = DEFAULT_RAW_QUOTE_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    search_log_path: Path = DEFAULT_SEARCH_LOG_PATH,
) -> dict[str, Any]:
    prereg_check = validate_h_a2_post_stress_normalization_control_exact_replay_preregistration(
        prereg_path
    )
    if prereg_check["status"] != "pass":
        raise RuntimeError(f"preregistration blocked: {prereg_check['blockers']}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        raw_summary = _run_base_replay(
            prereg_path=prereg_path,
            source_import_path=source_import_path,
            raw_quote_path=raw_quote_path,
            summary_path=tmp_root / "summary.json",
            report_path=tmp_root / "report.md",
            search_log_path=tmp_root / "search_log.jsonl",
        )

    summary = _transform_summary(raw_summary, prereg_path, source_import_path, raw_quote_path, search_log_path)
    _write_json(summary_path, summary)
    report_path.write_text(_render_report(summary), encoding="utf-8")
    _write_search_log(summary, search_log_path)
    return summary


def _run_base_replay(
    prereg_path: Path,
    source_import_path: Path,
    raw_quote_path: Path,
    summary_path: Path,
    report_path: Path,
    search_log_path: Path,
) -> dict[str, Any]:
    old_values = {
        "CANDIDATE_DATE": base.CANDIDATE_DATE,
        "CANDIDATE_DIRECTION": base.CANDIDATE_DIRECTION,
        "DEFAULT_PREREG_PATH": base.DEFAULT_PREREG_PATH,
        "DEFAULT_SOURCE_IMPORT_PATH": base.DEFAULT_SOURCE_IMPORT_PATH,
        "DEFAULT_RAW_QUOTE_PATH": base.DEFAULT_RAW_QUOTE_PATH,
        "validate": base.validate_h_a2_normal_control_exact_replay_preregistration,
    }
    try:
        base.CANDIDATE_DATE = CANDIDATE_DATE
        base.CANDIDATE_DIRECTION = CANDIDATE_DIRECTION
        base.DEFAULT_PREREG_PATH = prereg_path
        base.DEFAULT_SOURCE_IMPORT_PATH = source_import_path
        base.DEFAULT_RAW_QUOTE_PATH = raw_quote_path
        base.validate_h_a2_normal_control_exact_replay_preregistration = (
            validate_h_a2_post_stress_normalization_control_exact_replay_preregistration
        )
        return base.run_h_a2_normal_control_exact_replay(
            prereg_path=prereg_path,
            source_import_path=source_import_path,
            raw_quote_path=raw_quote_path,
            summary_path=summary_path,
            report_path=report_path,
            search_log_path=search_log_path,
        )
    finally:
        base.CANDIDATE_DATE = old_values["CANDIDATE_DATE"]
        base.CANDIDATE_DIRECTION = old_values["CANDIDATE_DIRECTION"]
        base.DEFAULT_PREREG_PATH = old_values["DEFAULT_PREREG_PATH"]
        base.DEFAULT_SOURCE_IMPORT_PATH = old_values["DEFAULT_SOURCE_IMPORT_PATH"]
        base.DEFAULT_RAW_QUOTE_PATH = old_values["DEFAULT_RAW_QUOTE_PATH"]
        base.validate_h_a2_normal_control_exact_replay_preregistration = old_values["validate"]


def _transform_summary(
    raw: dict[str, Any],
    prereg_path: Path,
    source_import_path: Path,
    raw_quote_path: Path,
    search_log_path: Path,
) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    summary = dict(raw)
    summary.update(
        {
            "schema_version": "h_a2_post_stress_normalization_control_exact_replay_v1",
            "experiment_id": "h_a2_post_stress_normalization_control_exact_replay",
            "generated_at_utc": generated_at,
            "source_preregistration": _relative(prereg_path),
            "source_import_diagnostic": _relative(source_import_path),
            "source_raw_quote_file": _relative(raw_quote_path),
            "conclusion_reason": (
                "This is a single-candidate post-stress normalization/control exact replay. It can report "
                "candidate-date PnL, but one trade is under-sampled and cannot validate H-A2."
            ),
            "research_log_slug": "higanbana-h-a2-post-stress-normalization-control-exact-replay",
            "research_log_path": "research_log/038-higanbana-h-a2-post-stress-normalization-control-exact-replay.md",
            "allowed_claims": [
                "The single post-stress normalization/control candidate date can be exact-replayed locally.",
                "The run reports mid_pnl and implementable_pnl separately for 2025-05-05 only.",
                "The result is E1 single-candidate diagnostic evidence only.",
            ],
            "forbidden_claims": [
                "Do not claim H-A2 edge is validated.",
                "Do not claim E2 acceptance-grade evidence.",
                "Do not approve paper trading.",
                "Do not approve operational validation.",
                "Do not approve real-money trading.",
                "Do not broaden the replay beyond 2025-05-05.",
                "Do not change threshold 0.001.",
                "Do not add a new OOS-selected filter.",
            ],
            "next_safe_action": (
                "Treat H-A2.57 as E1 single-candidate diagnostic evidence only. "
                "Use it with the previous normal/control exact replay to decide the next pre-registered "
                "sample-expansion or hypothesis-revision step; do not claim E2 or paper-trading readiness."
            ),
        }
    )
    summary["candidate"]["date"] = CANDIDATE_DATE
    summary["candidate"]["direction"] = CANDIDATE_DIRECTION
    summary["trial_policy"]["search_log"] = _relative(search_log_path)
    return summary


def _write_search_log(summary: dict[str, Any], path: Path) -> None:
    record = {
        "record_type": "h_a2_post_stress_normalization_control_exact_replay_trial",
        "experiment_id": summary["experiment_id"],
        "date": CANDIDATE_DATE,
        "direction": CANDIDATE_DIRECTION,
        "target_gap": summary["methodology"]["target_gap"],
        "width": summary["methodology"]["width"],
        "mapping_method": "nearest_discrete_strike_rounding",
        "threshold_search_used": False,
        "new_filter_search_used": False,
        "oos_tuning_used": False,
        "status": summary["status"],
        "blockers": summary["blockers"],
        "pnl": summary["pnl"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _render_report(summary: dict[str, Any]) -> str:
    selected = summary.get("selected_vertical") or {}
    pnl = summary.get("pnl") or {}
    lines = [
        "# H-A2 Post-Stress Normalization/Control Exact Replay",
        "",
        f"- Status: `{summary['status']}`",
        f"- Conclusion: `{summary['conclusion']}`",
        f"- Evidence tier: `{summary['evidence_tier']}`",
        f"- Candidate date: `{CANDIDATE_DATE}`",
        f"- Direction: `{CANDIDATE_DIRECTION}`",
        f"- Entry: `{summary['candidate']['entry_time_et']} ET`",
        f"- Forced close: `{summary['candidate']['forced_close_time_et']} ET`",
        "",
        "## Candidate And Strike Mapping",
        "",
        f"- Underlying at entry: `{summary['candidate']['underlying_entry_close']}`",
        f"- Underlying at forced close: `{summary['candidate']['underlying_forced_close']}`",
        f"- Target gap: `{summary['methodology']['target_gap']}`",
        f"- Width: `{summary['methodology']['width']}`",
        f"- Mapping method: `nearest_discrete_strike_rounding`",
    ]
    if selected:
        mapping = selected["mapping"]
        lines.extend(
            [
                f"- Long strike: `{mapping['long_strike']}`",
                f"- Short strike: `{mapping['short_strike']}`",
                f"- Realized long gap: `{mapping['realized_long_gap']}`",
                "",
                "## Legs",
                "",
                "| Side | Strike | Entry bid | Entry ask | Entry mid | Forced bid | Forced ask | Forced mid |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for leg in selected["legs"]:
            lines.append(
                f"| `{leg['side']}` | `{leg['strike']}` | `{leg['entry_bid']}` | `{leg['entry_ask']}` | "
                f"`{leg['entry_mid']}` | `{leg['forced_close_bid']}` | `{leg['forced_close_ask']}` | "
                f"`{leg['forced_close_mid']}` |"
            )
    if pnl:
        lines.extend(
            [
                "",
                "## PnL",
                "",
                "| Metric | Value |",
                "|---|---:|",
                f"| Entry mid debit | `{pnl['entry_mid_debit']}` |",
                f"| Forced-close mid value | `{pnl['forced_close_mid_value']}` |",
                f"| Mid PnL | `{pnl['mid_pnl']}` |",
                f"| Entry implementable debit | `{pnl['entry_implementable_debit']}` |",
                f"| Forced-close implementable credit | `{pnl['forced_close_implementable_credit']}` |",
                f"| Gross implementable PnL before fees | `{pnl['gross_implementable_pnl_before_fees']}` |",
                f"| Total fees | `{pnl['total_fees']}` |",
                f"| Implementable PnL | `{pnl['implementable_pnl']}` |",
                f"| Cost drag vs mid | `{pnl['cost_drag_vs_mid']}` |",
            ]
        )
    if summary["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{item}`" for item in summary["blockers"])
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Used only the already-downloaded post-stress normalization/control candidate-date DBN file.",
            "- Did not download data, call IBKR, call LLMs, retry GDELT, or broaden beyond `2025-05-05`.",
            "- This is E1 single-candidate diagnostic evidence only, not E2 acceptance evidence.",
            "- Paper trading, operational validation, and real-money trading remain forbidden.",
            "",
            "## Next Safe Action",
            "",
            summary["next_safe_action"],
            "",
        ]
    )
    return "\n".join(lines)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run H-A2 post-stress normalization/control bounded exact replay."
    )
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--search-log-path", type=Path, default=DEFAULT_SEARCH_LOG_PATH)
    args = parser.parse_args(argv)
    result = run_h_a2_post_stress_normalization_control_exact_replay(
        summary_path=args.summary_path,
        report_path=args.report_path,
        search_log_path=args.search_log_path,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
