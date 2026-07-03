from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "estimate_databento_cost.py"


def load_estimator():
    spec = importlib.util.spec_from_file_location("estimate_databento_cost", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Databento estimator")
    module = importlib.util.module_from_spec(spec)
    sys.modules["estimate_databento_cost"] = module
    spec.loader.exec_module(module)
    return module


class DatabentoCostEstimatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.estimator = load_estimator()

    def test_one_day_sample_builds_three_research_windows(self) -> None:
        requests = self.estimator.build_cost_requests("one_day_sample", start_date=date(2024, 1, 3))
        self.assertEqual(3, len(requests))
        self.assertEqual({"entry_a_0935", "entry_b_1000", "forced_close_1545"}, {request.window.split("_", 1)[1] for request in requests})
        self.assertTrue(all(request.dataset == "OPRA.PILLAR" for request in requests))
        self.assertTrue(all(request.schema == "cbbo-1m" for request in requests))
        self.assertTrue(all(request.symbols == ["SPY.OPT"] for request in requests))
        self.assertTrue(all(request.stype_in == "parent" for request in requests))

    def test_intraday_exit_profile_adds_target_stop_check_windows(self) -> None:
        requests = self.estimator.build_cost_requests(
            "one_day_sample",
            start_date=date(2024, 1, 3),
            window_profile="intraday_exit_30m",
        )
        window_names = [request.window.split("_", 1)[1] for request in requests]

        self.assertEqual(14, len(requests))
        self.assertIn("entry_a_0935", window_names)
        self.assertIn("entry_b_1000", window_names)
        self.assertIn("exit_check_1030", window_names)
        self.assertIn("exit_check_1530", window_names)
        self.assertIn("forced_close_1545", window_names)

    def test_one_month_pilot_skips_weekends(self) -> None:
        requests = self.estimator.build_cost_requests(
            "one_month_pilot",
            start_date=date(2024, 1, 6),
            end_date=date(2024, 1, 8),
        )
        self.assertEqual(3, len(requests))
        self.assertTrue(all(request.window.startswith("2024-01-08") for request in requests))

    def test_one_month_pilot_skips_us_market_holidays(self) -> None:
        requests = self.estimator.build_cost_requests(
            "one_month_pilot",
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 16),
        )
        self.assertEqual(3, len(requests))
        self.assertTrue(all(request.window.startswith("2024-01-16") for request in requests))

    def test_good_friday_is_not_a_market_session(self) -> None:
        self.assertFalse(self.estimator.is_market_session_date(date(2024, 3, 29)))

    def test_dry_run_does_not_require_api_key(self) -> None:
        requests = self.estimator.build_cost_requests("one_day_sample", start_date=date(2024, 1, 3))
        plan = self.estimator.render_plan(requests)
        self.assertEqual("dry_run", plan["mode"])
        self.assertEqual(3, len(plan["requests"]))
        self.assertEqual(3, plan["summary"]["total_request_count"])
        self.assertIn("upper-bound", plan["warning"])

    def test_summary_groups_requests_by_scenario(self) -> None:
        requests = []
        requests.extend(self.estimator.build_cost_requests("one_day_sample", start_date=date(2024, 1, 3)))
        requests.extend(
            self.estimator.build_cost_requests(
                "one_month_pilot",
                start_date=date(2024, 1, 8),
                end_date=date(2024, 1, 8),
            )
        )
        summary = self.estimator.summarize_requests(requests)
        self.assertEqual(6, summary["total_request_count"])
        self.assertEqual(3, summary["scenarios"]["one_day_sample"]["request_count"])
        self.assertEqual(3, summary["scenarios"]["one_month_pilot"]["request_count"])

    def test_daily_union_coalesces_intraday_windows_to_one_cost_request_per_day(self) -> None:
        requests = self.estimator.build_cost_requests(
            "one_day_sample",
            start_date=date(2024, 1, 3),
            window_profile="intraday_exit_30m",
        )
        coalesced = self.estimator.coalesce_cost_requests(requests, "daily_union")

        self.assertEqual(14, len(requests))
        self.assertEqual(1, len(coalesced))
        self.assertEqual("2024-01-03_daily_union", coalesced[0].window)
        self.assertEqual(min(request.start for request in requests), coalesced[0].start)
        self.assertEqual(max(request.end for request in requests), coalesced[0].end)
        self.assertIn("14 planned research window", coalesced[0].note)

    def test_daily_union_keeps_separate_market_dates(self) -> None:
        requests = self.estimator.build_cost_requests(
            "one_month_pilot",
            start_date=date(2024, 1, 3),
            end_date=date(2024, 1, 4),
            window_profile="intraday_exit_30m",
        )
        coalesced = self.estimator.coalesce_cost_requests(requests, "daily_union")

        self.assertEqual(28, len(requests))
        self.assertEqual(2, len(coalesced))
        self.assertEqual(["2024-01-03_daily_union", "2024-01-04_daily_union"], [request.window for request in coalesced])

    def test_custom_scenario_label_is_used_in_requests_and_summary(self) -> None:
        requests = self.estimator.build_cost_requests(
            "oos_2024_2025",
            start_date=date(2023, 12, 1),
            end_date=date(2023, 12, 1),
            scenario_label="insample_2023_12",
        )
        summary = self.estimator.summarize_requests(requests)

        self.assertTrue(all(request.scenario == "insample_2023_12" for request in requests))
        self.assertEqual(3, summary["scenarios"]["insample_2023_12"]["request_count"])
        self.assertNotIn("oos_2024_2025", summary["scenarios"])

    def test_live_cost_guard_blocks_too_many_requests_before_api_key_lookup(self) -> None:
        requests = self.estimator.build_cost_requests(
            "one_month_pilot",
            start_date=date(2024, 1, 8),
            end_date=date(2024, 1, 9),
        )
        with self.assertRaises(RuntimeError) as context:
            self.estimator.estimate_live_cost(requests, max_live_requests=3)
        self.assertIn("refusing 6 live Databento cost calls", str(context.exception))

    def test_default_databento_key_env_falls_back_to_project_alias(self) -> None:
        previous_default = os.environ.get("DATABENTO_API_KEY")
        previous_alias = os.environ.get("DATABENTO_SPY0DTE_API")
        os.environ.pop("DATABENTO_API_KEY", None)
        os.environ["DATABENTO_SPY0DTE_API"] = "test-key"
        try:
            self.assertEqual("test-key", self.estimator._databento_api_key_from_env())
        finally:
            if previous_default is not None:
                os.environ["DATABENTO_API_KEY"] = previous_default
            else:
                os.environ.pop("DATABENTO_API_KEY", None)
            if previous_alias is not None:
                os.environ["DATABENTO_SPY0DTE_API"] = previous_alias
            else:
                os.environ.pop("DATABENTO_SPY0DTE_API", None)

    def test_markdown_report_contains_scenario_summary_and_decision_rule(self) -> None:
        requests = self.estimator.build_cost_requests("one_day_sample", start_date=date(2024, 1, 3))
        report = self.estimator.render_markdown_report(self.estimator.render_plan(requests))
        self.assertIn("# Databento Cost Estimate Report", report)
        self.assertIn("`one_day_sample`", report)
        self.assertIn("Total estimated cost**: not available in dry-run mode", report)
        self.assertIn("Do not download data", report)

    def test_cli_writes_markdown_report_without_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "databento_report.md"
            requests = self.estimator.build_cost_requests("one_day_sample", start_date=date(2024, 1, 3))
            report_path.write_text(self.estimator.render_markdown_report(self.estimator.render_plan(requests)), encoding="utf-8")
            self.assertIn("Scenario Summary", report_path.read_text(encoding="utf-8"))

    def test_json_report_payload_is_machine_readable(self) -> None:
        requests = self.estimator.build_cost_requests("one_day_sample", start_date=date(2024, 1, 3))
        result = self.estimator.add_cost_decision(self.estimator.render_plan(requests))
        self.assertEqual("review", result["decision"]["status"])
        self.assertEqual(3, result["summary"]["total_request_count"])

    def test_cost_decision_marks_dry_run_for_review(self) -> None:
        requests = self.estimator.build_cost_requests("one_day_sample", start_date=date(2024, 1, 3))
        result = self.estimator.add_cost_decision(self.estimator.render_plan(requests))
        self.assertEqual("review", result["decision"]["status"])
        self.assertIn("Dry-run has no dollar estimate", result["decision"]["reason"])

    def test_cost_decision_pass_review_and_block_thresholds(self) -> None:
        low = self.estimator.add_cost_decision({"mode": "live", "total_estimated_cost_usd": 1.0, "requests": []})
        mid = self.estimator.add_cost_decision({"mode": "live", "total_estimated_cost_usd": 5.0, "requests": []})
        high = self.estimator.add_cost_decision({"mode": "live", "total_estimated_cost_usd": 25.0, "requests": []})
        self.assertEqual("pass", low["decision"]["status"])
        self.assertEqual("review", mid["decision"]["status"])
        self.assertEqual("block", high["decision"]["status"])

    def test_cost_decision_reviews_live_errors_even_when_cost_is_low(self) -> None:
        result = self.estimator.add_cost_decision(
            {
                "mode": "live",
                "total_estimated_cost_usd": 1.0,
                "requests": [],
                "errors": [{"window": "2024-01-15_entry_a_0935", "error": "no data"}],
            }
        )
        self.assertEqual("review", result["decision"]["status"])
        self.assertIn("request error", result["decision"]["reason"])

    def test_markdown_report_includes_decision_status(self) -> None:
        result = self.estimator.add_cost_decision(
            {
                "mode": "live",
                "total_estimated_cost_usd": 1.0,
                "requests": [],
                "planned_request_count": 14,
                "live_request_count": 1,
                "cost_granularity": "daily_union",
            }
        )
        report = self.estimator.render_markdown_report(result)
        self.assertIn("**Decision**: `pass`", report)
        self.assertIn("**Planned research windows**: 14", report)
        self.assertIn("**Live cost request count**: 1", report)
        self.assertIn("**Cost granularity**: `daily_union`", report)


if __name__ == "__main__":
    unittest.main()
