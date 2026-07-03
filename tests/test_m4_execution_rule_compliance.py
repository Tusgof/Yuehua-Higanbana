from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_m4_execution_rule_compliance.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_m4_execution_rule_compliance", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M4 execution-rule audit module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_m4_execution_rule_compliance"] = module
    spec.loader.exec_module(module)
    return module


class M4ExecutionRuleComplianceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = load_audit_module()

    def test_synthetic_probe_skips_missing_entry_and_future_close(self) -> None:
        probe = self.audit.synthetic_subsystem_a_probe()
        self.assertEqual("missing_quotes", probe["missing_entry_quote_status"])
        self.assertTrue(any("entry" in reason for reason in probe["missing_entry_quote_reasons"]))
        self.assertEqual("missing_quotes", probe["future_close_quote_status"])
        self.assertTrue(any("close" in reason for reason in probe["future_close_quote_reasons"]))

    def test_subsystem_b_close_selector_ignores_after_1545(self) -> None:
        audit = self.audit.audit_subsystem_b_policy()
        self.assertEqual([], audit["blockers"])
        self.assertEqual("2024-01-08T15:44:00-05:00", audit["close_selector_probe"])

    def test_real_artifact_audit_passes_without_market_entries_or_late_closes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            result = self.audit.run_audit(
                summary_path=tmp_root / "summary.json",
                report_path=tmp_root / "report.md",
            )
        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertGreater(result["component_trade_audit"]["counts"]["entry_fill_rows_checked"], 0)
        self.assertGreater(result["component_trade_audit"]["counts"]["close_timestamp_rows_checked"], 0)


if __name__ == "__main__":
    unittest.main()
