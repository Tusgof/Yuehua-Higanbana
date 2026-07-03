from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "capture_macro_calendar_snapshots.py"


def load_capture_module():
    spec = importlib.util.spec_from_file_location("capture_macro_calendar_snapshots", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load macro calendar capture module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaptureMacroCalendarSnapshotsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capture = load_capture_module()

    def test_build_capture_plan_has_one_request_per_official_source(self) -> None:
        plan = self.capture.build_capture_plan("2024-01-03")

        self.assertEqual("dry_run", plan["mode"])
        self.assertEqual(5, len(plan["requests"]))
        source_ids = {request["source_id"] for request in plan["requests"]}
        self.assertIn("federal_reserve_fomc_calendar", source_ids)
        self.assertIn("bls_release_calendar", source_ids)
        self.assertIn("RETAIL_SALES", plan["required_event_types"])
        for request in plan["requests"]:
            self.assertTrue(request["source_url"].startswith("https://"))
            self.assertIn("data\\raw\\spy_0dte\\macro_calendar", request["output_path"])
            self.assertRegex(request["output_path"], r"\.(html|json|xls)$")
        bls_request = next(request for request in plan["requests"] if request["source_id"] == "bls_release_calendar")
        self.assertEqual("https://www.bls.gov/schedule/2024/home.htm", bls_request["source_url"])
        census_request = next(request for request in plan["requests"] if request["source_id"] == "census_retail_release_schedule")
        self.assertEqual("https://www.census.gov/retail/marts/www/MARTSreleasedates.xls", census_request["source_url"])
        self.assertTrue(census_request["output_path"].endswith(".xls"))
        bea_request = next(request for request in plan["requests"] if request["source_id"] == "bea_release_schedule")
        self.assertTrue(bea_request["output_path"].endswith(".json"))
        self.assertEqual("bea_pce_release_pages", bea_request["capture_mode"])

    def test_capture_without_execute_does_not_fetch_network(self) -> None:
        result = self.capture.capture_snapshots("2024-01-03", execute=False)

        self.assertEqual("dry_run", result["mode"])
        self.assertIn("requests", result)

    def test_rejects_invalid_as_of_date(self) -> None:
        with self.assertRaisesRegex(self.capture.MacroCalendarCaptureError, "YYYY-MM-DD"):
            self.capture.build_capture_plan("20240103")

    def test_execute_writes_capture_manifest(self) -> None:
        payloads = {
            "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm": b"fed",
            "https://www.bls.gov/schedule/2024/home.htm": b"bls",
            "https://www.ismworld.org/supply-management-news-and-reports/reports/rob-report-calendar/": b"ism",
            "https://www.census.gov/retail/marts/www/MARTSreleasedates.xls": b"census",
        }

        original_fetch = self.capture._fetch_bytes
        original_fetch_bea = self.capture._fetch_bea_pce_release_pages_bytes
        self.capture._fetch_bytes = lambda url: payloads[url]
        self.capture._fetch_bea_pce_release_pages_bytes = lambda year: b"bea"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                result = self.capture.capture_snapshots("2024-01-03", output_root=Path(tmp), execute=True)
                manifest_path = Path(result["manifest_path"])

                self.assertTrue(manifest_path.exists())
                self.assertEqual(5, result["captured_count"])
                self.assertEqual("execute", result["mode"])
        finally:
            self.capture._fetch_bytes = original_fetch
            self.capture._fetch_bea_pce_release_pages_bytes = original_fetch_bea

    def test_execute_merges_existing_capture_manifest_by_source(self) -> None:
        payloads = {
            "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm": b"fed",
            "https://www.bls.gov/schedule/2024/home.htm": b"bls",
        }

        original_fetch = self.capture._fetch_bytes
        self.capture._fetch_bytes = lambda url: payloads[url]
        try:
            with tempfile.TemporaryDirectory() as tmp:
                output_root = Path(tmp)
                self.capture.capture_snapshots(
                    "2024-01-03",
                    output_root=output_root,
                    execute=True,
                    source_ids=["federal_reserve_fomc_calendar"],
                )
                result = self.capture.capture_snapshots(
                    "2024-01-03",
                    output_root=output_root,
                    execute=True,
                    source_ids=["bls_release_calendar"],
                )
                manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))

                self.assertEqual(2, manifest["captured_count"])
                self.assertEqual({"bls_release_calendar", "federal_reserve_fomc_calendar"}, {item["source_id"] for item in manifest["captured"]})
        finally:
            self.capture._fetch_bytes = original_fetch


if __name__ == "__main__":
    unittest.main()
