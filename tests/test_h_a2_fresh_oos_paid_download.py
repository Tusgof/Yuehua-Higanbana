from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_h_a2_fresh_oos_download import build_download_report, build_requests, evaluate_cost_gate
from scripts.validate_h_a2_fresh_oos_paid_download_decision import DEFAULT_PATH, validate


class H_A2FreshOOSPaidDownloadTests(unittest.TestCase):
    def test_committed_decision_passes(self) -> None:
        self.assertEqual("pass", validate()["status"])

    def test_wrong_provenance_blocks(self) -> None:
        payload = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        payload["cost_guard"]["account_provenance"] = "unknown"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "decision.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate(path)
        self.assertIn("account_provenance_must_be_primary_existing_account", result["blockers"])

    def test_request_scope_is_exactly_20_dates_and_40_requests(self) -> None:
        decision = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        requests = build_requests(decision)
        self.assertEqual(40, len(requests))
        self.assertEqual(20, len({request["date"] for request in requests}))
        self.assertEqual({"OPRA.PILLAR", "EQUS.MINI"}, {request["dataset"] for request in requests})

    def test_cost_gate_enforces_plan_ceiling_and_key_cap(self) -> None:
        decision = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        self.assertEqual("pass", evaluate_cost_gate(decision, 12.0, [])["status"])
        blocked = evaluate_cost_gate(decision, 12.7, [])
        self.assertIn("estimated_cost_exceeds_approved_ceiling", blocked["blockers"])

    def test_download_report_preserves_provider_quality_warning_dates(self) -> None:
        decision = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        downloads = [
            {"date": date_text, "source": "downloaded", "bytes": 1}
            for date_text in ("2025-08-13", "2025-08-19", "2025-08-25", "2025-09-12")
            for _ in range(10)
        ]
        report = build_download_report(
            decision,
            {"status": "pass", "total_estimated_cost_usd": 1.0},
            downloads,
            [],
            {"status": "pass"},
        )

        self.assertEqual(
            ["2025-08-13", "2025-08-19", "2025-08-25", "2025-09-12"],
            report["quality_warning_dates"],
        )


if __name__ == "__main__":
    unittest.main()
