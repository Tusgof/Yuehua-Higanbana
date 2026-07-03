from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_news_sources.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NewsSourceValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_module(VALIDATOR_PATH, "validate_news_sources")
        cls.plan = cls.validator.load_source_plan()

    def write_plan(self, plan: dict) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "news_sources.json"
        path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        return path

    def test_default_source_plan_validates(self) -> None:
        self.assertEqual([], self.validator.validate_source_plan())
        self.assertEqual("gdelt_doc_api", self.plan["primary_source_id"])

    def test_required_topics_are_covered(self) -> None:
        covered = {topic for source in self.plan["sources"] for topic in source["allowed_topics"]}
        for topic in self.plan["minimum_required_topics"]:
            self.assertIn(topic, covered)

    def test_rejects_missing_timestamp_discipline(self) -> None:
        plan = json.loads(json.dumps(self.plan))
        plan["anti_leakage_rules"]["published_at_must_be_lte_decision_time"] = False
        plan["anti_leakage_rules"]["required_item_fields"].remove("fetched_at_et")

        errors = self.validator.validate_source_plan(self.write_plan(plan))

        self.assertTrue(any("published_at_must_be_lte_decision_time" in error for error in errors))
        self.assertTrue(any("required_item_fields missing fetched_at_et" in error for error in errors))

    def test_rejects_key_required_primary_candidate(self) -> None:
        plan = json.loads(json.dumps(self.plan))
        plan["sources"][1]["archive_status"] = "candidate"
        plan["primary_source_id"] = "alpha_vantage_news_sentiment"

        errors = self.validator.validate_source_plan(self.write_plan(plan))

        self.assertTrue(any("key_required sources must be deferred" in error for error in errors))
        self.assertTrue(any("primary source must be a free candidate" in error for error in errors))

    def test_rejects_duplicate_source_id_and_non_https_url(self) -> None:
        plan = json.loads(json.dumps(self.plan))
        plan["sources"][1]["source_id"] = plan["sources"][0]["source_id"]
        plan["sources"][1]["source_url"] = "http://example.com"

        errors = self.validator.validate_source_plan(self.write_plan(plan))

        self.assertTrue(any("duplicate source_id" in error for error in errors))
        self.assertTrue(any("source_url must be https" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
