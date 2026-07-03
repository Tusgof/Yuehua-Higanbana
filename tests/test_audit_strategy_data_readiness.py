from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_strategy_data_readiness.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("audit_strategy_data_readiness", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load strategy data readiness auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditStrategyDataReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = load_auditor()

    def test_current_project_is_blocked_by_trade_count(self) -> None:
        result = self.auditor.audit_strategy_data_readiness()

        self.assertEqual("blocked", result["status"])
        self.assertEqual(90, result["totals"]["closed_trades"])
        self.assertIn("requires_minimum_trade_count_500", result["blockers"])
        self.assertNotIn("requires_bid_ask_quotes", result["blockers"])
        self.assertNotIn("requires_spy_bar_data", result["blockers"])
        self.assertFalse(result["sample_adequacy"]["trade_count_floor_met"])
        self.assertEqual(["under-sampled", "underpowered"], result["sample_adequacy"]["evidence_labels"])
        self.assertEqual("underpowered", result["sample_adequacy"]["power_status"])
        self.assertEqual("pending_experiment_return_distribution", result["sample_adequacy"]["mintrl_status"])
        self.assertEqual("pending_experiment_return_distribution", result["sample_adequacy"]["psr_status"])

    def test_ready_when_train_oos_and_trade_count_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {
                "in_sample_multimonth": root / "in_sample.json",
                "jan_2024_oos_adapter": root / "jan_adapter.json",
                "jan_2024_oos": root / "jan.json",
                "feb_2024_oos_adapter": root / "feb_adapter.json",
                "feb_2024_oos": root / "feb.json",
                "mar_2024_oos_adapter": root / "mar_adapter.json",
                "mar_2024_oos": root / "mar.json",
                "apr_2024_oos_adapter": root / "apr_adapter.json",
                "apr_2024_oos": root / "apr.json",
                "may_2024_oos_adapter": root / "may_adapter.json",
                "may_2024_oos": root / "may.json",
                "jun_2024_oos_adapter": root / "jun_adapter.json",
                "jun_2024_oos": root / "jun.json",
            }
            paths["in_sample_multimonth"].write_text(
                json.dumps(
                    {
                        "adapter_totals": {"candidate_ready_days": 450, "quote_rows": 1000, "bar_rows": 900},
                        "pnl_models": {"forced_close_only": {"candidate_days": 450, "closed_trades": 450}},
                    }
                ),
                encoding="utf-8",
            )
            paths["jan_2024_oos"].write_text(
                json.dumps({"candidate_days": 30, "closed_trades": 30, "trades": [{"date": "2024-01-02"}]}),
                encoding="utf-8",
            )
            paths["jan_2024_oos_adapter"].write_text(
                json.dumps({"candidate_ready_days": 30, "quote_rows": 100, "bar_rows": 90}),
                encoding="utf-8",
            )
            paths["feb_2024_oos"].write_text(
                json.dumps({"candidate_days": 20, "closed_trades": 20, "trades": [{"date": "2024-02-01"}]}),
                encoding="utf-8",
            )
            paths["feb_2024_oos_adapter"].write_text(
                json.dumps({"candidate_ready_days": 20, "quote_rows": 100, "bar_rows": 90}),
                encoding="utf-8",
            )
            paths["mar_2024_oos"].write_text(
                json.dumps({"candidate_days": 20, "closed_trades": 20, "trades": [{"date": "2024-03-01"}]}),
                encoding="utf-8",
            )
            paths["mar_2024_oos_adapter"].write_text(
                json.dumps({"candidate_ready_days": 20, "quote_rows": 100, "bar_rows": 90}),
                encoding="utf-8",
            )
            paths["apr_2024_oos"].write_text(
                json.dumps({"candidate_days": 20, "closed_trades": 20, "trades": [{"date": "2024-04-01"}]}),
                encoding="utf-8",
            )
            paths["apr_2024_oos_adapter"].write_text(
                json.dumps({"candidate_ready_days": 20, "quote_rows": 100, "bar_rows": 90}),
                encoding="utf-8",
            )
            paths["may_2024_oos"].write_text(
                json.dumps({"candidate_days": 20, "closed_trades": 20, "trades": [{"date": "2024-05-01"}]}),
                encoding="utf-8",
            )
            paths["may_2024_oos_adapter"].write_text(
                json.dumps({"candidate_ready_days": 20, "quote_rows": 100, "bar_rows": 90}),
                encoding="utf-8",
            )
            paths["jun_2024_oos"].write_text(
                json.dumps({"candidate_days": 20, "closed_trades": 20, "trades": [{"date": "2024-06-03"}]}),
                encoding="utf-8",
            )
            paths["jun_2024_oos_adapter"].write_text(
                json.dumps({"candidate_ready_days": 20, "quote_rows": 100, "bar_rows": 90}),
                encoding="utf-8",
            )

            result = self.auditor.audit_strategy_data_readiness(input_paths=paths)

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual(580, result["totals"]["closed_trades"])
        self.assertTrue(result["sample_adequacy"]["trade_count_floor_met"])
        self.assertEqual(
            ["sample_count_floor_met", "psr_mintrl_pending"],
            result["sample_adequacy"]["evidence_labels"],
        )
        self.assertEqual("pending_experiment_return_distribution", result["sample_adequacy"]["power_status"])

    def test_main_writes_json_and_markdown_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "strategy_data.json"
            report_path = Path(tmp) / "strategy_data.md"

            returncode = self.auditor.main(["--json-output", str(output_path), "--report-output", str(report_path)])

            self.assertEqual(0, returncode)
            result = json.loads(output_path.read_text(encoding="utf-8"))
            report = report_path.read_text(encoding="utf-8")
            self.assertIn(result["status"], {"blocked", "pass"})
            self.assertIn("Strategy Data Readiness Audit", report)
            self.assertIn("Evidence labels", report)
            self.assertIn("MinTRL status", report)


if __name__ == "__main__":
    unittest.main()
