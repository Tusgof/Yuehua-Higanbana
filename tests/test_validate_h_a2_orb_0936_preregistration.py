from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_orb_0936_preregistration import DEFAULT_PATH, validate


class HA2ORB0936PreregistrationTests(unittest.TestCase):
    def test_committed_preregistration_passes_without_external_wiki(self) -> None:
        result = validate(verify_wiki=False)

        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual("09:36:00", result["signal_available_time_et"])
        self.assertEqual("09:37:00", result["earliest_entry_quote_time_et"])
        self.assertEqual(60, result["execution_latency_seconds"])

    def test_rejects_entry_before_signal(self) -> None:
        payload = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        payload["execution_rule"]["earliest_entry_quote_time_et"] = "09:35:00"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate(path, verify_wiki=False)

        self.assertIn("execution_rule_invalid:earliest_entry_quote_time_et", result["blockers"])

    def test_rejects_random_split_or_oos_tuning(self) -> None:
        payload = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        payload["chronological_policy"]["random_split_allowed"] = True
        payload["chronological_policy"]["oos_tuning_allowed"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate(path, verify_wiki=False)

        self.assertIn("chronological_policy_invalid:random_split_allowed", result["blockers"])
        self.assertIn("chronological_policy_invalid:oos_tuning_allowed", result["blockers"])

    def test_rejects_interpolation_market_order_and_automatic_expansion(self) -> None:
        payload = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        payload["structure_rule"]["interpolation_allowed"] = True
        payload["execution_rule"]["entry_market_order_allowed"] = True
        payload["sample_adequacy_policy"]["automatic_expansion_allowed"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate(path, verify_wiki=False)

        self.assertIn("structure_rule_invalid:interpolation_allowed", result["blockers"])
        self.assertIn("execution_rule_invalid:entry_market_order_allowed", result["blockers"])
        self.assertIn("automatic_expansion_must_be_forbidden", result["blockers"])


if __name__ == "__main__":
    unittest.main()
