from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "experiments" / "hypothesis_registry.json"
DEFAULT_EVIDENCE_AUDIT_PATH = PROJECT_ROOT / "reports" / "evidence_tier_audit.json"
DEFAULT_READINESS_AUDIT_PATH = PROJECT_ROOT / "reports" / "research_readiness_audit.json"
DEFAULT_PAID_COST_AUDIT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "paid_cost_audit.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "research_acceptance_evaluation.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "research_acceptance_evaluation.md"

TIER_RANK = {"E0": 0, "E1": 1, "E2": 2, "E3": 3}
ACTIVE_STATUSES = {"active", "active_blocked", "parked", "proposed"}
REQUIRED_GATE_IDS = (
    "chronological_validation_without_oos_tuning",
    "mintrl_psr_dsr_handling",
    "implementable_pnl_with_cost_drag",
    "big_day_dependency_survival",
    "regime_coverage_or_explicit_scope_restriction",
    "benchmark_and_drawdown_comparison",
)
HARD_READINESS_BLOCKER_PREFIXES = (
    "requires_mintrl",
    "requires_wider_spy_0dte_data",
    "requires_real_news_archive",
    "requires_real_strategy_backtest_ablation",
    "requires_real_timestamp_clean_news_cases",
    "requires_news_",
    "gdelt_",
)


def evaluate_research_acceptance(
    *,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    evidence_audit_path: Path = DEFAULT_EVIDENCE_AUDIT_PATH,
    readiness_audit_path: Path = DEFAULT_READINESS_AUDIT_PATH,
    paid_cost_audit_path: Path = DEFAULT_PAID_COST_AUDIT_PATH,
) -> dict[str, Any]:
    registry = _load_json(registry_path)
    evidence_audit = _load_json(evidence_audit_path)
    readiness_audit = _load_json(readiness_audit_path)
    paid_cost_audit = _load_json(paid_cost_audit_path)

    hypotheses = _hypothesis_rows(registry, evidence_audit)
    candidates = [
        item
        for item in hypotheses
        if item["max_evidence_tier_rank"] >= TIER_RANK["E2"] and item["status"] in ACTIVE_STATUSES
    ]
    readiness_blockers = list(readiness_audit.get("blockers", []))
    hard_readiness_blockers = [
        blocker
        for blocker in readiness_blockers
        if any(str(blocker).startswith(prefix) for prefix in HARD_READINESS_BLOCKER_PREFIXES)
    ]

    blockers: list[str] = []
    if not candidates:
        blockers.append("no_strategy_hypothesis_at_e2_or_higher")
    if evidence_audit.get("status") != "pass":
        blockers.append("evidence_tier_audit_not_pass")
    if paid_cost_audit.get("status") != "pass":
        blockers.append("paid_cost_audit_not_pass")
    if readiness_audit.get("status") == "blocked" and (not candidates or hard_readiness_blockers):
        blockers.append("research_readiness_blocked")
    blockers.extend(f"readiness:{item}" for item in hard_readiness_blockers)
    candidate_gate_results = _evaluate_candidate_gate_results(candidates, registry_path=registry_path)
    for result in candidate_gate_results:
        for failed_gate in result["failed_gates"]:
            blockers.append(f"candidate:{result['hypothesis_id']}:{failed_gate}")

    if not candidates or blockers:
        status = "blocked"
    elif readiness_audit.get("status") == "blocked":
        status = "scope_restricted"
    else:
        status = "approved_for_operational_validation"

    return {
        "schema_version": "research_acceptance_evaluation_v1",
        "status": status,
        "research_acceptance_status": status,
        "hypothesis_count": len(hypotheses),
        "candidate_hypotheses": candidates,
        "candidate_gate_results": candidate_gate_results,
        "hypotheses": hypotheses,
        "blockers": sorted(set(blockers)),
        "hard_readiness_blockers": hard_readiness_blockers,
        "gate_requirements": ["registered_hypothesis_at_e2_or_higher", *REQUIRED_GATE_IDS, "paid_cost_guard_pass"],
        "operational_validation_allowed": status in {"approved_for_operational_validation", "scope_restricted"},
        "paper_trading_allowed": status in {"approved_for_operational_validation", "scope_restricted"},
        "real_money_allowed": False,
        "scope_restrictions": _scope_restrictions(readiness_blockers),
        "source_paths": {
            "registry": _relative(registry_path),
            "evidence_audit": _relative(evidence_audit_path),
            "readiness_audit": _relative(readiness_audit_path),
            "paid_cost_audit": _relative(paid_cost_audit_path),
        },
    }


