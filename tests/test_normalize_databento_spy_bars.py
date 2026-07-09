from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None

from tests.tiers import state_audit_capability


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "normalize_databento_spy_bars.py"


def load_normalizer():
    spec = importlib.util.spec_from_file_location("normalize_databento_spy_bars", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Databento SPY bar normalizer")
    module = importlib.util.module_from_spec(spec)
    sys.modules["normalize_databento_spy_bars"] = module
    spec.loader.exec_module(module)
    return module


@state_audit_capability("pandas", pd is not None)
class DatabentoSpyBarsNormalizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.normalizer = load_normalizer()

    def test_ts_to_et_iso(self) -> None:
        value = pd.Timestamp("2024-01-02T14:30:00Z")
        self.assertEqual("2024-01-02T09:30:00-05:00", self.normalizer.ts_to_et_iso(value))

    def test_normalize_frame_writes_valid_spy_rows(self) -> None:
        frame = pd.DataFrame(
            [
                {"open": 472.18, "high": 472.65, "low": 472.06, "close": 472.52, "volume": 47609, "symbol": "SPY"},
                {"open": 10.0, "high": 9.0, "low": 10.0, "close": 10.0, "volume": 1, "symbol": "SPY"},
                {"open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0, "volume": 1, "symbol": "QQQ"},
            ],
            index=pd.DatetimeIndex(
                [
                    "2024-01-02T14:30:00Z",
                    "2024-01-02T14:31:00Z",
                    "2024-01-02T14:32:00Z",
                ],
                name="ts_event",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "spy_bar.jsonl"
            result = self.normalizer.normalize_frame(frame, Path("raw.dbn.zst"), output_path)
            rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(3, result["input_rows"])
        self.assertEqual(1, result["output_rows"])
        self.assertEqual(1, result["skipped_non_spy"])
        self.assertEqual(1, result["skipped_invalid_ohlc"])
        self.assertEqual("2024-01-02T09:30:00-05:00", rows[0]["timestamp_et"])
        self.assertEqual("Databento", rows[0]["provider"])

    def test_manifest_dataset_id_uses_coverage_window(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_path = Path(temp_dir) / "raw.dbn.zst"
            raw_path.write_bytes(b"dbn")
            manifest = self.normalizer.build_manifest(raw_path, "2024-02-01", "2024-02-29")

        self.assertTrue(manifest["dataset_id"].startswith("databento-spy-bars-2024-02-01-to-2024-02-29-"))


if __name__ == "__main__":
    unittest.main()
