from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HYPOTHESIS_AUDIT = PROJECT_ROOT / "reports" / "hypothesis_registry_audit.json"
DEFAULT_EVIDENCE_AUDIT = PROJECT_ROOT / "reports" / "evidence_tier_audit.json"
DEFAULT_READINESS_AUDIT = PROJECT_ROOT / "reports" / "research_readiness_audit.json"
DEFAULT_PAID_COST_AUDIT = PROJECT_ROOT / "reports" / "data_cost" / "paid_cost_audit.json"


def build_project_state(
    hypothesis_audit_path: Path = DEFAULT_HYPOTHESIS_AUDIT,
    evidence_audit_path: Path = DEFAULT_EVIDENCE_AUDIT,
    readiness_audit_path: Path = DEFAULT_READINESS_AUDIT,
    paid_cost_audit_path: Path = DEFAULT_PAID_COST_AUDIT,
) -> dict[str, Any]:
    hypothesis_audit = _load_json(hypothesis_audit_path)
    evidence_audit = _load_json(evidence_audit_path)
    readiness_audit = _load_json(readiness_audit_path)
    paid_cost_audit = _load_json(paid_cost_audit_path)

    return {
        "status": _aggregate_status(
            [
                hypothesis_audit.get("status"),
                evidence_audit.get("status"),
                readiness_audit.get("status"),
                paid_cost_audit.get("status"),
            ]
        ),
        "hypotheses": [
            {
                "id": item.get("id"),
                "family": item.get("family"),
                "status": item.get("status"),
                "evidence_tiers": item.get("evidence_tiers", []),
                "blocker_count": len(item.get("blockers", [])),
                "warning_count": len(item.get("warnings", [])),
            }
            for item in hypothesis_audit.get("hypotheses", [])
        ],
        "evidence_tiers": {
            "status": evidence_audit.get("status"),
            "summary_count": evidence_audit.get("summary_count"),
            "blocker_count": len(evidence_audit.get("blockers", [])),
            "warning_count": len(evidence_audit.get("warnings", [])),
            "strict_missing_metadata": evidence_audit.get("strict_missing_metadata"),
        },
        "readiness": {
            "status": readiness_audit.get("status"),
            "blockers": readiness_audit.get("blockers", []),
            "blocker_count": len(readiness_audit.get("blockers", [])),
            "next_safe_actions": readiness_audit.get("next_safe_actions", []),
        },
        "paid_cost": {
            "status": paid_cost_audit.get("status"),
            "cost_guard_basis": paid_cost_audit.get("cost_guard_basis"),
            "cost_guard_used_usd": paid_cost_audit.get("cost_guard_used_usd"),
            "stop_threshold_usd": paid_cost_audit.get("stop_threshold_usd"),
            "remaining_before_stop_usd": paid_cost_audit.get("remaining_before_stop_usd"),
            "budget_policy": paid_cost_audit.get("budget_policy", {}),
        },
        "news_gdelt": _news_gdelt_state(readiness_audit),
        "sources": {
            "hypothesis_audit": _relative(hypothesis_audit_path),
            "evidence_audit": _relative(evidence_audit_path),
            "readiness_audit": _relative(readiness_audit_path),
            "paid_cost_audit": _relative(paid_cost_audit_path),
        },
    }


def render_markdown(state: dict[str, Any]) -> str:
    lines = [
        "# Higanbana Project State",
        "",
        f"- Overall status: `{state['status']}`",
        f"- Cost guard: `${state['paid_cost']['cost_guard_used_usd']}` / `${state['paid_cost']['stop_threshold_usd']}`",
        f"- Remaining before stop: `${state['paid_cost']['remaining_before_stop_usd']}`",
        f"- Evidence audit: `{state['evidence_tiers']['status']}` with {state['evidence_tiers']['blocker_count']} blockers and {state['evidence_tiers']['warning_count']} warnings",
        f"- Readiness: `{state['readiness']['status']}` with {state['readiness']['blocker_count']} blockers",
        "",
        "## Hypotheses",
        "",
        "| ID | Family | Status | Evidence tiers | Blockers | Warnings |",
        "|:--|:--|:--|:--|--:|--:|",
    ]
    for item in state["hypotheses"]:
        tiers = ", ".join(item["evidence_tiers"]) if item["evidence_tiers"] else "None"
        lines.append(
            f"| `{item['id']}` | `{item['family']}` | `{item['status']}` | {tiers} | {item['blocker_count']} | {item['warning_count']} |"
        )

    lines.extend(
        [
            "",
            "## News And GDELT",
            "",
            f"- News status: `{state['news_gdelt']['news_status']}`",
            f"- GDELT capture status: `{state['news_gdelt']['gdelt_capture_status']}`",
            f"- GDELT command-plan status: `{state['news_gdelt']['gdelt_command_plan_status']}`",
            f"- Not-attempted candidate days: {state['news_gdelt']['not_attempted_count']}",
            f"- Next unattempted trade date: `{state['news_gdelt']['next_unattempted_trade_date']}`",
            "",
            "## Next Safe Actions",
            "",
        ]
    )
    if state["readiness"]["next_safe_actions"]:
        lines.extend(f"- {item}" for item in state["readiness"]["next_safe_actions"])
    else:
        lines.append("- None")

    return "\n".join(lines) + "\n"


def _news_gdelt_state(readiness_audit: dict[str, Any]) -> dict[str, Any]:
    checks = {
        check.get("name"): check
        for check in readiness_audit.get("checks", [])
        if isinstance(check, dict) and check.get("name")
    }
    news = checks.get("news", {})
    capture = checks.get("gdelt_capture_status", {})
    command_plan = checks.get("gdelt_command_plan", {})
    return {
        "news_status": news.get("status"),
        "gdelt_capture_status": capture.get("status"),
        "gdelt_status_counts": capture.get("status_counts", {}),
        "gdelt_command_plan_status": command_plan.get("status"),
        "retry_pressure_status": command_plan.get("retry_pressure_status"),
        "not_attempted_count": command_plan.get("not_attempted_count"),
        "next_unattempted_trade_date": command_plan.get("next_unattempted_trade_date"),
    }


def _aggregate_status(statuses: list[Any]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if all(status == "pass" for status in statuses):
        return "pass"
    return "warning"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only report of current Higanbana project state.")
    parser.add_argument("--hypothesis-audit-path", type=Path, default=DEFAULT_HYPOTHESIS_AUDIT)
    parser.add_argument("--evidence-audit-path", type=Path, default=DEFAULT_EVIDENCE_AUDIT)
    parser.add_argument("--readiness-audit-path", type=Path, default=DEFAULT_READINESS_AUDIT)
    parser.add_argument("--paid-cost-audit-path", type=Path, default=DEFAULT_PAID_COST_AUDIT)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of Markdown.")
    args = parser.parse_args(argv)

    state = build_project_state(
        hypothesis_audit_path=args.hypothesis_audit_path,
        evidence_audit_path=args.evidence_audit_path,
        readiness_audit_path=args.readiness_audit_path,
        paid_cost_audit_path=args.paid_cost_audit_path,
    )
    if args.json:
        print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_markdown(state), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
