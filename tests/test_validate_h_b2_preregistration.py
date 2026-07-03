from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_h_b2_preregistration.py"
MANIFEST_PATH = PROJECT_ROOT / "experiments" / "h_b2_subsystem_b_scale_preregistration.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_h_b2_preregistration", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-B2 pre-registration validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_B2PreregistrationValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_manifest_passes(self) -> None:
        result = self.validator.validate_h_b2_preregistration(MANIFEST_PATH)

        self.assertEqual("pass", result["status"])
        self.assertEqual("H-B2", result["hypothesis_id"])
        self.assertEqual(8, result["independent_trial_count"])

    def test_validator_rejects_mutable_wing_grid(self) -> None:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        payload["strategy_template"]["protective_wing_gap_grid_usd"] = [10.0]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.validator.validate_h_b2_preregistration(path)

        self.assertEqual("blocked", result["status"])
        self.assertTrue(any(blocker.startswith("wing_grid_not_locked") for blocker in result["blockers"]))


if __name__ == "__main__":
    unittest.main()
