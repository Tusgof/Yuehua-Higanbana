from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "research_readiness_audit.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "research_readiness_audit.md"
GREEKS_OI_ENRICHMENT_REPORT = PROJECT_ROOT / "reports" / "greeks_oi_enrichment_probe_summary.json"
GAMMA_AGGREGATION_POLICY_DOC = PROJECT_ROOT / "docs" / "GAMMA_AGGREGATION_VALIDATION_POLICY.md"
GAMMA_AGGREGATION_DIAGNOSTIC_SUMMARY = PROJECT_ROOT / "reports" / "diagnostics" / "gamma_aggregation_diagnostic_summary.json"
DATABENTO_API_KEY_ENVS = ("DATABENTO_API_KEY", "DATABENTO_SPY0DTE_API")

REPORT_PATHS = {
    "macro_calendar": PROJECT_ROOT / "reports" / "macro_calendar_coverage_audit.json",
    "vix_vxv": PROJECT_ROOT / "reports" / "vix_vxv_coverage_audit.json",
    "news": PROJECT_ROOT / "reports" / "news_coverage_audit.json",
    "gdelt_capture_status": PROJECT_ROOT / "reports" / "news_gdelt_capture_status",
    "gdelt_command_plan": PROJECT_ROOT / "reports" / "news_gdelt_capture_command_plan.json",
    "paid_cost": PROJECT_ROOT / "reports" / "data_cost" / "paid_cost_audit.json",
    "research_logs": PROJECT_ROOT / "reports" / "research_log_audit.json",
    "strategy_data": PROJECT_ROOT / "reports" / "strategy_data_readiness_audit.json",
    "exp07_prompt_redesign": PROJECT_ROOT / "docs" / "EXP07_PROMPT_REDESIGN.md",
    "exp07_real_news_case_plan": PROJECT_ROOT / "reports" / "experiments" / "exp07_real_news_case_plan.json",
    "exp07_acceptance": PROJECT_ROOT / "reports" / "experiments" / "exp07_acceptance_evaluation.json",
    "exp07_strategy_ablation": PROJECT_ROOT / "reports" / "experiments" / "exp07_strategy_ablation_status.json",
    "aug_2023_databento_dry_run": PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "databento_cost_insample_2023_08_intraday_exit_30m_dryrun.json",
    "opra_statistics_oi_probe": PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "databento_opra_statistics_oi_probe_2024_01_03_schema.json",
    "opra_statistics_oi_download_probe": PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "databento_opra_statistics_oi_download_probe_2024_01_03.json",
}


def audit_research_readiness(
    report_paths: dict[str, Path] | None = None,
    process_env: dict[str, str] | None = None,
    user_env_getter: Callable[[str], str | None] | None = None,
    machine_env_getter: Callable[[str], str | None] | None = None,
) -> dict[str, Any]:
    paths = report_paths or REPORT_PATHS
    env = process_env if process_env is not None else os.environ
    get_user_env = user_env_getter or _get_user_env
    get_machine_env = machine_env_getter or _get_machine_env

    environment = {
        name: _env_status(name, env, get_user_env, get_machine_env)
        for name in DATABENTO_API_KEY_ENVS
    }
    environment.update({
        "HIGANBANA_OPENROUTER_API": _env_status("HIGANBANA_OPENROUTER_API", env, get_user_env, get_machine_env),
    })
    reports = {name: _load_report_artifact(path) for name, path in paths.items()}
    checks = _build_checks(reports, environment, paths)
    blockers = sorted({_normalize_blocker(blocker) for check in checks for blocker in check["blockers"]})

    return {
        "status": "blocked" if blockers else "ready",
        "blockers": blockers,
        "environment": environment,
        "checks": checks,
        "next_safe_actions": _next_safe_actions(blockers),
    }


