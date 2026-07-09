from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_h_a2_2022_spy_bar_source_decision.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_h_a2_2022_spy_bar_source_decision", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-A2 SPY bar source decision validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidateHA2SpyBarSourceDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_decision_artifact_passes(self) -> None:
        result = self.validator.validate_h_a2_2022_spy_bar_source_decision()

        self.assertEqual("pass", result["status"])
        self.assertEqual("run_no_paid_ibkr_data_only_probe_if_local_ibkr_setup_is_available", result["selected_next_action"])
        self.assertFalse(result["paid_data_allowed_by_this_decision"])

    def test_blocks_paid_provider_without_approval_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision_path = root / "decision.json"
            decision = json.loads(
                (PROJECT_ROOT / "experiments" / "h_a2_2022_spy_bar_source_decision.json").read_text(encoding="utf-8")
            )
            decision["paid_data_allowed_by_this_decision"] = True
            for item in decision["fallback_order"]:
                if item["provider"] == "FirstRate Data":
                    item["approval_required_before_execute"] = False
            decision_path.write_text(json.dumps(decision), encoding="utf-8")

            result = self.validator.validate_h_a2_2022_spy_bar_source_decision(decision_path=decision_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_allowed_by_this_decision_must_be_false", result["blockers"])
        self.assertIn("FirstRate Data_must_require_explicit_approval", result["blockers"])

    def test_blocks_removing_2022_09_forbidden_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision_path = root / "decision.json"
            decision = json.loads(
                (PROJECT_ROOT / "experiments" / "h_a2_2022_spy_bar_source_decision.json").read_text(encoding="utf-8")
            )
            decision["forbidden_actions"] = [
                item for item in decision["forbidden_actions"] if "2022-09 option data" not in item
            ]
            decision_path.write_text(json.dumps(decision), encoding="utf-8")

            result = self.validator.validate_h_a2_2022_spy_bar_source_decision(decision_path=decision_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_forbidden_action:Do not buy 2022-09 option data", result["blockers"])


if __name__ == "__main__":
    unittest.main()
