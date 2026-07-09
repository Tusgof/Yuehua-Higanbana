from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "estimate_h_a2_independent_validation_cost.py"
PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_independent_validation_paid_cost_plan_preregistration.json"
NORMAL_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_normal_control_sample_decision.json"


def load_estimator():
    spec = importlib.util.spec_from_file_location("estimate_h_a2_independent_validation_cost", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-A2 independent validation cost estimator")
    module = importlib.util.module_from_spec(spec)
    sys.modules["estimate_h_a2_independent_validation_cost"] = module
    spec.loader.exec_module(module)
    return module


class H_A2IndependentValidationCostEstimatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.estimator = load_estimator()

    def test_sample_batch_builds_one_day_option_and_underlying_requests(self) -> None:
        _prereg, batch, requests = self.estimator.build_batch_requests(PREREG_PATH)

        self.assertEqual("sample_cost_probe_high_vix_one_day", batch["batch_id"])
        self.assertEqual(15, len(requests))
        self.assertEqual({"2025-04-08"}, {request.date for request in requests})
        self.assertEqual(14, sum(1 for request in requests if request.dataset == "OPRA.PILLAR"))
        self.assertEqual(1, sum(1 for request in requests if request.dataset == "EQUS.MINI"))
        self.assertEqual("2025-04-08T13:30:00+00:00", requests[0].start)
        self.assertEqual("2025-04-08T13:40:00+00:00", requests[0].end)
        self.assertIn("2025-04-08_forced_close_1545", {request.window for request in requests})

    def test_normal_control_batch_builds_ten_days_of_metadata_requests(self) -> None:
        _decision, batch, requests = self.estimator.build_batch_requests(
            NORMAL_DECISION_PATH,
            "low_normal_vix_control_pack",
        )

        self.assertEqual("low_normal_vix_control_pack", batch["batch_id"])
        self.assertEqual(150, len(requests))
        self.assertEqual(10, len({request.date for request in requests}))
        self.assertEqual(140, sum(1 for request in requests if request.dataset == "OPRA.PILLAR"))
        self.assertEqual(10, sum(1 for request in requests if request.dataset == "EQUS.MINI"))
        self.assertIn("2025-02-03_entry_0935", {request.window for request in requests})
        self.assertIn("2025-02-14_forced_close_1545", {request.window for request in requests})

    def test_live_cost_result_uses_injected_provider_without_download(self) -> None:
        _prereg, _batch, requests = self.estimator.build_batch_requests(PREREG_PATH)
        result = self.estimator.estimate_live_cost(requests[:3], cost_provider=lambda _request: 0.1)

        self.assertEqual("live_metadata_cost_no_download", result["mode"])
        self.assertFalse(result["download_performed"])
        self.assertEqual(3, result["live_request_count"])
        self.assertEqual(0.3, result["total_estimated_cost_usd"])
        self.assertEqual([], result["errors"])

    def test_grouped_live_cost_reduces_normal_control_metadata_calls(self) -> None:
        _decision, _batch, requests = self.estimator.build_batch_requests(
            NORMAL_DECISION_PATH,
            "low_normal_vix_control_pack",
        )
        result = self.estimator.estimate_live_cost(
            requests,
            cost_provider=lambda _request: 0.1,
            group_requests=True,
        )

        self.assertEqual("live_metadata_cost_no_download_grouped_conservative", result["mode"])
        self.assertEqual(150, result["planned_request_count"])
        self.assertEqual(20, result["live_request_count"])
        self.assertEqual(150, result["grouped_from_request_count"])
        self.assertEqual(2.0, result["total_estimated_cost_usd"])
        self.assertIn("2025-02-03_opra_grouped_0930_1550", {request["window"] for request in result["requests"]})

    def test_decision_passes_metadata_estimate_but_still_forbids_download(self) -> None:
        prereg, batch, requests = self.estimator.build_batch_requests(PREREG_PATH)
        cost = self.estimator.estimate_live_cost(requests, cost_provider=lambda _request: 0.01)
        result = self.estimator.build_result(
            prereg,
            batch,
            requests,
            cost,
            prereg_validation={"status": "pass"},
            paid_cost_audit={
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 119.989706,
                "stop_threshold_usd": 125.0,
                "remaining_before_stop_usd": 5.010294,
            },
        )

        self.assertEqual("metadata_estimate_pass_next_download_decision_required", result["decision"]["status"])
        self.assertFalse(result["decision"]["download_allowed_under_current_guard"])
        self.assertTrue(result["decision"]["separate_download_decision_required"])
        self.assertEqual(120.139706, result["projected_usage_if_downloaded_usd"])

    def test_normal_control_decision_uses_selected_key_policy(self) -> None:
        decision, batch, requests = self.estimator.build_batch_requests(
            NORMAL_DECISION_PATH,
            "low_normal_vix_control_pack",
        )
        cost = self.estimator.estimate_live_cost(requests[:2], cost_provider=lambda _request: 0.01)
        result = self.estimator.build_result(
            decision,
            batch,
            requests[:2],
            cost,
            prereg_validation={"status": "pass"},
            paid_cost_audit={
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 120.494368,
                "stop_threshold_usd": 125.0,
                "remaining_before_stop_usd": 4.505632,
                "budget_policy": {
                    "per_key_caps_usd": {"DATABENTO_API_MO": 100.0},
                    "combined_pool_caps_usd": {"DATABENTO_API_MO+DATABENTO_API_AI": 200.0},
                },
            },
            selected_key_env="DATABENTO_API_MO",
        )

        self.assertEqual("DATABENTO_API_MO", result["selected_key_env_for_metadata_estimate"])
        self.assertEqual(100.0, result["selected_key_policy"]["selected_key_cap_usd"])
        self.assertEqual(200.0, result["selected_key_policy"]["mo_ai_combined_pool_cap_usd"])
        self.assertEqual("mo_ai_pool", result["selected_key_policy"]["active_guard"])
        self.assertFalse(result["selected_key_policy"]["key_value_stored"])

    def test_mo_ai_pool_does_not_use_legacy_remaining_headroom_as_blocker(self) -> None:
        decision, batch, requests = self.estimator.build_batch_requests(
            NORMAL_DECISION_PATH,
            "low_normal_vix_control_pack",
        )
        cost = self.estimator.estimate_live_cost(requests, cost_provider=lambda _request: 0.05)
        result = self.estimator.build_result(
            decision,
            batch,
            requests,
            cost,
            prereg_validation={"status": "pass"},
            paid_cost_audit={
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 120.494368,
                "stop_threshold_usd": 125.0,
                "remaining_before_stop_usd": 4.505632,
                "budget_policy": {
                    "per_key_caps_usd": {"DATABENTO_API_MO": 100.0},
                    "combined_pool_caps_usd": {"DATABENTO_API_MO+DATABENTO_API_AI": 200.0},
                },
            },
            selected_key_env="DATABENTO_API_MO",
        )

        self.assertEqual(7.5, result["cost_result"]["total_estimated_cost_usd"])
        self.assertEqual("metadata_estimate_pass_next_download_decision_required", result["decision"]["status"])
        self.assertNotIn("estimated_cost_exceeds_remaining_headroom", result["decision"]["blockers"])

    def test_decision_blocks_when_estimate_exceeds_headroom(self) -> None:
        prereg, batch, requests = self.estimator.build_batch_requests(PREREG_PATH)
        cost = self.estimator.estimate_live_cost(requests, cost_provider=lambda _request: 1.0)
        result = self.estimator.build_result(
            prereg,
            batch,
            requests,
            cost,
            prereg_validation={"status": "pass"},
            paid_cost_audit={
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 119.989706,
                "stop_threshold_usd": 125.0,
                "remaining_before_stop_usd": 5.010294,
            },
        )

        self.assertEqual("blocked", result["decision"]["status"])
        self.assertIn("estimated_cost_exceeds_remaining_headroom", result["decision"]["blockers"])
        self.assertFalse(result["decision"]["download_allowed_under_current_guard"])

    def test_dry_run_requires_live_metadata_before_download_decision(self) -> None:
        prereg, batch, requests = self.estimator.build_batch_requests(PREREG_PATH)
        result = self.estimator.build_result(
            prereg,
            batch,
            requests,
            None,
            prereg_validation={"status": "pass"},
            paid_cost_audit={
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 119.989706,
                "stop_threshold_usd": 125.0,
                "remaining_before_stop_usd": 5.010294,
            },
        )

        self.assertEqual("dry_run_no_download", result["mode"])
        self.assertIn("requires_live_metadata_cost", result["decision"]["blockers"])

    def test_cli_dry_run_writes_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_report = Path(tmp) / "cost.json"
            md_report = Path(tmp) / "cost.md"
            returncode = self.estimator.main(
                [
                    "--prereg-path",
                    str(PREREG_PATH),
                    "--json-report",
                    str(json_report),
                    "--md-report",
                    str(md_report),
                ]
            )

            self.assertEqual(0, returncode)
            result = json.loads(json_report.read_text(encoding="utf-8"))
            self.assertEqual("dry_run_no_download", result["mode"])
            self.assertIn("requires_live_metadata_cost", result["decision"]["blockers"])
            self.assertIn("H-A2 Independent Validation Cost Gate", md_report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