def write_reports(result: dict[str, Any], json_output: Path = DEFAULT_JSON_OUTPUT, report_output: Path = DEFAULT_REPORT_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Research Readiness Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Blocker count: {len(result['blockers'])}",
        "",
        "## Environment",
        "",
        "| Variable | Process env | User env | Machine env |",
        "|:--|:--:|:--:|:--:|",
    ]
    for name, status in result["environment"].items():
        lines.append(f"| `{name}` | {status['process']} | {status['user']} | {status['machine']} |")

    lines.extend(["", "## Checks", "", "| Check | Status | Details | Blockers |", "|:--|:--|:--|:--|"])
    for check in result["checks"]:
        blockers = ", ".join(f"`{blocker}`" for blocker in check["blockers"]) or "-"
        details = _check_details(check)
        lines.append(f"| {check['name']} | `{check['status']}` | {details} | {blockers} |")

    lines.extend(["", "## Next Safe Actions", ""])
    for action in result["next_safe_actions"]:
        lines.append(f"- {action}")

    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _check_details(check: dict[str, Any]) -> str:
    details = []
    if "known_committed_estimated_cost_usd" in check:
        details.append(f"known cost `${check['known_committed_estimated_cost_usd']}`")
    if "cost_guard_used_usd" in check:
        details.append(f"guard used `${check['cost_guard_used_usd']}`")
    if "cost_guard_basis" in check:
        details.append(f"basis `{check['cost_guard_basis']}`")
    if "remaining_before_stop_usd" in check:
        details.append(f"remaining `${check['remaining_before_stop_usd']}`")
    if "closed_trades" in check:
        details.append(f"closed trades `{check['closed_trades']}`")
    if "candidate_days" in check:
        details.append(f"candidate days `{check['candidate_days']}`")
    if "request_count" in check:
        details.append(f"requests `{check['request_count']}`")
    if "full_day_record_count" in check:
        details.append(f"full-day records `{check['full_day_record_count']}`")
    if "intraday_record_count" in check:
        details.append(f"intraday records `{check['intraday_record_count']}`")
    if "open_interest_record_count" in check:
        details.append(f"open interest records `{check['open_interest_record_count']}`")
    if "file_count" in check:
        details.append(f"files `{check['file_count']}`")
    if "retry_pressure_status" in check:
        details.append(f"retry pressure `{check['retry_pressure_status']}`")
    if "next_unattempted_trade_date" in check and check["next_unattempted_trade_date"]:
        details.append(f"next retry `{check['next_unattempted_trade_date']}`")
    status_counts = check.get("status_counts")
    if isinstance(status_counts, dict) and status_counts:
        rendered_counts = ", ".join(f"{name}={count}" for name, count in sorted(status_counts.items()))
        details.append(f"status counts `{rendered_counts}`")
    return "<br>".join(details) if details else "-"


def _build_checks(reports: dict[str, dict[str, Any] | None], environment: dict[str, dict[str, bool]], paths: dict[str, Path]) -> list[dict[str, Any]]:
    checks = [
        _report_check("macro_calendar", reports["macro_calendar"], paths["macro_calendar"], "requires_macro_calendar_audit_report"),
        _report_check("vix_vxv", reports["vix_vxv"], paths["vix_vxv"], "requires_vix_vxv_audit_report"),
        _report_check("news", reports["news"], paths["news"], "requires_news_coverage_audit_report"),
        _gdelt_capture_status_check(reports["gdelt_capture_status"], paths["gdelt_capture_status"]),
        _gdelt_command_plan_check(reports["gdelt_command_plan"], paths["gdelt_command_plan"]),
        _paid_cost_check(reports["paid_cost"], paths["paid_cost"]),
        _report_check("research_logs", reports["research_logs"], paths["research_logs"], "requires_research_log_audit_report"),
        _strategy_data_check(reports["strategy_data"], paths["strategy_data"]),
        _exp07_prompt_redesign_check(
            reports.get("exp07_prompt_redesign") or _load_report_artifact(REPORT_PATHS["exp07_prompt_redesign"]),
            paths.get("exp07_prompt_redesign", REPORT_PATHS["exp07_prompt_redesign"]),
            reports["news"],
        ),
        _exp07_real_news_case_plan_check(
            reports.get("exp07_real_news_case_plan"),
            paths.get("exp07_real_news_case_plan", REPORT_PATHS["exp07_real_news_case_plan"]),
        ),
        _exp07_acceptance_check(reports["exp07_acceptance"], paths["exp07_acceptance"]),
        _exp07_ablation_check(reports["exp07_strategy_ablation"], paths["exp07_strategy_ablation"]),
        _databento_aug_2023_check(reports["aug_2023_databento_dry_run"], paths["aug_2023_databento_dry_run"], environment),
        _opra_statistics_oi_probe_check(
            reports.get("opra_statistics_oi_probe"),
            paths.get("opra_statistics_oi_probe", REPORT_PATHS["opra_statistics_oi_probe"]),
            reports.get("opra_statistics_oi_download_probe"),
            paths.get("opra_statistics_oi_download_probe", REPORT_PATHS["opra_statistics_oi_download_probe"]),
        ),
        _openrouter_check(environment),
    ]
    return checks


