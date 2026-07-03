from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "plan_macro_calendar_capture_commands.py"


def load_planner():
    spec = importlib.util.spec_from_file_location("plan_macro_calendar_capture_commands", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load macro calendar capture command planner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PlanMacroCalendarCaptureCommandsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.planner = load_planner()

    def test_plans_source_by_source_commands_for_2022_2025(self) -> None:
        result = self.planner.plan_capture_commands(start_year=2022, end_year=2025)

        self.assertEqual("dry_run", result["mode"])
        self.assertEqual(5, result["source_count"])
        self.assertEqual(20, result["command_count"])
        self.assertIn("--as-of-date 2022-12-31 --source-id federal_reserve_fomc_calendar --execute", result["commands"][0]["command"])
        self.assertEqual("2025-12-31", result["commands"][-1]["as_of_date"])

    def test_rejects_reversed_year_range(self) -> None:
        with self.assertRaisesRegex(self.planner.MacroCalendarCaptureCommandPlanError, "start_year"):
            self.planner.plan_capture_commands(start_year=2025, end_year=2022)


if __name__ == "__main__":
    unittest.main()
