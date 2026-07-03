from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_m2_contracts.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_m2_contracts", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M2 contract validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class M2ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()
        cls.schema = cls.validator.load_schema()

    def test_schema_covers_required_record_types(self) -> None:
        expected = {
            "spy_bar",
            "option_quote",
            "vix_vxv",
            "macro_event",
            "news_item",
            "llm_assessment",
            "strategy_intent",
            "option_leg",
            "fill",
            "trade",
            "daily_pnl",
            "experiment_manifest",
            "report_metadata",
            "data_registry_manifest",
        }
        self.assertEqual(expected, set(self.schema["records"]))

    def test_valid_fixture_records_pass(self) -> None:
        path = PROJECT_ROOT / "tests" / "fixtures" / "m2_valid_records.json"
        errors = self.validator.validate_file(path, self.schema)
        self.assertEqual([], errors)

    def test_invalid_fixture_records_fail(self) -> None:
        path = PROJECT_ROOT / "tests" / "fixtures" / "m2_invalid_records.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["case"]):
                errors = self.validator.validate_record(case["record"], self.schema)
                self.assertTrue(errors)

    def test_option_quote_requires_bid_ask_for_implementable_pnl(self) -> None:
        record = {
            "record_type": "option_quote",
            "schema_version": "m2.0",
            "underlying": "SPY",
            "quote_timestamp_et": "2024-01-03T10:00:00-05:00",
            "expiration_date": "2024-01-03",
            "dte": 0.25,
            "right": "put",
            "strike": 470,
            "bid": 1.15,
            "ask": 1.2,
            "bid_size": 120,
            "ask_size": 105,
            "provider": "synthetic",
            "source": "fixture",
        }
        self.assertEqual([], self.validator.validate_record(record, self.schema))
        del record["bid"]
        self.assertTrue(self.validator.validate_record(record, self.schema))

    def test_registry_requires_provider_coverage_hash_and_schema(self) -> None:
        record = {
            "record_type": "data_registry_manifest",
            "schema_version": "m2.0",
            "dataset_id": "dataset-fixture",
            "provider": "synthetic",
            "source_url": "file://fixture",
            "ingested_at_et": "2024-01-04T08:00:00-05:00",
            "coverage_start": "2024-01-03",
            "coverage_end": "2024-01-03",
            "raw_sha256": "c" * 64,
            "schema_name": "m2_contracts",
            "schema_version_applied": "m2.0",
            "license_notes": "Synthetic fixture only.",
        }
        self.assertEqual([], self.validator.validate_record(record, self.schema))
        record.pop("provider")
        self.assertTrue(self.validator.validate_record(record, self.schema))


if __name__ == "__main__":
    unittest.main()
