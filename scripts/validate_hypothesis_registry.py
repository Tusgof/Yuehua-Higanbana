from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "experiments" / "hypothesis_registry.json"
DEFAULT_REPORTS_ROOT = PROJECT_ROOT / "reports"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "hypothesis_registry_audit.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "hypothesis_registry_audit.md"

ALLOWED_STATUSES = {"proposed", "active", "active_blocked", "parked", "falsified", "falsified-as-stated", "validated"}
ALLOWED_FAMILIES = {"subsystem_a", "subsystem_b", "gamma", "llm_news", "llm_price", "portfolio"}
ALLOWED_EVIDENCE_TIERS = {"E0", "E1", "E2", "E3"}
REQUIRED_FIELDS = {
    "id",
    "family",
    "status",
    "statement",
    "economic_rationale",
    "testable_predictions",
    "validation_criteria",
    "falsification_criteria",
    "required_data",
    "mintrl_falsify",
    "evidence",
    "dependencies",
    "decision_log",
}


def validate_hypothesis_registry(
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    reports_root: Path = DEFAULT_REPORTS_ROOT,
) -> dict[str, Any]:
    registry = _load_json(registry_path)
    hypotheses = registry.get("hypotheses", [])
    blockers: list[str] = []
    warnings: list[str] = []

    if registry.get("schema_version") != "hypothesis_registry_v1":
        blockers.append(f"unsupported_schema_version:{registry.get('schema_version')}")
    if not isinstance(hypotheses, list) or not hypotheses:
        blockers.append("hypotheses_missing_or_empty")
        hypotheses = []

    ids = [item.get("id") for item in hypotheses if isinstance(item, dict)]
    known_ids = {str(item_id) for item_id in ids if isinstance(item_id, str)}
    if len(ids) != len(known_ids):
        blockers.append("duplicate_or_invalid_hypothesis_id")

    summaries_with_hypothesis_ids = _find_summary_hypothesis_ids(reports_root)
    for summary in summaries_with_hypothesis_ids:
        if summary["hypothesis_id"] not in known_ids:
            blockers.append(f"summary_references_unknown_hypothesis:{summary['hypothesis_id']}:{summary['path']}")

    normalized: list[dict[str, Any]] = []
    for hypothesis in hypotheses:
        if not isinstance(hypothesis, dict):
            blockers.append("hypothesis_entry_not_object")
            continue
        hypothesis_id = str(hypothesis.get("id"))
        item_blockers, item_warnings = _validate_hypothesis(hypothesis, known_ids)
        blockers.extend(f"{hypothesis_id}:{item}" for item in item_blockers)
        warnings.extend(f"{hypothesis_id}:{item}" for item in item_warnings)
        normalized.append(
            {
                "id": hypothesis_id,
                "family": hypothesis.get("family"),
                "status": hypothesis.get("status"),
                "evidence_tiers": sorted(
                    {
                        evidence.get("evidence_tier")
                        for evidence in hypothesis.get("evidence", [])
                        if isinstance(evidence, dict) and evidence.get("evidence_tier")
                    }
                ),
                "dependency_count": len(hypothesis.get("dependencies", [])) if isinstance(hypothesis.get("dependencies"), list) else None,
                "evidence_count": len(hypothesis.get("evidence", [])) if isinstance(hypothesis.get("evidence"), list) else None,
                "blockers": item_blockers,
                "warnings": item_warnings,
            }
        )

    return {
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "warnings": warnings,
        "registry_path": _relative(registry_path),
        "reports_root": _relative(reports_root),
        "hypothesis_count": len(normalized),
        "summary_hypothesis_reference_count": len(summaries_with_hypothesis_ids),
        "hypotheses": normalized,
    }


