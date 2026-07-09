from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_2022_10_coarse_stress_preregistration import (
    validate_h_a2_2022_10_coarse_stress_preregistration,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_2022_10_coarse_stress_review_preregistration.json"


class ValidateHA2CoarseStressPreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_2022_10_coarse_stress_preregistration()

        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertFalse(result["research_log_required_for_this_preregistration"])

    def test_rejects_paid_or_ibkr_permission(self) -> None:
        data = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        data["guardrails"]["paid_data_allowed"] = True
        data["guardrails"]["ibkr_request_allowed"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = validate_h_a2_2022_10_coarse_stress_preregistration(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_allowed_must_be_false", result["blockers"])
        self.assertIn("ibkr_request_allowed_must_be_false", result["blockers"])

    def test_rejects_missing_forbidden_claims(self) -> None:
        data = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        data["decision_frame"]["forbidden_claims"] = []
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = validate_h_a2_2022_10_coarse_stress_preregistration(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_forbidden_claim:H-A2 edge is validated", result["blockers"])
        self.assertIn("missing_forbidden_claim:exact ORB entries/exits", result["blockers"])


if __name__ == "__main__":
    unittest.main()
