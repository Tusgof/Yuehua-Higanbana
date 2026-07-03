from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_m5_entry_timing_sensitivity.py"


def load_script():
    spec = importlib.util.spec_from_file_location("run_m5_entry_timing_sensitivity", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M5.3 script")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_m5_entry_timing_sensitivity"] = module
    spec.loader.exec_module(module)
    return module


class M5EntryTimingSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_script()

    def test_default_scenarios_cover_subsystems_and_timing_axes(self) -> None:
        scenarios = self.script.default_scenarios()

        self.assertEqual(12, len(scenarios))
        self.assertEqual({"sub_a", "sub_b"}, {row["subsystem"] for row in scenarios})
        self.assertIn("09:35:00", {row["entry_time"] for row in scenarios if row["subsystem"] == "sub_a"})
        self.assertIn("10:00:00", {row["entry_time"] for row in scenarios if row["subsystem"] == "sub_a"})
        self.assertIn("09:55:00", {row["entry_time"] for row in scenarios if row["subsystem"] == "sub_b"})
        self.assertIn("10:00:00", {row["entry_time"] for row in scenarios if row["subsystem"] == "sub_b"})

    def test_subsystem_a_recomputes_breakout_time(self) -> None:
        bars = [
            bar("2024-01-08T09:30:00-05:00", 100, 101, 99, 100),
            bar("2024-01-08T09:35:00-05:00", 100, 101, 99, 100.5),
            bar("2024-01-08T10:00:00-05:00", 100.5, 103, 100, 102.5),
        ]
        quotes = {
            "2024-01-08T10:00:00-05:00": [
                quote("2024-01-08T10:00:00-05:00", "call", 104.0),
                quote("2024-01-08T10:00:00-05:00", "call", 106.0),
            ]
        }

        day = self.script.build_subsystem_a_day("2024-01-08", bars, quotes, "10:00:00")

        self.assertEqual("candidate_ready", day["status"])
        self.assertEqual("2024-01-08T10:00:00-05:00", day["orb_signal"]["breakout_timestamp_et"])
        self.assertEqual("call", day["direction"])

    def test_subsystem_b_requires_exact_entry_snapshot(self) -> None:
        snapshots = {
            "2024-01-08T09:59:00-05:00": {100.0: quote("2024-01-08T09:59:00-05:00", "put", 100.0)}
        }

        self.assertIsNone(self.script.exact_snapshot_timestamp(snapshots, self.script.parse_time("10:00:00")))
        self.assertEqual(
            "2024-01-08T09:59:00-05:00",
            self.script.exact_snapshot_timestamp(snapshots, self.script.parse_time("09:59:00")),
        )

    def test_search_log_record_contains_timing_parameters(self) -> None:
        row = {
            "trial_index": 1,
            "scenario_id": "sub_a_orb_breakout_0935",
            "subsystem": "sub_a",
            "entry_time": "09:35:00",
            "timing_axis": "orb_breakout_time",
            "fill_model": "half_spread",
            "fee_per_contract": 0.64,
            "exit_model": "forced_close_only",
            "metrics": {"total_implementable_pnl": 1.0},
            "sample_adequacy": {"labels": ["under-sampled"]},
        }

        record = self.script.search_log_record(row)

        self.assertEqual("m5_entry_timing_sensitivity", record["experiment_id"])
        self.assertEqual("09:35:00", record["parameters"]["entry_time"])
        self.assertEqual("orb_breakout_time", record["parameters"]["timing_axis"])

    def test_write_search_log_writes_all_trials(self) -> None:
        rows = [
            {
                "trial_index": 1,
                "scenario_id": "sub_a_orb_breakout_0935",
                "subsystem": "sub_a",
                "entry_time": "09:35:00",
                "timing_axis": "orb_breakout_time",
                "fill_model": "half_spread",
                "fee_per_contract": 0.64,
                "exit_model": "forced_close_only",
                "metrics": {"total_implementable_pnl": 1.0},
                "sample_adequacy": {"labels": ["under-sampled"]},
            },
            {
                "trial_index": 2,
                "scenario_id": "sub_b_put_ratio_entry_1000",
                "subsystem": "sub_b",
                "entry_time": "10:00:00",
                "timing_axis": "entry_snapshot_time",
                "fill_model": "half_spread",
                "fee_per_contract": 0.64,
                "exit_model": "forced_close_only",
                "metrics": {"total_implementable_pnl": -1.0},
                "sample_adequacy": {"labels": ["under-sampled"]},
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "search.jsonl"
            self.script.write_search_log(rows, path)
            lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(2, len(lines))
        self.assertEqual("sub_b", lines[1]["parameters"]["subsystem"])


def bar(timestamp: str, open_: float, high: float, low: float, close: float) -> dict:
    return {"timestamp_et": timestamp, "open": open_, "high": high, "low": low, "close": close}


def quote(timestamp: str, right: str, strike: float) -> dict:
    return {
        "underlying": "SPY",
        "expiration_date": timestamp[:10],
        "quote_timestamp_et": timestamp,
        "right": right,
        "strike": strike,
        "bid": 1.0,
        "ask": 1.2,
    }


if __name__ == "__main__":
    unittest.main()
