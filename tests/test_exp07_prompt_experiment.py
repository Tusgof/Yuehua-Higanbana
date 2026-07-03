from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = PROJECT_ROOT / "scripts" / "run_exp07_prompt_experiment.py"
EVENT_POLICY_PATH = PROJECT_ROOT / "scripts" / "exp07_event_policy.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Exp07PromptExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_module(RUNNER_PATH, "run_exp07_prompt_experiment")
        cls.event_policy = load_module(EVENT_POLICY_PATH, "exp07_event_policy")

    def prompt_input(self, case):
        return self.runner.build_case_prompt_input(case)

    def test_policy_cases_load_from_fixture_without_preclassified_results(self) -> None:
        cases = self.runner.load_policy_cases()
        self.assertEqual(43, len(cases))
        self.assertEqual("quiet_vix18_normal_term_structure", cases[0]["case_id"])
        self.assertEqual("circuit_breaker_risk_vix24", cases[-1]["case_id"])
        self.assertTrue(all("prompt_input" in case for case in cases))
        self.assertTrue(all("preclassified_event_policy" not in case["prompt_input"] for case in cases))

    def test_archive_prompt_inputs_writes_hashed_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inputs.json"
            archived = self.runner.archive_prompt_inputs(path)
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(43, len(archived))
        self.assertEqual(archived, loaded)
        self.assertEqual(
            [
                "allow",
                "allow",
                "block",
                "block",
                "unknown",
                "unknown",
                "unknown",
                "unknown",
                "unknown",
                "unknown",
                "unknown",
                "allow",
                "allow",
                "block",
                "unknown",
                "allow",
                "allow",
                "unknown",
                "allow",
                "allow",
                "block",
                "allow",
                "allow",
                "allow",
                "allow",
                "unknown",
                "block",
                "block",
                "unknown",
                "allow",
                "allow",
                "allow",
                "unknown",
                "allow",
                "block",
                "unknown",
                "unknown",
                "unknown",
                "allow",
                "allow",
                "allow",
                "block",
                "block",
            ],
            [row["expected_decision"] for row in archived],
        )
        self.assertEqual("block", archived[-1]["prompt_input"]["preclassified_event_policy"]["decision"])
        self.assertTrue(all(len(row["input_hash"]) == 64 for row in archived))

    def test_dry_run_experiment_logs_all_cases_and_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "inputs.json"
            jsonl_path = Path(tmp) / "assessments.jsonl"
            archived = self.runner.archive_prompt_inputs(archive_path)
            results = self.runner.run_prompt_experiment(
                archived,
                "2024-01-03T09:20:00-05:00",
                assessment_jsonl_path=jsonl_path,
            )
            lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(129, len(results))
        self.assertEqual(129, len(lines))
        self.assertTrue(all(row["guarded_decision"] in self.runner.VALID_DECISIONS for row in results))
        self.assertTrue(all(json.loads(line)["record_type"] == "llm_assessment" for line in lines))

    def test_dry_run_experiment_can_limit_cases_and_prompt_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "inputs.json"
            jsonl_path = Path(tmp) / "assessments.jsonl"
            archived = self.runner.archive_prompt_inputs(archive_path)
            filtered = self.runner.filter_archived_cases(archived, ["quiet_vix18_normal_term_structure"])
            results = self.runner.run_prompt_experiment(
                filtered,
                "2024-01-03T09:20:00-05:00",
                assessment_jsonl_path=jsonl_path,
                prompt_variants=["A"],
            )
            lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()

        self.assertEqual(1, len(filtered))
        self.assertEqual(1, len(results))
        self.assertEqual(1, len(lines))
        self.assertEqual("quiet_vix18_normal_term_structure", results[0]["case_id"])
        self.assertEqual("A", results[0]["prompt_variant"])

    def test_summary_reports_stability_and_expected_mismatches(self) -> None:
        archived = self.runner.archive_prompt_inputs(Path(tempfile.mkdtemp()) / "inputs.json")
        results = self.runner.run_prompt_experiment(archived, "2024-01-03T09:20:00-05:00")
        summary = self.runner.summarize_results(results, live=False)
        self.assertEqual("dry_run_no_network", summary["mode"])
        self.assertEqual(43, summary["case_count"])
        self.assertEqual(129, summary["assessment_count"])
        self.assertIsNone(summary["openrouter_actual_cost_usd"])
        self.assertEqual(0, summary["openrouter_costed_assessment_count"])
        self.assertEqual(1.0, summary["parse_valid_rate"])
        self.assertEqual(18, summary["mismatch_count"])
        self.assertEqual(45, summary["unknown_policy_violation_count"])
        self.assertEqual(45, len(summary["unknown_policy_violations"]))
        self.assertEqual(43, summary["guarded_stable_case_count"])
        self.assertEqual(0, summary["guarded_mismatch_count"])
        self.assertEqual(0, summary["guarded_unknown_policy_violation_count"])

    def test_preclassifier_detects_scheduled_systemic_and_high_vol_events(self) -> None:
        cpi_case = self.runner.ARCHIVED_PROMPT_CASES[6]
        cpi_input = self.prompt_input(cpi_case)
        systemic_case = self.runner.ARCHIVED_PROMPT_CASES[2]
        systemic_input = self.prompt_input(systemic_case)
        high_vol_case = self.runner.ARCHIVED_PROMPT_CASES[10]
        high_vol_input = self.prompt_input(high_vol_case)
        self.assertEqual("unknown", self.runner.preclassify_event_policy(cpi_input)["decision"])
        self.assertEqual("block", self.runner.preclassify_event_policy(systemic_input)["decision"])
        self.assertEqual("unknown", self.runner.preclassify_event_policy(high_vol_input)["decision"])
        self.assertEqual("unknown", self.event_policy.preclassify_event_policy(cpi_input)["decision"])

    def test_preclassifier_allows_non_actionable_scheduled_references(self) -> None:
        next_week_case = self.runner.ARCHIVED_PROMPT_CASES[11]
        next_week_input = self.prompt_input(next_week_case)
        yesterday_case = self.runner.ARCHIVED_PROMPT_CASES[12]
        yesterday_input = self.prompt_input(yesterday_case)
        self.assertEqual("allow", self.runner.preclassify_event_policy(next_week_input)["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(yesterday_input)["decision"])

    def test_preclassifier_handles_v9_context_edges(self) -> None:
        after_close_case = self.runner.ARCHIVED_PROMPT_CASES[15]
        tomorrow_case = self.runner.ARCHIVED_PROMPT_CASES[16]
        mixed_case = self.runner.ARCHIVED_PROMPT_CASES[17]
        contained_stress_case = self.runner.ARCHIVED_PROMPT_CASES[18]
        panic_bid_case = self.runner.ARCHIVED_PROMPT_CASES[19]
        market_panic_case = self.runner.ARCHIVED_PROMPT_CASES[20]

        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(after_close_case))["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(tomorrow_case))["decision"])
        self.assertEqual("unknown", self.runner.preclassify_event_policy(self.prompt_input(mixed_case))["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(contained_stress_case))["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(panic_bid_case))["decision"])
        self.assertEqual("block", self.runner.preclassify_event_policy(self.prompt_input(market_panic_case))["decision"])

    def test_preclassifier_handles_v10_policy_fixture_edges(self) -> None:
        fomc_next_week_case = self.runner.ARCHIVED_PROMPT_CASES[21]
        treasury_yesterday_case = self.runner.ARCHIVED_PROMPT_CASES[22]
        emergency_drill_case = self.runner.ARCHIVED_PROMPT_CASES[23]
        single_stock_halt_case = self.runner.ARCHIVED_PROMPT_CASES[24]
        bank_stress_fed_case = self.runner.ARCHIVED_PROMPT_CASES[25]
        banking_systemic_case = self.runner.ARCHIVED_PROMPT_CASES[26]
        futures_halt_case = self.runner.ARCHIVED_PROMPT_CASES[27]

        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(fomc_next_week_case))["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(treasury_yesterday_case))["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(emergency_drill_case))["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(single_stock_halt_case))["decision"])
        self.assertEqual("unknown", self.runner.preclassify_event_policy(self.prompt_input(bank_stress_fed_case))["decision"])
        self.assertEqual("block", self.runner.preclassify_event_policy(self.prompt_input(banking_systemic_case))["decision"])
        self.assertEqual("block", self.runner.preclassify_event_policy(self.prompt_input(futures_halt_case))["decision"])

    def test_preclassifier_handles_v11_policy_fixture_edges(self) -> None:
        cpi_today_future_earnings_case = self.runner.ARCHIVED_PROMPT_CASES[28]
        powell_tomorrow_case = self.runner.ARCHIVED_PROMPT_CASES[29]
        cpi_yesterday_case = self.runner.ARCHIVED_PROMPT_CASES[30]
        treasury_tomorrow_case = self.runner.ARCHIVED_PROMPT_CASES[31]
        inversion_case = self.runner.ARCHIVED_PROMPT_CASES[32]
        normal_vix_case = self.runner.ARCHIVED_PROMPT_CASES[33]
        spy_halt_case = self.runner.ARCHIVED_PROMPT_CASES[34]

        self.assertEqual("unknown", self.runner.preclassify_event_policy(self.prompt_input(cpi_today_future_earnings_case))["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(powell_tomorrow_case))["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(cpi_yesterday_case))["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(treasury_tomorrow_case))["decision"])
        self.assertEqual("unknown", self.runner.preclassify_event_policy(self.prompt_input(inversion_case))["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(normal_vix_case))["decision"])
        self.assertEqual("block", self.runner.preclassify_event_policy(self.prompt_input(spy_halt_case))["decision"])

    def test_preclassifier_handles_v12_policy_fixture_edges(self) -> None:
        ism_case = self.runner.ARCHIVED_PROMPT_CASES[35]
        jolts_case = self.runner.ARCHIVED_PROMPT_CASES[36]
        retail_sales_case = self.runner.ARCHIVED_PROMPT_CASES[37]
        no_war_case = self.runner.ARCHIVED_PROMPT_CASES[38]
        limit_down_drill_case = self.runner.ARCHIVED_PROMPT_CASES[39]
        near_inversion_case = self.runner.ARCHIVED_PROMPT_CASES[40]
        war_case = self.runner.ARCHIVED_PROMPT_CASES[41]
        circuit_breaker_case = self.runner.ARCHIVED_PROMPT_CASES[42]

        self.assertEqual("unknown", self.runner.preclassify_event_policy(self.prompt_input(ism_case))["decision"])
        self.assertEqual("unknown", self.runner.preclassify_event_policy(self.prompt_input(jolts_case))["decision"])
        self.assertEqual("unknown", self.runner.preclassify_event_policy(self.prompt_input(retail_sales_case))["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(no_war_case))["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(limit_down_drill_case))["decision"])
        self.assertEqual("allow", self.runner.preclassify_event_policy(self.prompt_input(near_inversion_case))["decision"])
        self.assertEqual("block", self.runner.preclassify_event_policy(self.prompt_input(war_case))["decision"])
        self.assertEqual("block", self.runner.preclassify_event_policy(self.prompt_input(circuit_breaker_case))["decision"])

    def test_live_mode_can_use_injected_transport_without_network(self) -> None:
        def fake_transport(payload, api_key_env):
            return {
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15, "cost": 0.001},
                "choices": [{"message": {"content": '{"decision":"allow","risk_score_0_to_10":3}'}}],
            }

        archived = self.runner.archive_prompt_inputs(Path(tempfile.mkdtemp()) / "inputs.json")[:1]
        results = self.runner.run_prompt_experiment(
            archived,
            "2024-01-03T09:20:00-05:00",
            live=True,
            transport=fake_transport,
        )
        self.assertEqual(3, len(results))
        self.assertTrue(all(row["decision"] == "allow" for row in results))
        summary = self.runner.summarize_results(results, live=True)
        self.assertEqual(0.003, summary["openrouter_actual_cost_usd"])
        self.assertEqual(3, summary["openrouter_costed_assessment_count"])
        self.assertEqual({"prompt_tokens": 30, "completion_tokens": 15, "total_tokens": 45}, summary["openrouter_usage_totals"])

    def test_live_mode_retries_empty_openrouter_content(self) -> None:
        calls = {"count": 0}

        def flaky_transport(payload, api_key_env):
            calls["count"] += 1
            if calls["count"] == 1:
                return {"choices": [{"message": {"content": ""}}]}
            return {"choices": [{"message": {"content": '{"decision":"allow","risk_score_0_to_10":3}'}}]}

        archived = self.runner.archive_prompt_inputs(Path(tempfile.mkdtemp()) / "inputs.json")[:1]
        results = self.runner.run_prompt_experiment(
            archived,
            "2024-01-03T09:20:00-05:00",
            live=True,
            transport=flaky_transport,
        )
        self.assertEqual(4, calls["count"])
        self.assertEqual(3, len(results))

    def test_resume_mode_reuses_existing_assessment_rows(self) -> None:
        calls = {"count": 0}

        def fake_transport(payload, api_key_env):
            calls["count"] += 1
            return {"choices": [{"message": {"content": '{"decision":"allow","risk_score_0_to_10":3}'}}]}

        with tempfile.TemporaryDirectory() as tmp:
            jsonl_path = Path(tmp) / "assessments.jsonl"
            archived = self.runner.archive_prompt_inputs(Path(tmp) / "inputs.json")[:1]
            existing = self.runner.adapter.dry_run_prompt_variant(
                archived[0]["prompt_input"],
                "A",
                "2024-01-03T09:20:00-05:00",
            )
            self.runner.adapter.append_assessment_jsonl(jsonl_path, existing)
            existing_rows = self.runner.load_existing_assessments(jsonl_path)
            results = self.runner.run_prompt_experiment(
                archived,
                "2024-01-03T09:20:00-05:00",
                live=True,
                transport=fake_transport,
                assessment_jsonl_path=jsonl_path,
                existing_assessments=existing_rows,
            )
            lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()

        self.assertEqual(2, calls["count"])
        self.assertEqual(3, len(results))
        self.assertEqual(3, len(lines))


if __name__ == "__main__":
    unittest.main()
