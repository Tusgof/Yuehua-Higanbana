from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CRITERIA_PATH = PROJECT_ROOT / "tests" / "fixtures" / "exp07_acceptance_criteria_v1.json"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def evaluate_acceptance(summary: dict[str, Any], criteria: dict[str, Any]) -> dict[str, Any]:
    checks = []
    case_count = int(summary.get("case_count", 0))
    assessment_count = int(summary.get("assessment_count", 0))
    expected_assessments = case_count * int(criteria["expected_prompt_variant_count"])

    checks.append(_check("live_mode", summary.get("mode") == criteria["required_mode"]))
    checks.append(_check("minimum_case_count", case_count >= int(criteria["minimum_case_count"])))
    checks.append(_check("assessment_count_matches_case_matrix", assessment_count == expected_assessments))
    checks.append(_check("parse_valid_rate", float(summary.get("parse_valid_rate", 0.0)) >= float(criteria["minimum_parse_valid_rate"])))

    raw_rules = criteria["raw_llm_gate"]
    raw_checks = [
        _check("raw_mismatch_count", int(summary.get("mismatch_count", 0)) <= int(raw_rules["maximum_mismatch_count"])),
        _check(
            "raw_unknown_policy_violation_count",
            int(summary.get("unknown_policy_violation_count", 0)) <= int(raw_rules["maximum_unknown_policy_violation_count"]),
        ),
        _check("raw_all_cases_stable", not raw_rules["require_all_cases_stable"] or int(summary.get("stable_case_count", 0)) == case_count),
    ]

    guarded_rules = criteria["guarded_policy_candidate"]
    guarded_checks = [
        _check(
            "guarded_mismatch_count",
            int(summary.get("guarded_mismatch_count", 0)) <= int(guarded_rules["maximum_guarded_mismatch_count"]),
        ),
        _check(
            "guarded_unknown_policy_violation_count",
            int(summary.get("guarded_unknown_policy_violation_count", 0))
            <= int(guarded_rules["maximum_guarded_unknown_policy_violation_count"]),
        ),
        _check(
            "guarded_all_cases_stable",
            not guarded_rules["require_all_guarded_cases_stable"] or int(summary.get("guarded_stable_case_count", 0)) == case_count,
        ),
    ]

    integration_blockers = [
        name
        for name, required in criteria["strategy_integration_gate"].items()
        if required
    ]
    raw_status = "pass" if all(check["passed"] for check in checks + raw_checks) else "fail"
    guarded_status = "pass" if all(check["passed"] for check in checks + guarded_checks) else "fail"
    strategy_status = "blocked" if integration_blockers else ("pass" if guarded_status == "pass" else "fail")

    return {
        "criteria_version": criteria["criteria_version"],
        "summary_path": summary.get("summary_path", ""),
        "raw_llm_gate_status": raw_status,
        "guarded_policy_candidate_status": guarded_status,
        "strategy_integration_status": strategy_status,
        "strategy_integration_blockers": integration_blockers,
        "shared_checks": checks,
        "raw_llm_checks": raw_checks,
        "guarded_policy_checks": guarded_checks,
        "metrics": {
            "case_count": case_count,
            "assessment_count": assessment_count,
            "stable_case_count": int(summary.get("stable_case_count", 0)),
            "guarded_stable_case_count": int(summary.get("guarded_stable_case_count", 0)),
            "mismatch_count": int(summary.get("mismatch_count", 0)),
            "unknown_policy_violation_count": int(summary.get("unknown_policy_violation_count", 0)),
            "guarded_mismatch_count": int(summary.get("guarded_mismatch_count", 0)),
            "guarded_unknown_policy_violation_count": int(summary.get("guarded_unknown_policy_violation_count", 0)),
        },
    }


def write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Experiment 7 Acceptance Evaluation",
        "",
        f"- Criteria version: `{result['criteria_version']}`",
        f"- Raw LLM gate status: `{result['raw_llm_gate_status']}`",
        f"- Guarded policy candidate status: `{result['guarded_policy_candidate_status']}`",
        f"- Strategy integration status: `{result['strategy_integration_status']}`",
        "",
        "## Metrics",
        "",
    ]
    for key, value in result["metrics"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Strategy Integration Blockers", ""])
    for blocker in result["strategy_integration_blockers"]:
        lines.append(f"- `{blocker}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _check(name: str, passed: bool) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate Exp07 prompt-matrix acceptance criteria.")
    parser.add_argument("--criteria-path", type=Path, default=DEFAULT_CRITERIA_PATH)
    parser.add_argument("--summary-path", type=Path, default=None)
    parser.add_argument("--json-output-path", type=Path, default=PROJECT_ROOT / "reports" / "experiments" / "exp07_acceptance_evaluation.json")
    parser.add_argument("--report-path", type=Path, default=PROJECT_ROOT / "reports" / "experiments" / "exp07_acceptance_evaluation.md")
    args = parser.parse_args(argv)

    criteria = load_json(args.criteria_path)
    summary_path = args.summary_path or PROJECT_ROOT / criteria["default_summary_path"]
    summary = load_json(summary_path)
    summary["summary_path"] = str(summary_path)
    result = evaluate_acceptance(summary, criteria)

    args.json_output_path.parent.mkdir(parents=True, exist_ok=True)
    args.json_output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(args.report_path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
