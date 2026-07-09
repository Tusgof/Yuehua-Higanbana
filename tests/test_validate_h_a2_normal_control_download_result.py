from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.download_h_a2_normal_control_data import build_download_plan, build_result, execute_downloads
from scripts.validate_h_a2_normal_control_download_result import validate_h_a2_normal_control_download_result


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ValidateHA2NormalControlDownloadResultTests(unittest.TestCase):
    def _write_result(self, path: Path, mutator=None) -> None:
        plan = build_download_plan()

        def fake_downloader(request: dict) -> dict:
            return {**request, "source": "downloaded", "bytes": 123, "sha256": "abc"}

        result = build_result(
            plan,
            {
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 120.494368,
                "remaining_before_stop_usd": 4.505632,
            },
            execute_downloads(plan, downloader=fake_downloader),
        )
        if mutator:
            mutator(result)
        path.write_text(json.dumps(result), encoding="utf-8")

    def test_valid_fake_result_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result_path = Path(tmp) / "result.json"
            self._write_result(result_path)

            result = validate_h_a2_normal_control_download_result(result_path=result_path)

        self.assertEqual("pass", result["status"])
        self.assertEqual(20, result["request_count"])
        self.assertEqual(2460, result["total_bytes"])

    def test_blocks_scope_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result_path = Path(tmp) / "result.json"

            def mutate(result: dict) -> None:
                result["execution"]["downloads"][0]["date"] = "2025-02-18"
                result["execution"]["downloads"][0]["dataset"] = "XNAS.ITCH"

            self._write_result(result_path, mutate)

            result = validate_h_a2_normal_control_download_result(result_path=result_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("download_dates_must_match_decision", result["blockers"])
        self.assertIn("download_dataset_out_of_scope", result["blockers"])

    def test_blocks_empty_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result_path = Path(tmp) / "result.json"

            def mutate(result: dict) -> None:
                result["execution"]["downloads"][0]["bytes"] = 0

            self._write_result(result_path, mutate)

            result = validate_h_a2_normal_control_download_result(result_path=result_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("download_file_must_be_non_empty", result["blockers"])


if __name__ == "__main__":
    unittest.main()
