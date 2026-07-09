from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lib.environment import data_root, wiki_root
from tests.tiers import state_audit

from scripts.validate_h_a2_targeted_data_regime_expansion_plan import (
    DEFAULT_PLAN_PATH,
    validate_h_a2_targeted_data_regime_expansion_plan,
)


@state_audit(("HIGANBANA_DATA_ROOT", data_root()), ("HIGANBANA_WIKI_ROOT", wiki_root()))
class ValidateHA2TargetedDataRegimeExpansionPlanTests(unittest.TestCase):
    def test_current_plan_passes(self) -> None:
        result = validate_h_a2_targeted_data_regime_expansion_plan()

        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_targeted_data_regime_expansion_plan", result["experiment_id"])
        self.assertEqual("H-A2.64", result["planned_next_artifact"])
        self.assertIs(False, result["paid_download_allowed"])
        self.assertIs(False, result["paper_trading_allowed"])
        self.assertIn("H-A2.64", result["next_safe_action"])

    def test_rejects_broad_calendar_buying(self) -> None:
        data = self._load_plan()
        data["data_expansion_principles"]["broad_calendar_buying_allowed"] = True

        result = self._validate_temp(data)

        self.assertEqual("blocked", result["status"])
        self.assertIn("broad_calendar_buying_allowed_must_be_false", result["blockers"])

    def test_rejects_missing_entry_option_fields(self) -> None:
        data = self._load_plan()
        data["minimum_required_fields"]["option_chain_entry"]["minimum_fields"].remove("bid_px")
        data["minimum_required_fields"]["option_chain_entry"]["minimum_fields"].remove("ask_sz")

        result = self._validate_temp(data)

        self.assertEqual("blocked", result["status"])
        self.assertIn("entry_option_field_missing:bid_px", result["blockers"])
        self.assertIn("entry_option_field_missing:ask_sz", result["blockers"])

    def test_rejects_paid_download_permission(self) -> None:
        data = self._load_plan()
        data["guardrails"]["paid_download_allowed"] = True
        data["cost_and_execution_policy"]["paid_download_allowed_by_this_plan"] = True

        result = self._validate_temp(data)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_download_allowed_must_be_false", result["blockers"])
        self.assertIn("paid_download_allowed_by_this_plan_must_be_false", result["blockers"])

    def test_rejects_missing_train_target_set(self) -> None:
        data = self._load_plan()
        data["planned_target_sets"] = [
            item for item in data["planned_target_sets"] if item["target_set_id"] != "train_candidate_geometry_backfill"
        ]

        result = self._validate_temp(data)

        self.assertEqual("blocked", result["status"])
        self.assertIn("target_set_missing:train_candidate_geometry_backfill", result["blockers"])
        self.assertIn("train_geometry_backfill_must_be_priority_1", result["blockers"])

    @staticmethod
    def _load_plan() -> dict:
        return json.loads(DEFAULT_PLAN_PATH.read_text(encoding="utf-8-sig"))

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return validate_h_a2_targeted_data_regime_expansion_plan(plan_path=path)


if __name__ == "__main__":
    unittest.main()
