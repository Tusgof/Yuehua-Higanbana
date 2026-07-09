from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path
from unittest import TestCase

from tests.tiers import state_audit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_greeks_oi_feasibility.py"


def load_module():
    spec = importlib.util.spec_from_file_location("audit_greeks_oi_feasibility", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GreeksOiFeasibilityTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = load_module()

    def test_parse_databento_option_symbol(self) -> None:
        parsed = self.audit.parse_databento_option_symbol("SPY   240103C00420000")

        self.assertEqual("SPY", parsed["underlying"])
        self.assertEqual("2024-01-03", parsed["expiration_date"])
        self.assertEqual("call", parsed["right"])
        self.assertEqual(420.0, parsed["strike"])

    def test_implied_volatility_round_trip(self) -> None:
        price = self.audit.black_scholes_price_delta_gamma(
            spot=100.0,
            strike=100.0,
            years_to_expiry=30 / 365,
            rate=0.05,
            dividend_yield=0.0,
            volatility=0.2,
            right="call",
        )["price"]

        iv = self.audit.implied_volatility_bisection(
            target_price=price,
            spot=100.0,
            strike=100.0,
            years_to_expiry=30 / 365,
            rate=0.05,
            dividend_yield=0.0,
            right="call",
        )

        self.assertIsNotNone(iv)
        self.assertAlmostEqual(0.2, iv, places=4)

    @state_audit(("HIGANBANA_DATA_ROOT", PROJECT_ROOT / "data"))
    def test_current_project_audit_generates_feasibility_report(self) -> None:
        result = self.audit.audit_greeks_oi_feasibility()

        self.assertEqual("greeks_oi_feasibility_audit", result["record_type"])
        self.assertEqual("pass", result["quote_field_audit"]["status"])
        self.assertEqual("pass", result["underlying_join_audit"]["status"])
        self.assertEqual("pass", result["opra_oi_mapping_audit"]["status"])
        self.assertEqual("pass_with_caveats", result["greek_calculation_probe"]["status"])
        self.assertEqual(
            "blocked_until_normalized_quote_enrichment_and_gamma_aggregation_policy",
            result["strategy_use_status"],
        )

    @state_audit(("HIGANBANA_DATA_ROOT", PROJECT_ROOT / "data"))
    def test_write_reports_creates_json_and_markdown(self) -> None:
        result = self.audit.audit_greeks_oi_feasibility()
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "greeks_oi_feasibility_audit.json"
            md_path = Path(tmp) / "greeks_oi_feasibility_audit.md"

            self.audit.write_reports(result, json_path, md_path)

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            report = md_path.read_text(encoding="utf-8")
            self.assertEqual("greeks_oi_feasibility_audit", payload["record_type"])
            self.assertIn("# Greeks/OI Feasibility Audit", report)
            self.assertIn("OPRA OI Mapping", report)
