from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

try:
    from openpyxl import Workbook
except ModuleNotFoundError:
    Workbook = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "convert_macro_calendar_capture.py"
CAPTURE_ROOT = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "macro_calendar" / "2026-06-30"


def load_converter():
    spec = importlib.util.spec_from_file_location("convert_macro_calendar_capture", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load macro calendar converter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConvertMacroCalendarCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.converter = load_converter()

    def test_convert_real_capture_writes_importer_csv_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "macro_capture.csv"
            result = self.converter.convert_capture_to_csv(CAPTURE_ROOT, output_path)
            with output_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(result["record_count"], len(rows))
            self.assertGreater(result["record_count"], 20)
            for event_type in [
                "FOMC_DECISION",
                "FOMC_MINUTES",
                "CPI",
                "NFP",
                "PCE",
                "JOLTS",
                "ISM_MANUFACTURING",
                "ISM_SERVICES",
                "RETAIL_SALES",
            ]:
                self.assertIn(event_type, result["event_types"])

    def test_convert_output_can_be_imported_by_macro_importer(self) -> None:
        importer_path = PROJECT_ROOT / "scripts" / "import_macro_calendar_snapshots.py"
        spec = importlib.util.spec_from_file_location("import_macro_calendar_snapshots", importer_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load macro calendar importer")
        importer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(importer)

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "macro_capture.csv"
            self.converter.convert_capture_to_csv(CAPTURE_ROOT, output_path)
            result = importer.import_macro_calendar_snapshot(output_path, output_root=Path(tmp) / "out")

            self.assertGreater(result["record_count"], 20)
            self.assertIn("PCE", result["event_types"])
            self.assertIn("RETAIL_SALES", result["event_types"])

    def test_convert_uses_capture_root_year_instead_of_hardcoded_2026(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            capture_root = self._write_minimal_capture(Path(tmp) / "2025-12-31")
            output_path = Path(tmp) / "macro_capture.csv"
            result = self.converter.convert_capture_to_csv(capture_root, output_path)

            self.assertEqual("2025-01-03", result["coverage_start"])
            self.assertEqual("2025-02-19", result["coverage_end"])
            self.assertIn("FOMC_DECISION", result["event_types"])
            self.assertIn("PCE", result["event_types"])

    def test_convert_default_output_path_uses_capture_root_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            capture_root = self._write_minimal_capture(Path(tmp) / "2025-12-31")
            result = self.converter.convert_capture_to_csv(capture_root)
            output_path = Path(result["output_path"])

            self.assertEqual(capture_root / "official_macro_calendar_2025-12-31.csv", output_path)
            self.assertTrue(output_path.exists())

    def test_convert_fomc_month_range_uses_last_month(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            capture_root = self._write_minimal_capture(Path(tmp) / "2025-12-31")
            fomc_path = capture_root / "federal_reserve_fomc_calendar.html"
            fomc_path.write_text(
                """
                <h2>2025 FOMC Meetings</h2>
                <div class="fomc-meeting">
                  <div class="fomc-meeting__month"><strong>Apr/May</strong></div>
                  <div class="fomc-meeting__date">30-1</div>
                  Released May 28, 2025
                </div></div>
                <h2>2024 FOMC Meetings</h2>
                """,
                encoding="utf-8",
            )
            output_path = Path(tmp) / "macro_capture.csv"
            self.converter.convert_capture_to_csv(capture_root, output_path)

            with output_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertIn(
                {
                    "source_id": "federal_reserve_fomc_calendar",
                    "event_type": "FOMC_DECISION",
                    "event_date": "2025-05-01",
                    "release_time_et": "14:00",
                    "title": "FOMC decision 2025-05-01",
                },
                rows,
            )

    def test_convert_ism_without_historical_table_uses_release_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            capture_root = self._write_minimal_capture(Path(tmp) / "2025-12-31")
            (capture_root / "ism_pmi_release_calendar.html").write_text(
                """
                <p>The release schedule for the Manufacturing and Services ISM PMI Reports is listed below.</p>
                <h3>2026 ISM PMI Reports Release Dates</h3>
                <tbody>
                <tr><th>January 2026</th><td>5</td><td>7</td></tr>
                </tbody>
                """,
                encoding="utf-8",
            )
            output_path = Path(tmp) / "macro_capture.csv"
            self.converter.convert_capture_to_csv(capture_root, output_path)

            with output_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertIn(
                {
                    "source_id": "ism_pmi_release_calendar",
                    "event_type": "ISM_MANUFACTURING",
                    "event_date": "2025-01-03",
                    "release_time_et": "10:00",
                    "title": "ISM Manufacturing PMI",
                },
                rows,
            )
            self.assertIn(
                {
                    "source_id": "ism_pmi_release_calendar",
                    "event_type": "ISM_SERVICES",
                    "event_date": "2025-01-07",
                    "release_time_et": "10:00",
                    "title": "ISM Services PMI",
                },
                rows,
            )

    def test_convert_bls_yearly_list_schedule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            capture_root = self._write_minimal_capture(Path(tmp) / "2025-12-31")
            (capture_root / "bls_release_calendar.html").write_text(
                """
                <table>
                <tr><td>January 15, 2025</td><td>08:30 AM</td><td><strong>Consumer Price Index</strong></td></tr>
                <tr><td>January 10, 2025</td><td>08:30 AM</td><td><strong>Employment Situation</strong></td></tr>
                <tr><td>January 7, 2025</td><td>10:00 AM</td><td><strong>Job Openings and Labor Turnover Survey</strong></td></tr>
                <tr><td>January 17, 2025</td><td>10:00 AM</td><td><strong>State Job Openings and Labor Turnover</strong></td></tr>
                <tr><td>March 20, 2025</td><td>10:00 AM</td><td><strong>Employment Situation of Veterans</strong></td></tr>
                </table>
                """,
                encoding="utf-8",
            )
            output_path = Path(tmp) / "macro_capture.csv"
            self.converter.convert_capture_to_csv(capture_root, output_path)

            with output_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertIn(
                {
                    "source_id": "bls_release_calendar",
                    "event_type": "CPI",
                    "event_date": "2025-01-15",
                    "release_time_et": "08:30",
                    "title": "Consumer Price Index",
                },
                rows,
            )
            self.assertIn(
                {
                    "source_id": "bls_release_calendar",
                    "event_type": "NFP",
                    "event_date": "2025-01-10",
                    "release_time_et": "08:30",
                    "title": "Employment Situation",
                },
                rows,
            )
            self.assertIn(
                {
                    "source_id": "bls_release_calendar",
                    "event_type": "JOLTS",
                    "event_date": "2025-01-07",
                    "release_time_et": "10:00",
                    "title": "Job Openings and Labor Turnover Survey",
                },
                rows,
            )

    def test_convert_census_retail_xls_uses_capture_year(self) -> None:
        if Workbook is None:
            self.skipTest("openpyxl is not installed in this runtime")
        with tempfile.TemporaryDirectory() as tmp:
            capture_root = self._write_minimal_capture(Path(tmp) / "2025-12-31")
            (capture_root / "census_retail_release_schedule.html").unlink()
            workbook = Workbook()
            sheet = workbook.active
            sheet.append(["Advance Monthly Retail Sales Release Dates"])
            sheet.append(["(One Month Lag)"])
            sheet.append([])
            sheet.append(["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
            sheet.append([2024, 17, 15, 14, 15, 15, 18, 16, 15, 17, 17, 15, 17])
            sheet.append([2025, 16, 14, 17, 16, 15, 17, 17, 15, 16, 15, None, 16])
            workbook.save(capture_root / "census_retail_release_schedule.xls")

            output_path = Path(tmp) / "macro_capture.csv"
            self.converter.convert_capture_to_csv(capture_root, output_path)

            with output_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            retail_rows = [row for row in rows if row["event_type"] == "RETAIL_SALES"]

            self.assertEqual(11, len(retail_rows))
            self.assertIn(
                {
                    "source_id": "census_retail_release_schedule",
                    "event_type": "RETAIL_SALES",
                    "event_date": "2025-01-16",
                    "release_time_et": "08:30",
                    "title": "Advance Monthly Retail Trade Report released Jan 2025",
                },
                retail_rows,
            )
            self.assertFalse(any(row["event_date"].startswith("2024") for row in retail_rows))

    def test_convert_bea_release_pages_json_uses_embargo_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            capture_root = self._write_minimal_capture(Path(tmp) / "2025-12-31")
            (capture_root / "bea_release_schedule.html").unlink()
            (capture_root / "bea_release_schedule.json").write_text(
                json.dumps(
                    {
                        "source_id": "bea_release_schedule",
                        "capture_mode": "bea_pce_release_pages",
                        "year": 2025,
                        "pages": [
                            {
                                "title": "Personal Income and Outlays, December 2024",
                                "source_url": "https://www.bea.gov/news/2025/personal-income-and-outlays-december-2024",
                                "content": "EMBARGOED UNTIL RELEASE AT 8:30 a.m. EST, Friday, January 31, 2025",
                            },
                            {
                                "title": "Personal Income and Outlays, December 2023",
                                "source_url": "https://www.bea.gov/news/2024/personal-income-and-outlays-december-2023",
                                "content": "EMBARGOED UNTIL RELEASE AT 8:30 a.m. EST, Friday, January 26, 2024",
                            },
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            output_path = Path(tmp) / "macro_capture.csv"
            self.converter.convert_capture_to_csv(capture_root, output_path)

            with output_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            pce_rows = [row for row in rows if row["event_type"] == "PCE"]

            self.assertEqual(
                [
                    {
                        "source_id": "bea_release_schedule",
                        "event_type": "PCE",
                        "event_date": "2025-01-31",
                        "release_time_et": "08:30",
                        "title": "Personal Income and Outlays, December 2024",
                    }
                ],
                pce_rows,
            )

    def _write_minimal_capture(self, capture_root: Path) -> Path:
        capture_root.mkdir()
        (capture_root / "federal_reserve_fomc_calendar.html").write_text(
            """
            <h2>2025 FOMC Meetings</h2>
            <div class="fomc-meeting">
              <div class="fomc-meeting__month"><strong>January</strong></div>
              <div class="fomc-meeting__date">28-29</div>
              Released February 19, 2025
            </div></div>
            <h2>2024 FOMC Meetings</h2>
            """,
            encoding="utf-8",
        )
        (capture_root / "bls_release_calendar.html").write_text(
            """
            <h1>January 2025</h1>
            <td id="d0110"><strong>Employment Situation<br></strong><br>8:30 AM</td>
            <td id="d0114"><strong>Consumer Price Index<br></strong><br>8:30 AM</td>
            <td id="d0117"><strong>Job Openings and Labor Turnover Survey<br></strong><br>10:00 AM</td>
            """,
            encoding="utf-8",
        )
        (capture_root / "bea_release_schedule.html").write_text(
            """
            <td class="scheduled-date"><div class="release-date">January 31</div><small>8:30 AM</small></td>
            <td class="release-title">Personal Income and Outlays, December 2024</td>
            """,
            encoding="utf-8",
        )
        (capture_root / "ism_pmi_release_calendar.html").write_text(
            """
            <h2>2025 ISM PMI</h2>
            <tbody>
            <tr><th>January 2025</th><td>3</td><td>6</td></tr>
            </tbody>
            """,
            encoding="utf-8",
        )
        (capture_root / "census_retail_release_schedule.html").write_text(
            """
            <h2>Advance Monthly Retail Trade Report</h2>
            <tr><td>December 2024</td><td>January 16, 2025</td></tr>
            <h2>Monthly Retail Trade Report</h2>
            """,
            encoding="utf-8",
        )
        return capture_root


if __name__ == "__main__":
    unittest.main()
