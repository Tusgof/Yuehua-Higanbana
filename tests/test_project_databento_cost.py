from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "project_databento_cost.py"


def load_projector():
    spec = importlib.util.spec_from_file_location("project_databento_cost", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Databento projector")
    module = importlib.util.module_from_spec(spec)
    sys.modules["project_databento_cost"] = module
    spec.loader.exec_module(module)
    return module


class DatabentoProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.projector = load_projector()

    def test_projection_uses_average_successful_live_window_cost(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.json"
            source.write_text(
                json.dumps(
                    {
                        "mode": "live",
                        "total_estimated_cost_usd": 0.06,
                        "errors": [],
                        "summary": {"scenarios": {"one_day_sample": {"request_count": 3}}},
                        "requests": [
                            {"estimated_cost_usd": 0.01},
                            {"estimated_cost_usd": 0.02},
                            {"estimated_cost_usd": 0.03},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = self.projector.project_costs(source)
            self.assertEqual(0.02, result["average_cost_per_window_usd"])
            self.assertEqual(3, result["projections"]["one_day_sample"]["request_count"])
            self.assertAlmostEqual(0.06, result["projections"]["one_day_sample"]["projected_cost_usd"])

    def test_projection_can_target_custom_date_range_and_window_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.json"
            source.write_text(
                json.dumps(
                    {
                        "mode": "live",
                        "total_estimated_cost_usd": 0.28,
                        "errors": [],
                        "summary": {"scenarios": {"insample_2023_12_sample": {"request_count": 14}}},
                        "requests": [{"estimated_cost_usd": 0.02} for _ in range(14)],
                    }
                ),
                encoding="utf-8",
            )
            result = self.projector.project_costs(
                source,
                target_scenario="oos_2024_2025",
                target_start_date=date(2023, 12, 1),
                target_end_date=date(2023, 12, 31),
                target_window_profile="intraday_exit_30m",
                target_scenario_label="insample_2023_12",
            )

            self.assertEqual(280, result["projections"]["insample_2023_12"]["request_count"])
            self.assertAlmostEqual(5.6, result["projections"]["insample_2023_12"]["projected_cost_usd"])
            self.assertNotIn("oos_2024_2025", result["projections"])

    def test_markdown_report_contains_use_rule(self) -> None:
        report = self.projector.render_markdown(
            {
                "source_path": "source.json",
                "source_scenario": "one_month_pilot",
                "source_mode": "live",
                "source_successful_request_count": 63,
                "source_error_count": 0,
                "average_cost_per_window_usd": 0.02,
                "projections": {"full_research": {"request_count": 3000, "projected_cost_usd": 60.0}},
            }
        )
        self.assertIn("# Databento Cost Projection", report)
        self.assertIn("Do not download data", report)


if __name__ == "__main__":
    unittest.main()
