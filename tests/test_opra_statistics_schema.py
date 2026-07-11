from __future__ import annotations

import unittest

from lib.opra_statistics_schema import validate_opra_statistics_summary


def valid_summary() -> dict:
    return {
        "metadata": {"dataset": "OPRA.PILLAR", "schema": "statistics"},
        "row_count": 3,
        "columns": ["stat_type", "quantity", "symbol"],
        "ts_index_start": "2024-01-03 11:30:00+00:00",
        "ts_index_end": "2024-01-03 22:30:00+00:00",
        "has_stat_type": True,
        "has_quantity": True,
        "stat_type_counts": {"OPEN_INTEREST": 2, "CLOSE_PRICE": 1},
        "open_interest_record_count": 2,
        "unique_symbol_count": 2,
    }


class OpraStatisticsSchemaTests(unittest.TestCase):
    def test_valid_summary_passes(self) -> None:
        self.assertEqual([], validate_opra_statistics_summary(valid_summary()))

    def test_rejects_provider_schema_drift(self) -> None:
        summary = valid_summary()
        summary["metadata"]["schema"] = "definition"
        summary["stat_type_counts"] = {"CLOSE_PRICE": 1}
        summary["columns"].remove("quantity")

        errors = validate_opra_statistics_summary(summary)

        self.assertIn("summary.metadata.schema must be statistics", errors)
        self.assertIn("summary.stat_type_counts.OPEN_INTEREST must be positive", errors)
        self.assertIn("summary.columns must include quantity", errors)


if __name__ == "__main__":
    unittest.main()
