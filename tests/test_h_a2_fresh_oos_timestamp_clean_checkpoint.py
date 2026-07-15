from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_fresh_oos_timestamp_clean_checkpoint_preregistration import DEFAULT_PATH, validate
from scripts.run_h_a2_fresh_oos_timestamp_clean_checkpoint import _sample_statistics


class FreshOOSTimestampCleanCheckpointTests(unittest.TestCase):
    def test_committed_preregistration_passes_without_external_wiki_check(self) -> None:
        self.assertEqual("pass", validate(verify_wiki=False)["status"])

    def test_post_decision_feature_is_rejected(self) -> None:
        payload = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        payload["candidate_rule"]["post_decision_feature_allowed"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate(path, verify_wiki=False)
        self.assertIn("candidate_rule_invalid:post_decision_feature_allowed", result["blockers"])

    def test_numeric_breakout_threshold_is_rejected(self) -> None:
        payload = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        payload["candidate_rule"]["numeric_breakout_threshold"] = 0.001
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate(path, verify_wiki=False)
        self.assertIn("candidate_rule_invalid:numeric_breakout_threshold", result["blockers"])

    def test_single_candidate_is_under_sampled_and_underpowered(self) -> None:
        result = _sample_statistics([10.0])
        self.assertTrue(result["under_sampled"])
        self.assertTrue(result["underpowered"])
        self.assertIsNone(result["null_0"]["mintrl"])


if __name__ == "__main__":
    unittest.main()
