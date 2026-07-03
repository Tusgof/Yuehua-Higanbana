from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "import_vix_vxv_cboe.py"


def load_importer():
    spec = importlib.util.spec_from_file_location("import_vix_vxv_cboe", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load VIX/VXV importer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ImportVixVxvCboeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.importer = load_importer()

    def make_capture(self, root: Path) -> Path:
        capture_root = root / "2026-06-30"
        capture_root.mkdir(parents=True)
        vix_path = capture_root / "cboe_vix_history.csv"
        vxv_path = capture_root / "cboe_vix3m_history.csv"
        vix_path.write_text(
            "DATE,OPEN,HIGH,LOW,CLOSE\n01/02/2024,14,15,13,14.50\n01/03/2024,15,16,14,15.25\n",
            encoding="utf-8",
        )
        vxv_path.write_text(
            "DATE,OPEN,HIGH,LOW,CLOSE\n01/02/2024,17,18,16,17.50\n01/03/2024,18,19,17,18.25\n",
            encoding="utf-8",
        )
        captured = []
        for series, path in [("VIX", vix_path), ("VIX3M", vxv_path)]:
            payload = path.read_bytes()
            captured.append(
                {
                    "series": series,
                    "source_id": "cboe_volatility_index_history",
                    "provider": "Cboe",
                    "source_url": "https://example.test",
                    "output_path": str(path),
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
        (capture_root / "capture_manifest.json").write_text(
            json.dumps({"as_of_date": "2026-06-30", "captured": captured}, indent=2),
            encoding="utf-8",
        )
        return capture_root

    def test_import_writes_canonical_records_and_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture_root = self.make_capture(root)
            output_path = root / "out" / "vix_vxv.jsonl"
            registry_path = root / "registry" / "datasets.jsonl"
            summary_path = root / "summary.json"

            result = self.importer.import_vix_vxv(
                capture_root=capture_root,
                output_path=output_path,
                registry_path=registry_path,
                summary_path=summary_path,
                start_date=date(2024, 1, 2),
                end_date=date(2024, 1, 3),
            )

            records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
            registry = [json.loads(line) for line in registry_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(2, result["record_count"])
            self.assertEqual("vix_vxv", records[0]["record_type"])
            self.assertEqual(14.5, records[0]["vix_close"])
            self.assertEqual(17.5, records[0]["vxv_close"])
            self.assertEqual("data_registry_manifest", registry[0]["record_type"])
            self.assertTrue(summary_path.exists())

    def test_import_rejects_empty_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture_root = self.make_capture(root)
            with self.assertRaisesRegex(self.importer.VixVxvImportError, "no overlapping"):
                self.importer.import_vix_vxv(
                    capture_root=capture_root,
                    output_path=root / "out.jsonl",
                    registry_path=root / "datasets.jsonl",
                    summary_path=root / "summary.json",
                    start_date=date(2025, 1, 1),
                    end_date=date(2025, 1, 2),
                )


if __name__ == "__main__":
    unittest.main()
