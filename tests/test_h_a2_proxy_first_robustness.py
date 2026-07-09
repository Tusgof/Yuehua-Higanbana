from __future__ import annotations

import unittest

from scripts.run_h_a2_proxy_first_robustness import DEFAULT_SOURCE_SUMMARY_PATH, run_experiment
from scripts.validate_h_a2_proxy_first_robustness_summary import validate


class H_A2ProxyFirstRobustnessTest(unittest.TestCase):
    def test_run_and_validate_local_proxy_summary(self) -> None:
        self.assertTrue(DEFAULT_SOURCE_SUMMARY_PATH.exists())

        summary = run_experiment()
        self.assertEqual(summary["status"], "complete")
        self.assertEqual(summary["hypothesis_id"], "H-A2")
        self.assertEqual(summary["evidence_tier"], "E1")
        self.assertFalse(summary["network_used"])
        self.assertFalse(summary["paid_data_used"])
        self.assertFalse(summary["ibkr_request_used"])
        self.assertFalse(summary["llm_call_used"])
        self.assertFalse(summary["exact_2022_orb_tested"])
        self.assertEqual(summary["trial_policy"]["trial_count"], 4)

        result = validate()
        self.assertEqual(result["status"], "pass", result.get("errors"))


if __name__ == "__main__":
    unittest.main()
