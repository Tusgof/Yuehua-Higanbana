from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "download_h_g1_gamma_oi_data.py"
COST_REPORT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "h_g1_gamma_oi_12_date_cost_estimate.json"
V3_COST_REPORT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "h_g1_gamma_oi_v3_replacement_cost_estimate.json"


def load_downloader():
    spec = importlib.util.spec_from_file_location("download_h_g1_gamma_oi_data", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 OI downloader")
    module = importlib.util.module_from_spec(spec)
    sys.modules["download_h_g1_gamma_oi_data"] = module
    spec.loader.exec_module(module)
    return module


class H_G1GammaOiDownloaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.downloader = load_downloader()

    def test_build_download_plan_uses_cost_gate_requests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = self.downloader.build_download_plan(COST_REPORT_PATH, Path(tmp))

        self.assertEqual("H-G1", plan["hypothesis_id"])
        self.assertEqual("pass", plan["cost_gate_decision"]["status"])
        self.assertEqual(11, plan["request_count"])
        self.assertTrue(all(row["raw_path"].endswith("_full_utc_day_statistics.dbn.zst") for row in plan["requests"]))

    def test_plan_blocks_without_execute(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = self.downloader.build_download_plan(COST_REPORT_PATH, Path(tmp))
            result = self.downloader.build_result(
                plan,
                paid_cost_audit={
                    "status": "pass",
                    "cost_guard_basis": "user_reported_actual_usage",
                    "cost_guard_used_usd": 105.0,
                    "remaining_before_stop_usd": 20.0,
                },
                execution=None,
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("requires_execute", result["blockers"])

    def test_execute_downloads_accepts_injected_downloader(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = self.downloader.build_download_plan(COST_REPORT_PATH, Path(tmp))
            plan["requests"] = plan["requests"][:2]
            plan["request_count"] = 2
            execution = self.downloader.execute_downloads(
                plan,
                downloader=lambda request: {**request, "source": "downloaded", "bytes": 12, "sha256": "abc"},
            )
            result = self.downloader.build_result(
                plan,
                paid_cost_audit={
                    "status": "pass",
                    "cost_guard_basis": "user_reported_actual_usage",
                    "cost_guard_used_usd": 105.0,
                    "remaining_before_stop_usd": 20.0,
                },
                execution=execution,
            )

        self.assertEqual("pass", result["status"])
        self.assertEqual("download_complete", result["mode"])
        self.assertEqual(2, execution["downloaded_count"])
        self.assertEqual(24, execution["total_bytes"])

    def test_v3_download_plan_preserves_replacement_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = self.downloader.build_download_plan(V3_COST_REPORT_PATH, Path(tmp))
            execution = self.downloader.execute_downloads(
                plan,
                downloader=lambda request: {**request, "source": "downloaded", "bytes": 12, "sha256": "abc"},
            )
            result = self.downloader.build_result(
                plan,
                paid_cost_audit={
                    "status": "pass",
                    "cost_guard_basis": "user_reported_actual_usage",
                    "cost_guard_used_usd": 109.082227,
                    "remaining_before_stop_usd": 15.917773,
                },
                execution=execution,
            )

        self.assertEqual("h_g1_gamma_oi_v3_replacement", plan["scenario"])
        self.assertEqual(1, plan["request_count"])
        self.assertEqual("2023-09-13", plan["requests"][0]["date"])
        self.assertEqual("pass", result["status"])
        self.assertEqual("h_g1_gamma_oi_v3_replacement", result["scenario"])

    def test_blocks_when_cost_gate_does_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = self.downloader.build_download_plan(COST_REPORT_PATH, Path(tmp))
            plan["cost_gate_decision"] = {"status": "blocked", "download_allowed_under_current_guard": False}
            execution = {"downloads": [], "errors": [], "downloaded_count": 0, "cache_count": 0, "total_bytes": 0}
            result = self.downloader.build_result(
                plan,
                paid_cost_audit={
                    "status": "pass",
                    "cost_guard_basis": "user_reported_actual_usage",
                    "cost_guard_used_usd": 105.0,
                    "remaining_before_stop_usd": 20.0,
                },
                execution=execution,
            )

        self.assertIn("cost_gate_not_pass", result["blockers"])

    def test_cli_plan_writes_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_report = Path(tmp) / "download.json"
            md_report = Path(tmp) / "download.md"
            returncode = self.downloader.main(
                [
                    "--cost-report",
                    str(COST_REPORT_PATH),
                    "--raw-root",
                    str(Path(tmp) / "raw"),
                    "--json-report",
                    str(json_report),
                    "--md-report",
                    str(md_report),
                ]
            )

            self.assertEqual(0, returncode)
            result = json.loads(json_report.read_text(encoding="utf-8"))
            self.assertEqual("download_plan", result["mode"])
            self.assertIn("H-G1 Gamma/OI Download Result", md_report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
