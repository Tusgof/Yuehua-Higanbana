from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = PROJECT_ROOT / "scripts" / "openrouter_deepseek_adapter.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OpenRouterDeepSeekAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter = load_module(ADAPTER_PATH, "openrouter_deepseek_adapter")

    def test_payload_targets_deepseek_v4_flash_with_reasoning(self) -> None:
        prompt_input = self.adapter.build_prompt_input([], {"vix_close": 18.0, "vxv_close": 19.0})
        payload = self.adapter.build_chat_payload(prompt_input, "C")
        self.assertEqual("deepseek/deepseek-v4-flash", payload["model"])
        self.assertEqual({"effort": "high", "exclude": True}, payload["reasoning"])
        self.assertEqual({"type": "json_object"}, payload["response_format"])
        self.assertIn("volatility_condition", payload["messages"][0]["content"])

    def test_dry_run_prompt_matrix_outputs_valid_llm_assessments(self) -> None:
        assessments = self.adapter.run_dry_prompt_matrix(
            news_items=[{"headline": "Quiet market before open"}],
            vix_vxv={"vix_close": 18.0, "vxv_close": 19.0},
            created_at_et="2024-01-03T09:20:00-05:00",
        )
        self.assertEqual(["exp07-prompt-a-tail-risk-v12", "exp07-prompt-b-balanced-score-v12", "exp07-prompt-c-structured-assessment-v12"], [row["prompt_version"] for row in assessments])
        for assessment in assessments:
            self.assertEqual("OpenRouter/DeepSeek", assessment["provider"])
            self.assertEqual("allow", assessment["decision"])
            self.assertEqual([], self.adapter.validate_assessment(assessment))

    def test_parser_handles_explicit_decisions_and_risk_score(self) -> None:
        self.assertEqual("allow", self.adapter.parse_decision('{"decision":"go","risk_score":6}'))
        self.assertEqual("block", self.adapter.parse_decision('{"decision":"No-Go"}'))
        self.assertEqual("block", self.adapter.parse_decision('{"risk_score_0_to_10":7}'))
        self.assertEqual("allow", self.adapter.parse_decision('{"risk_score_0_to_10":4}'))
        self.assertEqual("unknown", self.adapter.parse_decision('{"decision":"neutral","risk_score":50}'))
        self.assertEqual("unknown", self.adapter.parse_decision("not-json"))

    def test_api_key_status_never_returns_secret_value(self) -> None:
        os.environ["HIGANBANA_OPENROUTER_API"] = "secret-value-for-test"
        try:
            status = self.adapter.api_key_status()
        finally:
            del os.environ["HIGANBANA_OPENROUTER_API"]
        self.assertEqual({"api_key_env": "HIGANBANA_OPENROUTER_API", "configured": True}, status)
        self.assertNotIn("secret-value-for-test", str(status))

    def test_api_key_status_uses_user_env_without_returning_secret(self) -> None:
        original_get_user_env = self.adapter._get_user_env
        self.adapter._get_user_env = lambda name: "user-secret-for-test" if name == "HIGANBANA_OPENROUTER_API" else None
        try:
            status = self.adapter.api_key_status()
        finally:
            self.adapter._get_user_env = original_get_user_env
        self.assertEqual({"api_key_env": "HIGANBANA_OPENROUTER_API", "configured": True}, status)
        self.assertNotIn("user-secret-for-test", str(status))

    def test_live_prompt_variant_uses_injected_transport_and_validates(self) -> None:
        prompt_input = self.adapter.build_prompt_input([], {"vix_close": 18.0, "vxv_close": 19.0})
        seen = {}

        def fake_transport(payload, api_key_env):
            seen["payload"] = payload
            seen["api_key_env"] = api_key_env
            return {
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15, "cost": 0.0012},
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({
                                "decision": "allow",
                                "risk_score": 3,
                                "reasons": ["fixture transport"],
                            })
                        }
                    }
                ]
            }

        assessment = self.adapter.live_prompt_variant(
            prompt_input,
            "B",
            "2024-01-03T09:20:00-05:00",
            transport=fake_transport,
        )
        self.assertEqual("HIGANBANA_OPENROUTER_API", seen["api_key_env"])
        self.assertEqual("deepseek/deepseek-v4-flash", seen["payload"]["model"])
        self.assertEqual("allow", assessment["decision"])
        self.assertEqual({"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}, assessment["_usage"])
        self.assertEqual(0.0012, assessment["_cost_usd"])
        self.assertEqual([], self.adapter.validate_assessment(assessment))

    def test_extract_response_usage_cost_accepts_known_cost_shapes(self) -> None:
        metadata = self.adapter.extract_response_usage_cost(
            {
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 20,
                    "total_tokens": 120,
                    "cost": "0.0045",
                }
            }
        )

        self.assertEqual({"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}, metadata["usage"])
        self.assertEqual(0.0045, metadata["cost_usd"])

    def test_build_headers_requires_env_and_keeps_secret_only_in_header(self) -> None:
        with self.assertRaises(self.adapter.OpenRouterAdapterError):
            self.adapter.build_headers("MISSING_HIGANBANA_TEST_ENV")

        os.environ["HIGANBANA_OPENROUTER_API"] = "secret-value-for-test"
        try:
            headers = self.adapter.build_headers()
        finally:
            del os.environ["HIGANBANA_OPENROUTER_API"]
        self.assertEqual("Bearer secret-value-for-test", headers["Authorization"])
        self.assertEqual("SPY 0DTE - Higanbana", headers["X-Title"])

    def test_build_headers_falls_back_to_user_env_and_prefers_process_env(self) -> None:
        original_get_user_env = self.adapter._get_user_env
        self.adapter._get_user_env = lambda name: "user-secret-for-test" if name == "HIGANBANA_OPENROUTER_API" else None
        try:
            headers = self.adapter.build_headers()
            self.assertEqual("Bearer user-secret-for-test", headers["Authorization"])
            os.environ["HIGANBANA_OPENROUTER_API"] = "process-secret-for-test"
            headers = self.adapter.build_headers()
            self.assertEqual("Bearer process-secret-for-test", headers["Authorization"])
        finally:
            self.adapter._get_user_env = original_get_user_env
            os.environ.pop("HIGANBANA_OPENROUTER_API", None)

    def test_openrouter_transport_wraps_timeout_for_runner_retry(self) -> None:
        original_urlopen = self.adapter.urllib.request.urlopen
        original_get_user_env = self.adapter._get_user_env
        self.adapter._get_user_env = lambda name: "user-secret-for-test" if name == "HIGANBANA_OPENROUTER_API" else None
        self.adapter.urllib.request.urlopen = lambda request, timeout: (_ for _ in ()).throw(TimeoutError("read timeout"))
        try:
            with self.assertRaisesRegex(self.adapter.OpenRouterAdapterError, "TimeoutError"):
                self.adapter._openrouter_transport({"messages": []}, "HIGANBANA_OPENROUTER_API")
        finally:
            self.adapter.urllib.request.urlopen = original_urlopen
            self.adapter._get_user_env = original_get_user_env

    def test_append_assessment_jsonl_writes_canonical_record_only(self) -> None:
        prompt_input = self.adapter.build_prompt_input([], {"vix_close": 18.0, "vxv_close": 19.0})
        assessment = self.adapter.dry_run_prompt_variant(
            prompt_input,
            "A",
            "2024-01-03T09:20:00-05:00",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "llm_assessment.jsonl"
            self.adapter.append_assessment_jsonl(path, assessment)
            record = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual("llm_assessment", record["record_type"])
        self.assertNotIn("_request_model", record)
        self.assertNotIn("_reasoning_effort", record)


if __name__ == "__main__":
    unittest.main()
