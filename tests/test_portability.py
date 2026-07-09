from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("scripts", "tests", "experiments")
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".py", ".txt", ".yaml", ".yml"}
FORBIDDEN_PATTERNS = {
    "machine_absolute_path": re.compile(r"(?i)\b[A-Z]:[/\\]Fogust\b"),
    "sibling_windows_venv": re.compile(
        r"(?i)Yuehua Investment Lab[/\\].venv[/\\]Scripts[/\\]python\.exe"
    ),
}


class PortabilityTests(unittest.TestCase):
    def test_runtime_and_control_artifacts_have_no_forbidden_machine_paths(self) -> None:
        failures: list[str] = []
        for root_name in SCAN_ROOTS:
            root = PROJECT_ROOT / root_name
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                    continue
                text = path.read_text(encoding="utf-8-sig")
                for pattern_name, pattern in FORBIDDEN_PATTERNS.items():
                    if pattern.search(text):
                        relative = path.relative_to(PROJECT_ROOT).as_posix()
                        failures.append(f"{pattern_name}:{relative}")
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