def _report_check(name: str, report: dict[str, Any] | None, path: Path, missing_blocker: str) -> dict[str, Any]:
    if report is None:
        return {"name": name, "status": "blocked", "source": str(path), "blockers": [missing_blocker]}
    blockers = list(report.get("blockers", []))
    status = "pass" if report.get("status") == "pass" and not blockers else "blocked"
    return {"name": name, "status": status, "source": str(path), "blockers": blockers}


def _gdelt_capture_status_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "gdelt_capture_status",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_gdelt_capture_status_report"],
        }
    blockers = list(report.get("blockers", []))
    status = "pass" if report.get("status") == "pass" and not blockers else "blocked"
    return {
        "name": "gdelt_capture_status",
        "status": status,
        "source": str(path),
        "status_counts": report.get("status_counts", {}),
        "file_count": report.get("file_count", 0),
        "blockers": blockers,
    }


def _gdelt_command_plan_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "gdelt_command_plan",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_gdelt_command_plan_report"],
        }
    retry_pressure = report.get("retry_pressure", {})
    retry_queue_summary = report.get("retry_queue_summary", {})
    pressure_status = str(retry_pressure.get("status", "unknown"))
    blockers = []
    if pressure_status == "cooldown_recommended":
        blockers.append("gdelt_retry_cooldown_recommended")
    elif pressure_status not in {"normal_retry", "unknown"}:
        blockers.append(f"gdelt_retry_pressure:{pressure_status}")
    return {
        "name": "gdelt_command_plan",
        "status": "pass" if not blockers else "blocked",
        "source": str(path),
        "retry_pressure_status": pressure_status,
        "next_unattempted_trade_date": retry_queue_summary.get("next_unattempted_trade_date"),
        "not_attempted_count": retry_queue_summary.get("not_attempted_count"),
        "blockers": blockers,
    }


def _paid_cost_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "paid_cost",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_paid_cost_audit_report"],
        }
    blockers = list(report.get("blockers", []))
    status = "pass" if report.get("status") == "pass" and not blockers else "blocked"
    return {
        "name": "paid_cost",
        "status": status,
        "source": str(path),
        "known_committed_estimated_cost_usd": report.get("known_committed_estimated_cost_usd"),
        "user_reported_actual_usage": report.get("user_reported_actual_usage"),
        "cost_guard_basis": report.get("cost_guard_basis"),
        "cost_guard_used_usd": report.get("cost_guard_used_usd"),
        "remaining_before_stop_usd": report.get("remaining_before_stop_usd"),
        "blockers": blockers,
    }


def _strategy_data_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "strategy_data",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_strategy_data_readiness_audit_report"],
        }
    blockers = [_normalize_blocker(blocker) for blocker in report.get("blockers", [])]
    status = "pass" if report.get("status") == "pass" and not blockers else "blocked"
    return {
        "name": "strategy_data",
        "status": status,
        "source": str(path),
        "closed_trades": report.get("totals", {}).get("closed_trades"),
        "candidate_days": report.get("totals", {}).get("candidate_days"),
        "blockers": blockers,
    }


