from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lib.environment import data_root, wiki_root
from tests.tiers import state_audit

from scripts.validate_h_a2_mechanism_revision_preregistration import (
    DEFAULT_PREREG_PATH,
    validate_h_a2_mechanism_revision_preregistration,
)


@state_audit(("HIGANBANA_DATA_ROOT", data_root()), ("HIGANBANA_WIKI_ROOT", wiki_root()))
class H_A2MechanismRevisionPreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_mechanism_revision_preregistration()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_mechanism_revision_preregistration", result["experiment_id"])
        self.assertEqual("h_a2_mechanism_revision_audit", result["planned_next_diagnostic"])
        self.assertEqual("local_no_paid_diagnostic", result["planned_next_mode"])
        self.assertFalse(result["paid_data_allowed"])
        self.assertFalse(result["exact_replay_allowed"])
        self.assertFalse(result["paper_trading_allowed"])

    def test_rejects_missing_h_a2_58_source(self) -> None:
        prereg = self._load_prereg()
        prereg["source_artifacts"] = [
            item for item in prereg["source_artifacts"] if item != "experiments/h_a2_post_two_exact_replay_decision.json"
        ]
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("source_artifact_missing:experiments/h_a2_post_two_exact_replay_decision.json", result["blockers"])

    def test_rejects_paid_data_permission(self) -> None:
        prereg = self._load_prereg()
        prereg["guardrails"]["paid_data_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_allowed_must_be_false", result["blockers"])

    def test_rejects_threshold_search_permission(self) -> None:
        prereg = self._load_prereg()
        prereg["anti_overfitting_controls"]["new_threshold_search_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("new_threshold_search_allowed_must_be_false", result["blockers"])

    def test_rejects_sample_expansion_from_this_artifact(self) -> None:
        prereg = self._load_prereg()
        prereg["sample_expansion_policy"]["sample_expansion_allowed_by_this_artifact"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("sample_expansion_allowed_must_be_false", result["blockers"])

    @staticmethod
    def _load_prereg() -> dict:
        return json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8-sig"))

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return validate_h_a2_mechanism_revision_preregistration(path)


if __name__ == "__main__":
    unittest.main()
