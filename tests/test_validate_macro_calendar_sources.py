from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_macro_calendar_sources.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MacroCalendarSourceValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_module(VALIDATOR_PATH, "validate_macro_calendar_sources")
        cls.plan = cls.validator.load_source_plan()

    def write_plan(self, plan: dict) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "macro_sources.json"
        path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        return path

    def test_default_source_plan_validates(self) -> None:
        self.assertEqual([], self.validator.validate_source_plan())
        self.assertEqual(5, len(self.plan["sources"]))

    def test_required_event_types_are_covered(self) -> None:
        covered = {event_type for source in self.plan["sources"] for event_type in source["event_types"]}
        for event_type in self.plan["minimum_required_event_types"]:
            self.assertIn(event_type, covered)

    def test_rejects_missing_required_event_type(self) -> None:
        plan = json.loads(json.dumps(self.plan))
        plan["sources"] = [source for source in plan["sources"] if source["source_id"] != "bea_release_schedule"]

        errors = self.validator.validate_source_plan(self.write_plan(plan))

        self.assertTrue(any("missing required macro event type PCE" in error for error in errors))

    def test_rejects_duplicate_source_id_and_non_https_url(self) -> None:
        plan = json.loads(json.dumps(self.plan))
        plan["sources"][1]["source_id"] = plan["sources"][0]["source_id"]
        plan["sources"][1]["source_url"] = "http://example.com"

        errors = self.validator.validate_source_plan(self.write_plan(plan))

        self.assertTrue(any("duplicate source_id" in error for error in errors))
        self.assertTrue(any("source_url must be https" in error for error in errors))

    def test_rejects_unknown_output_extension(self) -> None:
        plan = json.loads(json.dumps(self.plan))
        plan["sources"][4]["output_extension"] = "zip"

        errors = self.validator.validate_source_plan(self.write_plan(plan))

        self.assertTrue(any("output_extension must be html, json, or xls" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
