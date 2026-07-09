from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_h_g1_regime_date_set.py"
MANIFEST_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration.json"
V2_MANIFEST_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration_v2.json"
V3_MANIFEST_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration_v3.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_h_g1_regime_date_set", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 date-set validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_G1RegimeDateSetValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_manifest_passes(self) -> None:
        result = self.validator.validate_h_g1_regime_date_set(MANIFEST_PATH)

        self.assertEqual("pass", result["status"])
        self.assertEqual("H-G1", result["hypothesis_id"])
        self.assertEqual(12, result["date_count"])
        self.assertGreaterEqual(result["volatility_bucket_counts"]["high"], 3)
        self.assertGreaterEqual(result["split_counts"]["oos"], 4)

    def test_v2_repair_manifest_passes_with_ten_usable_dates(self) -> None:
        result = self.validator.validate_h_g1_regime_date_set(V2_MANIFEST_PATH)

        self.assertEqual("pass", result["status"])
        self.assertEqual("H-G1", result["hypothesis_id"])
        self.assertEqual(10, result["date_count"])
        self.assertGreaterEqual(result["volatility_bucket_counts"]["high"], 3)
        self.assertGreaterEqual(result["split_counts"]["in_sample"], 4)
        self.assertGreaterEqual(result["split_counts"]["oos"], 4)

    def test_v3_replacement_manifest_passes_with_one_cost_check_date(self) -> None:
        result = self.validator.validate_h_g1_regime_date_set(V3_MANIFEST_PATH)

        self.assertEqual("pass", result["status"])
        self.assertEqual("H-G1", result["hypothesis_id"])
        self.assertEqual(10, result["date_count"])
        self.assertEqual(1, result["opra_oi_status_counts"]["needs_metadata_cost_check"])
        self.assertGreaterEqual(result["volatility_bucket_counts"]["low"], 3)
        self.assertGreaterEqual(result["split_counts"]["in_sample"], 4)

    def test_v3_rejects_removed_date_still_present(self) -> None:
        payload = json.loads(V3_MANIFEST_PATH.read_text(encoding="utf-8"))
        for item in payload["selected_dates"]:
            if item["date"] == "2023-09-13":
                item["date"] = "2023-07-12"

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.validator.validate_h_g1_regime_date_set(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("v3_removed_date_still_present:2023-07-12", result["blockers"])

    def test_validator_rejects_missing_high_vol_regime(self) -> None:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        for item in payload["selected_dates"]:
            if item["volatility_bucket"] == "high":
                item["volatility_bucket"] = "normal"

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.validator.validate_h_g1_regime_date_set(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("minimum_count_not_met:high_volatility:0<3", result["blockers"])

    def test_validator_rejects_paid_action_before_validation(self) -> None:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        payload["data_policy"]["paid_action_before_manifest_validation"] = "allowed"

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.validator.validate_h_g1_regime_date_set(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_action_before_manifest_validation_not_forbidden", result["blockers"])


if __name__ == "__main__":
    unittest.main()
