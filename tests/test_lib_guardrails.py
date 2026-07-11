from __future__ import annotations

import unittest

from lib.guardrails import append_missing_fields, append_true_guardrails, status_from_blockers


class GuardrailTests(unittest.TestCase):
    def test_collects_missing_and_forbidden_fields(self) -> None:
        blockers: list[str] = []
        record = {"network_used": True, "hypothesis_id": "H-A2"}

        append_missing_fields(record, ["hypothesis_id", "evidence_tier"], blockers)
        append_true_guardrails(record, ["network_used", "paid_data_used"], blockers)

        self.assertEqual(
            ["missing_required_field:evidence_tier", "forbidden_guardrail_true:network_used"],
            blockers,
        )
        self.assertEqual("blocked", status_from_blockers(blockers))
        self.assertEqual("pass", status_from_blockers([]))
