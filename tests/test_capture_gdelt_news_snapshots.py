from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "capture_gdelt_news_snapshots.py"
SAMPLE_RESPONSE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "news_snapshots" / "gdelt_doc_artlist_sample.json"


def load_capture_module():
    spec = importlib.util.spec_from_file_location("capture_gdelt_news_snapshots", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load GDELT capture module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaptureGdeltNewsSnapshotsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capture = load_capture_module()

    def test_build_capture_plan_has_one_request_per_required_topic(self) -> None:
        plan = self.capture.build_capture_plan("2024-01-03T09:30:00-05:00", lookback_hours=24, max_records=5)

        self.assertEqual("dry_run", plan["mode"])
        self.assertEqual(5, len(plan["requests"]))
        topics = {request["topic"] for request in plan["requests"]}
        self.assertIn("market_panic", topics)
        self.assertIn("macro_policy_risk", topics)
        for request in plan["requests"]:
            self.assertIn("api.gdeltproject.org", request["url"])
            self.assertIn("maxrecords=5", request["url"])
            self.assertEqual("20240102143000", request["start_utc"])
            self.assertEqual("20240103143000", request["end_utc"])

    def test_parse_artlist_response_maps_to_importer_csv_rows(self) -> None:
        payload = json.loads(SAMPLE_RESPONSE_PATH.read_text(encoding="utf-8"))
        request = {
            "source_id": "gdelt_doc_api",
            "provider": "GDELT",
            "topic": "market_panic",
            "decision_time_et": "2024-01-03T09:30:00-05:00",
        }

        rows = self.capture.parse_artlist_response(payload, request)

        self.assertEqual(2, len(rows))
        self.assertEqual("market_panic", rows[0]["topic"])
        self.assertEqual("2024-01-03T14:20:00Z", rows[0]["published_at_utc"])
        self.assertTrue(rows[0]["url"].startswith("https://"))

    def test_capture_snapshot_without_execute_does_not_fetch_network(self) -> None:
        result = self.capture.capture_snapshot("2024-01-03T09:30:00-05:00", execute=False)

        self.assertEqual("dry_run", result["mode"])
        self.assertIn("requests", result)

    def test_main_writes_blocked_status_when_live_capture_is_unavailable(self) -> None:
        original_fetch_json = self.capture._fetch_json

        def fail_fetch(_url: str) -> dict[str, object]:
            raise self.capture.GdeltCaptureError("GDELT returned 429 Too Many Requests")

        self.capture._fetch_json = fail_fetch
        try:
            with tempfile.TemporaryDirectory() as tmp:
                status_path = Path(tmp) / "gdelt_status.json"
                output_path = Path(tmp) / "gdelt_snapshot.csv"

                returncode = self.capture.main(
                    [
                        "--decision-time-et",
                        "2024-01-03T09:30:00-05:00",
                        "--max-records",
                        "3",
                        "--output-path",
                        str(output_path),
                        "--status-output-path",
                        str(status_path),
                        "--execute",
                    ]
                )

                result = json.loads(status_path.read_text(encoding="utf-8"))

            self.assertEqual(2, returncode)
            self.assertEqual("blocked", result["status"])
            self.assertIn("gdelt_capture_unavailable", result["blockers"])
            self.assertFalse(output_path.exists())
        finally:
            self.capture._fetch_json = original_fetch_json

    def test_fetch_json_wraps_non_json_response_as_capture_error(self) -> None:
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args) -> None:
                return None

            def read(self) -> bytes:
                return b"<html>temporary upstream response</html>"

        original_urlopen = self.capture.urllib.request.urlopen

        def fake_urlopen(_url: str, timeout: int = 30) -> FakeResponse:
            return FakeResponse()

        self.capture.urllib.request.urlopen = fake_urlopen
        try:
            with self.assertRaisesRegex(self.capture.GdeltCaptureError, "non-JSON response"):
                self.capture._fetch_json("https://api.gdeltproject.org/api/v2/doc/doc")
        finally:
            self.capture.urllib.request.urlopen = original_urlopen


if __name__ == "__main__":
    unittest.main()
