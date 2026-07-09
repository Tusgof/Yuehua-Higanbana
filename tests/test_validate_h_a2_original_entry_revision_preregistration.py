from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lib.environment import data_root, wiki_root
from tests.tiers import state_audit

from scripts.validate_h_a2_original_entry_revision_preregistration import (
    DEFAULT_PREREG_PATH,
    validate_h_a2_original_entry_revision_preregistration,
)


@state_audit(("HIGANBANA_DATA_ROOT", data_root()), ("HIGANBANA_WIKI_ROOT", wiki_root()))
class H_A2OriginalEntryRevisionPreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_original_entry_revision_preregistration()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_original_entry_revision", result["experiment_id"])
        self.assertEqual(0.001, result["locked_threshold"])
        self.assertEqual("09:35:00", result["candidate_decision_time_et"])
        self.assertFalse(result["fifteen_minute_component_allowed"])
        self.assertFalse(result["network_allowed"])
        self.assertFalse(result["paid_data_allowed"])
        self.assertFalse(result["broker_request_allowed"])
        self.assertFalse(result["llm_call_allowed"])
        self.assertFalse(result["threshold_search_allowed"])
        self.assertFalse(result["new_filter_allowed"])
        self.assertEqual(5, result["planned_test_count"])

    def test_rejects_0945_decision_time(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["original_entry_rule"]["candidate_decision_time_et"] = "09:45:00"
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("candidate_decision_time_must_be_0935", result["blockers"])

    def test_rejects_fifteen_minute_component(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["original_entry_rule"]["fifteen_minute_conflict_component_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("fifteen_minute_conflict_component_allowed_must_be_false", result["blockers"])

    def test_rejects_threshold_change(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["original_entry_rule"]["opening_followthrough_threshold"] = 0.002
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("locked_threshold_must_be_0_001", result["blockers"])

    def test_rejects_paid_data_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["guardrails"]["paid_data_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_allowed_must_be_false", result["blockers"])

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_h_a2_original_entry_revision_preregistration(path)


if __name__ == "__main__":
    unittest.main()