def write_reports(
    result: dict[str, Any],
    json_output: Path = DEFAULT_JSON_OUTPUT,
    report_output: Path = DEFAULT_REPORT_OUTPUT,
) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Hypothesis Registry Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Blocker count: {len(result['blockers'])}",
        f"- Warning count: {len(result['warnings'])}",
        f"- Hypothesis count: {result['hypothesis_count']}",
        f"- Summary hypothesis references: {result['summary_hypothesis_reference_count']}",
        f"- Registry: `{result['registry_path']}`",
        "",
        "## Hypotheses",
        "",
        "| Hypothesis | Family | Status | Evidence tiers | Blockers |",
        "|:--|:--|:--|:--|:--|",
    ]
    for hypothesis in result["hypotheses"]:
        blockers = ", ".join(hypothesis["blockers"]) if hypothesis["blockers"] else "None"
        tiers = ", ".join(hypothesis["evidence_tiers"]) if hypothesis["evidence_tiers"] else "None"
        lines.append(
            f"| `{hypothesis['id']}` | `{hypothesis['family']}` | `{hypothesis['status']}` | {tiers} | {blockers} |"
        )

    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- `{blocker}`" for blocker in result["blockers"]) if result["blockers"] else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- `{warning}`" for warning in result["warnings"]) if result["warnings"] else lines.append("- None")

    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_hypothesis(hypothesis: dict[str, Any], known_ids: set[str]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    missing = sorted(REQUIRED_FIELDS - set(hypothesis))
    blockers.extend(f"missing_required_field:{field}" for field in missing)

    if hypothesis.get("family") not in ALLOWED_FAMILIES:
        blockers.append(f"invalid_family:{hypothesis.get('family')}")
    if hypothesis.get("status") not in ALLOWED_STATUSES:
        blockers.append(f"invalid_status:{hypothesis.get('status')}")

    for field in ("testable_predictions", "validation_criteria", "falsification_criteria", "required_data", "decision_log"):
        value = hypothesis.get(field)
        if not isinstance(value, list) or not value:
            blockers.append(f"{field}_must_be_non_empty_list")

    mintrl = hypothesis.get("mintrl_falsify")
    if not isinstance(mintrl, dict) or not mintrl:
        blockers.append("mintrl_falsify_must_be_non_empty_object")

    dependencies = hypothesis.get("dependencies")
    if not isinstance(dependencies, list):
        blockers.append("dependencies_must_be_list")
    else:
        for dependency in dependencies:
            if dependency not in known_ids:
                blockers.append(f"unknown_dependency:{dependency}")

    evidence_items = hypothesis.get("evidence")
    if not isinstance(evidence_items, list):
        blockers.append("evidence_must_be_list")
        evidence_items = []
    validated_evidence = False
    for evidence in evidence_items:
        if not isinstance(evidence, dict):
            blockers.append("evidence_item_must_be_object")
            continue
        tier = evidence.get("evidence_tier")
        if tier not in ALLOWED_EVIDENCE_TIERS:
            blockers.append(f"invalid_evidence_tier:{tier}")
        if tier in {"E2", "E3"}:
            validated_evidence = True
        if not evidence.get("path"):
            blockers.append("evidence_item_missing_path")

    if hypothesis.get("status") == "validated" and not validated_evidence:
        blockers.append("validated_status_requires_E2_or_E3_evidence")
    if hypothesis.get("status") in {"active", "active_blocked"} and not evidence_items:
        warnings.append("active_hypothesis_has_no_evidence_links")

    return blockers, warnings


def _find_summary_hypothesis_ids(root: Path) -> list[dict[str, str]]:
    if not root.exists():
        return []
    references: list[dict[str, str]] = []
    for path in sorted(root.rglob("*.json")):
        if path.name.endswith("_audit.json"):
            continue
        try:
            payload = _load_json(path)
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(payload, dict):
            continue
        hypothesis_id = payload.get("hypothesis_id")
        if isinstance(hypothesis_id, str) and hypothesis_id:
            references.append({"path": _relative(path), "hypothesis_id": hypothesis_id})
    return references


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the Higanbana hypothesis registry and summary references.")
    parser.add_argument("--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--reports-root", type=Path, default=DEFAULT_REPORTS_ROOT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = validate_hypothesis_registry(args.registry_path, args.reports_root)
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
