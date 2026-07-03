from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "capture_vix_vxv_cboe.py"


def load_capture_module():
    spec = importlib.util.spec_from_file_location("capture_vix_vxv_cboe", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load VIX/VXV capture module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaptureVixVxvCboeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capture = load_capture_module()

    def test_build_capture_plan_has_vix_and_vix3m_requests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = self.capture.build_capture_plan(date(2026, 6, 30), output_root=Path(tmp))

        self.assertEqual("dry_run", plan["mode"])
        self.assertEqual("2026-06-30", plan["as_of_date"])
        self.assertEqual(2, len(plan["requests"]))
        self.assertEqual({"VIX", "VIX3M"}, {request["series"] for request in plan["requests"]})
        for request in plan["requests"]:
            self.assertIn("cdn.cboe.com", request["source_url"])

    def test_capture_execute_writes_manifest_with_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_plan = Path(tmp) / "source_plan.json"
            source_plan.write_text(
                json.dumps(
                    {
                        "primary_source_id": "cboe_volatility_index_history",
                        "sources": [
                            {
                                "source_id": "cboe_volatility_index_history",
                                "provider": "Cboe",
                                "vix_url": "https://example.test/vix.csv",
                                "vxv_url": "https://example.test/vix3m.csv",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            self.capture._fetch_bytes = lambda url: f"DATE,OPEN,HIGH,LOW,CLOSE\n01/03/2024,{url[-7:]},1,1,1\n".encode("utf-8")

            result = self.capture.capture_vix_vxv(date(2026, 6, 30), source_plan_path=source_plan, output_root=Path(tmp), execute=True)

            manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
            self.assertEqual(2, result["captured_count"])
            self.assertEqual(2, len(manifest["captured"]))
            self.assertTrue(all(item["sha256"] for item in manifest["captured"]))


if __name__ == "__main__":
    unittest.main()
