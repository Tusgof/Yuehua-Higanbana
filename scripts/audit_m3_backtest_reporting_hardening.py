from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PNL_SUMMARY = PROJECT_ROOT / "reports" / "pilots" / "dec_2024_daily_union_pilot_pnl_m3_summary.json"
DEFAULT_PNL_REPORT = PROJECT_ROOT / "reports" / "pilots" / "dec_2024_daily_union_pilot_pnl_m3_report.md"
DEFAULT_SENSITIVITY_SUMMARY = PROJECT_ROOT / "reports" / "pilots" / "jan_2024_pilot_sensitivity_summary.json"
DEFAULT_SENSITIVITY_REPORT = PROJECT_ROOT / "reports" / "pilots" / "jan_2024_pilot_sensitivity_report.md"
DEFAULT_SEARCH_LOG = PROJECT_ROOT / "reports" / "experiments" / "search_logs" / "jan_2024_pilot_sensitivity_search_log.jsonl"
DEFAULT_GUARDRAIL_AUDIT = PROJECT_ROOT / "reports" / "m3_experiment_guardrails_audit.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "m3_backtest_reporting_hardening_audit.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "m3_backtest_reporting_hardening_audit.md"


def audit_hardening(
    pnl_summary_path: Path = DEFAULT_PNL_SUMMARY,
    pnl_report_path: Path = DEFAULT_PNL_REPORT,
    sensitivity_summary_path: Path = DEFAULT_SENSITIVITY_SUMMARY,
    sensitivity_report_path: Path = DEFAULT_SENSITIVITY_REPORT,
    search_log_path: Path = DEFAULT_SEARCH_LOG,
    guardrail_audit_path: Path = DEFAULT_GUARDRAIL_AUDIT,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    pnl_summary = _load_json_or_block(pnl_summary_path, "pnl_summary", blockers)
    pnl_report = _load_text_or_block(pnl_report_path, "pnl_report", blockers)
    sensitivity_summary = _load_json_or_block(sensitivity_summary_path, "sensitivity_summary", blockers)
    sensitivity_report = _load_text_or_block(sensitivity_report_path, "sensitivity_report", blockers)
    search_records = _load_jsonl_or_block(search_log_path, "search_log", blockers)
    guardrail_audit = _load_json_or_block(guardrail_audit_path, "guardrail_audit", blockers)

    if isinstance(pnl_summary, dict):
        checks.append(_check_pnl_model(pnl_summary))
        checks.append(_check_sample_adequacy(pnl_summary))
        checks.append(_check_big_day_dependency(pnl_summary))
    if isinstance(pnl_report, str):
        checks.append(
            _check_report_terms(
                "pnl_report",
                pnl_report,
                [["implementable_pnl"], ["mid_pnl"], ["cost drag", "total_cost_drag"], ["under-sampled"], ["underpowered"], ["big-day", "big-day dependency"]],
            )
        )
    if isinstance(sensitivity_summary, dict):
        checks.append(_check_search_summary(sensitivity_summary))
        checks.append(_check_dsr_blocker(sensitivity_summary))
    if isinstance(sensitivity_report, str):
        checks.append(_check_report_terms("sensitivity_report", sensitivity_report, [["search log"], ["dsr"], ["trial"], ["parameter", "scenario"]]))
    if isinstance(search_records, list) and isinstance(sensitivity_summary, dict):
        checks.append(_check_search_log_records(search_records, sensitivity_summary))
    if isinstance(guardrail_audit, dict):
        checks.append(_check_guardrail_audit(guardrail_audit))

    for check in checks:
        blockers.extend(check["blockers"])

    return {
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "checks": checks,
        "inputs": {
            "pnl_summary": str(pnl_summary_path),
            "pnl_report": str(pnl_report_path),
            "sensitivity_summary": str(sensitivity_summary_path),
            "sensitivity_report": str(sensitivity_report_path),
            "search_log": str(search_log_path),
            "guardrail_audit": str(guardrail_audit_path),
        },
    }


def write_reports(
    result: dict[str, Any],
    json_output: Path = DEFAULT_JSON_OUTPUT,
    report_output: Path = DEFAULT_REPORT_OUTPUT,
) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# M3 Backtest Reporting Hardening Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Blocker count: {len(result['blockers'])}",
        "",
        "## Checks",
        "",
        "| Check | Status | Blockers |",
        "|:--|:--:|:--|",
    ]
    for check in result["checks"]:
        blockers = ", ".join(f"`{blocker}`" for blocker in check["blockers"]) if check["blockers"] else "None"
        lines.append(f"| `{check['name']}` | `{check['status']}` | {blockers} |")
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- `{blocker}`" for blocker in result["blockers"]) if result["blockers"] else lines.append("- None")
    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _check_pnl_model(summary: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    for key in ("total_mid_pnl", "total_implementable_pnl", "total_cost_drag", "fee_per_contract", "fill_model", "pnl_model"):
        if key not in summary:
            blockers.append(f"pnl_model.missing:{key}")
    pnl_model = summary.get("pnl_model", {})
    if isinstance(pnl_model, dict):
        for key in ("mid_pnl", "implementable_pnl"):
            if key not in pnl_model:
                blockers.append(f"pnl_model.description_missing:{key}")
    else:
        blockers.append("pnl_model.not_object")
    return _check("pnl_model", blockers)


def _check_sample_adequacy(summary: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    adequacy = summary.get("sample_adequacy")
    if not isinstance(adequacy, dict):
        blockers.append("sample_adequacy.missing")
    else:
        labels = set(adequacy.get("labels") or [])
        for label in ("under-sampled", "underpowered"):
            if label not in labels:
                blockers.append(f"sample_adequacy.label_missing:{label}")
        for key in ("closed_trades", "mintrl_status", "psr_status", "power_note"):
            if key not in adequacy:
                blockers.append(f"sample_adequacy.missing:{key}")
    return _check("sample_adequacy", blockers)


def _check_big_day_dependency(summary: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    dependency = summary.get("big_day_dependency")
    if not isinstance(dependency, dict):
        blockers.append("big_day_dependency.missing")
    else:
        for key in ("method", "original_closed_trades", "removed_trade_count", "retained_closed_trades", "retained_total_implementable_pnl", "status"):
            if key not in dependency:
                blockers.append(f"big_day_dependency.missing:{key}")
        if "implementable_pnl" not in str(dependency.get("method", "")):
            blockers.append("big_day_dependency.method_not_implementable_pnl_based")
    return _check("big_day_dependency", blockers)


def _check_search_summary(summary: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    for key in ("search_log", "parameter_grid", "selection_rule", "scenario_count", "scenarios"):
        if key not in summary:
            blockers.append(f"search_summary.missing:{key}")
    search_log = summary.get("search_log", {})
    if isinstance(search_log, dict):
        if search_log.get("all_trials_recorded") is not True:
            blockers.append("search_summary.all_trials_recorded_not_true")
        if not isinstance(search_log.get("trial_count"), int):
            blockers.append("search_summary.trial_count_missing")
    else:
        blockers.append("search_summary.search_log_not_object")
    if summary.get("selection_rule", {}).get("acceptance_use") != "diagnostic_only_not_oos_tuning":
        blockers.append("search_summary.selection_rule_not_diagnostic_only")
    return _check("search_summary", blockers)


def _check_dsr_blocker(summary: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    dsr = summary.get("dsr_assessment")
    if not isinstance(dsr, dict):
        blockers.append("dsr_assessment.missing")
    else:
        if dsr.get("status") != "blocked":
            blockers.append(f"dsr_assessment.unexpected_status:{dsr.get('status')}")
        for key in ("reason", "trial_count", "required_before_acceptance"):
            if key not in dsr:
                blockers.append(f"dsr_assessment.missing:{key}")
    return _check("dsr_assessment", blockers)


def _check_search_log_records(records: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    trial_count = summary.get("search_log", {}).get("trial_count")
    if len(records) != trial_count:
        blockers.append(f"search_log.line_count_mismatch:{len(records)}!={trial_count}")
    seen_trial_indexes: set[int] = set()
    for index, record in enumerate(records, start=1):
        if record.get("record_type") != "parameter_search_trial":
            blockers.append(f"search_log.record_{index}.wrong_record_type")
        if not isinstance(record.get("parameters"), dict):
            blockers.append(f"search_log.record_{index}.missing_parameters")
        if not isinstance(record.get("metrics"), dict):
            blockers.append(f"search_log.record_{index}.missing_metrics")
        if isinstance(record.get("trial_index"), int):
            seen_trial_indexes.add(record["trial_index"])
        else:
            blockers.append(f"search_log.record_{index}.missing_trial_index")
    if isinstance(trial_count, int) and seen_trial_indexes != set(range(1, trial_count + 1)):
        blockers.append("search_log.non_contiguous_trial_indexes")
    return _check("search_log_records", blockers)


def _check_guardrail_audit(audit: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if audit.get("status") != "pass":
        blockers.append(f"guardrail_audit.unexpected_status:{audit.get('status')}")
    if audit.get("blockers"):
        blockers.append("guardrail_audit.has_blockers")
    if audit.get("experiment_count") != 10:
        blockers.append(f"guardrail_audit.unexpected_experiment_count:{audit.get('experiment_count')}")
    return _check("guardrail_audit", blockers)


def _check_report_terms(name: str, text: str, term_groups: list[list[str]]) -> dict[str, Any]:
    lowered = text.lower()
    blockers = []
    for terms in term_groups:
        if not any(term.lower() in lowered for term in terms):
            blockers.append(f"{name}.missing_term:{'/'.join(terms)}")
    return _check(name, blockers)


def _check(name: str, blockers: list[str]) -> dict[str, Any]:
    return {"name": name, "status": "blocked" if blockers else "pass", "blockers": blockers}


def _load_json_or_block(path: Path, name: str, blockers: list[str]) -> Any:
    if not path.exists():
        blockers.append(f"{name}.missing_file:{path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        blockers.append(f"{name}.invalid_json:{exc.lineno}")
        return None


def _load_jsonl_or_block(path: Path, name: str, blockers: list[str]) -> list[dict[str, Any]] | None:
    if not path.exists():
        blockers.append(f"{name}.missing_file:{path}")
        return None
    records: list[dict[str, Any]] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            blockers.append(f"{name}.invalid_jsonl_line:{index}")
            continue
        if isinstance(record, dict):
            records.append(record)
        else:
            blockers.append(f"{name}.non_object_line:{index}")
    return records


def _load_text_or_block(path: Path, name: str, blockers: list[str]) -> str | None:
    if not path.exists():
        blockers.append(f"{name}.missing_file:{path}")
        return None
    return path.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit M3 backtest/reporting hardening closure artifacts.")
    parser.add_argument("--pnl-summary-path", type=Path, default=DEFAULT_PNL_SUMMARY)
    parser.add_argument("--pnl-report-path", type=Path, default=DEFAULT_PNL_REPORT)
    parser.add_argument("--sensitivity-summary-path", type=Path, default=DEFAULT_SENSITIVITY_SUMMARY)
    parser.add_argument("--sensitivity-report-path", type=Path, default=DEFAULT_SENSITIVITY_REPORT)
    parser.add_argument("--search-log-path", type=Path, default=DEFAULT_SEARCH_LOG)
    parser.add_argument("--guardrail-audit-path", type=Path, default=DEFAULT_GUARDRAIL_AUDIT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)
    result = audit_hardening(
        args.pnl_summary_path,
        args.pnl_report_path,
        args.sensitivity_summary_path,
        args.sensitivity_report_path,
        args.search_log_path,
        args.guardrail_audit_path,
    )
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
