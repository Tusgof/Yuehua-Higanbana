from __future__ import annotations

import unittest

from scripts.download_h_a2_independent_validation_data import build_download_plan, build_result, execute_downloads


class DownloadHA2IndependentValidationDataTests(unittest.TestCase):
    def test_build_download_plan_uses_only_one_day_and_15_requests(self) -> None:
        plan = build_download_plan()

        self.assertEqual("h_a2_independent_validation_2025_04_08", plan["scenario"])
        self.assertEqual(15, plan["request_count"])
        self.assertEqual(0.504662, plan["total_estimated_cost_usd"])
        self.assertEqual({"2025-04-08"}, {item["date"] for item in plan["requests"]})

    def test_plan_without_execute_is_blocked(self) -> None:
        plan = build_download_plan()
        result = build_result(
            plan,
            {
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 119.989706,
                "remaining_before_stop_usd": 5.010294,
            },
            execution=None,
        )

        self.assertEqual("blocked", result["status"])
        self.assertIn("requires_execute", result["blockers"])

    def test_execute_with_fake_downloader_passes(self) -> None:
        plan = build_download_plan()

        def fake_downloader(request: dict) -> dict:
            return {
                **request,
                "source": "downloaded",
                "bytes": 123,
                "sha256": "abc",
            }

        execution = execute_downloads(plan, downloader=fake_downloader)
        result = build_result(
            plan,
            {
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 119.989706,
                "remaining_before_stop_usd": 5.010294,
            },
            execution=execution,
        )

        self.assertEqual("pass", result["status"])
        self.assertEqual(15, execution["downloaded_count"])
        self.assertEqual(1845, execution["total_bytes"])

    def test_blocks_when_remaining_headroom_is_too_small(self) -> None:
        plan = build_download_plan()
        execution = {"downloads": [{"bytes": 123}], "errors": [], "downloaded_count": 1, "cache_count": 0, "total_bytes": 123}

        result = build_result(
            plan,
            {
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 124.9,
                "remaining_before_stop_usd": 0.1,
            },
            execution=execution,
        )

        self.assertEqual("blocked", result["status"])
        self.assertIn("estimated_cost_exceeds_remaining_headroom", result["blockers"])


if __name__ == "__main__":
    unittest.main()
