from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_h_g1_manifest_v3_bucket_failure_diagnostic.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_h_g1_manifest_v3_bucket_failure_diagnostic", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 manifest v3 bucket failure diagnostic module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_G1ManifestV3BucketFailureDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_bucket_from_blocker_parses_policy_bucket(self) -> None:
        self.assertEqual("otm_call", self.module._bucket_from_blocker("otm_call_computed_rate_below_60pct"))

    def test_run_diagnostic_identifies_opposite_right_bucket_failure(self) -> None:
        rows = [
            _row("2024-05-21", "call", 101.0, 100.0, 100, "computed_with_caveats", bid=0.09, ask=0.11),
            _row("2024-05-21", "call", 102.0, 100.0, 100, "computed_with_caveats", bid=0.04, ask=0.06),
            _row("2024-05-21", "put", 101.0, 100.0, 5, "blocked_mid_outside_black_scholes_bracket", bid=1.0, ask=1.2),
            _row("2024-05-21", "put", 102.0, 100.0, 5, "blocked_mid_outside_black_scholes_bracket", bid=2.0, ask=2.2),
            _row("2024-05-21", "put", 103.0, 100.0, 5, "blocked_mid_outside_black_scholes_bracket", bid=3.0, ask=3.2),
        ]
        summary = {
            "validation_gates": {
                "coverage": {
                    "bucket_weighted_coverage": {
                        "required_bucket_failures": {
                            "2024-05-21": ["otm_call_computed_rate_below_60pct"],
                        }
                    }
                }
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "rows.jsonl"
            summary_path = root / "summary.json"
            output_json = root / "diagnostic.json"
            output_report = root / "diagnostic.md"
            input_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            summary_path.write_text(json.dumps(summary), encoding="utf-8")

            result = self.module.run_diagnostic(input_path, summary_path)
            self.module.write_outputs(result, output_json, output_report)
            written = json.loads(output_json.read_text(encoding="utf-8"))
            report_text = output_report.read_text(encoding="utf-8")

        item = result["failed_buckets"][0]
        self.assertFalse(result["paid_data_used"])
        self.assertFalse(result["network_used"])
        self.assertEqual("diagnostic_complete_h_g1_still_blocked", result["decision"]["status"])
        self.assertEqual("otm_call", item["bucket"])
        self.assertEqual({"opposite_right_for_bucket": 3}, item["blocked_side_alignment_counts"])
        self.assertEqual(1.0, result["summary"]["opposite_right_blocked_row_share"])
        self.assertIn("bucket-definition/policy problem", result["summary"]["primary_diagnosis"])
        self.assertEqual(result["decision"]["status"], written["decision"]["status"])
        self.assertIn("H-G1 Manifest V3 Bucket Failure Diagnostic", report_text)


def _row(
    date: str,
    right: str,
    strike: float,
    underlying: float,
    open_interest: int,
    status: str,
    bid: float,
    ask: float,
) -> dict[str, object]:
    row: dict[str, object] = {
        "quote_timestamp_et": f"{date}T09:35:00-04:00",
        "right": right,
        "strike": strike,
        "underlying_price": underlying,
        "bid": bid,
        "ask": ask,
        "mid": (bid + ask) / 2.0,
        "open_interest": open_interest,
        "greeks_status": status,
    }
    if status == "computed_with_caveats":
        row["gamma"] = 0.01
    return row


if __name__ == "__main__":
    unittest.main()
