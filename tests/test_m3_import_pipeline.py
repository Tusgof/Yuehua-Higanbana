from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMPORTER_PATH = PROJECT_ROOT / "scripts" / "import_m3_fixture.py"
RAW_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "m3_fixture_raw.json"


def load_importer():
    spec = importlib.util.spec_from_file_location("import_m3_fixture", IMPORTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M3 importer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class M3ImportPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.importer = load_importer()

    def test_import_fixture_writes_normalized_files_and_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            result = self.importer.import_raw_dataset(RAW_FIXTURE, output_root)

            self.assertEqual(6, result["record_count"])
            self.assertIn("option_quote", result["record_types"])
            for written_file in result["written_files"]:
                path = Path(written_file)
                self.assertTrue(path.exists())
                self.assertTrue(path.read_text(encoding="utf-8").strip())

            registry_path = Path(result["registry_path"])
            registry_rows = [json.loads(line) for line in registry_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len(registry_rows))
            registry = registry_rows[0]
            self.assertEqual("synthetic", registry["provider"])
            self.assertEqual("m2_contracts", registry["schema_name"])
            self.assertRegex(registry["raw_sha256"], r"^[0-9a-f]{64}$")

    def test_import_rejects_bad_option_spread(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "out"
            raw_copy = Path(tmp) / "bad_raw.json"
            shutil.copyfile(RAW_FIXTURE, raw_copy)
            payload = json.loads(raw_copy.read_text(encoding="utf-8"))
            payload["records"][1]["bid"] = 1.30
            payload["records"][1]["ask"] = 1.20
            raw_copy.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaises(self.importer.ImportErrorWithContext):
                self.importer.import_raw_dataset(raw_copy, output_root)

    def test_quality_check_rejects_duplicate_quote_keys(self) -> None:
        payload = json.loads(RAW_FIXTURE.read_text(encoding="utf-8"))
        duplicate_quote = dict(payload["records"][1])
        payload["records"].append(duplicate_quote)
        errors = self.importer.quality_check_records(payload["records"])
        self.assertTrue(any("duplicate logical key" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
