from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_hypothesis_registry.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_hypothesis_registry", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load hypothesis registry validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidateHypothesisRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_registry_passes(self) -> None:
        result = self.validator.validate_hypothesis_registry()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual(7, result["hypothesis_count"])

    def test_rejects_missing_falsification_criteria(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "hypothesis_registry.json"
            registry = valid_registry()
            registry["hypotheses"][0]["falsification_criteria"] = []
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            result = self.validator.validate_hypothesis_registry(registry_path, reports_root=Path(tmp) / "reports")

        self.assertEqual("blocked", result["status"])
        self.assertIn("H-X1:falsification_criteria_must_be_non_empty_list", result["blockers"])

    def test_rejects_unknown_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "hypothesis_registry.json"
            registry = valid_registry()
            registry["hypotheses"][0]["dependencies"] = ["H-MISSING"]
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            result = self.validator.validate_hypothesis_registry(registry_path, reports_root=Path(tmp) / "reports")

        self.assertEqual("blocked", result["status"])
        self.assertIn("H-X1:unknown_dependency:H-MISSING", result["blockers"])

    def test_rejects_validated_status_without_e2_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "hypothesis_registry.json"
            registry = valid_registry()
            registry["hypotheses"][0]["status"] = "validated"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            result = self.validator.validate_hypothesis_registry(registry_path, reports_root=Path(tmp) / "reports")

        self.assertEqual("blocked", result["status"])
        self.assertIn("H-X1:validated_status_requires_E2_or_E3_evidence", result["blockers"])

    def test_rejects_summary_reference_to_unknown_hypothesis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = root / "hypothesis_registry.json"
            reports_root = root / "reports"
            reports_root.mkdir()
            registry_path.write_text(json.dumps(valid_registry()), encoding="utf-8")
            (reports_root / "summary.json").write_text(json.dumps({"hypothesis_id": "H-UNKNOWN"}), encoding="utf-8")

            result = self.validator.validate_hypothesis_registry(registry_path, reports_root=reports_root)

        self.assertEqual("blocked", result["status"])
        self.assertTrue(any(blocker.startswith("summary_references_unknown_hypothesis:H-UNKNOWN") for blocker in result["blockers"]))


def valid_registry() -> dict[str, object]:
    return {
        "schema_version": "hypothesis_registry_v1",
        "hypotheses": [
            {
                "id": "H-X1",
                "family": "subsystem_a",
                "status": "active",
                "statement": "Fixture hypothesis.",
                "economic_rationale": "Fixture rationale.",
                "testable_predictions": ["Prediction."],
                "validation_criteria": ["Validation."],
                "falsification_criteria": ["Falsification."],
                "required_data": ["Data."],
                "mintrl_falsify": {"status": "pending"},
                "evidence": [{"path": "reports/example.json", "evidence_tier": "E1"}],
                "dependencies": [],
                "decision_log": [{"date": "2026-07-03", "decision": "active"}],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
