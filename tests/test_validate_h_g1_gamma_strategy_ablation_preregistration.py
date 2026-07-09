from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_h_g1_gamma_strategy_ablation_preregistration.py"
PREREG_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_strategy_ablation_preregistration.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_h_g1_gamma_strategy_ablation_preregistration", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 strategy-ablation preregistration validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_G1GammaStrategyAblationPreregistrationValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_preregistration_passes(self) -> None:
        result = self.validator.validate_h_g1_gamma_strategy_ablation_preregistration(PREREG_PATH)

        self.assertEqual("pass", result["status"])
        self.assertEqual("H-G1", result["hypothesis_id"])
        self.assertEqual(4, result["variant_count"])

    def test_validator_rejects_strategy_pnl_in_preregistration(self) -> None:
        payload = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        payload["strategy_pnl_used"] = True

        result = self._validate_payload(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("strategy_pnl_used_not_false", result["blockers"])

    def test_validator_rejects_oos_tuning(self) -> None:
        payload = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        payload["chronological_split"]["oos_tuning_allowed"] = True

        result = self._validate_payload(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("oos_tuning_allowed_not_false", result["blockers"])

    def test_validator_rejects_missing_dsr_policy(self) -> None:
        payload = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        payload["search_log_policy"]["dsr_required_if_selecting_best"] = False

        result = self._validate_payload(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("dsr_required_if_selecting_best_not_true", result["blockers"])

    def test_validator_rejects_changed_trial_count(self) -> None:
        payload = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        payload["variant_count_policy"]["total_trial_count"] = 5

        result = self._validate_payload(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("trial_count_not_locked:5", result["blockers"])

    def test_validator_rejects_true_net_gamma_claim_without_inventory_source(self) -> None:
        payload = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        payload["proxy_wording_policy"]["forbidden_terms_without_inventory_source"].remove("true market-maker net gamma")

        result = self._validate_payload(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_forbidden_proxy_term:true market-maker net gamma", result["blockers"])

    def _validate_payload(self, payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return self.validator.validate_h_g1_gamma_strategy_ablation_preregistration(path)


if __name__ == "__main__":
    unittest.main()
