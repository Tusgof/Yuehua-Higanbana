from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_h_g1_policy_manifest_decision.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_h_g1_policy_manifest_decision", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 policy/manifest decision module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_G1PolicyManifestDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_policy_revision_alone_is_rejected_when_any_bucket_is_below_notional_floor(self) -> None:
        diagnostic = {
            "summary": {"all_failures_are_black_scholes_bracket_blocks": True},
            "failed_buckets": [
                {"date": "2023-07-12", "bucket": "otm_put", "computed_rate": 0.54, "computed_oi_notional_share": 0.66},
                {"date": "2024-01-03", "bucket": "otm_put", "computed_rate": 0.35, "computed_oi_notional_share": 0.91},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "bucket_failure.json"
            output_json = root / "decision.json"
            output_report = root / "decision.md"
            input_path.write_text(json.dumps(diagnostic), encoding="utf-8")

            result = self.module.run_decision(input_path)
            self.module.write_outputs(result, output_json, output_report)
            written = json.loads(output_json.read_text(encoding="utf-8"))
            report = output_report.read_text(encoding="utf-8")

        self.assertEqual("policy_revision_alone_rejected_manifest_v3_required", result["decision"]["status"])
        self.assertEqual(["2023-07-12 otm_put"], result["findings"]["below_notional_floor_buckets"])
        self.assertEqual(1, result["findings"]["high_notional_row_rate_failure_count"])
        self.assertFalse(result["paid_data_used"])
        self.assertFalse(result["network_used"])
        self.assertEqual(result["decision"]["status"], written["decision"]["status"])
        self.assertIn("H-G1 Policy / Manifest Decision", report)


if __name__ == "__main__":
    unittest.main()
