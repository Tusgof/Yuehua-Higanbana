from __future__ import annotations

import unittest

from lib.timestamps import (
    interval_close_available_at,
    is_available_by,
    parse_timestamp_et,
    require_available_by,
    require_execution_timeline,
    require_interval_close_available_by,
    timestamp_et_iso,
)


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

    def test_interval_start_bar_close_is_available_after_the_interval(self) -> None:
        available = interval_close_available_at("2026-05-01T09:35:00-04:00")

        self.assertEqual("2026-05-01T09:36:00-04:00", available.isoformat())

    def test_interval_start_bar_close_cannot_be_used_before_interval_end(self) -> None:
        with self.assertRaisesRegex(ValueError, "not available before the interval ends"):
            require_interval_close_available_by(
                "2026-05-01T09:35:00-04:00",
                "2026-05-01T09:35:59-04:00",
                label="09:35 confirmation close",
            )

        require_interval_close_available_by(
            "2026-05-01T09:35:00-04:00",
            "2026-05-01T09:36:00-04:00",
            label="09:35 confirmation close",
        )

    def test_execution_timeline_accepts_signal_then_decision_then_quote(self) -> None:
        require_execution_timeline(
            signal_available_timestamp="2026-05-01T09:36:00-04:00",
            order_decision_timestamp="2026-05-01T09:36:00-04:00",
            entry_quote_timestamp="2026-05-01T09:37:00-04:00",
        )

    def test_execution_timeline_stops_before_pnl_when_entry_precedes_signal(self) -> None:
        pnl_computed = False
        with self.assertRaisesRegex(ValueError, "signal is not available"):
            require_execution_timeline(
                signal_available_timestamp="2026-05-01T09:36:00-04:00",
                order_decision_timestamp="2026-05-01T09:35:00-04:00",
                entry_quote_timestamp="2026-05-01T09:35:00-04:00",
            )
            pnl_computed = True

        self.assertFalse(pnl_computed)

    def test_execution_timeline_rejects_quote_before_decision(self) -> None:
        with self.assertRaisesRegex(ValueError, "entry quote precedes"):
            require_execution_timeline(
                signal_available_timestamp="2026-05-01T09:36:00-04:00",
                order_decision_timestamp="2026-05-01T09:37:00-04:00",
                entry_quote_timestamp="2026-05-01T09:36:00-04:00",
            )
