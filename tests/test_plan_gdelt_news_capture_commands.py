from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "plan_gdelt_news_capture_commands.py"


def load_planner():
    spec = importlib.util.spec_from_file_location("plan_gdelt_news_capture_commands", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load GDELT command planner")
    module = importlib.util.module_from_spec(spec)
    sys.modules["plan_gdelt_news_capture_commands"] = module
    spec.loader.exec_module(module)
    return module


class PlanGdeltNewsCaptureCommandsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.planner = load_planner()

    def test_plan_uses_candidate_ready_days_only_and_preserves_et_offset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter_path = root / "adapter.json"
            status_path = root / "status.json"
            adapter_path.write_text(
                json.dumps(
                    {
                        "days": [
                            {"date": "2023-09-15", "status": "candidate_ready"},
                            {"date": "2024-01-05", "status": "candidate_ready"},
                            {"date": "2024-01-03", "status": "no_trade"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            status_path.write_text(json.dumps({"status": "blocked", "blockers": ["gdelt_capture_unavailable"]}), encoding="utf-8")

            result = self.planner.plan_capture_commands([adapter_path], status_path, max_records=3, lookback_hours=12)

        self.assertEqual("dry_run_no_network", result["mode"])
        self.assertEqual("ready_to_retry", result["status"])
        self.assertTrue(result["live_retry_allowed"])
        self.assertEqual(["gdelt_capture_unavailable"], result["blockers"])
        self.assertEqual(2, result["candidate_day_count"])
        self.assertEqual("2023-09-15T09:30:00-04:00", result["commands"][0]["decision_time_et"])
        self.assertEqual("2024-01-05T09:30:00-05:00", result["commands"][1]["decision_time_et"])
        self.assertIn("--max-records 3", result["commands"][0]["command"])
        self.assertIn("--lookback-hours 12", result["commands"][0]["command"])
        self.assertIn("--execute", result["commands"][0]["command"])

    def test_write_reports_creates_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = {
                "mode": "dry_run_no_network",
                "status": "ready_to_retry",
                "live_retry_allowed": True,
                "candidate_day_count": 1,
                "command_count": 1,
                "max_records": 5,
                "lookback_hours": 24,
                "latest_capture_status": {"status": "missing"},
                "blockers": [],
                "commands": [
                    {
                        "trade_date": "2024-01-05",
                        "command": "python scripts\\capture_gdelt_news_snapshots.py --decision-time-et 2024-01-05T09:30:00-05:00 --execute",
                    }
                ],
                "next_step": "Retry later.",
            }
            json_output = root / "plan.json"
            report_output = root / "plan.md"

            self.planner.write_reports(result, json_output, report_output)

            self.assertEqual(result, json.loads(json_output.read_text(encoding="utf-8")))
            report = report_output.read_text(encoding="utf-8")
            self.assertIn("# GDELT News Capture Command Plan", report)
            self.assertIn("- Live retry allowed now: `True`", report)
            self.assertIn("2024-01-05T09:30:00-05:00", report)

    def test_plan_includes_daily_retry_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter_path = root / "adapter.json"
            status_path = root / "latest.json"
            status_dir = root / "statuses"
            status_dir.mkdir()
            adapter_path.write_text(
                json.dumps({"days": [{"date": "2023-09-01", "status": "candidate_ready"}]}),
                encoding="utf-8",
            )
            status_path.write_text(json.dumps({"status": "blocked", "blockers": ["gdelt_capture_unavailable"]}), encoding="utf-8")
            (status_dir / "2023-09-01.json").write_text(
                json.dumps({"status": "blocked", "blockers": ["gdelt_capture_unavailable"]}),
                encoding="utf-8",
            )

            result = self.planner.plan_capture_commands(
                [adapter_path],
                status_path,
                status_dir,
                max_records=5,
                lookback_hours=24,
            )

        self.assertEqual({"blocked": 1}, result["daily_status_counts"])
        self.assertEqual("blocked", result["commands"][0]["latest_status"]["status"])

    def test_plan_summarizes_next_unattempted_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter_path = root / "adapter.json"
            status_path = root / "latest.json"
            status_dir = root / "statuses"
            status_dir.mkdir()
            adapter_path.write_text(
                json.dumps(
                    {
                        "days": [
                            {"date": "2023-09-01", "status": "candidate_ready"},
                            {"date": "2023-09-07", "status": "candidate_ready"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            status_path.write_text(json.dumps({"status": "blocked", "blockers": ["gdelt_capture_unavailable"]}), encoding="utf-8")
            (status_dir / "2023-09-01.json").write_text(
                json.dumps({"status": "blocked", "blockers": ["gdelt_capture_unavailable"]}),
                encoding="utf-8",
            )

            result = self.planner.plan_capture_commands(
                [adapter_path],
                status_path,
                status_dir,
                max_records=5,
                lookback_hours=24,
            )

        summary = result["retry_queue_summary"]
        self.assertEqual(1, summary["attempted_status_file_count"])
        self.assertEqual(1, summary["blocked_status_file_count"])
        self.assertEqual(1, summary["not_attempted_count"])
        self.assertEqual("2023-09-07", summary["next_unattempted_trade_date"])
        self.assertIn("2023-09-07T09:30:00-04:00", summary["next_unattempted_command"])
        self.assertEqual("normal_retry", result["retry_pressure"]["status"])

    def test_plan_recommends_cooldown_after_three_blocked_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter_path = root / "adapter.json"
            status_path = root / "latest.json"
            status_dir = root / "statuses"
            status_dir.mkdir()
            adapter_path.write_text(
                json.dumps(
                    {
                        "days": [
                            {"date": "2023-09-01", "status": "candidate_ready"},
                            {"date": "2023-09-07", "status": "candidate_ready"},
                            {"date": "2023-10-02", "status": "candidate_ready"},
                            {"date": "2023-10-05", "status": "candidate_ready"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            status_path.write_text(json.dumps({"status": "blocked", "blockers": ["gdelt_capture_unavailable"]}), encoding="utf-8")
            for trade_date in ["2023-09-01", "2023-09-07", "2023-10-02"]:
                (status_dir / f"{trade_date}.json").write_text(
                    json.dumps({"status": "blocked", "blockers": ["gdelt_capture_unavailable"]}),
                    encoding="utf-8",
                )

            result = self.planner.plan_capture_commands(
                [adapter_path],
                status_path,
                status_dir,
                max_records=5,
                lookback_hours=24,
            )

        self.assertEqual("cooldown_recommended", result["retry_pressure"]["status"])
        self.assertEqual("blocked_cooldown", result["status"])
        self.assertFalse(result["live_retry_allowed"])
        self.assertEqual(3, result["retry_pressure"]["threshold"])
        self.assertIn("Pause live GDELT --execute retries", result["next_step"])

    def test_missing_days_array_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            adapter_path = Path(tmp) / "adapter.json"
            adapter_path.write_text(json.dumps({"candidate_ready_days": 1}), encoding="utf-8")

            with self.assertRaises(self.planner.GdeltNewsCaptureCommandPlanError):
                self.planner.plan_capture_commands([adapter_path], Path(tmp) / "missing_status.json")


if __name__ == "__main__":
    unittest.main()
