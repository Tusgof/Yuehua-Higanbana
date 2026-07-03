from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp07_event_policy import preclassify_event_policy
import openrouter_deepseek_adapter as adapter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_ARCHIVE = PROJECT_ROOT / "reports" / "experiments" / "exp07_prompt_inputs.json"
DEFAULT_ASSESSMENT_JSONL = PROJECT_ROOT / "reports" / "experiments" / "exp07_prompt_assessments.jsonl"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "exp07_prompt_summary.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "experiments" / "exp07_prompt_report.md"
VALID_DECISIONS = {"allow", "block", "unknown"}
LIVE_ATTEMPTS = 3


DEFAULT_POLICY_CASES_PATH = PROJECT_ROOT / "tests" / "fixtures" / "exp07_policy_cases_v12.json"


def load_policy_cases(path: Path = DEFAULT_POLICY_CASES_PATH) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    cases = []
    for row in rows:
        prompt_input = dict(row["prompt_input"])
        prompt_input.pop("preclassified_event_policy", None)
        cases.append({
            "case_id": row["case_id"],
            "expected_decision": row["expected_decision"],
            "prompt_input": prompt_input,
        })
    return cases


ARCHIVED_PROMPT_CASES = load_policy_cases()


def archive_prompt_inputs(path: Path, cases: list[dict[str, Any]] = ARCHIVED_PROMPT_CASES) -> list[dict[str, Any]]:
    archived = []
    for case in cases:
        prompt_input = build_case_prompt_input(case)
        prompt_input["preclassified_event_policy"] = preclassify_event_policy(prompt_input)
        input_hash = _sha256_json(prompt_input)
        archived.append({
            "case_id": case["case_id"],
            "expected_decision": case["expected_decision"],
            "input_hash": input_hash,
            "prompt_input": prompt_input,
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(archived, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return archived


def filter_archived_cases(archived_cases: list[dict[str, Any]], case_ids: list[str] | None = None) -> list[dict[str, Any]]:
    if not case_ids:
        return archived_cases
    wanted = set(case_ids)
    filtered = [case for case in archived_cases if case["case_id"] in wanted]
    found = {case["case_id"] for case in filtered}
    missing = sorted(wanted - found)
    if missing:
        raise adapter.OpenRouterAdapterError(f"unknown Exp07 case_id(s): {missing}")
    return filtered


def build_case_prompt_input(case: dict[str, Any]) -> dict[str, Any]:
    if "prompt_input" in case:
        prompt_input = dict(case["prompt_input"])
        prompt_input.pop("preclassified_event_policy", None)
        return prompt_input
    return adapter.build_prompt_input(case["news_items"], case["vix_vxv"], case["market_context"])


def run_prompt_experiment(
    archived_cases: list[dict[str, Any]],
    created_at_et: str,
    live: bool = False,
    api_key_env: str = adapter.DEFAULT_API_KEY_ENV,
    assessment_jsonl_path: Path | None = None,
    transport: Any | None = None,
    existing_assessments: dict[tuple[str, str], dict[str, Any]] | None = None,
    prompt_variants: list[str] | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    variants = _selected_prompt_variants(prompt_variants)
    if assessment_jsonl_path is not None and existing_assessments is None:
        assessment_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        assessment_jsonl_path.write_text("", encoding="utf-8")

    for case in archived_cases:
        for variant in variants:
            prompt_version = adapter.PROMPT_VARIANTS[variant]["version"]
            existing_key = (case["input_hash"], prompt_version)
            reused_existing = False
            if existing_assessments is not None and existing_key in existing_assessments:
                assessment = existing_assessments[existing_key]
                reused_existing = True
            elif live:
                for attempt in range(1, LIVE_ATTEMPTS + 1):
                    try:
                        assessment = adapter.live_prompt_variant(
                            case["prompt_input"],
                            variant,
                            created_at_et,
                            api_key_env=api_key_env,
                            transport=transport,
                        )
                        break
                    except adapter.OpenRouterAdapterError:
                        if attempt == LIVE_ATTEMPTS:
                            raise
                        time.sleep(1)
            else:
                assessment = adapter.dry_run_prompt_variant(case["prompt_input"], variant, created_at_et)
            errors = adapter.validate_assessment(assessment)
            if errors:
                raise adapter.OpenRouterAdapterError("\n".join(errors))
            if assessment_jsonl_path is not None and not reused_existing:
                adapter.append_assessment_jsonl(assessment_jsonl_path, assessment)
            preclassified_policy = case["prompt_input"].get("preclassified_event_policy", {})
            guarded_decision = apply_guarded_decision(assessment["decision"], preclassified_policy)
            results.append({
                "case_id": case["case_id"],
                "expected_decision": case["expected_decision"],
                "prompt_variant": variant,
                "prompt_version": assessment["prompt_version"],
                "input_hash": case["input_hash"],
                "assessment_id": assessment["assessment_id"],
                "decision": assessment["decision"],
                "guarded_decision": guarded_decision,
                "preclassified_event_policy": preclassified_policy,
                "parse_valid": assessment["decision"] in VALID_DECISIONS,
                "openrouter_cost_usd": assessment.get("_cost_usd"),
                "openrouter_usage": assessment.get("_usage", {}),
            })
    return results


def load_existing_assessments(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    if not path.exists():
        return {}
    existing: dict[tuple[str, str], dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        assessment = json.loads(line)
        errors = adapter.validate_assessment(assessment)
        if errors:
            raise adapter.OpenRouterAdapterError(f"{path}:{line_number}: " + "\n".join(errors))
        existing[(assessment["input_hash"], assessment["prompt_version"])] = assessment
    return existing


def write_existing_assessments(path: Path, existing: dict[tuple[str, str], dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for assessment in existing.values():
            handle.write(json.dumps(assessment, ensure_ascii=False, sort_keys=True) + "\n")


def apply_guarded_decision(raw_decision: str, preclassified_event_policy: dict[str, Any]) -> str:
    policy_decision = preclassified_event_policy.get("decision")
    if policy_decision in VALID_DECISIONS:
        return policy_decision
    return raw_decision


def summarize_results(results: list[dict[str, Any]], live: bool) -> dict[str, Any]:
    by_case: dict[str, dict[str, Any]] = {}
    by_variant: dict[str, dict[str, Any]] = {}
    mismatches = []
    unknown_policy_violations = []
    guarded_mismatches = []
    guarded_unknown_policy_violations = []
    for result in results:
        case_row = by_case.setdefault(result["case_id"], {"decisions": [], "guarded_decisions": [], "expected_decision": result["expected_decision"]})
        case_row["decisions"].append(result["decision"])
        case_row["guarded_decisions"].append(result["guarded_decision"])
        variant_row = by_variant.setdefault(result["prompt_variant"], {"decisions": [], "parse_valid_count": 0, "assessment_count": 0})
        variant_row["decisions"].append(result["decision"])
        variant_row["assessment_count"] += 1
        variant_row["parse_valid_count"] += 1 if result["parse_valid"] else 0
        if result["expected_decision"] != "unknown" and result["decision"] != result["expected_decision"]:
            mismatches.append(result)
        if result["expected_decision"] == "unknown" and result["decision"] != "unknown":
            unknown_policy_violations.append(result)
        if result["expected_decision"] != "unknown" and result["guarded_decision"] != result["expected_decision"]:
            guarded_mismatches.append(result)
        if result["expected_decision"] == "unknown" and result["guarded_decision"] != "unknown":
            guarded_unknown_policy_violations.append(result)

    for row in by_case.values():
        row["unique_decisions"] = sorted(set(row["decisions"]))
        row["unique_guarded_decisions"] = sorted(set(row["guarded_decisions"]))
        row["stable_across_prompts"] = len(row["unique_decisions"]) == 1
        row["guarded_stable_across_prompts"] = len(row["unique_guarded_decisions"]) == 1
    for row in by_variant.values():
        row["unique_decisions"] = sorted(set(row["decisions"]))
        row["parse_valid_rate"] = row["parse_valid_count"] / row["assessment_count"] if row["assessment_count"] else 0.0

    assessment_count = len(results)
    cost_values = [row["openrouter_cost_usd"] for row in results if isinstance(row.get("openrouter_cost_usd"), int | float)]
    usage_totals = _usage_totals(results)
    return {
        "mode": "live_openrouter" if live else "dry_run_no_network",
        "case_count": len(by_case),
        "assessment_count": assessment_count,
        "openrouter_actual_cost_usd": round(sum(float(value) for value in cost_values), 8) if cost_values else None,
        "openrouter_costed_assessment_count": len(cost_values),
        "openrouter_usage_totals": usage_totals,
        "parse_valid_rate": sum(1 for row in results if row["parse_valid"]) / assessment_count if assessment_count else 0.0,
        "stable_case_count": sum(1 for row in by_case.values() if row["stable_across_prompts"]),
        "guarded_stable_case_count": sum(1 for row in by_case.values() if row["guarded_stable_across_prompts"]),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "unknown_policy_violation_count": len(unknown_policy_violations),
        "unknown_policy_violations": unknown_policy_violations,
        "guarded_mismatch_count": len(guarded_mismatches),
        "guarded_mismatches": guarded_mismatches,
        "guarded_unknown_policy_violation_count": len(guarded_unknown_policy_violations),
        "guarded_unknown_policy_violations": guarded_unknown_policy_violations,
        "by_case": by_case,
        "by_variant": by_variant,
    }


def write_report(path: Path, summary: dict[str, Any], input_archive: Path, assessment_jsonl: Path) -> None:
    lines = [
        "# Experiment 7 Prompt Pre-Experiment",
        "",
        f"- Mode: `{summary['mode']}`",
        f"- Cases: {summary['case_count']}",
        f"- Assessments: {summary['assessment_count']}",
        f"- OpenRouter actual cost: `{summary['openrouter_actual_cost_usd']}`",
        f"- OpenRouter costed assessments: {summary['openrouter_costed_assessment_count']} / {summary['assessment_count']}",
        f"- Parse valid rate: {summary['parse_valid_rate']:.2%}",
        f"- Stable cases across prompts: {summary['stable_case_count']} / {summary['case_count']}",
        f"- Guarded stable cases across prompts: {summary['guarded_stable_case_count']} / {summary['case_count']}",
        f"- Expected-decision mismatches: {summary['mismatch_count']}",
        f"- Unknown-policy violations: {summary['unknown_policy_violation_count']}",
        f"- Guarded unknown-policy violations: {summary['guarded_unknown_policy_violation_count']}",
        f"- Input archive: `{input_archive}`",
        f"- Assessment JSONL: `{assessment_jsonl}`",
        "",
        "## Case Stability",
        "",
        "| Case | Expected | Raw Decisions | Guarded Decisions | Raw Stable | Guarded Stable |",
        "|:--|:--|:--|:--|:--|:--|",
    ]
    for case_id, row in summary["by_case"].items():
        lines.append(
            f"| `{case_id}` | `{row['expected_decision']}` | `{', '.join(row['unique_decisions'])}` | "
            f"`{', '.join(row['unique_guarded_decisions'])}` | `{row['stable_across_prompts']}` | "
            f"`{row['guarded_stable_across_prompts']}` |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _selected_prompt_variants(prompt_variants: list[str] | None = None) -> list[str]:
    if not prompt_variants:
        return sorted(adapter.PROMPT_VARIANTS)
    normalized = [variant.upper() for variant in prompt_variants]
    unknown = sorted(set(normalized) - set(adapter.PROMPT_VARIANTS))
    if unknown:
        raise adapter.OpenRouterAdapterError(f"unknown prompt variant(s): {unknown}")
    return sorted(set(normalized))


def _usage_totals(results: list[dict[str, Any]]) -> dict[str, int]:
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for result in results:
        usage = result.get("openrouter_usage")
        if not isinstance(usage, dict):
            continue
        for key in totals:
            value = usage.get(key)
            if isinstance(value, int):
                totals[key] += value
    return totals


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Experiment 7 prompt A/B/C pre-experiment.")
    parser.add_argument("--live", action="store_true", help="Call OpenRouter live. Default is dry-run only.")
    parser.add_argument("--api-key-env", default=adapter.DEFAULT_API_KEY_ENV)
    parser.add_argument("--created-at-et", default=datetime.now().astimezone().isoformat())
    parser.add_argument("--input-archive", type=Path, default=DEFAULT_INPUT_ARCHIVE)
    parser.add_argument("--assessment-jsonl", type=Path, default=DEFAULT_ASSESSMENT_JSONL)
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--case-id", action="append", default=[], help="Limit the run to one or more fixture case ids.")
    parser.add_argument("--prompt-variant", action="append", choices=sorted(adapter.PROMPT_VARIANTS), default=[], help="Limit the run to one or more prompt variants.")
    parser.add_argument("--resume", action="store_true", help="Reuse existing assessment JSONL rows and call only missing rows.")
    args = parser.parse_args()

    archived = archive_prompt_inputs(args.input_archive)
    archived = filter_archived_cases(archived, args.case_id)
    existing_assessments = load_existing_assessments(args.assessment_jsonl) if args.resume else None
    if existing_assessments is not None:
        write_existing_assessments(args.assessment_jsonl, existing_assessments)
    results = run_prompt_experiment(
        archived,
        args.created_at_et,
        live=args.live,
        api_key_env=args.api_key_env,
        assessment_jsonl_path=args.assessment_jsonl,
        existing_assessments=existing_assessments,
        prompt_variants=args.prompt_variant,
    )
    summary = summarize_results(results, live=args.live)
    summary["input_archive"] = str(args.input_archive)
    summary["assessment_jsonl"] = str(args.assessment_jsonl)
    summary["api_key"] = adapter.api_key_status(args.api_key_env)
    args.summary_path.parent.mkdir(parents=True, exist_ok=True)
    args.summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(args.report_path, summary, args.input_archive, args.assessment_jsonl)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
