from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lib.io import write_jsonl
from lib.regime_inputs import load_macro_events_by_date, load_vix_vxv, previous_vix_record


class RegimeInputTests(unittest.TestCase):
    def test_loads_vix_and_macro_rows_for_new_callers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vix_path = root / "vix.jsonl"
            macro_path = root / "macro.jsonl"
            write_jsonl(vix_path, [{"date": "2024-01-03"}, {"date": "2024-01-02"}])
            write_jsonl(
                macro_path,
                [
                    {"record_type": "other"},
                    {"record_type": "macro_event", "event_timestamp_et": "2024-01-03T10:00:00-05:00"},
                ],
            )

            vix_rows = load_vix_vxv(vix_path)
            macro_rows = load_macro_events_by_date(macro_path)

        self.assertEqual(["2024-01-02", "2024-01-03"], [row["date"] for row in vix_rows])
        self.assertEqual("2024-01-03", previous_vix_record("2024-01-04", vix_rows)["date"])
        self.assertEqual(1, len(macro_rows["2024-01-03"]))
