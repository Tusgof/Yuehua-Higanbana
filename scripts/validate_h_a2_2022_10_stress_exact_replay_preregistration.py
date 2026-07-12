from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = PROJECT_ROOT / "experiments" / "h_a2_2022_10_stress_exact_replay_preregistration.json"


def validate(path: Path = DEFAULT_PATH) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    blockers: list[str] = []
    rule = payload.get("decision_rule", {})
    guardrails = payload.get("guardrails", {})
    if payload.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_H-A2")
    if rule.get("decision_time_et") != "09:35:00":
        blockers.append("decision_time_must_be_0935")
    if rule.get("future_1545_followthrough_as_decision_feature_allowed") is not False:
        blockers.append("future_followthrough_must_be_forbidden")
    if guardrails.get("lookahead_allowed") is not False:
        blockers.append("lookahead_must_be_forbidden")
    if payload.get("trade_density_checkpoint", {}).get("minimum_candidate_trades_for_september_stage") != 2:
        blockers.append("minimum_trade_density_must_be_2")
    return {"status": "pass" if not blockers else "blocked", "blockers": blockers}


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "pass" else 1)
