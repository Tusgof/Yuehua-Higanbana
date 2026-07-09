from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ACCEPTANCE_PATH = PROJECT_ROOT / "reports" / "research_acceptance_evaluation.json"
DEFAULT_CHECKLIST_PATH = PROJECT_ROOT / "config" / "real_money_launch_checklist.example.json"
DEFAULT_IBKR_CONFIG_PATH = PROJECT_ROOT / "config" / "ibkr.example.json"
DEFAULT_KILL_SWITCH_PATH = PROJECT_ROOT / "config" / "kill_switch.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "real_money_launch_gate_audit.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "real_money_launch_gate_audit.md"

REQUIRED_CHECKLIST_FLAGS = (
    "research_acceptance_passed",
    "options_permission_approved",
    "cash_account_constraints_documented",
    "defined_risk_only_confirmed",
    "user_real_money_approval_recorded",
    "kill_switch_tested",
    "forced_close_tested",
    "backup_close_order_plan_tested",
)


def audit_real_money_launch_gate(
    *,
    acceptance_path: Path = DEFAULT_ACCEPTANCE_PATH,
    checklist_path: Path = DEFAULT_CHECKLIST_PATH,
    ibkr_config_path: Path = DEFAULT_IBKR_CONFIG_PATH,
    kill_switch_path: Path = DEFAULT_KILL_SWITCH_PATH,
) -> dict[str, Any]:
    acceptance = _load_json(acceptance_path)
    checklist = _load_json(checklist_path)
    ibkr_config = _load_json(ibkr_config_path)
    kill_switch = _load_json(kill_switch_path)

    blockers: list[str] = []

    if acceptance.get("status") != "approved_for_operational_validation":
        blockers.append(f"research_acceptance_not_approved:{acceptance.get('status')}")
    if acceptance.get("real_money_allowed") is not True:
        blockers.append("research_acceptance_real_money_not_allowed")

    for flag in REQUIRED_CHECKLIST_FLAGS:
        if checklist.get(flag) is not True:
            blockers.append(f"checklist_missing:{flag}")

    if checklist.get("first_live_max_risk_usd") is None:
        blockers.append("checklist_missing:first_live_max_risk_usd")
    elif checklist.get("first_live_max_risk_usd", 0) <= 0:
        blockers.append("checklist_invalid:first_live_max_risk_usd")

    if ibkr_config.get("mode") != "live":
        blockers.append(f"ibkr_config_not_live:{ibkr_config.get('mode')}")
    if ibkr_config.get("transmit_enabled") is not True:
        blockers.append("ibkr_transmit_disabled")
    if ibkr_config.get("options_permission_confirmed") is not True:
        blockers.append("ibkr_options_permission_not_confirmed")
    if ibkr_config.get("account_type") != "cash":
        blockers.append(f"ibkr_account_type_not_cash:{ibkr_config.get('account_type')}")
    if ibkr_config.get("forced_close_time_et") != "15:45:00":
        blockers.append("ibkr_forced_close_time_not_1545")

    if kill_switch.get("enabled") is True:
        blockers.append("kill_switch_enabled")

    return {
        "schema_version": "real_money_launch_gate_audit_v1",
        "status": "blocked" if blockers else "pass",
        "real_money_allowed": not blockers,
        "blockers": sorted(set(blockers)),
        "required_checklist_flags": list(REQUIRED_CHECKLIST_FLAGS),
        "source_paths": {
            "acceptance": _relative(acceptance_path),
            "checklist": _relative(checklist_path),
            "ibkr_config": _relative(ibkr_config_path),
            "kill_switch": _relative(kill_switch_path),
        },
        "notes": [
            "This audit is read-only and never transmits orders.",
            "The example config is expected to remain blocked until research, permission, approval, and kill-switch gates pass.",
        ],
    }


def write_reports(result: dict[str, Any], json_output: Path, report_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Real-Money Launch Gate Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Real money allowed: `{result['real_money_allowed']}`",
        f"- Blocker count: {len(result['blockers'])}",
        "",
        "## Blockers",
        "",
    ]
    if result["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in result["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Source Paths", ""])
    lines.extend(f"- `{key}`: `{value}`" for key, value in result["source_paths"].items())
    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit the real-money launch gate without transmitting orders.")
    parser.add_argument("--acceptance-path", type=Path, default=DEFAULT_ACCEPTANCE_PATH)
    parser.add_argument("--checklist-path", type=Path, default=DEFAULT_CHECKLIST_PATH)
    parser.add_argument("--ibkr-config-path", type=Path, default=DEFAULT_IBKR_CONFIG_PATH)
    parser.add_argument("--kill-switch-path", type=Path, default=DEFAULT_KILL_SWITCH_PATH)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = audit_real_money_launch_gate(
        acceptance_path=args.acceptance_path,
        checklist_path=args.checklist_path,
        ibkr_config_path=args.ibkr_config_path,
        kill_switch_path=args.kill_switch_path,
    )
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
