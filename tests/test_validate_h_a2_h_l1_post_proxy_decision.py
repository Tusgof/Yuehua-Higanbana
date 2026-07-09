from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_h_l1_post_proxy_decision import validate_h_a2_h_l1_post_proxy_decision


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_h_l1_post_proxy_decision.json"


class ValidateHA2HL1PostProxyDecisionTests(unittest.TestCase):
    def test_current_decision_passes(self) -> None:
        result = validate_h_a2_h_l1_post_proxy_decision()

        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual("pre_register_h_a2_residual_adverse_day_analysis", result["selected_path"])
        self.assertIs(False, result["network_allowed"])
        self.assertIs(False, result["paid_data_allowed"])
        self.assertIs(False, result["llm_call_allowed"])
        self.assertIs(False, result["paper_trading_allowed"])

    def test_rejects_execution_permissions(self) -> None:
        data = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
        data["guardrails"]["network_allowed"] = True
        data["guardrails"]["paid_data_allowed"] = True
        data["guardrails"]["llm_call_allowed"] = True
        data["guardrails"]["paper_trading_allowed"] = True

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decision.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            result = validate_h_a2_h_l1_post_proxy_decision(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("network_allowed_must_be_false", result["blockers"])
        self.assertIn("paid_data_allowed_must_be_false", result["blockers"])
        self.assertIn("llm_call_allowed_must_be_false", result["blockers"])
        self.assertIn("paper_trading_allowed_must_be_false", result["blockers"])

    def test_rejects_live_llm_path(self) -> None:
        data = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
        data["selected_next_path"]["path_id"] = "live_llm_prompt_research_now"
        data["next_artifact_requirements"]["must_not_use_llm"] = False

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decision.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            result = validate_h_a2_h_l1_post_proxy_decision(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("selected_path_must_be_h_a2_residual_analysis", result["blockers"])
        self.assertIn("must_not_use_llm_must_be_true", result["blockers"])


if __name__ == "__main__":
    unittest.main()
