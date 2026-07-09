from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_independent_validation_download_result import (
    validate_h_a2_independent_validation_download_result,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ValidateHA2IndependentValidationDownloadResultTests(unittest.TestCase):
    def test_current_download_result_passes(self) -> None:
        result = validate_h_a2_independent_validation_download_result()

        self.assertEqual("pass", result["status"])
        self.assertEqual("h_a2_independent_validation_2025_04_08", result["scenario"])
        self.assertEqual(15, result["request_count"])
        self.assertEqual(54014593, result["total_bytes"])
        self.assertEqual(0.504662, result["total_estimated_cost_usd"])

    def test_blocks_scope_expansion_or_non_download_result(self) -> None:
        source = PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_h_a2_independent_validation_2025_04_08.json"
        with tempfile.TemporaryDirectory() as tmp:
            result_path = Path(tmp) / "result.json"
            payload = json.loads(source.read_text(encoding="utf-8"))
            payload["mode"] = "requires_execute"
            payload["download_performed"] = False
            payload["request_count"] = 16
            payload["selected_batch"]["dates"] = ["2025-04-08", "2025-04-09"]
            result_path.write_text(json.dumps(payload), encoding="utf-8")

            result = validate_h_a2_independent_validation_download_result(result_path=result_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("mode_must_be_download_complete", result["blockers"])
        self.assertIn("download_performed_must_be_true", result["blockers"])
        self.assertIn("request_count_must_be_15", result["blockers"])
        self.assertIn("selected_dates_must_be_2025_04_08_only", result["blockers"])

    def test_blocks_threshold_or_forbidden_claim_drift(self) -> None:
        source = PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_h_a2_independent_validation_2025_04_08.json"
        with tempfile.TemporaryDirectory() as tmp:
            result_path = Path(tmp) / "result.json"
            payload = json.loads(source.read_text(encoding="utf-8"))
            payload["locked_signal_under_validation"]["opening_followthrough_threshold"] = 0.002
            payload["forbidden_claims"] = []
            result_path.write_text(json.dumps(payload), encoding="utf-8")

            result = validate_h_a2_independent_validation_download_result(result_path=result_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("threshold_must_remain_0_001", result["blockers"])
        self.assertIn("missing_forbidden_claim:Do not claim H-A2 edge is validated.", result["blockers"])


if __name__ == "__main__":
    unittest.main()
