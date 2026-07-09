from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "plan_gdelt_bulk_raw_manifest.py"


def load_planner():
    spec = importlib.util.spec_from_file_location("plan_gdelt_bulk_raw_manifest", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load GDELT bulk raw manifest planner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PlanGdeltBulkRawManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.planner = load_planner()

    def test_planner_matches_expected_master_files_without_raw_download(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command_plan_path = root / "command_plan.json"
            master_path = root / "masterfilelist.txt"
            command_plan_path.write_text(
                json.dumps(
                    {
                        "lookback_hours": 1,
                        "commands": [
                            {
                                "trade_date": "2024-01-03",
                                "decision_time_et": "2024-01-03T09:30:00-05:00",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            master_path.write_text(
                "\n".join(
                    [
                        "100 hash-a http://data.gdeltproject.org/gdeltv2/20240103133000.gkg.csv.zip",
                        "200 hash-b http://data.gdeltproject.org/gdeltv2/20240103134500.gkg.csv.zip",
                        "300 hash-c http://data.gdeltproject.org/gdeltv2/20240103140000.mentions.CSV.zip",
                        "400 hash-d http://data.gdeltproject.org/gdeltv2/20240103141500.export.CSV.zip",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = self.planner.plan_bulk_raw_manifest(
                command_plan_path=command_plan_path,
                master_file_list_path=master_path,
                families=["gkg", "mentions", "export"],
            )

        self.assertEqual("ready_for_one_file_probe", result["status"])
        self.assertEqual("metadata_only_no_raw_download", result["mode"])
        self.assertEqual(15, result["expected_file_count"])
        self.assertEqual(4, result["matched_file_count"])
        self.assertEqual(11, result["missing_file_count"])
        self.assertEqual(1000, result["estimated_total_compressed_bytes"])
        self.assertEqual(11, len(result["missing_manifest_items"]))
        self.assertEqual(5, result["by_family"]["gkg"]["expected_file_count"])
        self.assertEqual(2, result["by_family"]["gkg"]["matched_file_count"])
        self.assertTrue(all(item["download_status"] == "not_downloaded_metadata_only" for item in result["manifest_items"]))

    def test_unknown_family_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command_plan_path = root / "command_plan.json"
            master_path = root / "masterfilelist.txt"
            command_plan_path.write_text(json.dumps({"commands": [{"trade_date": "2024-01-03", "decision_time_et": "2024-01-03T09:30:00-05:00"}]}), encoding="utf-8")
            master_path.write_text("", encoding="utf-8")

            with self.assertRaises(self.planner.GdeltBulkRawManifestError):
                self.planner.plan_bulk_raw_manifest(command_plan_path=command_plan_path, master_file_list_path=master_path, families=["rss"])


if __name__ == "__main__":
    unittest.main()
