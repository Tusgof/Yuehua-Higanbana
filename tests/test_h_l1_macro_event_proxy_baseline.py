from __future__ import annotations

import unittest
from pathlib import Path

from scripts.run_h_l1_macro_event_proxy_baseline import DEFAULT_SOURCE_SUMMARY_PATH, run_experiment
from scripts.validate_h_l1_macro_event_proxy_baseline_summary import validate
from tests.tiers import state_audit


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@state_audit(("HIGANBANA_DATA_ROOT", PROJECT_ROOT / "data"))
class HL1MacroEventProxyBaselineTest(unittest.TestCase):
    def test_run_and_validate_local_macro_event_baseline(self) -> None:
        self.assertTrue(DEFAULT_SOURCE_SUMMARY_PATH.exists())

        summary = run_experiment()
        self.assertEqual(summary["status"], "complete")
        self.assertEqual(summary["hypothesis_id"], "H-L1")
        self.assertEqual(summary["evidence_tier"], "E1")
        self.assertTrue(summary["not_llm_news_evidence"])
        self.assertFalse(summary["network_used"])
        self.assertFalse(summary["paid_data_used"])
        self.assertFalse(summary["gdelt_retry_used"])
        self.assertFalse(summary["llm_call_used"])
        self.assertFalse(summary["broker_request_used"])
        self.assertFalse(summary["llm_gate_tested"])
        self.assertFalse(summary["real_news_tested"])
        self.assertEqual(summary["trial_policy"]["trial_count"], 4)

        result = validate()
        self.assertEqual(result["status"], "pass", result.get("errors"))


if __name__ == "__main__":
    unittest.main()
