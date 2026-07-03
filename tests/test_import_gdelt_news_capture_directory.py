from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "import_gdelt_news_capture_directory.py"


def load_importer():
    spec = importlib.util.spec_from_file_location("import_gdelt_news_capture_directory", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load GDELT directory importer")
    module = importlib.util.module_from_spec(spec)
    sys.modules["import_gdelt_news_capture_directory"] = module
    spec.loader.exec_module(module)
    return module


class ImportGdeltNewsCaptureDirectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.importer = load_importer()

    def test_import_capture_directory_combines_snapshots_and_reuses_news_importer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "gdelt"
            input_dir.mkdir()
            _write_snapshot(
                input_dir / "2024-01-05.csv",
                [
                    _row("market_panic", "2024-01-05T14:00:00Z", "Market selloff fear", "https://example.com/a"),
                    _row("systemic_banking_stress", "2024-01-05T14:01:00Z", "Bank funding stress", "https://example.com/b"),
                    _row("war_escalation", "2024-01-05T14:02:00Z", "Geopolitical risk rises", "https://example.com/c"),
                ],
            )
            _write_snapshot(
                input_dir / "2024-01-08.csv",
                [
                    _row("index_halt_circuit_breaker", "2024-01-08T14:03:00Z", "Trading halt watch", "https://example.com/d"),
                    _row("macro_policy_risk", "2024-01-08T14:04:00Z", "Fed inflation risk", "https://example.com/e"),
                ],
            )
            output_root = root / "out"
            combined_path = root / "combined.csv"
            summary_path = root / "summary.json"
            report_path = root / "summary.md"

            result = self.importer.import_capture_directory(input_dir, output_root=output_root, combined_snapshot_path=combined_path, summary_path=summary_path, report_path=report_path)

            self.assertEqual(2, result["snapshot_count"])
            self.assertEqual(5, result["combined_row_count"])
            self.assertEqual(5, result["record_count"])
            self.assertTrue(combined_path.exists())
            self.assertTrue((output_root / "data" / "normalized" / "spy_0dte" / "news" / "news_item.jsonl").exists())
            self.assertEqual(result, json.loads(summary_path.read_text(encoding="utf-8")))
            self.assertIn("GDELT News Capture Directory Import Summary", report_path.read_text(encoding="utf-8"))

    def test_empty_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(self.importer.GdeltNewsDirectoryImportError):
                self.importer.import_capture_directory(Path(tmp), output_root=Path(tmp) / "out")


def _write_snapshot(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=load_importer().FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def _row(topic: str, published_at_utc: str, headline: str, url: str) -> dict[str, str]:
    return {
        "source_id": "gdelt_doc_api",
        "topic": topic,
        "decision_time_et": "2024-01-08T09:30:00-05:00",
        "fetched_at_utc": published_at_utc,
        "published_at_utc": published_at_utc,
        "source_name": "example.com",
        "headline": headline,
        "url": url,
    }


if __name__ == "__main__":
    unittest.main()
