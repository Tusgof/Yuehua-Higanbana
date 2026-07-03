from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = PROJECT_ROOT / "scripts" / "provider_adapters.py"
FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "provider_samples"


def load_adapter():
    spec = importlib.util.spec_from_file_location("provider_adapters", ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load provider adapters")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProviderAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter = load_adapter()

    def test_optionsdx_like_sample_maps_to_canonical_option_quotes(self) -> None:
        records = self.adapter.parse_optionsdx_quote_csv(FIXTURE_DIR / "optionsdx_option_quote_sample.csv")
        self.assertEqual(2, len(records))
        self.assertEqual("OptionsDX", records[0]["provider"])
        self.assertEqual("put", records[0]["right"])
        self.assertEqual("SPY", records[0]["underlying"])
        self.assertEqual([], self.adapter.validate_record(records[0]))

    def test_thetadata_like_sample_maps_to_canonical_option_quotes(self) -> None:
        records = self.adapter.parse_thetadata_quote_csv(FIXTURE_DIR / "thetadata_option_quote_sample.csv")
        self.assertEqual(2, len(records))
        self.assertEqual("ThetaData", records[0]["provider"])
        self.assertEqual("put", records[0]["right"])
        self.assertEqual(0.0, records[0]["dte"])
        self.assertEqual([], self.adapter.validate_record(records[0]))

    def test_adapter_rejects_missing_bid_ask(self) -> None:
        record = {
            "record_type": "option_quote",
            "schema_version": "m2.0",
            "underlying": "SPY",
            "quote_timestamp_et": "2024-01-03T10:00:00-05:00",
            "expiration_date": "2024-01-03",
            "dte": 0.0,
            "right": "put",
            "strike": 470.0,
            "bid": 1.2,
            "ask": 1.1,
            "bid_size": 1,
            "ask_size": 1,
            "provider": "Synthetic",
            "source": "unit-test",
        }
        with self.assertRaises(ValueError):
            self.adapter.validate_option_quotes([record])


if __name__ == "__main__":
    unittest.main()
