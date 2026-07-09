from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from lib.environment import data_root
from tests.tiers import state_audit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "plan_h_a2_2022_h2_stress_purchase.py"


def load_module():
    spec = importlib.util.spec_from_file_location("plan_h_a2_2022_h2_stress_purchase", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-A2 stress purchase planner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@state_audit(("HIGANBANA_DATA_ROOT", data_root()))
class HA22022H2StressPurchasePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_plan_selects_top_vix_months_without_paid_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.module.build_estimate(
                summary_path=root / "summary.json",
                report_path=root / "report.md",
            )

        self.assertEqual("complete", result["status"])
        self.assertEqual("projection_no_databento_api_call", result["mode"])
        self.assertTrue(result["no_new_paid_data"])
        ranked_months = [row["month"] for row in result["ranked_2022_h2_months"]]
        self.assertEqual("2022-10", ranked_months[0])
        self.assertEqual("2022-09", ranked_months[1])
        self.assertEqual(["2022-10", "2022-09"], result["purchase_candidates"][0]["months"])
        self.assertEqual(["2022-10", "2022-09", "2022-07"], result["purchase_candidates"][1]["months"])
        self.assertGreater(result["cost_guard"]["remaining_before_stop_usd"], 0)
        self.assertIn(result["recommendation"]["status"], {"live_cost_check_top2_only", "pause_until_topup_or_live_cost_lower"})


if __name__ == "__main__":
    unittest.main()
