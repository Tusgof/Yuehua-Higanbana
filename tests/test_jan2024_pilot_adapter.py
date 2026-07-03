from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_jan2024_pilot_adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("run_jan2024_pilot_adapter", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load pilot adapter")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_jan2024_pilot_adapter"] = module
    spec.loader.exec_module(module)
    return module


class Jan2024PilotAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter = load_adapter()

    def test_is_rth(self) -> None:
        self.assertTrue(self.adapter.is_rth("2024-01-02T09:30:00-05:00"))
        self.assertTrue(self.adapter.is_rth("2024-01-02T15:59:00-05:00"))
        self.assertFalse(self.adapter.is_rth("2024-01-02T16:00:00-05:00"))

    def test_evaluate_trade_date_finds_candidate_ready_day(self) -> None:
        bars = [
            bar("2024-01-02T09:30:00-05:00", 100, 101, 99, 100),
            bar("2024-01-02T09:31:00-05:00", 100, 101, 99, 100),
            bar("2024-01-02T09:34:00-05:00", 100, 101, 99, 100),
            bar("2024-01-02T09:35:00-05:00", 101, 103, 101, 102),
        ]
        quotes = [
            quote("2024-01-02T09:35:00-05:00", "call", 102, 1.0, 1.1),
            quote("2024-01-02T09:35:00-05:00", "call", 104, 0.4, 0.5),
            quote("2024-01-02T09:35:00-05:00", "call", 106, 0.1, 0.2),
        ]
        result = self.adapter.evaluate_trade_date("2024-01-02", bars, quotes)
        self.assertEqual("candidate_ready", result["status"])
        self.assertEqual("call", result["direction"])
        self.assertEqual(2, len(result["legs"]))

    def test_run_pilot_adapter_writes_summary_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bar_path = root / "bars.jsonl"
            quote_path = root / "quotes.jsonl"
            summary_path = root / "summary.json"
            report_path = root / "report.md"
            write_jsonl(
                bar_path,
                [
                    bar("2024-01-02T09:30:00-05:00", 100, 101, 99, 100),
                    bar("2024-01-02T09:31:00-05:00", 100, 101, 99, 100),
                    bar("2024-01-02T09:34:00-05:00", 100, 101, 99, 100),
                    bar("2024-01-02T09:35:00-05:00", 101, 103, 101, 102),
                ],
            )
            write_jsonl(
                quote_path,
                [
                    quote("2024-01-02T09:35:00-05:00", "call", 102, 1.0, 1.1),
                    quote("2024-01-02T09:35:00-05:00", "call", 104, 0.4, 0.5),
                    quote("2024-01-02T09:35:00-05:00", "call", 106, 0.1, 0.2),
                ],
            )
            summary = self.adapter.run_pilot_adapter(bar_path, quote_path, summary_path, report_path)
            self.assertTrue(summary_path.exists())
            self.assertTrue(report_path.exists())

        self.assertEqual(1, summary["candidate_ready_days"])


def bar(timestamp_et: str, open_: float, high: float, low: float, close: float) -> dict:
    return {
        "record_type": "spy_bar",
        "schema_version": "m2.0",
        "symbol": "SPY",
        "timestamp_et": timestamp_et,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": 100,
        "provider": "test",
        "source": "test",
    }


def quote(timestamp_et: str, right: str, strike: float, bid: float, ask: float) -> dict:
    return {
        "record_type": "option_quote",
        "schema_version": "m2.0",
        "underlying": "SPY",
        "quote_timestamp_et": timestamp_et,
        "expiration_date": timestamp_et[:10],
        "dte": 0,
        "right": right,
        "strike": strike,
        "bid": bid,
        "ask": ask,
        "bid_size": 10,
        "ask_size": 10,
        "provider": "test",
        "source": "test",
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
