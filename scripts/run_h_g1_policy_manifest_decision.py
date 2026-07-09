from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUCKET_FAILURE_DIAGNOSTIC = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_bucket_failure_diagnostic.json"
OUTPUT_JSON = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_policy_manifest_decision.json"
OUTPUT_REPORT = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_policy_manifest_decision.md"
NOTIONAL_FLOOR = 0.80


def run_decision(input_path: Path = BUCKET_FAILURE_DIAGNOSTIC) -> dict[str, Any]:
    diagnostic = _load_json(input_path)
    failed_buckets = diagnostic.get("failed_buckets", [])
    if not isinstance(failed_buckets, list) or not failed_buckets:
        raise ValueError("h_g1_bucket_failure_diagnostic has no failed_buckets")

    below_notional = [
        _bucket_identity(item) for item in failed_buckets
        if float(item.get("computed_oi_notional_share", 0.0)) < NOTIONAL_FLOOR
    ]
    high_notional_row_rate_failures = [
        _bucket_identity(item) for item in failed_buckets
        if float(item.get("computed_rate", 0.0)) < 0.60
        and float(item.get("computed_oi_notional_share", 0.0)) >= NOTIONAL_FLOOR
    ]
    all_black_scholes_blocks = bool(diagnostic.get("summary", {}).get("all_failures_are_black_scholes_bracket_blocks"))

    return {
        "record_type": "h_g1_policy_manifest_decision",
        "schema_version": "h_g1_policy_manifest_decision_v1",
        "hypothesis_id": "H-G1",
        "evidence_tier": "E1",
        "conclusion": "ยังสรุปไม่ได้",
        "source_diagnostic": _relative(input_path),
        "paid_data_used": False,
        "network_used": False,
        "candidate_policy": {
            "name": "v2.1_review_candidate_not_adopted",
            "notional_floor": NOTIONAL_FLOOR,
            "row_rate_floor_treatment": "warning_not_primary_pass_gate",
            "rationale": "H-G1 signal is exposure-weighted; row-rate alone can overweight low-notional rows, but notional coverage cannot excuse a material uncovered bucket.",
        },
        "findings": {
            "failed_bucket_count": len(failed_buckets),
            "all_failures_are_black_scholes_bracket_blocks": all_black_scholes_blocks,
            "high_notional_row_rate_failure_count": len(high_notional_row_rate_failures),
            "below_notional_floor_count": len(below_notional),
            "below_notional_floor_buckets": below_notional,
            "high_notional_row_rate_failure_buckets": high_notional_row_rate_failures,
        },
        "decision": {
            "status": "policy_revision_alone_rejected_manifest_v3_required",
            "recommended_next_step": "Draft policy v2.1 as a review artifact and create a manifest v3 replacement plan for the below-floor bucket before any new paid OI pull.",
            "why": "Four failures look like row-rate policy strictness, but 2023-07-12 otm_put keeps only 0.662545 computed OI-notional coverage; relaxing the policy alone would hide a material uncovered bucket.",
            "forbidden_actions": [
                "Do not claim H-G1 coverage pass.",
                "Do not use NOVI/net-gamma as a strategy filter.",
                "Do not buy replacement OI before a v3 manifest validates.",
                "Do not edit policy v2 to make the current 10-date set pass silently.",
            ],
        },
        "tier_blockers": [
            "E1 diagnostic decision only",
            "H-G1 remains coverage-blocked",
            "No strategy-return MinTRL/PSR evidence",
            "No true dealer-side gamma inventory data",
        ],
    }


def write_outputs(result: dict[str, Any], output_json: Path = OUTPUT_JSON, output_report: Path = OUTPUT_REPORT) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(_format_report(result), encoding="utf-8")


def _format_report(result: dict[str, Any]) -> str:
    findings = result["findings"]
    decision = result["decision"]
    candidate = result["candidate_policy"]
    lines = [
        "# H-G1 Policy / Manifest Decision",
        "",
        f"- Status: `{decision['status']}`",
        f"- Conclusion: `{result['conclusion']}`",
        f"- Evidence tier: `{result['evidence_tier']}`",
        f"- Paid data used: `{result['paid_data_used']}`",
        f"- Network used: `{result['network_used']}`",
        "",
        "## Decision",
        "",
        decision["why"],
        "",
        f"Recommended next step: {decision['recommended_next_step']}",
        "",
        "## Findings",
        "",
        f"- Failed bucket count: `{findings['failed_bucket_count']}`",
        f"- All failures are Black-Scholes bracket blocks: `{findings['all_failures_are_black_scholes_bracket_blocks']}`",
        f"- High-notional row-rate failures: `{findings['high_notional_row_rate_failure_count']}`",
        f"- Below-notional-floor buckets: `{findings['below_notional_floor_count']}`",
        f"- Below-notional-floor list: `{', '.join(findings['below_notional_floor_buckets'])}`",
        "",
        "## Candidate Policy Review",
        "",
        f"- Candidate name: `{candidate['name']}`",
        f"- Notional floor: `{candidate['notional_floor']}`",
        f"- Row-rate treatment: `{candidate['row_rate_floor_treatment']}`",
        f"- Rationale: {candidate['rationale']}",
        "",
        "## Forbidden Actions",
        "",
    ]
    lines.extend(f"- {item}" for item in decision["forbidden_actions"])
    lines.extend(["", "## Tier Blockers", ""])
    lines.extend(f"- {item}" for item in result["tier_blockers"])
    lines.append("")
    return "\n".join(lines)


def _bucket_identity(item: dict[str, Any]) -> str:
    return f"{item.get('date')} {item.get('bucket')}"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Decide whether H-G1 needs policy review, manifest v3, or both.")
    parser.add_argument("--input", type=Path, default=BUCKET_FAILURE_DIAGNOSTIC)
    parser.add_argument("--output-json", type=Path, default=OUTPUT_JSON)
    parser.add_argument("--output-report", type=Path, default=OUTPUT_REPORT)
    args = parser.parse_args(argv)

    result = run_decision(args.input)
    write_outputs(result, args.output_json, args.output_report)
    print(json.dumps({"status": result["decision"]["status"], "below_notional_floor_count": result["findings"]["below_notional_floor_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
