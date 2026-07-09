from __future__ import annotations

import unittest

from scripts.download_h_a2_normal_control_data import build_download_plan, build_result, execute_downloads


class DownloadHA2NormalControlDataTests(unittest.TestCase):
    def test_build_download_plan_uses_only_approved_pack(self) -> None:
        plan = build_download_plan()

        self.assertEqual("h_a2_normal_control_low_normal_vix_control_pack", plan["scenario"])
        self.assertEqual(150, plan["planned_required_request_count"])
        self.assertEqual(20, plan["metadata_grouped_request_count"])
        self.assertEqual(20, plan["request_count"])
        self.assertEqual(5.398913, plan["total_estimated_cost_usd"])
        self.assertEqual(
            {
                "2025-02-03",
                "2025-02-04",
                "2025-02-05",
                "2025-02-06",
                "2025-02-07",
                "2025-02-10",
                "2025-02-11",
                "2025-02-12",
                "2025-02-13",
                "2025-02-14",
            },
            {item["date"] for item in plan["requests"]},
        )

    def test_plan_without_execute_is_blocked(self) -> None:
        plan = build_download_plan()
        result = build_result(
            plan,
            {
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 120.494368,
                "remaining_before_stop_usd": 4.505632,
            },
            execution=None,
        )

        self.assertEqual("blocked", result["status"])
        self.assertIn("requires_execute", result["blockers"])

    def test_execute_with_fake_downloader_passes_under_selected_key_guard(self) -> None:
        plan = build_download_plan()

        def fake_downloader(request: dict) -> dict:
            return {**request, "source": "downloaded", "bytes": 123, "sha256": "abc"}

        execution = execute_downloads(plan, downloader=fake_downloader)
        result = build_result(
            plan,
            {
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 120.494368,
                "remaining_before_stop_usd": 4.505632,
            },
            execution=execution,
        )

        self.assertEqual("pass", result["status"])
        self.assertEqual(20, execution["downloaded_count"])
        self.assertEqual(2460, execution["total_bytes"])

    def test_blocks_selected_key_cap_breach(self) -> None:
        plan = build_download_plan()
        plan["cost_guard"] = {**plan["cost_guard"], "projected_selected_key_usage_if_downloaded_usd": 100.0}
        execution = {"downloads": [{"bytes": 123}], "errors": [], "downloaded_count": 1, "cache_count": 0, "total_bytes": 123}

        result = build_result(plan, {"status": "pass"}, execution)

        self.assertEqual("blocked", result["status"])
        self.assertIn("projected_selected_key_usage_must_remain_below_cap", result["blockers"])


if __name__ == "__main__":
    unittest.main()
