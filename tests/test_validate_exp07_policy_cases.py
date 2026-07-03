from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_exp07_policy_cases.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Exp07PolicyCaseValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_module(VALIDATOR_PATH, "validate_exp07_policy_cases")
        cls.cases = cls.validator.load_policy_case_rows()

    def write_cases(self, cases: list[dict]) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "cases.json"
        path.write_text(json.dumps(cases, indent=2), encoding="utf-8")
        return path

    def write_spec(self, spec: dict) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "spec.json"
        path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        return path

    def test_default_fixture_validates(self) -> None:
        self.assertEqual(43, len(self.cases))
        self.assertEqual([], self.validator.validate_policy_cases())

    def test_default_policy_spec_covers_every_fixture_case_once(self) -> None:
        spec = self.validator.load_policy_spec()
        errors = self.validator.validate_policy_spec(spec, self.cases)

        self.assertEqual([], errors)

    def test_rejects_duplicate_case_id(self) -> None:
        cases = json.loads(json.dumps(self.cases))
        cases[1]["case_id"] = cases[0]["case_id"]

        errors = self.validator.validate_policy_cases(self.write_cases(cases))

        self.assertTrue(any("duplicate case_id" in error for error in errors))

    def test_rejects_embedded_preclassified_policy(self) -> None:
        cases = json.loads(json.dumps(self.cases))
        cases[0]["prompt_input"]["preclassified_event_policy"] = {"decision": "allow"}

        errors = self.validator.validate_policy_cases(self.write_cases(cases))

        self.assertTrue(any("must not embed preclassified_event_policy" in error for error in errors))

    def test_rejects_missing_required_prompt_field(self) -> None:
        cases = json.loads(json.dumps(self.cases))
        del cases[0]["prompt_input"]["news_items"]

        errors = self.validator.validate_policy_cases(self.write_cases(cases))

        self.assertTrue(any("prompt_input missing news_items" in error for error in errors))
        self.assertTrue(any("news_items must be a non-empty array" in error for error in errors))

    def test_rejects_expected_decision_drift(self) -> None:
        cases = json.loads(json.dumps(self.cases))
        cases[0]["expected_decision"] = "block"

        errors = self.validator.validate_policy_cases(self.write_cases(cases))

        self.assertTrue(any("does not match preclassified decision=allow" in error for error in errors))

    def test_rejects_policy_spec_missing_case(self) -> None:
        spec = self.validator.load_policy_spec()
        spec["categories"][0]["case_ids"].remove("quiet_vix18_normal_term_structure")

        errors = self.validator.validate_policy_cases(spec_path=self.write_spec(spec))

        self.assertTrue(any("policy spec missing case_id quiet_vix18_normal_term_structure" in error for error in errors))

    def test_rejects_policy_spec_case_in_wrong_decision_category(self) -> None:
        spec = self.validator.load_policy_spec()
        spec["categories"][0]["case_ids"].append("systemic_banking_panic_vix34")

        errors = self.validator.validate_policy_cases(spec_path=self.write_spec(spec))

        self.assertTrue(any("does not match category decision=allow" in error for error in errors))
        self.assertTrue(any("policy spec duplicate case_id systemic_banking_panic_vix34" in error for error in errors))

    def test_rejects_policy_spec_duplicate_category_id(self) -> None:
        spec = self.validator.load_policy_spec()
        spec["categories"][1]["category_id"] = spec["categories"][0]["category_id"]

        errors = self.validator.validate_policy_cases(spec_path=self.write_spec(spec))

        self.assertTrue(any("duplicate category_id" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
