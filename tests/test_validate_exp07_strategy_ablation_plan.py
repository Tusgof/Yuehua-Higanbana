from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_exp07_strategy_ablation_plan.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_exp07_strategy_ablation_plan", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Exp07 ablation validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidateExp07StrategyAblationPlanTests(unittest.TestCase):
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

    def test_rejects_raw_llm_gate_that_can_block_trades(self) -> None:
        plan = json.loads(json.dumps(self.plan))
        for variant in plan["policy_variants"]:
            if variant["variant_id"] == "raw_llm_observation_only":
                variant["can_block_trade"] = True
        errors = self.validator.validate_plan(self.write_plan(plan))
        self.assertTrue(any("raw_llm_observation_only cannot block trades" in error for error in errors))

    def test_rejects_missing_tail_risk_metric(self) -> None:
        plan = json.loads(json.dumps(self.plan))
        plan["required_metrics"].remove("es99")
        errors = self.validator.validate_plan(self.write_plan(plan))
        self.assertTrue(any("missing required metrics" in error and "es99" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
