from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None

from tests.tiers import state_audit_capability


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "probe_databento_opra_statistics.py"


def load_probe():
    spec = importlib.util.spec_from_file_location("probe_databento_opra_statistics", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load OPRA statistics probe")
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_databento_opra_statistics"] = module
    spec.loader.exec_module(module)
    return module


class DatabentoOpraStatisticsEnumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.probe = load_probe()

    def test_stat_type_name_maps_open_interest_integer(self) -> None:
        self.assertEqual("OPEN_INTEREST", self.probe._stat_type_name(9))

    def test_stat_type_name_maps_open_interest_without_databento_package(self) -> None:
        with patch.dict(sys.modules, {"databento": None}):
            self.assertEqual("OPEN_INTEREST", self.probe._stat_type_name(9))
            self.assertEqual("CLOSE_PRICE", self.probe._stat_type_name(11))


@state_audit_capability("pandas", pd is not None)
class DatabentoOpraStatisticsProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.probe = load_probe()

    def test_summarize_statistics_frame_counts_open_interest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_path = Path(tmp) / "sample.dbn.zst"
            raw_path.write_bytes(b"sample")
            frame = pd.DataFrame(
                {
                    "stat_type": [9, 9, 11],
                    "update_action": [1, 1, 1],
                    "quantity": [100, 150, 0],
                    "price": [0, 0, 425000000000],
                    "symbol": ["SPY   240103C00420000", "SPY   240103P00420000", "SPY   240103C00425000"],
                },
                index=pd.to_datetime(
                    [
                        "2024-01-03T00:00:00Z",
                        "2024-01-03T00:00:01Z",
                        "2024-01-03T00:00:02Z",
                    ]
                ),
            )
            summary = self.probe.summarize_statistics_frame(frame, raw_path, {"schema": "statistics"})
            self.assertEqual(3, summary["row_count"])
            self.assertEqual(2, summary["open_interest_record_count"])
            self.assertEqual({"OPEN_INTEREST": 2, "CLOSE_PRICE": 1}, summary["stat_type_counts"])
            self.assertEqual(100.0, summary["open_interest_quantity"]["min"])
            self.assertEqual(150.0, summary["open_interest_quantity"]["max"])
            self.assertEqual(3, summary["unique_symbol_count"])

    def test_build_result_blocks_missing_open_interest(self) -> None:
        result = self.probe.build_result(
            {"estimated_cost_usd": 0.1},
            {"source": "cache"},
            {
                "row_count": 3,
                "has_stat_type": True,
                "open_interest_record_count": 0,
            },
        )
        self.assertEqual("blocked", result["status"])
        self.assertIn("requires_open_interest_records", result["blockers"])


if __name__ == "__main__":
    unittest.main()
