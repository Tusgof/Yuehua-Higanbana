from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "experiments" / "hypothesis_registry.json"
DEFAULT_REPORTS_ROOT = PROJECT_ROOT / "reports"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "evidence_tier_audit.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "evidence_tier_audit.md"

ALLOWED_TIERS = {"E0", "E1", "E2", "E3"}
ACCEPTANCE_VALUES = {
    "ผ่าน",
    "pass",
    "passed",
    "accepted",
    "validated",
    "approved",
    "approved_for_operational_validation",
}


def validate_evidence_tiers(
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    reports_root: Path = DEFAULT_REPORTS_ROOT,
    *,
    strict_missing_metadata: bool = False,
) -> dict[str, Any]:
    known_hypotheses = _load_known_hypotheses(registry_path)
    blockers: list[str] = []
    warnings: list[str] = []
    summaries: list[dict[str, Any]] = []

    for path in _iter_top_level_summaries(reports_root):
        try:
            payload = _load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            blockers.append(f"summary_unreadable:{_relative(path)}:{exc.__class__.__name__}")
            continue
        if not isinstance(payload, dict):
            warnings.append(f"summary_not_object:{_relative(path)}")
            continue

        summary_result = _validate_summary(path, payload, known_hypotheses, strict_missing_metadata)
        blockers.extend(summary_result["blockers"])
        warnings.extend(summary_result["warnings"])
        summaries.append(summary_result["summary"])

    return {
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "warnings": warnings,
        "strict_missing_metadata": strict_missing_metadata,
        "registry_path": _relative(registry_path),
        "reports_root": _relative(reports_root),
        "summary_count": len(summaries),
        "summaries": summaries,
    }


def write_reports(
    result: dict[str, Any],
    json_output: Path = DEFAULT_JSON_OUTPUT,
    report_output: Path = DEFAULT_REPORT_OUTPUT,
) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Evidence Tier Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Blocker count: {len(result['blockers'])}",
        f"- Warning count: {len(result['warnings'])}",
        f"- Strict missing metadata: `{result['strict_missing_metadata']}`",
        f"- Summary count: {result['summary_count']}",
        "",
        "## Summaries",
        "",
        "| Path | Hypothesis | Tier | Acceptance claim | Blockers | Warnings |",
        "|:--|:--|:--|:--|:--|:--|",
    ]
    for summary in result["summaries"]:
        lines.append(
            "| {path} | {hypothesis} | {tier} | {acceptance} | {blockers} | {warnings} |".format(
                path=f"`{summary['path']}`",
                hypothesis=f"`{summary['hypothesis_id']}`" if summary["hypothesis_id"] else "None",
                tier=f"`{summary['evidence_tier']}`" if summary["evidence_tier"] else "None",
                acceptance="yes" if summary["acceptance_claim"] else "no",
                blockers=", ".join(f"`{item}`" for item in summary["blockers"]) or "None",
                warnings=", ".join(f"`{item}`" for item in summary["warnings"]) or "None",
            )
        )

    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- `{blocker}`" for blocker in result["blockers"]) if result["blockers"] else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- `{warning}`" for warning in result["warnings"]) if result["warnings"] else lines.append("- None")

    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_summary(
    path: Path,
    payload: dict[str, Any],
    known_hypotheses: set[str],
    strict_missing_metadata: bool,
) -> dict[str, Any]:
    rel = _relative(path)
    blockers: list[str] = []
    warnings: list[str] = []

    hypothesis_id = payload.get("hypothesis_id")
    evidence_tier = payload.get("evidence_tier")
    tier_blockers = payload.get("tier_blockers")
    acceptance_claim = _has_acceptance_claim(payload)

    missing_fields = [
        field
        for field, value in (
            ("hypothesis_id", hypothesis_id),
            ("evidence_tier", evidence_tier),
            ("tier_blockers", tier_blockers),
        )
        if value is None
    ]
    if missing_fields:
        message = f"missing_evidence_metadata:{rel}:{','.join(missing_fields)}"
        if strict_missing_metadata or acceptance_claim:
            blockers.append(message)
        else:
            warnings.append(message)

    if hypothesis_id is not None:
        if not isinstance(hypothesis_id, str) or not hypothesis_id:
            blockers.append(f"invalid_hypothesis_id:{rel}:{hypothesis_id}")
        elif hypothesis_id not in known_hypotheses:
            blockers.append(f"unknown_hypothesis_id:{rel}:{hypothesis_id}")

    if evidence_tier is not None and evidence_tier not in ALLOWED_TIERS:
        blockers.append(f"invalid_evidence_tier:{rel}:{evidence_tier}")

    if evidence_tier in {"E0", "E1"} and (not isinstance(tier_blockers, list) or not tier_blockers):
        blockers.append(f"low_tier_requires_tier_blockers:{rel}:{evidence_tier}")

    if acceptance_claim and evidence_tier not in {"E2", "E3"}:
        blockers.append(f"acceptance_claim_below_E2:{rel}:{evidence_tier}")

    return {
        "summary": {
            "path": rel,
            "hypothesis_id": hypothesis_id if isinstance(hypothesis_id, str) else None,
            "evidence_tier": evidence_tier if isinstance(evidence_tier, str) else None,
            "acceptance_claim": acceptance_claim,
            "blockers": blockers,
            "warnings": warnings,
        },
        "blockers": blockers,
        "warnings": warnings,
    }


def _has_acceptance_claim(payload: dict[str, Any]) -> bool:
    fields = (
        "conclusion",
        "research_decision",
        "strategy_integration_status",
        "acceptance_status",
        "research_acceptance_status",
        "operational_validation_status",
    )
    for field in fields:
        value = payload.get(field)
        if isinstance(value, str) and _is_acceptance_value(value):
            return True
    return False


def _is_acceptance_value(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in ACCEPTANCE_VALUES:
        return True
    return normalized.startswith("ผ่าน") or normalized.startswith("accepted") or normalized.startswith("approved")


def _iter_top_level_summaries(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for subdir in ("baselines", "experiments", "diagnostics"):
        folder = root / subdir
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.json")):
            if path.name.endswith(("_summary.json", "_evaluation.json", "_status.json", "_audit.json")):
                candidates.append(path)
    return candidates


def _load_known_hypotheses(path: Path) -> set[str]:
    payload = _load_json(path)
    hypotheses = payload.get("hypotheses", []) if isinstance(payload, dict) else []
    return {
        item["id"]
        for item in hypotheses
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"]
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate evidence-tier metadata and acceptance claims.")
    parser.add_argument("--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--reports-root", type=Path, default=DEFAULT_REPORTS_ROOT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--strict-missing-metadata", action="store_true")
    args = parser.parse_args(argv)

    result = validate_evidence_tiers(
        registry_path=args.registry_path,
        reports_root=args.reports_root,
        strict_missing_metadata=args.strict_missing_metadata,
    )
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
