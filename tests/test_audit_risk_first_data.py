from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path
from unittest import TestCase


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_risk_first_data.py"


def load_module():
    spec = importlib.util.spec_from_file_location("audit_risk_first_data", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AuditRiskFirstDataTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = load_module()

    def test_current_project_audit_is_blocked_with_risk_first_fields(self) -> None:
        result = self.audit.audit_risk_first_data()

        self.assertEqual("blocked", result["status"])
        self.assertIn("requires_mintrl_psr_sample_adequacy", result["blockers"])
        self.assertEqual(90, result["sample_inference_audit"]["sample_length"])
        self.assertIn("observed_sharpe", result["sample_inference_audit"])
        self.assertIn("skewness", result["sample_inference_audit"])
        self.assertIn("kurtosis", result["sample_inference_audit"])
        self.assertIn("first_order_autocorrelation", result["sample_inference_audit"])
        self.assertEqual(2, len(result["sample_inference_audit"]["psr_mintrl_approximation"]["rows"]))

    def test_current_project_audit_reports_regime_and_greeks_blockers(self) -> None:
        result = self.audit.audit_risk_first_data()

        coverage = result["regime_coverage_audit"]["coverage"]
        self.assertIn("vix_bucket", coverage)
        self.assertIn("macro_bucket", coverage)
        self.assertIn("trend_bucket", coverage)
        self.assertIn("subperiod_bucket", coverage)
        self.assertIn("missing_reference_pre_break_regime_trades", result["regime_coverage_audit"]["blockers"])
        self.assertIn(
            "greeks_data_probe:normalized_option_quotes_missing_vendor_greeks",
            result["blockers"],
        )
        self.assertIn(
            "greeks_data_probe:normalized_option_quotes_missing_open_interest",
            result["blockers"],
        )

    def test_write_reports_creates_json_and_markdown(self) -> None:
        result = self.audit.audit_risk_first_data()
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "risk_first_data_audit.json"
            md_path = Path(tmp) / "risk_first_data_audit.md"

            self.audit.write_reports(result, json_path, md_path)

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            report = md_path.read_text(encoding="utf-8")
            self.assertEqual("risk_first_data_audit", payload["record_type"])
            self.assertIn("# Risk-First Data Audit", report)
            self.assertIn("PSR / MinTRL", report)
