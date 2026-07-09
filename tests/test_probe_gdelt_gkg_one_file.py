from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "probe_gdelt_gkg_one_file.py"


def load_probe():
    spec = importlib.util.spec_from_file_location("probe_gdelt_gkg_one_file", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load GDELT GKG one-file probe")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProbeGdeltGkgOneFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.probe = load_probe()

    def test_probe_reports_field_mapping_blockers_without_canonical_import_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_zip = root / "20240103140000.gkg.csv.zip"
            inner_name = "20240103140000.gkg.csv"
            row = [
                "20240103140000-0",
                "20240103140000",
                "1",
                "example.com",
                "https://example.com/market-stress-test",
                "",
                "",
                "ECON_STOCKMARKET;CRISISLEX_CRISISLEXREC",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "1.1,2.2,3.3",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
            with zipfile.ZipFile(source_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(inner_name, "\t".join(row) + "\n")

            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "manifest_items": [
                            {
                                "family": "gkg",
                                "available_in_master_file_list": True,
                                "compressed_bytes": source_zip.stat().st_size,
                                "trade_date": "2024-01-03",
                                "decision_time_et": "2024-01-03T09:30:00-05:00",
                                "gdelt_file_timestamp_utc": "20240103140000",
                                "basename": source_zip.name,
                                "source_url": source_zip.as_uri(),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = self.probe.probe_gdelt_gkg_one_file(
                manifest_path=manifest_path,
                raw_dir=root / "raw",
                json_output=root / "probe.json",
                report_output=root / "probe.md",
            )
            self.assertTrue(Path(result["raw_zip_path"]).exists())

        self.assertEqual("blocked_requires_enrichment_or_policy", result["status"])
        self.assertEqual(1, result["row_count"])
        self.assertEqual(1, result["https_url_count"])
        self.assertEqual(1, result["non_empty_source_count"])
        self.assertEqual("blocked", result["field_mapping"]["headline"]["status"])
        self.assertEqual("surrogate_only", result["field_mapping"]["published_at_et"]["status"])
        self.assertIn("gkg_has_no_verified_headline_field", result["blockers"])
        self.assertIn("gkg_topic_mapping_not_pre_registered", result["blockers"])


if __name__ == "__main__":
    unittest.main()
