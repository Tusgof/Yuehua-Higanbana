from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "resolve_databento_integrity_redownload.py"


def load_module():
    spec = importlib.util.spec_from_file_location("resolve_databento_integrity_redownload", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Databento integrity resolver")
    module = importlib.util.module_from_spec(spec)
    sys.modules["resolve_databento_integrity_redownload"] = module
    spec.loader.exec_module(module)
    return module


class DatabentoIntegrityClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resolver = load_module()

    def test_case_1_restores_historical_hash(self) -> None:
        self.assertEqual(("case_1", "restored_from_provider"), self.resolver.classify("historical", "historical", "current"))

    def test_case_2_accepts_provider_revision(self) -> None:
        self.assertEqual(("case_2", "provider_revision_accepted"), self.resolver.classify("current", "historical", "current"))

    def test_case_3_escalates_unexplained_result(self) -> None:
        self.assertEqual(("case_3", "escalated_unexplained"), self.resolver.classify("fresh", "historical", "current"))


if __name__ == "__main__":
    unittest.main()
