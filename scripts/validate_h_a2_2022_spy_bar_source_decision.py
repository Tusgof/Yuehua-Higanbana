from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_2022_spy_bar_source_decision.json"
DEFAULT_BLOCKER_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_spy_bars_plan_h_a2_2022_10_unavailable.json"
DEFAULT_DOC_PATH = PROJECT_ROOT / "docs" / "H_A2_2022_SPY_BAR_SOURCE_DECISION.md"


def validate_h_a2_2022_spy_bar_source_decision(
    decision_path: Path = DEFAULT_DECISION_PATH,
    blocker_path: Path = DEFAULT_BLOCKER_PATH,
    doc_path: Path = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    decision = _load_json(decision_path)
    blocker = _load_json(blocker_path)
    doc_text = doc_path.read_text(encoding="utf-8") if doc_path.exists() else ""

    if decision.get("schema_version") != "h_a2_2022_spy_bar_source_decision_v1":
        blockers.append("unsupported_schema_version")
    if decision.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if decision.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if decision.get("status") != "decision_complete":
        blockers.append("status_must_be_decision_complete")
    if decision.get("selected_next_action") != "run_no_paid_ibkr_data_only_probe_if_local_ibkr_setup_is_available":
        blockers.append("selected_next_action_must_be_no_paid_ibkr_probe")

    if blocker.get("status") != "blocked":
        blockers.append("databento_blocker_must_be_blocked")
    if blocker.get("decision") != "databento_cannot_supply_2022_10_spy_underlying_bars":
        blockers.append("databento_blocker_decision_mismatch")
    if blocker.get("available_start") != "2023-03-28T00:00:00+00:00":
        blockers.append("databento_available_start_mismatch")

    required_data = decision.get("required_data", {})
    if required_data.get("symbol") != "SPY":
        blockers.append("required_symbol_must_be_spy")
    if required_data.get("bar_size") != "1 minute":
        blockers.append("required_bar_size_must_be_1_minute")
    if "2022-10-03" not in required_data.get("minimum_window", "") or "2022-10-31" not in required_data.get("minimum_window", ""):
        blockers.append("minimum_window_must_cover_2022_10")

    if decision.get("paid_data_allowed_by_this_decision") is not False:
        blockers.append("paid_data_allowed_by_this_decision_must_be_false")
    for field in ["research_log_required", "paper_trading_allowed", "live_trading_allowed"]:
        if decision.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    providers = {item.get("provider"): item for item in decision.get("fallback_order", [])}
    ibkr = providers.get("IBKR TWS API")
    if not ibkr:
        blockers.append("ibkr_candidate_missing")
    else:
        if ibkr.get("rank") != 1:
            blockers.append("ibkr_must_be_rank_1")
        if ibkr.get("approval_required_before_execute") is not False:
            blockers.append("ibkr_data_only_probe_should_not_require_purchase_approval")

    for paid_provider in ["FirstRate Data", "Alpha Vantage Premium", "Massive/Polygon-style stock aggregates"]:
        item = providers.get(paid_provider)
        if not item:
            blockers.append(f"{paid_provider}_candidate_missing")
        elif item.get("approval_required_before_execute") is not True:
            blockers.append(f"{paid_provider}_must_require_explicit_approval")

    forbidden_text = "\n".join(decision.get("forbidden_actions", []))
    for phrase in [
        "Do not buy 2022-09 option data",
        "Do not buy a new paid provider",
        "Do not transmit orders",
        "Do not rerun H-A2 stress diagnostics",
    ]:
        if phrase not in forbidden_text:
            blockers.append(f"missing_forbidden_action:{phrase}")

    for phrase in [
        "Do not buy 2022-09 option data",
        "IBKR can be used only as a data-only source",
        "IEX-only bars cannot become acceptance-grade",
    ]:
        if phrase not in doc_text:
            blockers.append(f"decision_doc_missing:{phrase}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "decision_path": _relative(decision_path),
        "selected_next_action": decision.get("selected_next_action"),
        "databento_blocker": blocker.get("decision"),
        "paid_data_allowed_by_this_decision": decision.get("paid_data_allowed_by_this_decision"),
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the H-A2 2022 SPY bar source decision artifact.")
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    parser.add_argument("--blocker-path", type=Path, default=DEFAULT_BLOCKER_PATH)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_2022_spy_bar_source_decision(args.decision_path, args.blocker_path, args.doc_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
