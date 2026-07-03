from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_exp07_real_news_case_plan.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_exp07_real_news_case_plan", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Exp07 real-news case validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidateExp07RealNewsCasePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()
        cls.plan = cls.validator.load_plan()

    def write_plan(self, plan: dict) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
        with tmp:
            json.dump(plan, tmp)
        return Path(tmp.name)

    def test_default_plan_validates(self) -> None:
        self.assertEqual([], self.validator.validate_plan())

    def test_rejects_synthetic_research_cases(self) -> None:
        plan = json.loads(json.dumps(self.plan))
        plan["acceptance_bar"]["synthetic_cases_allowed_for_research"] = True

        errors = self.validator.validate_plan(self.write_plan(plan))

        self.assertTrue(any("synthetic_cases_allowed_for_research must be false" in error for error in errors))

    def test_rejects_missing_prompt_family(self) -> None:
        plan = json.loads(json.dumps(self.plan))
        plan["prompt_template_families"] = [
            family for family in plan["prompt_template_families"] if family["family_id"] != "evidence_first_rubric"
        ]

        errors = self.validator.validate_plan(self.write_plan(plan))

        self.assertTrue(any("missing prompt template families" in error and "evidence_first_rubric" in error for error in errors))

    def test_rejects_zero_captured_without_blocker(self) -> None:
        plan = json.loads(json.dumps(self.plan))
        plan["blockers"].remove("requires_real_timestamp_clean_news_cases")

        errors = self.validator.validate_plan(self.write_plan(plan))

        self.assertTrue(any("0 captured candidates" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
