from __future__ import annotations

import unittest

from lib.timestamps import is_available_by, parse_timestamp_et, require_available_by, timestamp_et_iso


class TimestampTests(unittest.TestCase):
    def test_normalizes_utc_to_eastern(self) -> None:
        timestamp = parse_timestamp_et("2024-01-03T14:30:00Z")

        self.assertEqual("America/New_York", timestamp.tzinfo.key)
        self.assertEqual("2024-01-03T09:30:00-05:00", timestamp_et_iso("2024-01-03T14:30:00Z"))

    def test_rejects_timezone_naive_timestamp(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone"):
            parse_timestamp_et("2024-01-03T09:30:00")

    def test_rejects_post_decision_input(self) -> None:
        self.assertTrue(is_available_by("2024-01-03T14:30:00Z", "2024-01-03T09:35:00-05:00"))
        with self.assertRaisesRegex(ValueError, "news"):
            require_available_by("2024-01-03T09:36:00-05:00", "2024-01-03T09:35:00-05:00", label="news")
