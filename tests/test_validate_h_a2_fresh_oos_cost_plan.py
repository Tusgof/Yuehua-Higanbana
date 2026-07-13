from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_fresh_oos_cost_plan import DEFAULT_PATH, validate


class H_A2FreshOOSCostPlanTests(unittest.TestCase):
    def test_committed_plan_passes(self) -> None:
        self.assertEqual("pass", validate()["status"])

    def test_purchase_or_scope_drift_blocks(self) -> None:
        payload = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        payload["authorization"]["download_performed"] = True
        payload["target_windows"][0]["vix_bucket"] = "prior_vix_above_25"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "plan.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate(path)
        self.assertEqual("blocked", result["status"])
        self.assertIn("download_must_not_be_performed", result["blockers"])
        self.assertIn("both_in_scope_vix_buckets_required", result["blockers"])


if __name__ == "__main__":
    unittest.main()
