from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_g1_local_cache_overlap_scan import validate_h_g1_local_cache_overlap_scan


class ValidateHG1LocalCacheOverlapScanTests(unittest.TestCase):
    def test_current_report_passes_and_preserves_guardrails(self) -> None:
        result = validate_h_g1_local_cache_overlap_scan()
        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual("blocked_no_additional_no_paid_overlap", result["scan_status"])
        self.assertEqual(0, result["additional_no_paid_gamma_ready_dates"])
        self.assertEqual(2, result["projected_no_paid_gamma_ready_intersection"])
        self.assertIs(False, result["strategy_use_allowed"])
        self.assertIs(False, result["paid_data_approved"])

    def test_rejects_strategy_use_or_paid_data_approval(self) -> None:
        source = Path("reports/diagnostics/h_g1_local_cache_overlap_scan.json")
        data = json.loads(source.read_text(encoding="utf-8"))
        data["strategy_use_allowed"] = True
        data["paid_data_approved"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scan.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            result = validate_h_g1_local_cache_overlap_scan(path)
        self.assertEqual("blocked", result["status"])
        self.assertIn("strategy_use_allowed_must_be_false", result["blockers"])
        self.assertIn("paid_data_approved_must_be_false", result["blockers"])

    def test_rejects_fixed_n_rule(self) -> None:
        source = Path("reports/diagnostics/h_g1_local_cache_overlap_scan.json")
        data = json.loads(source.read_text(encoding="utf-8"))
        data["mintrl_psr_feasibility_gate"]["fixed_n_rule_used"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scan.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            result = validate_h_g1_local_cache_overlap_scan(path)
        self.assertEqual("blocked", result["status"])
        self.assertIn("fixed_n_rule_must_not_be_used", result["blockers"])


if __name__ == "__main__":
    unittest.main()
