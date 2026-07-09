from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None

from tests.tiers import state_audit_capability


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "normalize_databento_options.py"


def load_normalizer():
    spec = importlib.util.spec_from_file_location("normalize_databento_options", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Databento normalizer")
    module = importlib.util.module_from_spec(spec)
    sys.modules["normalize_databento_options"] = module
    spec.loader.exec_module(module)
    return module


@state_audit_capability("pandas", pd is not None)
class DatabentoNormalizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.normalizer = load_normalizer()

    def test_trade_date_from_window_name(self) -> None:
        self.assertEqual("2024-01-02", self.normalizer.trade_date_from_window_name("2024-01-02_entry_a_0935.dbn.zst"))

    def test_ts_to_et_iso(self) -> None:
        value = pd.Timestamp("2024-01-02T14:35:00Z")
        self.assertEqual("2024-01-02T09:35:00-05:00", self.normalizer.ts_to_et_iso(value))

    def test_combined_raw_hash_is_stable(self) -> None:
        first = self.normalizer.combined_raw_hash([])
        second = self.normalizer.combined_raw_hash([])
        self.assertEqual(first, second)
        self.assertEqual(64, len(first))

    def test_valid_quote_mask_keeps_zero_bid_with_positive_ask(self) -> None:
        frame = pd.DataFrame(
            [
                {"bid_px_00": 0.0, "ask_px_00": 0.01},
                {"bid_px_00": -0.01, "ask_px_00": 0.01},
                {"bid_px_00": 0.0, "ask_px_00": 0.0},
                {"bid_px_00": 0.02, "ask_px_00": 0.01},
            ]
        )

        self.assertEqual([True, False, False, False], self.normalizer.valid_quote_mask(frame).tolist())


if __name__ == "__main__":
    unittest.main()
