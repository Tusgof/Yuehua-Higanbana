from __future__ import annotations

import importlib.util
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
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "inspect_databento_raw.py"


def load_inspector():
    spec = importlib.util.spec_from_file_location("inspect_databento_raw", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Databento raw inspector")
    module = importlib.util.module_from_spec(spec)
    sys.modules["inspect_databento_raw"] = module
    spec.loader.exec_module(module)
    return module


@state_audit_capability("pandas", pd is not None)
class DatabentoRawInspectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inspector = load_inspector()

    def test_parse_databento_option_symbol(self) -> None:
        parsed = self.inspector.parse_databento_option_symbol("SPY   240102C00402000")
        self.assertEqual(
            {"underlying": "SPY", "expiration": "2024-01-02", "right": "call", "strike": 402.0},
            parsed,
        )

    def test_summarize_frame_counts_valid_bid_ask_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.dbn.zst"
            path.write_bytes(b"sample")
            frame = pd.DataFrame(
                {
                    "bid_px_00": [1.0, 0.0, 2.0],
                    "ask_px_00": [1.1, 0.1, 1.9],
                    "symbol": [
                        "SPY   240102C00402000",
                        "SPY   240102P00402000",
                        "SPY   240102C00403000",
                    ],
                },
                index=pd.to_datetime(
                    [
                        "2024-01-02T14:31:00Z",
                        "2024-01-02T14:32:00Z",
                        "2024-01-02T14:33:00Z",
                    ]
                ),
            )
            summary = self.inspector.summarize_frame(frame, path, {"dataset": "OPRA.PILLAR", "schema": "cbbo-1m"})
            self.assertEqual(3, summary["row_count"])
            self.assertEqual(1, summary["valid_bid_ask_rows"])
            self.assertEqual(["call", "put"], summary["rights"])
            self.assertEqual(["2024-01-02"], summary["expirations"])
            self.assertEqual(402.0, summary["strike_min"])
            self.assertEqual(403.0, summary["strike_max"])


if __name__ == "__main__":
    unittest.main()
