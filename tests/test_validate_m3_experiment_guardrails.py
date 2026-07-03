from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_m3_experiment_guardrails.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_m3_experiment_guardrails", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M3 guardrail validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidateM3ExperimentGuardrailsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_guardrails_pass(self) -> None:
        result = self.validator.validate_guardrails()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual(10, result["experiment_count"])

    def test_rejects_random_split_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path, guardrail_path = self.write_case(Path(tmp))
            guardrails = json.loads(guardrail_path.read_text(encoding="utf-8"))
            guardrails["defaults"]["validation_policy"]["split_method"] = "random_kfold"
            guardrail_path.write_text(json.dumps(guardrails), encoding="utf-8")

            result = self.validator.validate_guardrails(manifest_path, guardrail_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("exp01_test:forbidden_split_method:random_kfold", result["blockers"])

    def test_rejects_missing_search_log_policy_for_required_experiment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path, guardrail_path = self.write_case(Path(tmp))
            guardrails = json.loads(guardrail_path.read_text(encoding="utf-8"))
            guardrails["defaults"]["search_log_policy"]["trial_count_required"] = False
            guardrail_path.write_text(json.dumps(guardrails), encoding="utf-8")

            result = self.validator.validate_guardrails(manifest_path, guardrail_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("exp01_test:search_log_policy.trial_count_required_must_be_true", result["blockers"])

    def test_rejects_bad_strike_mapping_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path, guardrail_path = self.write_case(Path(tmp))
            guardrails = json.loads(guardrail_path.read_text(encoding="utf-8"))
            guardrails["defaults"]["strike_mapping_policy"]["method"] = "continuous_moneyness_interpolation"
            guardrail_path.write_text(json.dumps(guardrails), encoding="utf-8")

            result = self.validator.validate_guardrails(manifest_path, guardrail_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("exp01_test:strike_mapping_policy.unsupported_method:continuous_moneyness_interpolation", result["blockers"])

    def test_rejects_non_chronological_windows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path, guardrail_path = self.write_case(Path(tmp))
            manifests = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifests[0]["train_window"] = {"start": "2024-01-01", "end": "2024-12-31"}
            manifest_path.write_text(json.dumps(manifests), encoding="utf-8")

            result = self.validator.validate_guardrails(manifest_path, guardrail_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("exp01_test:non_chronological_windows", result["blockers"])
        self.assertIn("exp01_test:unexpected_train_start:2024-01-01", result["blockers"])

    @staticmethod
    def write_case(root: Path) -> tuple[Path, Path]:
        manifest_path = root / "experiment_manifests.json"
        guardrail_path = root / "m3_experiment_guardrails.json"
        manifest_path.write_text(json.dumps([valid_manifest()]), encoding="utf-8")
        guardrail_path.write_text(json.dumps(valid_guardrails()), encoding="utf-8")
        return manifest_path, guardrail_path


def valid_manifest() -> dict[str, object]:
    return {
        "record_type": "experiment_manifest",
        "schema_version": "m2.0",
        "experiment_id": "exp01_test",
        "hypothesis": "Search-aware guardrail fixture.",
        "data_window": {"start": "2022-05-11", "end": "2026-06-29"},
        "train_window": {"start": "2022-05-11", "end": "2023-12-31"},
        "oos_window": {"start": "2024-01-01", "end": "2026-06-29"},
        "parameters_locked_before_oos": True,
        "metrics": ["sharpe", "max_drawdown"],
    }


def valid_guardrails() -> dict[str, object]:
    return {
        "schema_version": "m3_guardrails_v1",
        "defaults": {
            "validation_policy": {
                "split_method": "chronological",
                "forbid_random_split": True,
                "forbid_oos_tuning": True,
                "fit_only_before_decision_timestamp": True,
                "allowed_split_methods": ["chronological", "expanding_window", "rolling_window", "purged_embargoed"],
            },
            "search_log_policy": {
                "trial_count_required": True,
                "parameter_grid_required": True,
                "record_all_trials_required": True,
                "dsr_required_if_selecting_best_sharpe": True,
                "dsr_blocker_allowed_if_search_log_incomplete": True,
                "search_log_path_template": "reports/experiments/search_logs/{experiment_id}_search_log.jsonl",
            },
            "strike_mapping_policy": {
                "method": "nearest_discrete_strike_rounding",
                "tie_breaker": "prefer_lower_debit_then_nearest_defined_risk",
                "interpolation_allowed_for_research_only": False,
                "disclose_in_report": True,
            },
        },
        "experiments": {
            "exp01_test": {
                "requires_search_log_policy": True,
                "requires_strike_mapping_policy": True,
            }
        },
    }


if __name__ == "__main__":
    unittest.main()
