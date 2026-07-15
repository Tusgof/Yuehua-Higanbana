from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_h_a2_orb_0936_untouched_inventory import (
    DEFAULT_COST_JSON,
    DEFAULT_INVENTORY_JSON,
    classify_local_dates,
    discover_date_named_raw_files,
    select_chronological_cost_dates,
)


class HA2ORB0936UntouchedInventoryTests(unittest.TestCase):
    def test_classification_excludes_legacy_and_explicitly_viewed_dates(self) -> None:
        result = classify_local_dates(
            {"2024-12-31", "2025-02-03", "2026-05-01"},
            {"2025-02-03"},
        )

        self.assertEqual(["2026-05-01"], result["untouched_dates"])

    def test_daily_history_filename_is_not_misclassified_as_trade_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "2026-03-01_2026-06-04_spy_daily_history.dbn.zst").touch()
            (root / "2026-04-27_opra_grouped_0930_1550.dbn.zst").touch()

            result = discover_date_named_raw_files(root)

        self.assertEqual(["2026-04-27"], list(result))

    def test_cost_selection_is_chronological_and_ex_ante(self) -> None:
        vix_rows = [
            {"date": "2026-04-24", "vix_close": 18.0},
            {"date": "2026-04-27", "vix_close": 17.0},
            {"date": "2026-04-28", "vix_close": 16.0},
            {"date": "2026-04-29", "vix_close": 26.0},
            {"date": "2026-04-30", "vix_close": 19.0},
        ]
        selected = select_chronological_cost_dates(
            vix_rows,
            {"2026-04-28"},
            set(),
            after_date="2026-04-24",
            limit=2,
        )

        self.assertEqual(["2026-04-27", "2026-04-29"], [row["date"] for row in selected])
        self.assertTrue(all(row["trend_regime"] == "pending_prior_only_spy_daily_history" for row in selected))

    def test_committed_inventory_does_not_parse_outcomes(self) -> None:
        inventory = json.loads(DEFAULT_INVENTORY_JSON.read_text(encoding="utf-8"))

        self.assertFalse(inventory["guardrails"]["target_outcomes_parsed"])
        self.assertFalse(inventory["guardrails"]["option_pnl_read"])
        self.assertEqual(20, inventory["untouched_local_date_count"])
        self.assertNotIn("2026-03-01", inventory["untouched_dates"])
        self.assertEqual("preregister_import_coverage_validation_before_outcomes", inventory["decision"])

    def test_committed_cost_plan_is_not_purchase_authorization(self) -> None:
        plan = json.loads(DEFAULT_COST_JSON.read_text(encoding="utf-8"))

        self.assertEqual(20, plan["target_date_count"])
        self.assertFalse(plan["authorization"]["user_approval_recorded"])
        self.assertFalse(plan["authorization"]["purchase_allowed_by_this_artifact"])
        self.assertTrue(all(row["date"] > "2026-04-24" for row in plan["target_dates"]))
        self.assertNotIn("pnl", json.dumps(plan["target_dates"]).lower())


if __name__ == "__main__":
    unittest.main()
