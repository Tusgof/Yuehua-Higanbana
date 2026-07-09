from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PythonSupportTests(unittest.TestCase):
    def test_supported_python_version(self) -> None:
        self.assertGreaterEqual(sys.version_info[:2], (3, 12))
        self.assertLess(sys.version_info[:2], (3, 15))

    def test_supported_version_is_documented(self) -> None:
        agents = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Python 3.12 through 3.14", agents)

    def test_databento_is_pinned_as_optional_only(self) -> None:
        requirements = (PROJECT_ROOT / "requirements-optional.txt").read_text(encoding="utf-8")
        self.assertIn("databento==0.80.0", requirements)
