from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GDELT_PLAN_PATH = PROJECT_ROOT / "reports" / "news_gdelt_capture_command_plan.json"
DEFAULT_NEWS_AUDIT_PATH = PROJECT_ROOT / "reports" / "news_coverage_audit.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "experiments" / "exp07_real_news_case_plan.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "experiments" / "exp07_real_news_case_plan.md"

PROMPT_TEMPLATE_FAMILIES = [
    {
        "family_id": "role_only_analyst",
        "purpose": "Test whether a simple expert role can interpret real pre-entry news without policy scaffolding.",
        "failure_mode": "Overconfident or vague rationale.",
    },
    {
        "family_id": "structured_json_classifier",
        "purpose": "Test parser stability and consistent decision fields.",
        "failure_mode": "Becomes a hidden keyword checklist instead of contextual interpretation.",
    },
    {
        "family_id": "few_shot_real_news_examples",
        "purpose": "Test whether real examples improve ambiguous classification.",
        "failure_mode": "Overfits to the chosen examples.",
    },
    {
        "family_id": "evidence_first_rubric",
        "purpose": "Require concrete input evidence before risk classification.",
        "failure_mode": "May miss latent risk not explicit in headlines.",
    },
    {
        "family_id": "scenario_branching_prompt",
        "purpose": "Compare benign, base, and stress interpretations before deciding.",
        "failure_mode": "Higher cost and more verbose outputs.",
    },
    {
        "family_id": "self_consistency_ensemble",
        "purpose": "Measure agreement across repeated calls or prompt variants.",
        "failure_mode": "Higher cost and slower decision path.",
    },
]

REQUIRED_CASE_GROUPS = [
    "normal_quiet_day",
    "scheduled_macro_day",
    "large_intraday_move_day",
    "volatility_spike_day",
    "geopolitical_shock_or_war_risk_day",
    "banking_or_liquidity_stress_day",
    "index_etf_futures_disruption_day",
    "false_alarm_day",
]

REQUIRED_NEWS_FIELDS = [
    "published_at",
    "fetched_at",
    "source",
    "url",
    "headline",
    "decision_time_et",
]


class Exp07RealNewsCasePlanError(ValueError):
    pass


def build_plan(gdelt_plan_path: Path = DEFAULT_GDELT_PLAN_PATH, news_audit_path: Path = DEFAULT_NEWS_AUDIT_PATH) -> dict[str, Any]:
    gdelt_plan = _load_json(gdelt_plan_path)
    news_audit = _load_optional_json(news_audit_path)
    commands = gdelt_plan.get("commands", [])
    if not isinstance(commands, list):
        raise Exp07RealNewsCasePlanError(f"{gdelt_plan_path} missing commands array")

    candidate_queue = [_case_candidate_from_command(command) for command in commands if isinstance(command, dict)]
    captured_count = sum(1 for candidate in candidate_queue if candidate["capture_status"] == "captured")
    news_blockers = [] if news_audit is None else list(news_audit.get("blockers", []))

    blockers = []
    if not candidate_queue:
        blockers.append("requires_candidate_day_queue")
    if news_audit is None or "requires_real_news_archive" in news_blockers:
        blockers.append("requires_real_news_archive")
    if captured_count == 0:
        blockers.append("requires_real_timestamp_clean_news_cases")

    return {
        "plan_version": "exp07-real-news-case-plan-v1",
        "status": "blocked" if blockers else "ready_for_prompt_family_pre_experiment",
        "collection_status": "ready_to_collect" if candidate_queue else "blocked",
        "blockers": blockers,
        "gdelt_plan_path": str(gdelt_plan_path),
        "news_audit_path": str(news_audit_path),
        "candidate_day_count": len(candidate_queue),
        "captured_candidate_count": captured_count,
        "retry_pressure": gdelt_plan.get("retry_pressure", {}),
        "next_unattempted_trade_date": gdelt_plan.get("retry_queue_summary", {}).get("next_unattempted_trade_date"),
        "required_news_fields": REQUIRED_NEWS_FIELDS,
        "required_case_groups": REQUIRED_CASE_GROUPS,
        "prompt_template_families": PROMPT_TEMPLATE_FAMILIES,
        "candidate_queue": candidate_queue,
        "acceptance_bar": {
            "synthetic_cases_allowed_for_research": False,
            "requires_timestamp_clean_inputs": True,
            "requires_real_news_snapshots": True,
            "requires_costed_live_rows": True,
            "strategy_ablation_required_after_prompt_pass": True,
        },
        "next_step": _next_step(gdelt_plan.get("retry_pressure", {}), blockers),
    }


