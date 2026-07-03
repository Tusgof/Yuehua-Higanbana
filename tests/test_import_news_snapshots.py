from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "import_news_snapshots.py"
SNAPSHOT_PATH = PROJECT_ROOT / "tests" / "fixtures" / "news_snapshots" / "gdelt_news_sample.csv"


def load_importer():
    spec = importlib.util.spec_from_file_location("import_news_snapshots", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load news importer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ImportNewsSnapshotsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.importer = load_importer()

    def test_import_snapshot_writes_news_items_and_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.importer.import_news_snapshot(SNAPSHOT_PATH, output_root=Path(tmp))
            news_path = Path(result["normalized_path"])
            registry_path = Path(result["registry_path"])

            self.assertTrue(news_path.exists())
            self.assertTrue(registry_path.exists())
            news_items = [json.loads(line) for line in news_path.read_text(encoding="utf-8").splitlines()]
            registry = [json.loads(line) for line in registry_path.read_text(encoding="utf-8").splitlines()]

            self.assertEqual(5, len(news_items))
            self.assertEqual("news_item", news_items[0]["record_type"])
            self.assertEqual("data_registry_manifest", registry[0]["record_type"])
            self.assertEqual(result["manifest"]["raw_sha256"], registry[0]["raw_sha256"])
            self.assertIn("market_panic", result["topics"])
            self.assertIn("systemic_banking_stress", result["topics"])
            self.assertIn("macro_policy_risk", result["topics"])
            for item in news_items:
                self.assertEqual("2024-01-03T09:30:00-05:00", item["decision_time_et"])
                self.assertLessEqual(item["published_at_et"], item["decision_time_et"])
                self.assertLessEqual(item["fetched_at_et"], item["decision_time_et"])

    def test_import_rejects_topic_not_allowed_for_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_snapshot = Path(tmp) / "bad_news_snapshot.csv"
            bad_snapshot.write_text(
                "\n".join(
                    [
                        "source_id,topic,decision_time_et,fetched_at_utc,published_at_utc,source_name,headline,url",
                        "sec_newsroom,war_escalation,2024-01-03T09:30:00-05:00,2024-01-03T14:20:00Z,2024-01-03T14:00:00Z,SEC,Official notice,https://example.com/sec/notice",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(self.importer.NewsImportError, "not allowed"):
                self.importer.import_news_snapshot(bad_snapshot, output_root=Path(tmp) / "out")

    def test_import_rejects_lookahead_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_snapshot = Path(tmp) / "bad_news_snapshot.csv"
            bad_snapshot.write_text(
                "\n".join(
                    [
                        "source_id,topic,decision_time_et,fetched_at_utc,published_at_utc,source_name,headline,url",
                        "gdelt_doc_api,market_panic,2024-01-03T09:30:00-05:00,2024-01-03T14:35:00Z,2024-01-03T14:00:00Z,Reuters,Late fetched item,https://example.com/gdelt/late",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(self.importer.NewsImportError, "after decision_time_et"):
                self.importer.import_news_snapshot(bad_snapshot, output_root=Path(tmp) / "out")

    def test_import_rejects_missing_required_topics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            partial_snapshot = Path(tmp) / "partial_news_snapshot.csv"
            partial_snapshot.write_text(
                "\n".join(
                    [
                        "source_id,topic,decision_time_et,fetched_at_utc,published_at_utc,source_name,headline,url",
                        "gdelt_doc_api,market_panic,2024-01-03T09:30:00-05:00,2024-01-03T14:20:00Z,2024-01-03T14:00:00Z,Reuters,Market stress,https://example.com/gdelt/market-only",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(self.importer.NewsImportError, "missing required news topics"):
                self.importer.import_news_snapshot(partial_snapshot, output_root=Path(tmp) / "out")


if __name__ == "__main__":
    unittest.main()
