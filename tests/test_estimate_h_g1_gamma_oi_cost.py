from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "estimate_h_g1_gamma_oi_cost.py"
MANIFEST_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration.json"


def load_estimator():
    spec = importlib.util.spec_from_file_location("estimate_h_g1_gamma_oi_cost", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 OI cost estimator")
    module = importlib.util.module_from_spec(spec)
    sys.modules["estimate_h_g1_gamma_oi_cost"] = module
    spec.loader.exec_module(module)
    return module


class H_G1GammaOiCostEstimatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.estimator = load_estimator()

    def test_build_full_day_requests_uses_only_missing_oi_dates(self) -> None:
        _manifest, requests, existing = self.estimator.build_full_day_requests(MANIFEST_PATH)

        self.assertEqual(11, len(requests))
        self.assertEqual([{"date": "2024-01-03", "opra_oi_status": "existing_probe"}], existing)
        self.assertNotIn("2024-01-03", {request.date for request in requests})
        self.assertTrue(all(request.schema == "statistics" for request in requests))
        self.assertTrue(all(request.symbols == ["SPY.OPT"] for request in requests))
        self.assertTrue(all(request.start.endswith("T00:00:00+00:00") for request in requests))
        self.assertTrue(all(request.window.endswith("_full_utc_day_statistics") for request in requests))

    def test_live_cost_result_uses_injected_provider_without_download(self) -> None:
        _manifest, requests, _existing = self.estimator.build_full_day_requests(MANIFEST_PATH)
        result = self.estimator.estimate_live_cost(requests[:2], cost_provider=lambda _request: 0.35)

        self.assertEqual("live_metadata_cost_no_download", result["mode"])
        self.assertFalse(result["download_performed"])
        self.assertEqual(2, result["live_request_count"])
        self.assertEqual(0.7, result["total_estimated_cost_usd"])
        self.assertEqual([], result["errors"])

    def test_decision_passes_when_live_estimate_fits_headroom(self) -> None:
        manifest, requests, existing = self.estimator.build_full_day_requests(MANIFEST_PATH)
        cost = self.estimator.estimate_live_cost(requests[:2], cost_provider=lambda _request: 0.5)
        result = self.estimator.build_result(
            manifest,
            requests[:2],
            existing,
            cost,
            manifest_validation={"status": "pass"},
            paid_cost_audit={
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 105.0,
                "stop_threshold_usd": 125.0,
                "remaining_before_stop_usd": 20.0,
            },
        )

        self.assertEqual("pass", result["decision"]["status"])
        self.assertTrue(result["decision"]["download_allowed_under_current_guard"])
        self.assertEqual(106.0, result["projected_usage_if_downloaded_usd"])

    def test_decision_blocks_when_estimate_exceeds_headroom(self) -> None:
        manifest, requests, existing = self.estimator.build_full_day_requests(MANIFEST_PATH)
        cost = self.estimator.estimate_live_cost(requests[:2], cost_provider=lambda _request: 11.0)
        result = self.estimator.build_result(
            manifest,
            requests[:2],
            existing,
            cost,
            manifest_validation={"status": "pass"},
            paid_cost_audit={
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 105.0,
                "stop_threshold_usd": 125.0,
                "remaining_before_stop_usd": 20.0,
            },
        )

        self.assertEqual("blocked", result["decision"]["status"])
        self.assertIn("estimated_cost_exceeds_remaining_headroom", result["decision"]["blockers"])
        self.assertFalse(result["decision"]["download_allowed_under_current_guard"])

    def test_dry_run_requires_live_metadata_before_download(self) -> None:
        manifest, requests, existing = self.estimator.build_full_day_requests(MANIFEST_PATH)
        result = self.estimator.build_result(
            manifest,
            requests,
            existing,
            None,
            manifest_validation={"status": "pass"},
            paid_cost_audit={
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 105.0,
                "stop_threshold_usd": 125.0,
                "remaining_before_stop_usd": 20.0,
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
                    "--manifest-path",
                    str(MANIFEST_PATH),
                    "--json-report",
                    str(json_report),
                    "--md-report",
                    str(md_report),
                ]
            )

            self.assertEqual(0, returncode)
            result = json.loads(json_report.read_text(encoding="utf-8"))
            self.assertEqual("dry_run_no_download", result["mode"])
            self.assertIn("H-G1 Gamma/OI Cost Gate", md_report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