def _opra_statistics_oi_probe_check(
    report: dict[str, Any] | None,
    path: Path,
    download_report: dict[str, Any] | None,
    download_path: Path,
) -> dict[str, Any]:
    if report is None:
        return {
            "name": "opra_statistics_oi_probe",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_opra_statistics_oi_probe_report"],
        }

    checks = {
        item.get("label"): item.get("record_count")
        for item in report.get("record_count_checks", [])
        if isinstance(item, dict)
    }
    blockers: list[str] = []
    full_day_records = int(checks.get("full_utc_day") or 0)
    intraday_records = int(checks.get("intraday_research_window") or 0)
    if report.get("status") not in {"pass", "pass_with_timing_caveat"}:
        blockers.append("requires_opra_statistics_oi_probe_pass")
    if not report.get("has_stat_type_field"):
        blockers.append("requires_opra_statistics_stat_type_field")
    if full_day_records <= 0:
        blockers.append("requires_opra_statistics_full_day_records")
    if report.get("status") == "pass_with_timing_caveat" and full_day_records > 0 and intraday_records == 0:
        if download_report is None:
            blockers.append("requires_controlled_opra_statistics_download_import_probe")

    open_interest_record_count = None
    if download_report is not None:
        inspection = download_report.get("inspection", {})
        open_interest_record_count = inspection.get("open_interest_record_count") if isinstance(inspection, dict) else None
        if download_report.get("status") != "pass":
            blockers.append("requires_opra_statistics_download_probe_pass")
        if not isinstance(open_interest_record_count, int) or open_interest_record_count <= 0:
            blockers.append("requires_opra_statistics_open_interest_records")

    return {
        "name": "opra_statistics_oi_probe",
        "status": "pass" if not blockers else "blocked",
        "source": f"{path}; {download_path}",
        "full_day_record_count": full_day_records,
        "intraday_record_count": intraday_records,
        "open_interest_record_count": open_interest_record_count,
        "blockers": blockers,
    }


def _exp07_prompt_redesign_check(report: dict[str, Any] | None, path: Path, news_report: dict[str, Any] | None) -> dict[str, Any]:
    blockers = []
    if report is None:
        blockers.append("requires_exp07_prompt_redesign_doc")
    elif "real timestamp-clean news" not in str(report.get("text", "")).lower():
        blockers.append("requires_exp07_real_news_prompt_design")

    news_blockers = [] if news_report is None else list(news_report.get("blockers", []))
    if news_report is None or "requires_real_news_archive" in news_blockers:
        blockers.append("requires_real_timestamp_clean_news_cases_for_exp07_prompt_research")

    return {
        "name": "exp07_prompt_redesign",
        "status": "ready_for_real_news_prompt_design" if not blockers else "blocked",
        "source": str(path),
        "blockers": blockers,
        "note": "Synthetic/policy prompt matrices are infrastructure-only and must not be counted as Exp07 research evidence.",
    }


def _exp07_real_news_case_plan_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "exp07_real_news_case_plan",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_exp07_real_news_case_plan"],
        }
    blockers = list(report.get("blockers", []))
    return {
        "name": "exp07_real_news_case_plan",
        "status": "ready_for_prompt_family_pre_experiment" if report.get("status") == "ready_for_prompt_family_pre_experiment" and not blockers else "blocked",
        "source": str(path),
        "candidate_days": report.get("candidate_day_count"),
        "captured_candidate_days": report.get("captured_candidate_count"),
        "blockers": blockers,
    }


def _exp07_acceptance_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "exp07_acceptance",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_exp07_acceptance_report"],
        }
    blockers = list(report.get("strategy_integration_blockers", []))
    status = "pass" if report.get("strategy_integration_status") == "pass" and not blockers else "blocked"
    return {"name": "exp07_acceptance", "status": status, "source": str(path), "blockers": blockers}


