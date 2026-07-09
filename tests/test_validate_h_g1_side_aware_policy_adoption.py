from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_h_g1_side_aware_policy_adoption.py"
ADOPTION_PATH = PROJECT_ROOT / "experiments" / "h_g1_side_aware_bucket_policy_adoption.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_h_g1_side_aware_policy_adoption", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 side-aware policy adoption validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_G1SideAwarePolicyAdoptionValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_adoption_passes(self) -> None:
        result = self.validator.validate_h_g1_side_aware_policy_adoption(ADOPTION_PATH)

        self.assertEqual("pass", result["status"])
        self.assertEqual("H-G1", result["hypothesis_id"])
        self.assertEqual("h_g1_required_bucket_policy_v3_side_aware", result["policy_id"])

    def test_validator_rejects_strategy_use_allowed(self) -> None:
        payload = json.loads(ADOPTION_PATH.read_text(encoding="utf-8"))
        payload["adoption_scope"]["strategy_use_allowed"] = True

        result = self._validate_payload(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("adoption_scope_strategy_use_allowed_not_false", result["blockers"])

    def test_validator_rejects_paid_data_allowed(self) -> None:
        payload = json.loads(ADOPTION_PATH.read_text(encoding="utf-8"))
        payload["adoption_scope"]["paid_data_allowed"] = True

        result = self._validate_payload(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("adoption_scope_paid_data_allowed_not_false", result["blockers"])

    def test_validator_rejects_hidden_opposite_right_rows(self) -> None:
        payload = json.loads(ADOPTION_PATH.read_text(encoding="utf-8"))
        payload["required_bucket_rules"]["opposite_right_itm_rows"]["must_remain_visible"] = False

        result = self._validate_payload(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("opposite_right_itm_not_visible", result["blockers"])

    def test_validator_rejects_wrong_candidate(self) -> None:
        payload = json.loads(ADOPTION_PATH.read_text(encoding="utf-8"))
        payload["adopted_candidate"] = "candidate_a_current_v2_moneyness_only"

        result = self._validate_payload(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("unexpected_adopted_candidate:candidate_a_current_v2_moneyness_only", result["blockers"])

    def _validate_payload(self, payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adoption.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return self.validator.validate_h_g1_side_aware_policy_adoption(path)


if __name__ == "__main__":
    unittest.main()

