from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lib.environment import data_root
from tests.tiers import state_audit

from scripts.run_h_a2_independent_validation_import_diagnostic import (
    run_h_a2_independent_validation_import_diagnostic,
)
from scripts.validate_h_a2_independent_validation_import_diagnostic import (
    DEFAULT_SUMMARY_PATH,
    validate_h_a2_independent_validation_import_diagnostic,
)


@state_audit(("HIGANBANA_DATA_ROOT", data_root()))
class H_A2IndependentValidationImportDiagnosticTests(unittest.TestCase):
    def test_run_diagnostic_outputs_local_e1_no_candidate_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = run_h_a2_independent_validation_import_diagnostic(
                summary_path=tmp_path / "summary.json",
                report_path=tmp_path / "report.md",
                search_log_path=tmp_path / "search_log.jsonl",
                build_root=tmp_path / "build",
            )

        self.assertEqual("complete", result["status"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual(15, result["raw_file_inventory"]["actual_file_count"])
        self.assertEqual(390, result["spy_underlying_import"]["row_count"])
        self.assertEqual(14, result["opra_quote_import"]["window_count"])
        self.assertFalse(result["candidate_signal_reconstruction"]["locked_signal_true"])
        self.assertEqual("no_candidate_trade_signal", result["entry_exit_quote_availability"]["status"])
        self.assertFalse(result["additional_download_used"])
        self.assertFalse(result["exact_replay_used"])
        self.assertFalse(result["strategy_pnl_computed"])
        self.assertFalse(result["paper_trading_allowed"])

    def test_current_summary_validates_after_run(self) -> None:
        run_h_a2_independent_validation_import_diagnostic()
        result = validate_h_a2_independent_validation_import_diagnostic()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("h_a2_independent_validation_import_diagnostic", result["experiment_id"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual("no_candidate_trade_signal_on_high_vix_sample", result["decision"])
        self.assertFalse(result["locked_signal_true"])
        self.assertTrue(result["research_log_required"])

    def test_validator_rejects_paid_or_e2_claim(self) -> None:
        run_h_a2_independent_validation_import_diagnostic()
        payload = json.loads(DEFAULT_SUMMARY_PATH.read_text(encoding="utf-8"))
        payload["evidence_tier"] = "E2"
        payload["additional_download_used"] = True
        payload["paper_trading_allowed"] = True
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("evidence_tier_must_be_e1", result["blockers"])
        self.assertIn("additional_download_used_must_be_false", result["blockers"])
        self.assertIn("paper_trading_allowed_must_be_false", result["blockers"])

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return validate_h_a2_independent_validation_import_diagnostic(path)


if __name__ == "__main__":
    unittest.main()
