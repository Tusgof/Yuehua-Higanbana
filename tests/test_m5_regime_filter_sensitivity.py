from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_m5_regime_filter_sensitivity.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_m5_regime_filter_sensitivity", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M5.5 regime filter module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_m5_regime_filter_sensitivity"] = module
    spec.loader.exec_module(module)
    return module


class M5RegimeFilterSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def test_default_scenarios_cover_vix_macro_and_combined_filters(self) -> None:
        scenarios = self.runner.default_scenarios()
        scenario_ids = {row["scenario_id"] for row in scenarios}

        self.assertEqual(9, len(scenarios))
        self.assertIn("unfiltered_control", scenario_ids)
        self.assertIn("vix_15_25_prev_close", scenario_ids)
        self.assertIn("exclude_major_macro_same_day", scenario_ids)
        self.assertIn("vix_15_25_non_inverted_exclude_major_macro", scenario_ids)

    def test_previous_vix_record_uses_prior_date_only(self) -> None:
        rows = [
            {"date": "2024-01-02", "vix_close": 13.0, "vxv_close": 15.0},
            {"date": "2024-01-03", "vix_close": 99.0, "vxv_close": 100.0},
        ]

        result = self.runner.previous_vix_record("2024-01-03", rows)

        self.assertEqual("2024-01-02", result["date"])
        self.assertEqual(13.0, result["vix_close"])

    def test_filter_decision_blocks_major_macro_same_day(self) -> None:
        scenario = self.runner.scenario("exclude_major_macro_same_day", exclude_event_types=["CPI", "NFP"])
        vix_rows = [{"date": "2024-01-10", "vix_close": 18.0, "vxv_close": 20.0}]
        macro_by_date = {
            "2024-01-11": [
                {"event_timestamp_et": "2024-01-11T08:30:00-05:00", "event_type": "CPI", "importance": "high"}
            ]
        }

        decision = self.runner.filter_decision("2024-01-11", scenario, vix_rows, macro_by_date)

        self.assertFalse(decision["allow"])
        self.assertIn("same-day excluded macro event: CPI", decision["reasons"])

    def test_novi_blocker_requires_real_inputs(self) -> None:
        blocker = self.runner.novi_net_gamma_blocker()

        self.assertEqual("blocked_missing_inputs", blocker["status"])
        self.assertIn("open interest", blocker["reason"])
        self.assertIn("gamma", blocker["reason"])

    def test_write_search_log_writes_all_filter_trials(self) -> None:
        rows = [
            {
                "trial_index": 1,
                "scenario_id": "unfiltered_control",
                "vix_min": None,
                "vix_max": None,
                "require_non_inverted_term": False,
                "exclude_high_importance_macro": False,
                "exclude_event_types": [],
                "vix_timestamp_policy": "previous_available_close_before_trade_date",
                "macro_timestamp_policy": "scheduled_same_day_known_before_entry",
                "candidate_days_before_filter": 2,
                "filtered_out_trades": 0,
                "closed_trades": 2,
                "metrics": {"trade_count": 2},
                "sample_adequacy": {"labels": ["under-sampled"]},
            },
            {
                "trial_index": 2,
                "scenario_id": "vix_below_25_prev_close",
                "vix_min": None,
                "vix_max": 25.0,
                "require_non_inverted_term": False,
                "exclude_high_importance_macro": False,
                "exclude_event_types": [],
                "vix_timestamp_policy": "previous_available_close_before_trade_date",
                "macro_timestamp_policy": "scheduled_same_day_known_before_entry",
                "candidate_days_before_filter": 2,
                "filtered_out_trades": 1,
                "closed_trades": 1,
                "metrics": {"trade_count": 1},
                "sample_adequacy": {"labels": ["under-sampled"]},
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "search.jsonl"
            self.runner.write_search_log(rows, path)
            lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(2, len(lines))
        self.assertEqual("m5_regime_filter_sensitivity", lines[0]["experiment_id"])
        self.assertEqual(25.0, lines[1]["parameters"]["vix_max"])


if __name__ == "__main__":
    unittest.main()