def _exp07_ablation_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "exp07_strategy_ablation",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_exp07_strategy_ablation_status_report"],
        }
    blockers = [_normalize_blocker(blocker) for blocker in report.get("blockers", [])]
    status = "ready" if report.get("status") == "ready" and not blockers else "blocked"
    return {"name": "exp07_strategy_ablation", "status": status, "source": str(path), "blockers": blockers}


def _databento_aug_2023_check(
    report: dict[str, Any] | None,
    path: Path,
    environment: dict[str, dict[str, bool]],
) -> dict[str, Any]:
    blockers = []
    if report is None:
        blockers.append("requires_aug_2023_databento_dry_run_plan")
    if not _has_any_databento_env(environment):
        blockers.append("requires_databento_api_key_for_aug_2023_live_cost")
    return {
        "name": "aug_2023_databento",
        "status": "blocked" if blockers else "ready_for_live_cost_estimate",
        "source": str(path),
        "request_count": _databento_request_count(report),
        "blockers": blockers,
    }


def _openrouter_check(environment: dict[str, dict[str, bool]]) -> dict[str, Any]:
    status = environment["HIGANBANA_OPENROUTER_API"]
    blockers = []
    if not _has_any_env_scope(status):
        blockers.append("requires_openrouter_api_key_for_live_llm_experiments")
    return {
        "name": "openrouter_llm",
        "status": "available" if not blockers else "blocked",
        "blockers": blockers,
        "note": "Only use for guarded smoke tests or approved prompt experiments.",
    }


def _databento_request_count(report: dict[str, Any] | None) -> int | None:
    if report is None:
        return None
    if isinstance(report.get("request_count"), int):
        return report["request_count"]
    if isinstance(report.get("total_request_count"), int):
        return report["total_request_count"]
    requests = report.get("requests")
    if isinstance(requests, list):
        return len(requests)
    return None


def _next_safe_actions(blockers: list[str]) -> list[str]:
    actions = []
    if "requires_databento_api_key_for_aug_2023_live_cost" in blockers:
        actions.append("Configure `DATABENTO_API_KEY` or `DATABENTO_SPY0DTE_API`, then run the Aug 2023 chunked live cost estimate before any download.")
    gdelt_cooldown = "gdelt_retry_cooldown_recommended" in blockers
    if gdelt_cooldown:
        actions.append("Pause additional live GDELT `--execute` retries until HTTP 429 pressure clears; monitor the command plan before retrying one candidate day.")
    if not gdelt_cooldown and ("requires_real_news_archive" in blockers or "requires_news_coverage_audit_report" in blockers):
        actions.append("Retry timestamp-safe GDELT capture after HTTP 429 pressure clears, then import and audit the real news archive.")
    if "requires_real_timestamp_clean_news_cases_for_exp07_prompt_research" in blockers:
        actions.append("Do not run another synthetic Exp07 prompt matrix as research; build real timestamp-clean news cases first.")
    if "requires_real_timestamp_clean_news_cases" in blockers:
        actions.append("Use `reports\\experiments\\exp07_real_news_case_plan.md` as the collection plan before any Exp07 prompt-family run.")
    if "requires_controlled_opra_statistics_download_import_probe" in blockers:
        actions.append("OPRA statistics/OI metadata probe passed with timing caveat; next run a controlled one-day full-day statistics download/import probe, inspect `stat_type` values and timestamp semantics, then decide whether Databento OI can support gamma-family research.")
    if "requires_mintrl_psr_sample_adequacy" in blockers or "requires_wider_spy_0dte_data" in blockers:
        if GREEKS_OI_ENRICHMENT_REPORT.exists() and GAMMA_AGGREGATION_POLICY_DOC.exists() and GAMMA_AGGREGATION_DIAGNOSTIC_SUMMARY.exists():
            actions.append("Before any further broad Databento download, use `reports\\risk_first_data_audit.md`, `reports\\greeks_oi_enrichment_probe_report.md`, `docs\\GAMMA_AGGREGATION_VALIDATION_POLICY.md`, and `reports\\diagnostics\\gamma_aggregation_diagnostic_summary.json` as the pre-purchase checkpoint: expand the pre-registered H-G1 gamma/OI regime date set, choose missing-regime H-A2 stress/pre-break coverage, or revise toward a higher-density strategy hypothesis; then re-run paid-cost/readiness audits and confirm actual provider usage remains below the stop threshold.")
        elif GREEKS_OI_ENRICHMENT_REPORT.exists() and GAMMA_AGGREGATION_POLICY_DOC.exists():
            actions.append("Before any further broad Databento download, use `reports\\risk_first_data_audit.md`, `reports\\greeks_oi_enrichment_probe_report.md`, and `docs\\GAMMA_AGGREGATION_VALIDATION_POLICY.md` as the pre-purchase checkpoint: run a diagnostic gamma aggregation against the policy gates, choose targeted pre-break/high-VIX/major-regime coverage, or revise toward a higher-density strategy hypothesis; then re-run paid-cost/readiness audits and confirm actual provider usage remains below the stop threshold.")
        elif GREEKS_OI_ENRICHMENT_REPORT.exists():
            actions.append("Before any further broad Databento download, use `reports\\risk_first_data_audit.md` and `reports\\greeks_oi_enrichment_probe_report.md` as the pre-purchase checkpoint: define gamma aggregation/scaling validation, choose targeted pre-break/high-VIX/major-regime coverage, or revise toward a higher-density strategy hypothesis; then re-run paid-cost/readiness audits and confirm actual provider usage remains below the stop threshold.")
        else:
            actions.append("Before any further broad Databento download, use `reports\\risk_first_data_audit.md` and `reports\\greeks_oi_feasibility_audit.md` as the pre-purchase checkpoint: choose normalized quote enrichment for gamma-family research, targeted pre-break/high-VIX/major-regime coverage, or a revised higher-density strategy hypothesis; then re-run paid-cost/readiness audits and confirm actual provider usage remains below the stop threshold.")
    if not actions:
        actions.append("Proceed to the next locked experiment gate.")
    return actions


