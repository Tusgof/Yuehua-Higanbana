from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "scripts" / "operational_bridge_m7.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location("operational_bridge_m7", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M7 bridge")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class M7OperationalBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def test_example_config_contains_no_live_transmit(self) -> None:
        config = self.bridge.load_json(PROJECT_ROOT / "config" / "ibkr.example.json")
        self.assertEqual("paper", config["mode"])
        self.assertFalse(config["transmit_enabled"])
        self.assertNotIn("password", str(config).lower())
        self.assertNotIn("token", str(config).lower())

    def test_ticket_builder_rejects_entry_market_order_and_transmit(self) -> None:
        with self.assertRaises(self.bridge.OperationalBridgeError):
            self.bridge.build_order_ticket(intent(), capped_put_ratio_legs(), 0.10, order_type="MARKET")
        with self.assertRaises(self.bridge.OperationalBridgeError):
            self.bridge.build_order_ticket(intent(), capped_put_ratio_legs(), 0.10, transmit=True)

    def test_ticket_builder_requires_protective_wing(self) -> None:
        unsafe_legs = capped_put_ratio_legs()[:2]
        with self.assertRaises(self.bridge.OperationalBridgeError):
            self.bridge.build_order_ticket(intent(), unsafe_legs, 0.10)

    def test_pre_transmit_validation_blocks_by_default(self) -> None:
        ticket = self.bridge.build_order_ticket(intent(), capped_put_ratio_legs(), 0.10)
        config = self.bridge.load_json(PROJECT_ROOT / "config" / "ibkr.example.json")
        kill_switch = self.bridge.load_json(PROJECT_ROOT / "config" / "kill_switch.json")
        errors = self.bridge.pre_transmit_validate(
            ticket,
            config,
            {"open_positions": 0, "estimated_max_loss": 10.0},
            kill_switch,
        )
        self.assertTrue(any("kill switch active" in error for error in errors))
        self.assertTrue(any("transmit_enabled is false" in error for error in errors))

    def test_paper_bridge_email_close_workflow_and_launch_gate(self) -> None:
        ticket = self.bridge.build_order_ticket(intent(), capped_put_ratio_legs(), 0.10)
        dry_run = self.bridge.paper_trade_dry_run(ticket)
        self.assertFalse(dry_run["would_submit"])
        self.assertEqual(3, dry_run["close_plan_steps"])
        self.assertEqual("backup_forced_close_must_be_active", ticket["close_plan"][-1]["action"])

        email = self.bridge.email_alert_payload("daily_summary", "No-Go", "Fixture body", "user@example.com")
        self.assertTrue(email["dry_run"])
        self.assertEqual("user@example.com", email["to"])

        checklist = self.bridge.load_json(PROJECT_ROOT / "config" / "real_money_launch_checklist.example.json")
        status = self.bridge.launch_checklist_status(checklist)
        self.assertEqual("blocked", status["status"])
        self.assertIn("research_acceptance_passed", status["missing"])


def intent() -> dict:
    return {
        "intent_id": "intent-001",
        "strategy_id": "subsystem_b_put_ratio_capped",
        "entry_time_et": "2024-01-03T10:00:00-05:00",
    }


def capped_put_ratio_legs() -> list[dict]:
    return [
        {"leg_id": "near", "underlying": "SPY", "expiration_date": "2024-01-03", "right": "put", "strike": 470, "side": "buy", "quantity": 1},
        {"leg_id": "short", "underlying": "SPY", "expiration_date": "2024-01-03", "right": "put", "strike": 466, "side": "sell", "quantity": 2},
        {"leg_id": "wing", "underlying": "SPY", "expiration_date": "2024-01-03", "right": "put", "strike": 464, "side": "buy", "quantity": 1},
    ]


if __name__ == "__main__":
    unittest.main()
