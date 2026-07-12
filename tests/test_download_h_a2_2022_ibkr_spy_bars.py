from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from scripts.download_h_a2_2022_ibkr_spy_bars import normalize_bars


class DownloadH_A2IbkrSpyBarsTests(unittest.TestCase):
    def test_normalize_bars_preserves_raw_and_canonical_fields(self) -> None:
        bar = SimpleNamespace(
            date=datetime(2022, 10, 3, 13, 30, tzinfo=timezone.utc),
            open=361.0,
            high=362.0,
            low=360.5,
            close=361.5,
            volume=1000,
            average=361.4,
            barCount=25,
        )
        raw, canonical = normalize_bars("2022-10-03", [bar])
        self.assertEqual(1, len(raw))
        self.assertEqual("2022-10-03T09:30:00-04:00", canonical[0]["timestamp_et"])
        self.assertEqual("Interactive Brokers", canonical[0]["provider"])
        self.assertEqual(25, raw[0]["bar_count"])


if __name__ == "__main__":
    unittest.main()