def _normalize_blocker(blocker: str) -> str:
    if blocker == "requires_minimum_trade_count_500":
        return "requires_mintrl_psr_sample_adequacy"
    return blocker


def _load_report_artifact(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if path.is_dir():
        return _load_gdelt_capture_status_dir(path)
    if path.suffix.lower() in {".md", ".txt"}:
        return {"status": "pass", "text": path.read_text(encoding="utf-8")}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_gdelt_capture_status_dir(path: Path) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    blockers: set[str] = set()
    file_count = 0
    for status_path in sorted(path.glob("*.json")):
        payload = json.loads(status_path.read_text(encoding="utf-8"))
        file_count += 1
        status = str(payload.get("status", "missing"))
        status_counts[status] = status_counts.get(status, 0) + 1
        for blocker in payload.get("blockers", []):
            blockers.add(str(blocker))
        if status != "captured":
            blockers.add(f"gdelt_capture_not_captured:{status_path.stem}")
    if file_count == 0:
        blockers.add("requires_gdelt_capture_status_files")
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": sorted(blockers),
        "file_count": file_count,
        "status_counts": status_counts,
    }


def _has_any_env_scope(status: dict[str, bool]) -> bool:
    return any(status.values())


def _has_any_databento_env(environment: dict[str, dict[str, bool]]) -> bool:
    return any(_has_any_env_scope(environment[name]) for name in DATABENTO_API_KEY_ENVS)


def _env_status(
    name: str,
    process_env: dict[str, str],
    user_env_getter: Callable[[str], str | None],
    machine_env_getter: Callable[[str], str | None],
) -> dict[str, bool]:
    return {
        "process": bool(process_env.get(name)),
        "user": bool(user_env_getter(name)),
        "machine": bool(machine_env_getter(name)),
    }


def _get_user_env(name: str) -> str | None:
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value)
    except OSError:
        return None


def _get_machine_env(name: str) -> str | None:
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value)
    except OSError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Higanbana research readiness without live API calls.")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = audit_research_readiness()
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
