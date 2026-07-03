from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "plan_databento_spy_bars.py"


def load_planner():
    spec = importlib.util.spec_from_file_location("plan_databento_spy_bars", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Databento SPY bars planner")
    module = importlib.util.module_from_spec(spec)
    sys.modules["plan_databento_spy_bars"] = module
    spec.loader.exec_module(module)
    return module


class DatabentoSpyBarsPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.planner = load_planner()

    def test_default_api_key_env_matches_project_config(self) -> None:
        self.assertEqual("DATABENTO_API_KEY", self.planner.DEFAULT_API_KEY_ENV)

    def test_default_databento_key_env_falls_back_to_project_alias(self) -> None:
        previous_default = os.environ.get("DATABENTO_API_KEY")
        previous_alias = os.environ.get("DATABENTO_SPY0DTE_API")
        os.environ.pop("DATABENTO_API_KEY", None)
        os.environ["DATABENTO_SPY0DTE_API"] = "test-key"
        try:
            self.assertEqual("test-key", self.planner._databento_api_key_from_env())
        finally:
            if previous_default is not None:
                os.environ["DATABENTO_API_KEY"] = previous_default
            else:
                os.environ.pop("DATABENTO_API_KEY", None)
            if previous_alias is not None:
                os.environ["DATABENTO_SPY0DTE_API"] = previous_alias
            else:
                os.environ.pop("DATABENTO_SPY0DTE_API", None)

    def test_default_plan_requires_review_without_live_cost(self) -> None:
        plan = self.planner.build_plan()
        self.assertEqual("review", plan["decision"]["status"])
        self.assertEqual("EQUS.MINI", plan["request"]["dataset"])
        self.assertEqual("ohlcv-1m", plan["request"]["schema"])
        self.assertIsNone(plan["request"]["estimated_cost_usd"])

    def test_small_live_cost_plan_passes_inside_approved_scope(self) -> None:
        plan = self.planner.build_plan(estimated_cost_usd=0.01)
        self.assertEqual("pass", plan["decision"]["status"])
        self.assertIn("approved scope", plan["decision"]["reason"])


if __name__ == "__main__":
    unittest.main()