def write_reports(result: dict[str, Any], json_output: Path = DEFAULT_JSON_OUTPUT, report_output: Path = DEFAULT_REPORT_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Exp07 Real News Case Plan",
        "",
        f"- Status: `{result['status']}`",
        f"- Collection status: `{result['collection_status']}`",
        f"- Candidate days: `{result['candidate_day_count']}`",
        f"- Captured candidate days: `{result['captured_candidate_count']}`",
        f"- Retry pressure: `{result.get('retry_pressure', {}).get('status', 'unknown')}`",
        f"- Next unattempted trade date: `{result.get('next_unattempted_trade_date') or '-'}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = result.get("blockers") or []
    lines.extend(f"- `{blocker}`" for blocker in blockers) if blockers else lines.append("- None")

    lines.extend(["", "## Required Case Groups", ""])
    lines.extend(f"- `{group}`" for group in result["required_case_groups"])

    lines.extend(["", "## Prompt Template Families", "", "| Family | Purpose | Failure Mode |", "|:--|:--|:--|"])
    for family in result["prompt_template_families"]:
        lines.append(f"| `{family['family_id']}` | {family['purpose']} | {family['failure_mode']} |")

    lines.extend(["", "## Required News Fields", ""])
    lines.extend(f"- `{field}`" for field in result["required_news_fields"])

    lines.extend(["", "## Candidate Queue", "", "| Trade Date | Decision Time | Split | Capture Status |", "|:--|:--|:--|:--|"])
    for candidate in result["candidate_queue"]:
        lines.append(
            f"| `{candidate['trade_date']}` | `{candidate['decision_time_et']}` | "
            f"`{candidate['split']}` | `{candidate['capture_status']}` |"
        )

    lines.extend(["", "## Next Step", "", str(result["next_step"])])
    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _case_candidate_from_command(command: dict[str, Any]) -> dict[str, Any]:
    trade_date = str(command.get("trade_date", "")).strip()
    if not trade_date:
        raise Exp07RealNewsCasePlanError("GDELT command missing trade_date")
    latest_status = command.get("latest_status", {})
    capture_status = str(latest_status.get("status", "not_attempted")) if isinstance(latest_status, dict) else "not_attempted"
    return {
        "trade_date": trade_date,
        "decision_time_et": str(command.get("decision_time_et", "")),
        "split": "oos" if trade_date >= "2024-01-01" else "in_sample",
        "capture_status": capture_status,
        "raw_output_path": str(command.get("output_path", "")),
        "status_output_path": str(command.get("status_output_path", "")),
        "planned_case_groups": REQUIRED_CASE_GROUPS,
    }


def _next_step(retry_pressure: dict[str, Any], blockers: list[str]) -> str:
    if retry_pressure.get("status") == "cooldown_recommended":
        return "Pause live GDELT retries, then capture one candidate day at a time after 429 pressure clears."
    if "requires_real_timestamp_clean_news_cases" in blockers:
        return "Capture or import real timestamp-clean news snapshots before running any Exp07 prompt-family experiment."
    return "Run the prompt-family pre-experiment on the captured real-news case archive."


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise Exp07RealNewsCasePlanError(f"required input missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Exp07RealNewsCasePlanError(f"{path} must contain a JSON object")
    return payload


def _load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _load_json(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan Exp07 real-news prompt-family cases without live API calls.")
    parser.add_argument("--gdelt-plan-path", type=Path, default=DEFAULT_GDELT_PLAN_PATH)
    parser.add_argument("--news-audit-path", type=Path, default=DEFAULT_NEWS_AUDIT_PATH)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = build_plan(args.gdelt_plan_path, args.news_audit_path)
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
