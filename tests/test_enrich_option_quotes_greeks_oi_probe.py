from __future__ import annotations

import importlib.util
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import TestCase
from zoneinfo import ZoneInfo

from tests.tiers import state_audit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "enrich_option_quotes_greeks_oi_probe.py"
UTC = ZoneInfo("UTC")


def load_module():
    spec = importlib.util.spec_from_file_location("enrich_option_quotes_greeks_oi_probe", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class EnrichOptionQuotesGreeksOiProbeTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.enricher = load_module()

    def test_latest_oi_before_uses_only_prior_records(self) -> None:
        rows = [
            {"ts_recv_dt": datetime(2024, 1, 3, 11, 30, tzinfo=UTC), "quantity": 10},
            {"ts_recv_dt": datetime(2024, 1, 3, 14, 40, tzinfo=UTC), "quantity": 20},
        ]

        selected = self.enricher.latest_oi_before(rows, datetime(2024, 1, 3, 14, 31, tzinfo=UTC))

        self.assertEqual(10, selected["quantity"])

    def test_enrich_quote_adds_timestamp_safe_fields(self) -> None:
        quote = {
            "record_type": "option_quote",
            "schema_version": "m2.0",
            "underlying": "SPY",
            "quote_timestamp_et": "2024-01-03T09:56:00-05:00",
            "expiration_date": "2024-01-03",
            "dte": 0,
            "right": "call",
            "strike": 470.0,
            "bid": 1.05,
            "ask": 1.06,
            "bid_size": 10,
            "ask_size": 10,
            "provider": "Databento",
            "source": "fixture",
            "databento_symbol": "SPY   240103C00470000",
        }
        bars = [
            {"timestamp_et": "2024-01-03T09:55:00-05:00", "close": 469.9},
            {"timestamp_et": "2024-01-03T09:56:00-05:00", "close": 469.97},
        ]
        oi_lookup = {
            "SPY   240103C00470000": [
                {
                    "ts_recv_dt": datetime(2024, 1, 3, 11, 30, tzinfo=UTC),
                    "ts_recv_utc": "2024-01-03T11:30:00+00:00",
                    "quantity": 123,
                }
            ]
        }

        enriched = self.enricher.enrich_quote(quote, bars, oi_lookup)

        self.assertEqual("option_quote_greeks_oi_probe", enriched["record_type"])
        self.assertEqual(469.97, enriched["underlying_price"])
        self.assertEqual(123, enriched["open_interest"])
        self.assertEqual("computed_with_caveats", enriched["greeks_status"])
        self.assertIn("implied_volatility", enriched)
        self.assertIn("delta", enriched)
        self.assertIn("gamma", enriched)

    @state_audit(("HIGANBANA_DATA_ROOT", PROJECT_ROOT / "data"))
    def test_current_project_enrichment_probe_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_jsonl = root / "option_quote_enriched.jsonl"
            summary_output = root / "summary.json"
            report_output = root / "report.md"

            result = self.enricher.run_enrichment_probe(
                output_jsonl=output_jsonl,
                summary_output=summary_output,
                report_output=report_output,
            )

            self.assertEqual("pass", result["status"])
            self.assertGreater(result["quote_count"], 0)
            self.assertGreater(result["open_interest_join_count"], 0)
            self.assertGreater(result["computed_greeks_count"], 0)
            self.assertTrue(output_jsonl.exists())
            self.assertEqual(result, json.loads(summary_output.read_text(encoding="utf-8")))
            self.assertIn("# Greeks/OI Enrichment Probe", report_output.read_text(encoding="utf-8"))
