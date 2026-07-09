from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_h_g1_manifest_v3_plan.py"
PLAN_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration_v3_plan.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_h_g1_manifest_v3_plan", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 v3 plan validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_G1ManifestV3PlanValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_plan_passes(self) -> None:
        result = self.validator.validate_h_g1_manifest_v3_plan(PLAN_PATH)

        self.assertEqual("pass", result["status"])
        self.assertEqual("H-G1", result["hypothesis_id"])
        self.assertEqual("2023-07-12", result["blocked_bucket"]["date"])
        self.assertEqual("otm_put", result["blocked_bucket"]["bucket"])
        self.assertLess(result["blocked_bucket"]["computed_oi_notional_share"], 0.8)

    def test_validator_rejects_paid_action_before_concrete_manifest_validation(self) -> None:
        payload = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        payload["data_policy"]["paid_action_before_concrete_manifest_validation"] = "allowed"

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.validator.validate_h_g1_manifest_v3_plan(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_action_before_concrete_manifest_validation_not_forbidden", result["blockers"])

    def test_validator_rejects_post_hoc_gamma_selection_input(self) -> None:
        payload = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        payload["candidate_selection_rules"]["forbidden_selection_inputs"].remove("computed gamma proxy")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.validator.validate_h_g1_manifest_v3_plan(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_forbidden_selection_input:computed gamma proxy", result["blockers"])

    def test_validator_rejects_wrong_replacement_target(self) -> None:
        payload = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        payload["replacement_objective"]["target_split"] = "oos"

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.validator.validate_h_g1_manifest_v3_plan(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("unexpected_replacement_target_split:oos", result["blockers"])


if __name__ == "__main__":
    unittest.main()
