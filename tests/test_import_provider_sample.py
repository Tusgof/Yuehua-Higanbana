from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "import_provider_sample.py"
FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "provider_samples"


def load_importer():
    spec = importlib.util.spec_from_file_location("import_provider_sample", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load provider sample importer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ImportProviderSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.importer = load_importer()

    def test_import_optionsdx_sample_writes_jsonl_and_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            result = self.importer.import_provider_sample(
                "optionsdx",
                FIXTURE_DIR / "optionsdx_option_quote_sample.csv",
                output_root,
            )
            quote_path = Path(result["normalized_path"])
            registry_path = Path(result["registry_path"])

            self.assertTrue(quote_path.exists())
            self.assertTrue(registry_path.exists())
            records = [json.loads(line) for line in quote_path.read_text(encoding="utf-8").splitlines()]
            registry = [json.loads(line) for line in registry_path.read_text(encoding="utf-8").splitlines()]

            self.assertEqual(2, len(records))
            self.assertEqual("OptionsDX", records[0]["provider"])
            self.assertEqual("data_registry_manifest", registry[0]["record_type"])
            self.assertEqual(result["manifest"]["raw_sha256"], registry[0]["raw_sha256"])

    def test_import_rejects_unsupported_provider(self) -> None:
        with self.assertRaises(ValueError):
            self.importer.parse_provider_sample(
                "unknown",
                FIXTURE_DIR / "optionsdx_option_quote_sample.csv",
            )


if __name__ == "__main__":
    unittest.main()
