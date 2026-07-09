from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "probe_ibkr_spy_bars_readiness.py"


def load_probe():
    spec = importlib.util.spec_from_file_location("probe_ibkr_spy_bars_readiness", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load IBKR readiness probe")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IbkrSpyBarsReadinessProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.probe = load_probe()

    def test_blocked_when_no_local_port_and_no_python_client(self) -> None:
        result = self.probe.build_readiness_result(
            port_checks=[{"port": 7497, "status": "closed", "error": "ConnectionRefusedError"}],
            package_checks=[{"package": "ib_insync", "available": False}, {"package": "ibapi", "available": False}],
            generated_at_utc="2026-07-04T00:00:00+00:00",
        )

        self.assertEqual("blocked_local_ibkr_unavailable", result["status"])
        self.assertIn("no_local_ibkr_api_port_listening", result["blockers"])
        self.assertIn("missing_ibkr_python_client", result["blockers"])
        self.assertFalse(result["guardrails"]["historical_data_requested"])
        self.assertFalse(result["guardrails"]["orders_transmitted"])
        self.assertFalse(result["guardrails"]["paid_data_used"])
        self.assertFalse(result["paper_trading_allowed"])
        self.assertIn("stop for clear user direction", result["next_safe_action"])

    def test_ready_only_when_port_and_python_client_are_available(self) -> None:
        result = self.probe.build_readiness_result(
            port_checks=[{"port": 7497, "status": "open"}],
            package_checks=[{"package": "ib_insync", "available": True}, {"package": "ibapi", "available": False}],
            generated_at_utc="2026-07-04T00:00:00+00:00",
        )

        self.assertEqual("ready_for_manual_data_probe", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual([7497], result["open_ports"])
        self.assertEqual(["ib_insync"], result["available_packages"])
        self.assertIn("separate explicit IBKR historical-bars data probe", result["next_safe_action"])

    def test_main_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_output = Path(tmp) / "ibkr_readiness.json"
            report_output = Path(tmp) / "ibkr_readiness.md"

            returncode = self.probe.main(
                [
                    "--ports",
                    "1",
                    "--json-output",
                    str(json_output),
                    "--report-output",
                    str(report_output),
                ]
            )

            self.assertEqual(0, returncode)
            result = json.loads(json_output.read_text(encoding="utf-8"))
            report = report_output.read_text(encoding="utf-8")
            self.assertIn(result["status"], {"blocked_local_ibkr_unavailable", "ready_for_manual_data_probe"})
            self.assertIn("IBKR SPY Bars Readiness Probe", report)
            self.assertIn("Orders transmitted", report)
            self.assertFalse(result["guardrails"]["orders_transmitted"])


if __name__ == "__main__":
    unittest.main()
