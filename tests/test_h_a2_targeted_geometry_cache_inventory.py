from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_targeted_geometry_cache_inventory import (
    DEFAULT_REPORT_PATH,
    validate_h_a2_targeted_geometry_cache_inventory,
)


class TestHA2TargetedGeometryCacheInventory(unittest.TestCase):
    def test_report_passes_guardrails(self) -> None:
        result = validate_h_a2_targeted_geometry_cache_inventory()
        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual(30, result["train_target_date_count"])
        self.assertEqual(2, result["normal_control_candidate_ready_count"])
        self.assertEqual(13, result["stress_missing_underlying_bar_count"])

    def test_rejects_live_metadata_cost_call(self) -> None:
        data = json.loads(DEFAULT_REPORT_PATH.read_text(encoding="utf-8"))
        data["cost_estimate"]["live_metadata_call_used"] = True
        data["guardrails"]["live_metadata_cost_call_used"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = validate_h_a2_targeted_geometry_cache_inventory(path)
        self.assertEqual("blocked", result["status"])
        self.assertIn("live_metadata_call_must_be_false", result["blockers"])
        self.assertIn("guardrail_must_be_false:live_metadata_cost_call_used", result["blockers"])

    def test_rejects_train_cache_gap(self) -> None:
        data = json.loads(DEFAULT_REPORT_PATH.read_text(encoding="utf-8"))
        for target in data["target_sets"]:
            if target["target_set_id"] == "train_candidate_geometry_backfill":
                target["ready_for_local_geometry_parser_count"] = 29
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = validate_h_a2_targeted_geometry_cache_inventory(path)
        self.assertEqual("blocked", result["status"])
        self.assertIn("train_cache_must_be_ready_for_all_target_dates", result["blockers"])


if __name__ == "__main__":
    unittest.main()