def write_report(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Research Acceptance Evaluation",
        "",
        f"- Status: `{result['status']}`",
        f"- Operational validation allowed: `{result['operational_validation_allowed']}`",
        f"- Paper trading allowed: `{result['paper_trading_allowed']}`",
        f"- Real money allowed: `{result['real_money_allowed']}`",
        f"- Candidate hypotheses: {len(result['candidate_hypotheses'])}",
        "",
        "## Hypotheses",
        "",
        "| ID | Status | Max tier | E2+ candidate | Evidence paths |",
        "|:--|:--|:--|:--|--:|",
    ]
    for item in result["hypotheses"]:
        lines.append(
            f"| `{item['id']}` | `{item['status']}` | `{item['max_evidence_tier']}` | `{item['is_e2_candidate']}` | {item['evidence_path_count']} |"
        )

    lines.extend(["", "## Blockers", ""])
    if result["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in result["blockers"])
    else:
        lines.append("- none")

    lines.extend(["", "## Gate Requirements", ""])
    lines.extend(f"- `{item}`" for item in result["gate_requirements"])

    lines.extend(["", "## Candidate Gate Results", ""])
    if result["candidate_gate_results"]:
        lines.extend(
            [
                "| Hypothesis | Passed gates | Failed gates | Evidence paths |",
                "|:--|:--|:--|:--|",
            ]
        )
        for item in result["candidate_gate_results"]:
            lines.append(
                "| `{hypothesis}` | {passed} | {failed} | {paths} |".format(
                    hypothesis=item["hypothesis_id"],
                    passed=", ".join(f"`{gate}`" for gate in item["passed_gates"]) or "None",
                    failed=", ".join(f"`{gate}`" for gate in item["failed_gates"]) or "None",
                    paths=", ".join(f"`{path}`" for path in item["evidence_paths"]) or "None",
                )
            )
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _hypothesis_rows(registry: dict[str, Any], evidence_audit: dict[str, Any]) -> list[dict[str, Any]]:
    audit_tiers_by_hypothesis: dict[str, list[str]] = {}
    for summary in evidence_audit.get("summaries", []):
        if not isinstance(summary, dict):
            continue
        hypothesis_id = summary.get("hypothesis_id")
        tier = summary.get("evidence_tier")
        if isinstance(hypothesis_id, str) and isinstance(tier, str):
            audit_tiers_by_hypothesis.setdefault(hypothesis_id, []).append(tier)

    rows = []
    for hypothesis in registry.get("hypotheses", []):
        if not isinstance(hypothesis, dict):
            continue
        tiers = []
        evidence = hypothesis.get("evidence", [])
        if isinstance(evidence, list):
            tiers.extend(item.get("evidence_tier") for item in evidence if isinstance(item, dict))
        tiers.extend(audit_tiers_by_hypothesis.get(hypothesis.get("id"), []))
        valid_tiers = [tier for tier in tiers if tier in TIER_RANK]
        max_tier = max(valid_tiers, key=lambda tier: TIER_RANK[tier]) if valid_tiers else None
        max_rank = TIER_RANK[max_tier] if max_tier else -1
        e2_evidence_paths = [
            item.get("path")
            for item in evidence
            if isinstance(item, dict)
            and isinstance(item.get("path"), str)
            and TIER_RANK.get(item.get("evidence_tier"), -1) >= TIER_RANK["E2"]
        ]
        rows.append(
            {
                "id": hypothesis.get("id"),
                "family": hypothesis.get("family"),
                "status": hypothesis.get("status"),
                "max_evidence_tier": max_tier,
                "max_evidence_tier_rank": max_rank,
                "is_e2_candidate": max_rank >= TIER_RANK["E2"] and hypothesis.get("status") in ACTIVE_STATUSES,
                "evidence_path_count": len(evidence) if isinstance(evidence, list) else 0,
                "e2_evidence_paths": e2_evidence_paths,
            }
        )
    return rows


def _evaluate_candidate_gate_results(candidates: list[dict[str, Any]], *, registry_path: Path) -> list[dict[str, Any]]:
    results = []
    for candidate in candidates:
        evidence_payloads: list[tuple[str, dict[str, Any]]] = []
        evidence_errors: list[str] = []
        for raw_path in candidate.get("e2_evidence_paths", []):
            path = _resolve_evidence_path(str(raw_path), registry_path)
            if path is None:
                evidence_errors.append(f"missing_evidence_path:{raw_path}")
                continue
            try:
                payload = _load_json(path)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                evidence_errors.append(f"unreadable_evidence_path:{raw_path}:{exc.__class__.__name__}")
                continue
            evidence_payloads.append((_relative(path), payload))

        passed_gates = []
        failed_gates = list(evidence_errors)
        if not evidence_payloads:
            failed_gates.append("missing_e2_evidence_artifact")
        for gate_id in REQUIRED_GATE_IDS:
            if any(_payload_passes_gate(payload, gate_id) for _, payload in evidence_payloads):
                passed_gates.append(gate_id)
            else:
                failed_gates.append(gate_id)

        results.append(
            {
                "hypothesis_id": candidate["id"],
                "passed_gates": passed_gates,
                "failed_gates": failed_gates,
                "evidence_paths": [path for path, _ in evidence_payloads],
            }
        )
    return results


def _payload_passes_gate(payload: dict[str, Any], gate_id: str) -> bool:
    if gate_id == "chronological_validation_without_oos_tuning":
        if payload.get("no_oos_tuning") is True or payload.get("random_split_used") is False:
            return True
        return _deep_contains_value(payload, "oos_tuning", "forbidden") or _deep_contains_value(payload, "split_method", "chronological")
    if gate_id == "mintrl_psr_dsr_handling":
        return _has_resolved_mintrl_psr(payload) and _has_resolved_dsr(payload)
    if gate_id == "implementable_pnl_with_cost_drag":
        return _has_any_key(payload, {"implementable_pnl", "implementable_pnl_usd", "total_implementable_pnl", "total_implementable_pnl_usd"}) and _has_any_key(
            payload, {"cost_drag", "total_cost_drag", "friction_drag_ratio"}
        )
    if gate_id == "big_day_dependency_survival":
        return _has_status(payload, {"big_day_dependency", "big_day_dependency_result"}, {"pass", "passed", "survived"})
    if gate_id == "regime_coverage_or_explicit_scope_restriction":
        return _has_any_key(payload, {"regime_trade_counts", "regime_coverage", "regime_coverage_status", "scope_restrictions"})
    if gate_id == "benchmark_and_drawdown_comparison":
        return _has_any_key(payload, {"benchmark_comparison", "benchmark_and_drawdown_comparison"}) and _has_any_key(
            payload, {"max_drawdown", "drawdown_curve", "benchmark_drawdown_delta", "max_drawdown_delta"}
        )
    raise ValueError(f"Unknown gate id: {gate_id}")


def _has_resolved_mintrl_psr(payload: dict[str, Any]) -> bool:
    has_mintrl = _has_any_key(payload, {"mintrl", "minimum_track_record_length", "mintrl_status"})
    has_psr = _has_any_key(payload, {"psr", "probabilistic_sharpe_ratio", "psr_status"})
    if not (has_mintrl and has_psr):
        return False
    blocked_markers = {"blocked", "pending", "under-sampled", "underpowered", "insufficient"}
    return not any(marker in _string_values(payload, keys={"mintrl", "mintrl_status", "psr", "psr_status"}) for marker in blocked_markers)


def _has_resolved_dsr(payload: dict[str, Any]) -> bool:
    trial_count = _first_numeric_value(payload, {"trial_count", "independent_trial_count", "source_trial_count", "effective_trial_count"})
    if trial_count is None or trial_count <= 1:
        return True
    if _has_any_key(payload, {"dsr", "deflated_sharpe_ratio", "dsr_value"}):
        blocked_markers = {"blocked", "pending"}
        return not any(marker in _string_values(payload, keys={"dsr", "dsr_status"}) for marker in blocked_markers)
    return False


def _resolve_evidence_path(raw_path: str, registry_path: Path) -> Path | None:
    path = Path(raw_path)
    candidates = [path] if path.is_absolute() else [registry_path.parent / path, registry_path.parent.parent / path, PROJECT_ROOT / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _has_status(payload: dict[str, Any], keys: set[str], allowed: set[str]) -> bool:
    for item in _deep_values_for_keys(payload, keys):
        if isinstance(item, dict):
            status = item.get("status")
            if isinstance(status, str) and status.strip().lower() in allowed:
                return True
    return False


def _has_any_key(value: Any, keys: set[str]) -> bool:
    if isinstance(value, dict):
        return any(key in value for key in keys) or any(_has_any_key(item, keys) for item in value.values())
    if isinstance(value, list):
        return any(_has_any_key(item, keys) for item in value)
    return False


def _deep_contains_value(value: Any, key: str, expected: str) -> bool:
    if isinstance(value, dict):
        return any(
            (item_key == key and isinstance(item_value, str) and item_value.strip().lower() == expected)
            or _deep_contains_value(item_value, key, expected)
            for item_key, item_value in value.items()
        )
    if isinstance(value, list):
        return any(_deep_contains_value(item, key, expected) for item in value)
    return False


def _deep_values_for_keys(value: Any, keys: set[str]) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys:
                found.append(item)
            found.extend(_deep_values_for_keys(item, keys))
    elif isinstance(value, list):
        for item in value:
            found.extend(_deep_values_for_keys(item, keys))
    return found


def _string_values(value: Any, *, keys: set[str] | None = None) -> set[str]:
    values: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if keys is None or key in keys:
                if isinstance(item, str):
                    values.add(item.strip().lower())
                elif isinstance(item, dict):
                    status = item.get("status")
                    if isinstance(status, str):
                        values.add(status.strip().lower())
            values.update(_string_values(item, keys=keys))
    elif isinstance(value, list):
        for item in value:
            values.update(_string_values(item, keys=keys))
    return values


def _first_numeric_value(value: Any, keys: set[str]) -> float | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys and isinstance(item, (int, float)):
                return float(item)
            nested = _first_numeric_value(item, keys)
            if nested is not None:
                return nested
    elif isinstance(value, list):
        for item in value:
            nested = _first_numeric_value(item, keys)
            if nested is not None:
                return nested
    return None


def _scope_restrictions(readiness_blockers: list[Any]) -> list[str]:
    restrictions = []
    if any(str(item).startswith("requires_news_") or str(item).startswith("requires_real_news") for item in readiness_blockers):
        restrictions.append("news_llm_features_disallowed")
    if any(str(item).startswith("gdelt_") for item in readiness_blockers):
        restrictions.append("gdelt_capture_unavailable")
    if any(str(item).startswith("requires_mintrl") or str(item) == "requires_wider_spy_0dte_data" for item in readiness_blockers):
        restrictions.append("strategy_acceptance_sample_inadequate")
    return sorted(set(restrictions))


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
    parser = argparse.ArgumentParser(description="Evaluate whether any Higanbana hypothesis is ready for operational validation.")
    parser.add_argument("--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--evidence-audit-path", type=Path, default=DEFAULT_EVIDENCE_AUDIT_PATH)
    parser.add_argument("--readiness-audit-path", type=Path, default=DEFAULT_READINESS_AUDIT_PATH)
    parser.add_argument("--paid-cost-audit-path", type=Path, default=DEFAULT_PAID_COST_AUDIT_PATH)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = evaluate_research_acceptance(
        registry_path=args.registry_path,
        evidence_audit_path=args.evidence_audit_path,
        readiness_audit_path=args.readiness_audit_path,
        paid_cost_audit_path=args.paid_cost_audit_path,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(result, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
