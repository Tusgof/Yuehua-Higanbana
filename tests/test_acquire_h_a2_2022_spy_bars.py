from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.acquire_h_a2_2022_spy_bars import EXPECTED_FULL_DAY_MINUTES, run_acquisition_tool
from scripts.validate_m2_contracts import load_schema, validate_record


class AcquireHA22022SpyBarsTests(unittest.TestCase):
    def test_fixture_mode_writes_valid_canonical_spy_bars_and_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run_acquisition_tool(
                mode="fixture",
                manifest_path=root / "manifest.json",
                coverage_path=root / "coverage.json",
                import_summary_path=root / "import_summary.json",
                report_path=root / "coverage.md",
                output_path=root / "spy_bar.jsonl",
            )
            rows = [json.loads(line) for line in (root / "spy_bar.jsonl").read_text(encoding="utf-8").splitlines()]

        schema = load_schema()
        self.assertEqual(21 * EXPECTED_FULL_DAY_MINUTES, len(rows))
        self.assertEqual([], validate_record(rows[0], schema))
        self.assertEqual("2022-10-03T09:30:00-04:00", rows[0]["timestamp_et"])
        self.assertEqual("2022-10-31T16:00:00-04:00", rows[-1]["timestamp_et"])
        self.assertEqual("fixture_pass_real_data_not_imported", result["coverage"]["status"])
        self.assertTrue(result["coverage"]["gates"]["canonical_import_pass"])
        self.assertTrue(result["coverage"]["gates"]["orb_timestamp_coverage_pass"])
        self.assertTrue(result["coverage"]["gates"]["full_session_coverage_pass"])
        self.assertTrue(result["coverage"]["gates"]["join_to_existing_2022_10_option_quotes_pass"])
        self.assertFalse(result["coverage"]["ready_for_exact_rerun"])
        self.assertFalse(result["manifest"]["guardrails"]["external_network_used"])
        self.assertFalse(result["manifest"]["guardrails"]["paid_data_used"])
        self.assertFalse(result["manifest"]["guardrails"]["ibkr_historical_request_used"])
        self.assertFalse(result["manifest"]["guardrails"]["orders_transmitted"])
        self.assertTrue(result["manifest"]["guardrails"]["fixture_data_imported"])

    def test_dry_run_writes_plan_artifacts_without_import_or_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_path = root / "spy_bar.jsonl"
            result = run_acquisition_tool(
                mode="dry-run",
                manifest_path=root / "manifest.json",
                coverage_path=root / "coverage.json",
                import_summary_path=root / "import_summary.json",
                report_path=root / "coverage.md",
                output_path=output_path,
            )

        self.assertFalse(output_path.exists())
        self.assertEqual("dry_run_ready", result["manifest"]["status"])
        self.assertEqual("dry_run_no_rows", result["coverage"]["status"])
        self.assertEqual("dry_run_no_import", result["import_summary"]["status"])
        self.assertFalse(result["coverage"]["gates"]["canonical_import_pass"])
        self.assertFalse(result["coverage"]["ready_for_exact_rerun"])
        self.assertFalse(result["manifest"]["guardrails"]["fixture_data_imported"])
        self.assertFalse(result["manifest"]["guardrails"]["external_network_used"])
        self.assertFalse(result["manifest"]["guardrails"]["paid_data_used"])
        self.assertFalse(result["manifest"]["guardrails"]["orders_transmitted"])

    def test_fixture_mode_keeps_exact_rerun_and_trading_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run_acquisition_tool(
                mode="fixture",
                manifest_path=root / "manifest.json",
                coverage_path=root / "coverage.json",
                import_summary_path=root / "import_summary.json",
                report_path=root / "coverage.md",
                output_path=root / "spy_bar.jsonl",
            )

        self.assertFalse(result["import_summary"]["ready_for_exact_rerun"])
        self.assertFalse(result["import_summary"]["paper_trading_allowed"])
        self.assertFalse(result["import_summary"]["operational_validation_allowed"])
        self.assertFalse(result["import_summary"]["real_money_allowed"])
        self.assertFalse(result["import_summary"]["strategy_pnl_used"])
        self.assertIn("live historical-bars request only after readiness", result["import_summary"]["next_safe_action"])


if __name__ == "__main__":
    unittest.main()
