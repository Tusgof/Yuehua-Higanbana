from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "download_databento_data.py"


def load_downloader():
    spec = importlib.util.spec_from_file_location("download_databento_data", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Databento downloader")
    module = importlib.util.module_from_spec(spec)
    sys.modules["download_databento_data"] = module
    spec.loader.exec_module(module)
    return module


class DatabentoDownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.downloader = load_downloader()

    def test_default_api_key_env_matches_project_config(self) -> None:
        self.assertEqual("DATABENTO_API_KEY", self.downloader.DEFAULT_API_KEY_ENV)

    def test_default_databento_key_env_falls_back_to_project_alias(self) -> None:
        previous_default = os.environ.get("DATABENTO_API_KEY")
        previous_alias = os.environ.get("DATABENTO_SPY0DTE_API")
        os.environ.pop("DATABENTO_API_KEY", None)
        os.environ["DATABENTO_SPY0DTE_API"] = "test-key"
        try:
            self.assertEqual("test-key", self.downloader._databento_api_key_from_env())
        finally:
            if previous_default is not None:
                os.environ["DATABENTO_API_KEY"] = previous_default
            else:
                os.environ.pop("DATABENTO_API_KEY", None)
            if previous_alias is not None:
                os.environ["DATABENTO_SPY0DTE_API"] = previous_alias
            else:
                os.environ.pop("DATABENTO_SPY0DTE_API", None)

    def test_build_download_plan_from_passed_cost_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "cost.json"
            output_root = Path(tmp) / "raw"
            report_path.write_text(json.dumps(_cost_report("pass")), encoding="utf-8")
            plan = self.downloader.build_download_plan(report_path, output_root)
            self.assertEqual("download_plan", plan["mode"])
            self.assertEqual("one_month_pilot", plan["scenario"])
            self.assertEqual(1, plan["request_count"])
            self.assertTrue(plan["items"][0]["output_path"].endswith(".dbn.zst"))

    def test_download_plan_rejects_review_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "cost.json"
            report_path.write_text(json.dumps(_cost_report("review")), encoding="utf-8")
            with self.assertRaises(ValueError):
                self.downloader.build_download_plan(report_path, Path(tmp) / "raw")

    def test_download_plan_allows_review_report_with_explicit_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "cost.json"
            report_path.write_text(json.dumps(_cost_report("review")), encoding="utf-8")
            plan = self.downloader.build_download_plan(
                report_path,
                Path(tmp) / "raw",
                allow_review_decision=True,
                approval_note="user approved reviewed Feb intraday download",
            )
            self.assertEqual("review", plan["decision"]["status"])
            self.assertEqual("user approved reviewed Feb intraday download", plan["approval_note"])

    def test_download_plan_rejects_too_many_requests(self) -> None:
        report = _cost_report("pass")
        report["requests"].append(dict(report["requests"][0], window="2024-01-02_entry_b_1000"))
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "cost.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaises(ValueError):
                self.downloader.build_download_plan(report_path, Path(tmp) / "raw", max_download_requests=1)

    def test_execute_download_plan_reuses_existing_local_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "raw" / "one_month_pilot" / "2024-01-02_entry_a_0935.dbn.zst"
            output_path.parent.mkdir(parents=True)
            output_path.write_bytes(b"cached-data")
            plan = {
                "mode": "download_plan",
                "items": [
                    {
                        "dataset": "OPRA.PILLAR",
                        "symbols": ["SPY.OPT"],
                        "schema": "cbbo-1m",
                        "stype_in": "parent",
                        "start": "2024-01-02T14:30:00+00:00",
                        "end": "2024-01-02T14:40:00+00:00",
                        "window": "2024-01-02_entry_a_0935",
                        "output_path": str(output_path),
                    }
                ],
            }
            previous_key = os.environ.get("TEST_DATABENTO_KEY")
            previous_module = sys.modules.get("databento")
            os.environ["TEST_DATABENTO_KEY"] = "test-key"
            sys.modules["databento"] = _fake_databento_module()
            try:
                result = self.downloader.execute_download_plan(plan, "TEST_DATABENTO_KEY")
            finally:
                if previous_key is None:
                    os.environ.pop("TEST_DATABENTO_KEY", None)
                else:
                    os.environ["TEST_DATABENTO_KEY"] = previous_key
                if previous_module is None:
                    sys.modules.pop("databento", None)
                else:
                    sys.modules["databento"] = previous_module
            self.assertEqual("download_complete", result["mode"])
            self.assertEqual("cache", result["downloaded"][0]["source"])
            self.assertEqual(len(b"cached-data"), result["downloaded"][0]["bytes"])

    def test_execute_download_plan_redownloads_zero_byte_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "raw" / "one_month_pilot" / "2024-01-02_entry_a_0935.dbn.zst"
            output_path.parent.mkdir(parents=True)
            output_path.write_bytes(b"")
            plan = {
                "mode": "download_plan",
                "items": [
                    {
                        "dataset": "OPRA.PILLAR",
                        "symbols": ["SPY.OPT"],
                        "schema": "cbbo-1m",
                        "stype_in": "parent",
                        "start": "2024-01-02T14:30:00+00:00",
                        "end": "2024-01-02T14:40:00+00:00",
                        "window": "2024-01-02_entry_a_0935",
                        "output_path": str(output_path),
                    }
                ],
            }
            previous_key = os.environ.get("TEST_DATABENTO_KEY")
            previous_module = sys.modules.get("databento")
            os.environ["TEST_DATABENTO_KEY"] = "test-key"
            sys.modules["databento"] = _fake_databento_module(payload=b"redownloaded")
            try:
                result = self.downloader.execute_download_plan(plan, "TEST_DATABENTO_KEY")
            finally:
                if previous_key is None:
                    os.environ.pop("TEST_DATABENTO_KEY", None)
                else:
                    os.environ["TEST_DATABENTO_KEY"] = previous_key
                if previous_module is None:
                    sys.modules.pop("databento", None)
                else:
                    sys.modules["databento"] = previous_module
            self.assertEqual("downloaded", result["downloaded"][0]["source"])
            self.assertEqual(len(b"redownloaded"), result["downloaded"][0]["bytes"])
            self.assertFalse(output_path.with_name(f"{output_path.name}.download").exists())

    def test_execute_download_plan_retries_stale_temp_file_collision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "raw" / "one_month_pilot" / "2024-01-02_entry_a_0935.dbn.zst"
            output_path.parent.mkdir(parents=True)
            plan = {
                "mode": "download_plan",
                "items": [
                    {
                        "dataset": "OPRA.PILLAR",
                        "symbols": ["SPY.OPT"],
                        "schema": "cbbo-1m",
                        "stype_in": "parent",
                        "start": "2024-01-02T14:30:00+00:00",
                        "end": "2024-01-02T14:40:00+00:00",
                        "window": "2024-01-02_entry_a_0935",
                        "output_path": str(output_path),
                    }
                ],
            }
            previous_key = os.environ.get("TEST_DATABENTO_KEY")
            previous_module = sys.modules.get("databento")
            os.environ["TEST_DATABENTO_KEY"] = "test-key"
            sys.modules["databento"] = _fake_databento_module(payload=b"retry-ok", fail_once=True)
            try:
                result = self.downloader.execute_download_plan(plan, "TEST_DATABENTO_KEY")
            finally:
                if previous_key is None:
                    os.environ.pop("TEST_DATABENTO_KEY", None)
                else:
                    os.environ["TEST_DATABENTO_KEY"] = previous_key
                if previous_module is None:
                    sys.modules.pop("databento", None)
                else:
                    sys.modules["databento"] = previous_module
            self.assertEqual("downloaded", result["downloaded"][0]["source"])
            self.assertEqual(len(b"retry-ok"), result["downloaded"][0]["bytes"])


def _cost_report(status: str) -> dict:
    return {
        "mode": "live",
        "decision": {"status": status, "reason": "test"},
        "errors": [],
        "total_estimated_cost_usd": 1.0,
        "summary": {"scenarios": {"one_month_pilot": {"request_count": 1}}},
        "requests": [
            {
                "dataset": "OPRA.PILLAR",
                "symbols": ["SPY.OPT"],
                "schema": "cbbo-1m",
                "stype_in": "parent",
                "start": "2024-01-02T14:30:00+00:00",
                "end": "2024-01-02T14:40:00+00:00",
                "window": "2024-01-02_entry_a_0935",
                "estimated_cost_usd": 0.02,
            }
        ],
    }


def _fake_databento_module(payload: bytes | None = None, fail_once: bool = False):
    class FakeTimeSeries:
        def __init__(self):
            self.failed = False

        def get_range(self, **kwargs):
            if payload is None:
                raise AssertionError("Databento API should not be called when local cache exists")
            if fail_once and not self.failed:
                self.failed = True
                Path(kwargs["path"]).write_bytes(b"stale-temp")
                raise FileExistsError(kwargs["path"])
            Path(kwargs["path"]).write_bytes(payload)

    class FakeHistorical:
        def __init__(self, api_key):
            self.timeseries = FakeTimeSeries()

    return types.SimpleNamespace(Historical=FakeHistorical)


if __name__ == "__main__":
    unittest.main()
