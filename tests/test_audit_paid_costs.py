from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_paid_costs.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("audit_paid_costs", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load paid cost auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditPaidCostsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = load_auditor()

    def test_current_committed_cost_remains_under_stop_threshold(self) -> None:
        result = self.auditor.audit_paid_costs()

        self.assertEqual("pass", result["status"])
        self.assertGreaterEqual(result["known_committed_estimated_cost_usd"], result["stop_threshold_usd"])
        self.assertEqual("user_reported_actual_usage", result["cost_guard_basis"])
        self.assertLess(result["cost_guard_used_usd"], result["stop_threshold_usd"])
        self.assertGreater(result["remaining_before_stop_usd"], 0)
        self.assertTrue(result["committed_items"])
        reconciliation = result["cost_guard_reconciliation"]
        self.assertEqual("pass", reconciliation["actual_usage_basis"]["status"])
        self.assertEqual(64.64, reconciliation["actual_usage_basis"]["used_usd"])
        self.assertEqual(60.36, reconciliation["actual_usage_basis"]["remaining_usd"])
        self.assertEqual("blocked", reconciliation["known_committed_estimate_basis"]["status"])
        self.assertEqual(169.90613, reconciliation["known_committed_estimate_basis"]["used_usd"])
        self.assertEqual(-44.90613, reconciliation["known_committed_estimate_basis"]["remaining_usd"])
        self.assertFalse(any(item["item_id"] == "spy_bars:2024_08_chunk5" for item in result["estimated_only_items"]))

    def test_temp_cost_root_sums_completed_downloads_without_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "databento_download_result_alpha.json").write_text(
                json.dumps({"mode": "download_complete", "scenario": "alpha", "total_estimated_cost_usd": 2.5}),
                encoding="utf-8",
            )
            (root / "databento_cost_alpha.json").write_text(
                json.dumps({"mode": "live", "scenario": "alpha", "total_estimated_cost_usd": 2.5}),
                encoding="utf-8",
            )
            (root / "databento_cost_beta_dryrun.json").write_text(
                json.dumps({"mode": "dry_run", "scenario": "beta"}),
                encoding="utf-8",
            )
            (root / "databento_spy_bars_download_result_2023_09.json").write_text(
                json.dumps({"mode": "download_complete", "request": {"estimated_cost_usd": 0.1}}),
                encoding="utf-8",
            )
            (root / "databento_opra_statistics_oi_download_probe_2024_01_03.json").write_text(
                json.dumps(
                    {
                        "mode": "opra_statistics_oi_download_probe",
                        "status": "pass",
                        "plan": {"estimated_cost_usd": 0.354911148548, "window": "2024-01-03_full_utc_day_statistics"},
                    }
                ),
                encoding="utf-8",
            )

            result = self.auditor.audit_paid_costs(root, stop_threshold_usd=10.0, experiment_root=root / "experiments")

        self.assertEqual("pass", result["status"])
        self.assertEqual(2.954911, result["known_committed_estimated_cost_usd"])
        self.assertEqual([], result["estimated_only_items"])

    def test_stop_threshold_blocks_when_committed_cost_reaches_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "databento_download_result_alpha.json").write_text(
                json.dumps({"mode": "download_complete", "scenario": "alpha", "total_estimated_cost_usd": 101.0}),
                encoding="utf-8",
            )

            result = self.auditor.audit_paid_costs(root, stop_threshold_usd=100.0, experiment_root=root / "experiments")

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_cost_stop_threshold_reached", result["blockers"])

    def test_user_reported_actual_usage_overrides_guard_basis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            usage_path = root / "user_reported_actual_usage.json"
            (root / "databento_download_result_alpha.json").write_text(
                json.dumps({"mode": "download_complete", "scenario": "alpha", "total_estimated_cost_usd": 92.0}),
                encoding="utf-8",
            )
            usage_path.write_text(
                json.dumps(
                    {
                        "actual_usage_usd": 49.37,
                        "reported_at_utc": "2026-06-30T19:27:41Z",
                        "source": "user_reported_databento_account_usage",
                    }
                ),
                encoding="utf-8",
            )

            result = self.auditor.audit_paid_costs(
                root,
                stop_threshold_usd=125.0,
                experiment_root=root / "experiments",
                user_reported_usage_path=usage_path,
            )

        self.assertEqual("pass", result["status"])
        self.assertEqual(92.0, result["known_committed_estimated_cost_usd"])
        self.assertEqual("user_reported_actual_usage", result["cost_guard_basis"])
        self.assertEqual(49.37, result["cost_guard_used_usd"])
        self.assertEqual(75.63, result["remaining_before_stop_usd"])
        self.assertEqual(75.63, result["cost_guard_reconciliation"]["actual_usage_basis"]["remaining_usd"])
        self.assertEqual(33.0, result["cost_guard_reconciliation"]["known_committed_estimate_basis"]["remaining_usd"])

    def test_pending_spy_bars_plan_is_estimated_only_until_download_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "databento_spy_bars_plan_2024_08_chunk5.json").write_text(
                json.dumps({"mode": "plan", "request": {"estimated_cost_usd": 0.001630961895}}),
                encoding="utf-8",
            )

            result = self.auditor.audit_paid_costs(root, stop_threshold_usd=10.0, experiment_root=root / "experiments")

        self.assertEqual(
            [{"estimated_cost_usd": 0.001631, "item_id": "spy_bars:2024_08_chunk5", "mode": "plan", "provider": "Databento", "scenario": None, "source_path": str(root / "databento_spy_bars_plan_2024_08_chunk5.json")}],
            result["estimated_only_items"],
        )

    def test_openrouter_prompt_summary_cost_is_counted_when_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_cost_root = root / "data_cost"
            experiment_root = root / "experiments"
            data_cost_root.mkdir()
            experiment_root.mkdir()
            (data_cost_root / "databento_download_result_alpha.json").write_text(
                json.dumps({"mode": "download_complete", "scenario": "alpha", "total_estimated_cost_usd": 2.5}),
                encoding="utf-8",
            )
            (experiment_root / "exp07_prompt_v13_summary.json").write_text(
                json.dumps(
                    {
                        "mode": "live_openrouter",
                        "assessment_count": 3,
                        "openrouter_costed_assessment_count": 3,
                        "openrouter_actual_cost_usd": 0.01234567,
                    }
                ),
                encoding="utf-8",
            )
            (experiment_root / "exp07_prompt_v12_summary.json").write_text(
                json.dumps({"mode": "live_openrouter", "assessment_count": 129}),
                encoding="utf-8",
            )

            result = self.auditor.audit_paid_costs(data_cost_root, stop_threshold_usd=10.0, experiment_root=experiment_root)

        self.assertEqual("pass", result["status"])
        self.assertEqual(2.512346, result["known_committed_estimated_cost_usd"])
        self.assertTrue(any(item["provider"] == "OpenRouter/DeepSeek" for item in result["committed_items"]))
        self.assertTrue(any(item.get("source_path", "").endswith("exp07_prompt_v12_summary.json") for item in result["unpriced_items"]))

    def test_main_writes_json_and_markdown_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "paid_cost.json"
            report_path = Path(tmp) / "paid_cost.md"

            returncode = self.auditor.main(["--json-output", str(output_path), "--report-output", str(report_path)])

            self.assertEqual(0, returncode)
            result = json.loads(output_path.read_text(encoding="utf-8"))
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("known_committed_estimated_cost_usd", result)
            self.assertIn("Paid Cost Audit", report)


if __name__ == "__main__":
    unittest.main()
