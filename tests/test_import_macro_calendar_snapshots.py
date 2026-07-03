from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "import_macro_calendar_snapshots.py"
SNAPSHOT_PATH = PROJECT_ROOT / "tests" / "fixtures" / "macro_calendar_snapshots" / "official_macro_calendar_sample.csv"


def load_importer():
    spec = importlib.util.spec_from_file_location("import_macro_calendar_snapshots", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load macro calendar importer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ImportMacroCalendarSnapshotsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.importer = load_importer()

    def test_import_snapshot_writes_macro_events_and_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.importer.import_macro_calendar_snapshot(SNAPSHOT_PATH, output_root=Path(tmp))
            event_path = Path(result["normalized_path"])
            registry_path = Path(result["registry_path"])

            self.assertTrue(event_path.exists())
            self.assertTrue(registry_path.exists())
            events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
            registry = [json.loads(line) for line in registry_path.read_text(encoding="utf-8").splitlines()]

            self.assertEqual(9, len(events))
            self.assertEqual("macro_event", events[0]["record_type"])
            self.assertEqual("data_registry_manifest", registry[0]["record_type"])
            self.assertEqual(result["manifest"]["raw_sha256"], registry[0]["raw_sha256"])
            self.assertIn("CPI", result["event_types"])
            self.assertIn("FOMC_DECISION", result["event_types"])
            self.assertIn("FOMC_MINUTES", result["event_types"])

    def test_import_rejects_event_type_not_allowed_for_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_snapshot = Path(tmp) / "bad_macro_snapshot.csv"
            bad_snapshot.write_text(
                "\n".join(
                    [
                        "source_id,event_type,event_date,release_time_et,title",
                        "federal_reserve_fomc_calendar,CPI,2024-01-11,08:30,Consumer Price Index",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(self.importer.MacroCalendarImportError):
                self.importer.import_macro_calendar_snapshot(bad_snapshot, output_root=Path(tmp) / "out")

    def test_import_rejects_missing_required_event_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            partial_snapshot = Path(tmp) / "partial_macro_snapshot.csv"
            partial_snapshot.write_text(
                "\n".join(
                    [
                        "source_id,event_type,event_date,release_time_et,title",
                        "federal_reserve_fomc_calendar,FOMC_DECISION,2024-01-31,14:00,FOMC statement",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(self.importer.MacroCalendarImportError, "missing required event types"):
                self.importer.import_macro_calendar_snapshot(partial_snapshot, output_root=Path(tmp) / "out")


if __name__ == "__main__":
    unittest.main()
