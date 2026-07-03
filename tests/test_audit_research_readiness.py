from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_research_readiness.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("audit_research_readiness", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load research readiness auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditResearchReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = load_auditor()

    def test_current_project_readiness_is_blocked_by_data_and_news(self) -> None:
        result = self.auditor.audit_research_readiness(
            process_env={},
            user_env_getter=lambda name: "configured" if name == "HIGANBANA_OPENROUTER_API" else None,
        )

        self.assertEqual("blocked", result["status"])
        self.assertIn("requires_databento_api_key_for_aug_2023_live_cost", result["blockers"])
        self.assertIn("gdelt_capture_unavailable", result["blockers"])
        self.assertIn("requires_real_news_archive", result["blockers"])
        self.assertIn("requires_real_timestamp_clean_news_cases_for_exp07_prompt_research", result["blockers"])
        self.assertIn("requires_wider_spy_0dte_data", result["blockers"])
        self.assertFalse(result["environment"]["DATABENTO_API_KEY"]["user"])
        self.assertFalse(result["environment"]["DATABENTO_API_KEY"]["machine"])
        self.assertTrue(result["environment"]["HIGANBANA_OPENROUTER_API"]["user"])
        exp07_redesign = next(check for check in result["checks"] if check["name"] == "exp07_prompt_redesign")
        self.assertEqual("blocked", exp07_redesign["status"])
        self.assertTrue(any("confirm actual provider usage remains below" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("run a diagnostic gamma aggregation against the policy gates" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("define gamma aggregation/scaling validation" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("Continue SPY-only Databento data acquisition" in action for action in result["next_safe_actions"]))

    def test_openrouter_availability_does_not_make_exp07_prompt_research_ready_without_real_news(self) -> None:
        result = self.auditor.audit_research_readiness(
            process_env={"HIGANBANA_OPENROUTER_API": "configured"},
            user_env_getter=lambda name: None,
        )

        openrouter = next(check for check in result["checks"] if check["name"] == "openrouter_llm")
        exp07_redesign = next(check for check in result["checks"] if check["name"] == "exp07_prompt_redesign")
        self.assertEqual("available", openrouter["status"])
        self.assertEqual("blocked", exp07_redesign["status"])
        self.assertIn("requires_real_timestamp_clean_news_cases_for_exp07_prompt_research", result["blockers"])
        self.assertTrue(any("Do not run another synthetic Exp07 prompt matrix" in action for action in result["next_safe_actions"]))

    def test_machine_env_keys_satisfy_live_api_key_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {
                "macro_calendar": root / "macro.json",
                "vix_vxv": root / "vix.json",
                "news": root / "news.json",
                "gdelt_capture_status": root / "gdelt_statuses",
                "gdelt_command_plan": root / "gdelt_plan.json",
                "paid_cost": root / "paid_cost.json",
                "research_logs": root / "research_logs.json",
                "strategy_data": root / "strategy_data.json",
                "exp07_real_news_case_plan": root / "real_news_case_plan.json",
                "exp07_acceptance": root / "acceptance.json",
                "exp07_strategy_ablation": root / "ablation.json",
                "aug_2023_databento_dry_run": root / "databento.json",
                "opra_statistics_oi_probe": root / "opra_statistics_oi_probe.json",
                "opra_statistics_oi_download_probe": root / "opra_statistics_oi_download_probe.json",
            }
            for key in ["macro_calendar", "vix_vxv", "news", "paid_cost", "research_logs", "strategy_data"]:
                paths[key].write_text(json.dumps({"status": "pass", "blockers": []}), encoding="utf-8")
            paths["gdelt_capture_status"].mkdir()
            (paths["gdelt_capture_status"] / "2023-09-01.json").write_text(
                json.dumps({"status": "captured", "blockers": []}),
                encoding="utf-8",
            )
            paths["gdelt_command_plan"].write_text(
                json.dumps(
                    {
                        "retry_pressure": {"status": "normal_retry"},
                        "retry_queue_summary": {"next_unattempted_trade_date": None, "not_attempted_count": 0},
                    }
                ),
                encoding="utf-8",
            )
            paths["exp07_real_news_case_plan"].write_text(
                json.dumps({"status": "ready_for_prompt_family_pre_experiment", "blockers": [], "candidate_day_count": 8, "captured_candidate_count": 8}),
                encoding="utf-8",
            )
            paths["exp07_acceptance"].write_text(
                json.dumps({"strategy_integration_status": "pass", "strategy_integration_blockers": []}),
                encoding="utf-8",
            )
            paths["exp07_strategy_ablation"].write_text(json.dumps({"status": "ready", "blockers": []}), encoding="utf-8")
            paths["aug_2023_databento_dry_run"].write_text(json.dumps({"request_count": 322}), encoding="utf-8")
            paths["opra_statistics_oi_probe"].write_text(
                json.dumps(
                    {
                        "status": "pass_with_timing_caveat",
                        "has_stat_type_field": True,
                        "record_count_checks": [
                            {"label": "intraday_research_window", "record_count": 0},
                            {"label": "full_utc_day", "record_count": 1},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            paths["opra_statistics_oi_download_probe"].write_text(
                json.dumps({"status": "pass", "inspection": {"open_interest_record_count": 5}}),
                encoding="utf-8",
            )

            result = self.auditor.audit_research_readiness(
                report_paths=paths,
                process_env={},
                user_env_getter=lambda name: None,
                machine_env_getter=lambda name: "configured" if name in {"DATABENTO_API_KEY", "HIGANBANA_OPENROUTER_API"} else None,
            )

        self.assertNotIn("requires_databento_api_key_for_aug_2023_live_cost", result["blockers"])
        self.assertNotIn("requires_openrouter_api_key_for_live_llm_experiments", result["blockers"])
        self.assertTrue(result["environment"]["DATABENTO_API_KEY"]["machine"])
        self.assertTrue(result["environment"]["HIGANBANA_OPENROUTER_API"]["machine"])

    def test_databento_project_alias_satisfies_live_api_key_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {
                "macro_calendar": root / "macro.json",
                "vix_vxv": root / "vix.json",
                "news": root / "news.json",
                "gdelt_capture_status": root / "gdelt_statuses",
                "gdelt_command_plan": root / "gdelt_plan.json",
                "paid_cost": root / "paid_cost.json",
                "research_logs": root / "research_logs.json",
                "strategy_data": root / "strategy_data.json",
                "exp07_real_news_case_plan": root / "real_news_case_plan.json",
                "exp07_acceptance": root / "acceptance.json",
                "exp07_strategy_ablation": root / "ablation.json",
                "aug_2023_databento_dry_run": root / "databento.json",
                "opra_statistics_oi_probe": root / "opra_statistics_oi_probe.json",
                "opra_statistics_oi_download_probe": root / "opra_statistics_oi_download_probe.json",
            }
            for key in ["macro_calendar", "vix_vxv", "news", "paid_cost", "research_logs", "strategy_data"]:
                paths[key].write_text(json.dumps({"status": "pass", "blockers": []}), encoding="utf-8")
            paths["gdelt_capture_status"].mkdir()
            (paths["gdelt_capture_status"] / "2023-09-01.json").write_text(
                json.dumps({"status": "captured", "blockers": []}),
                encoding="utf-8",
            )
            paths["gdelt_command_plan"].write_text(
                json.dumps(
                    {
                        "retry_pressure": {"status": "normal_retry"},
                        "retry_queue_summary": {"next_unattempted_trade_date": None, "not_attempted_count": 0},
                    }
                ),
                encoding="utf-8",
            )
            paths["exp07_real_news_case_plan"].write_text(
                json.dumps({"status": "ready_for_prompt_family_pre_experiment", "blockers": [], "candidate_day_count": 8, "captured_candidate_count": 8}),
                encoding="utf-8",
            )
            paths["exp07_acceptance"].write_text(
                json.dumps({"strategy_integration_status": "pass", "strategy_integration_blockers": []}),
                encoding="utf-8",
            )
            paths["exp07_strategy_ablation"].write_text(json.dumps({"status": "ready", "blockers": []}), encoding="utf-8")
            paths["aug_2023_databento_dry_run"].write_text(json.dumps({"request_count": 322}), encoding="utf-8")
            paths["opra_statistics_oi_probe"].write_text(
                json.dumps(
                    {
                        "status": "pass_with_timing_caveat",
                        "has_stat_type_field": True,
                        "record_count_checks": [
                            {"label": "intraday_research_window", "record_count": 0},
                            {"label": "full_utc_day", "record_count": 1},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            paths["opra_statistics_oi_download_probe"].write_text(
                json.dumps({"status": "pass", "inspection": {"open_interest_record_count": 5}}),
                encoding="utf-8",
            )

            result = self.auditor.audit_research_readiness(
                report_paths=paths,
                process_env={"DATABENTO_SPY0DTE_API": "x", "HIGANBANA_OPENROUTER_API": "y"},
                user_env_getter=lambda name: None,
            )

        self.assertNotIn("requires_databento_api_key_for_aug_2023_live_cost", result["blockers"])
        self.assertTrue(result["environment"]["DATABENTO_SPY0DTE_API"]["process"])

    def test_ready_state_has_no_blockers_when_reports_and_env_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {
                "macro_calendar": root / "macro.json",
                "vix_vxv": root / "vix.json",
                "news": root / "news.json",
                "gdelt_capture_status": root / "gdelt_statuses",
                "gdelt_command_plan": root / "gdelt_plan.json",
                "paid_cost": root / "paid_cost.json",
                "research_logs": root / "research_logs.json",
                "strategy_data": root / "strategy_data.json",
                "exp07_real_news_case_plan": root / "real_news_case_plan.json",
                "exp07_acceptance": root / "acceptance.json",
                "exp07_strategy_ablation": root / "ablation.json",
                "aug_2023_databento_dry_run": root / "databento.json",
                "opra_statistics_oi_probe": root / "opra_statistics_oi_probe.json",
                "opra_statistics_oi_download_probe": root / "opra_statistics_oi_download_probe.json",
            }
            paths["macro_calendar"].write_text(json.dumps({"status": "pass", "blockers": []}), encoding="utf-8")
            paths["vix_vxv"].write_text(json.dumps({"status": "pass", "blockers": []}), encoding="utf-8")
            paths["news"].write_text(json.dumps({"status": "pass", "blockers": []}), encoding="utf-8")
            paths["gdelt_capture_status"].mkdir()
            (paths["gdelt_capture_status"] / "2023-09-01.json").write_text(
                json.dumps({"status": "captured", "blockers": []}),
                encoding="utf-8",
            )
            paths["gdelt_command_plan"].write_text(
                json.dumps(
                    {
                        "retry_pressure": {"status": "normal_retry"},
                        "retry_queue_summary": {"next_unattempted_trade_date": None, "not_attempted_count": 0},
                    }
                ),
                encoding="utf-8",
            )
            paths["paid_cost"].write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "blockers": [],
                        "known_committed_estimated_cost_usd": 10.0,
                        "remaining_before_stop_usd": 90.0,
                    }
                ),
                encoding="utf-8",
            )
            paths["research_logs"].write_text(json.dumps({"status": "pass", "blockers": []}), encoding="utf-8")
            paths["strategy_data"].write_text(
                json.dumps({"status": "pass", "blockers": [], "totals": {"closed_trades": 500, "candidate_days": 500}}),
                encoding="utf-8",
            )
            paths["exp07_real_news_case_plan"].write_text(
                json.dumps({"status": "ready_for_prompt_family_pre_experiment", "blockers": [], "candidate_day_count": 8, "captured_candidate_count": 8}),
                encoding="utf-8",
            )
            paths["exp07_acceptance"].write_text(
                json.dumps({"strategy_integration_status": "pass", "strategy_integration_blockers": []}),
                encoding="utf-8",
            )
            paths["exp07_strategy_ablation"].write_text(json.dumps({"status": "ready", "blockers": []}), encoding="utf-8")
            paths["aug_2023_databento_dry_run"].write_text(json.dumps({"request_count": 322}), encoding="utf-8")
            paths["opra_statistics_oi_probe"].write_text(
                json.dumps(
                    {
                        "status": "pass_with_timing_caveat",
                        "has_stat_type_field": True,
                        "record_count_checks": [
                            {"label": "intraday_research_window", "record_count": 0},
                            {"label": "full_utc_day", "record_count": 1},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            paths["opra_statistics_oi_download_probe"].write_text(
                json.dumps({"status": "pass", "inspection": {"open_interest_record_count": 5}}),
                encoding="utf-8",
            )

            result = self.auditor.audit_research_readiness(
                report_paths=paths,
                process_env={"DATABENTO_API_KEY": "x", "HIGANBANA_OPENROUTER_API": "y"},
                user_env_getter=lambda name: None,
            )

        self.assertEqual("ready", result["status"])
        self.assertEqual([], result["blockers"])

    def test_research_log_blocker_is_included_in_aggregate_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {
                "macro_calendar": root / "macro.json",
                "vix_vxv": root / "vix.json",
                "news": root / "news.json",
                "gdelt_capture_status": root / "gdelt_statuses",
                "gdelt_command_plan": root / "gdelt_plan.json",
                "paid_cost": root / "paid_cost.json",
                "research_logs": root / "research_logs.json",
                "strategy_data": root / "strategy_data.json",
                "exp07_real_news_case_plan": root / "real_news_case_plan.json",
                "exp07_acceptance": root / "acceptance.json",
                "exp07_strategy_ablation": root / "ablation.json",
                "aug_2023_databento_dry_run": root / "databento.json",
            }
            for key in ["macro_calendar", "vix_vxv", "news", "paid_cost", "strategy_data"]:
                paths[key].write_text(json.dumps({"status": "pass", "blockers": []}), encoding="utf-8")
            paths["gdelt_capture_status"].mkdir()
            (paths["gdelt_capture_status"] / "2023-09-01.json").write_text(
                json.dumps({"status": "captured", "blockers": []}),
                encoding="utf-8",
            )
            paths["gdelt_command_plan"].write_text(
                json.dumps(
                    {
                        "retry_pressure": {"status": "normal_retry"},
                        "retry_queue_summary": {"next_unattempted_trade_date": None, "not_attempted_count": 0},
                    }
                ),
                encoding="utf-8",
            )
            paths["research_logs"].write_text(
                json.dumps({"status": "blocked", "blockers": ["missing_research_log:exp07_prompt_v12_summary"]}),
                encoding="utf-8",
            )
            paths["exp07_real_news_case_plan"].write_text(
                json.dumps({"status": "ready_for_prompt_family_pre_experiment", "blockers": [], "candidate_day_count": 8, "captured_candidate_count": 8}),
                encoding="utf-8",
            )
            paths["exp07_acceptance"].write_text(
                json.dumps({"strategy_integration_status": "pass", "strategy_integration_blockers": []}),
                encoding="utf-8",
            )
            paths["exp07_strategy_ablation"].write_text(json.dumps({"status": "ready", "blockers": []}), encoding="utf-8")
            paths["aug_2023_databento_dry_run"].write_text(json.dumps({"request_count": 322}), encoding="utf-8")

            result = self.auditor.audit_research_readiness(
                report_paths=paths,
                process_env={"DATABENTO_API_KEY": "x", "HIGANBANA_OPENROUTER_API": "y"},
                user_env_getter=lambda name: None,
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_research_log:exp07_prompt_v12_summary", result["blockers"])

    def test_gdelt_capture_status_blocker_is_included_in_aggregate_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {
                "macro_calendar": root / "macro.json",
                "vix_vxv": root / "vix.json",
                "news": root / "news.json",
                "gdelt_capture_status": root / "gdelt_statuses",
                "gdelt_command_plan": root / "gdelt_plan.json",
                "paid_cost": root / "paid_cost.json",
                "research_logs": root / "research_logs.json",
                "strategy_data": root / "strategy_data.json",
                "exp07_real_news_case_plan": root / "real_news_case_plan.json",
                "exp07_acceptance": root / "acceptance.json",
                "exp07_strategy_ablation": root / "ablation.json",
                "aug_2023_databento_dry_run": root / "databento.json",
            }
            for key in ["macro_calendar", "vix_vxv", "news", "paid_cost", "research_logs", "strategy_data"]:
                paths[key].write_text(json.dumps({"status": "pass", "blockers": []}), encoding="utf-8")
            paths["gdelt_capture_status"].mkdir()
            (paths["gdelt_capture_status"] / "2023-09-01.json").write_text(
                json.dumps({"status": "blocked", "blockers": ["gdelt_capture_unavailable"]}),
                encoding="utf-8",
            )
            paths["gdelt_command_plan"].write_text(
                json.dumps(
                    {
                        "retry_pressure": {"status": "normal_retry"},
                        "retry_queue_summary": {"next_unattempted_trade_date": "2023-09-07", "not_attempted_count": 1},
                    }
                ),
                encoding="utf-8",
            )
            paths["exp07_real_news_case_plan"].write_text(
                json.dumps({"status": "ready_for_prompt_family_pre_experiment", "blockers": [], "candidate_day_count": 8, "captured_candidate_count": 8}),
                encoding="utf-8",
            )
            paths["exp07_acceptance"].write_text(
                json.dumps({"strategy_integration_status": "pass", "strategy_integration_blockers": []}),
                encoding="utf-8",
            )
            paths["exp07_strategy_ablation"].write_text(json.dumps({"status": "ready", "blockers": []}), encoding="utf-8")
            paths["aug_2023_databento_dry_run"].write_text(json.dumps({"request_count": 322}), encoding="utf-8")

            result = self.auditor.audit_research_readiness(
                report_paths=paths,
                process_env={"DATABENTO_API_KEY": "x", "HIGANBANA_OPENROUTER_API": "y"},
                user_env_getter=lambda name: None,
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("gdelt_capture_unavailable", result["blockers"])
        self.assertIn("gdelt_capture_not_captured:2023-09-01", result["blockers"])

    def test_gdelt_retry_cooldown_is_included_in_aggregate_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {
                "macro_calendar": root / "macro.json",
                "vix_vxv": root / "vix.json",
                "news": root / "news.json",
                "gdelt_capture_status": root / "gdelt_statuses",
                "gdelt_command_plan": root / "gdelt_plan.json",
                "paid_cost": root / "paid_cost.json",
                "research_logs": root / "research_logs.json",
                "strategy_data": root / "strategy_data.json",
                "exp07_real_news_case_plan": root / "real_news_case_plan.json",
                "exp07_acceptance": root / "acceptance.json",
                "exp07_strategy_ablation": root / "ablation.json",
                "aug_2023_databento_dry_run": root / "databento.json",
            }
            for key in ["macro_calendar", "vix_vxv", "news", "paid_cost", "research_logs", "strategy_data"]:
                paths[key].write_text(json.dumps({"status": "pass", "blockers": []}), encoding="utf-8")
            paths["gdelt_capture_status"].mkdir()
            (paths["gdelt_capture_status"] / "2023-09-01.json").write_text(
                json.dumps({"status": "captured", "blockers": []}),
                encoding="utf-8",
            )
            paths["gdelt_command_plan"].write_text(
                json.dumps(
                    {
                        "retry_pressure": {"status": "cooldown_recommended"},
                        "retry_queue_summary": {
                            "next_unattempted_trade_date": "2023-10-05",
                            "not_attempted_count": 22,
                        },
                    }
                ),
                encoding="utf-8",
            )
            paths["exp07_real_news_case_plan"].write_text(
                json.dumps({"status": "ready_for_prompt_family_pre_experiment", "blockers": [], "candidate_day_count": 8, "captured_candidate_count": 8}),
                encoding="utf-8",
            )
            paths["exp07_acceptance"].write_text(
                json.dumps({"strategy_integration_status": "pass", "strategy_integration_blockers": []}),
                encoding="utf-8",
            )
            paths["exp07_strategy_ablation"].write_text(json.dumps({"status": "ready", "blockers": []}), encoding="utf-8")
            paths["aug_2023_databento_dry_run"].write_text(json.dumps({"request_count": 322}), encoding="utf-8")

            result = self.auditor.audit_research_readiness(
                report_paths=paths,
                process_env={"DATABENTO_API_KEY": "x", "HIGANBANA_OPENROUTER_API": "y"},
                user_env_getter=lambda name: None,
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("gdelt_retry_cooldown_recommended", result["blockers"])
        gdelt_plan = next(check for check in result["checks"] if check["name"] == "gdelt_command_plan")
        self.assertEqual("cooldown_recommended", gdelt_plan["retry_pressure_status"])
        self.assertEqual("2023-10-05", gdelt_plan["next_unattempted_trade_date"])
        self.assertTrue(any("Pause additional live GDELT" in action for action in result["next_safe_actions"]))
        self.assertFalse(any(action.startswith("Retry timestamp-safe GDELT") for action in result["next_safe_actions"]))

    def test_main_writes_json_and_markdown_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "readiness.json"
            report_path = Path(tmp) / "readiness.md"

            returncode = self.auditor.main(["--json-output", str(output_path), "--report-output", str(report_path)])

            self.assertEqual(0, returncode)
            result = json.loads(output_path.read_text(encoding="utf-8"))
            report = report_path.read_text(encoding="utf-8")
            self.assertIn(result["status"], {"blocked", "ready"})
            self.assertIn("Research Readiness Audit", report)
            self.assertIn("| Check | Status | Details | Blockers |", report)
            self.assertIn("known cost", report)
            self.assertIn("closed trades", report)
            self.assertIn("status counts", report)


if __name__ == "__main__":
    unittest.main()
