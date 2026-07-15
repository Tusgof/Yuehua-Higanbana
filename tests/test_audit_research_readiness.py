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
        lib_usage = next(check for check in result["checks"] if check["name"] == "new_script_lib_usage")
        self.assertEqual("pass", lib_usage["status"])
        self.assertEqual(0, lib_usage["bypassing_lib_count"])
        exp07_redesign = next(check for check in result["checks"] if check["name"] == "exp07_prompt_redesign")
        self.assertEqual("blocked", exp07_redesign["status"])
        self.assertTrue(any("H-A2 09:36 ORB is pre-registered as E0 design evidence" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("09:35 confirmation bar closes at 09:36" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("0 fresh local dates because all 525 local dates" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("20 chronological control dates with a $14.21628 ceiling" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("exact MinTRL remains unknown" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("fresh OOS checkpoint is complete as E1 methodology-failure evidence" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("stress geometry remains blocked by 13 missing real 2022 SPY underlying-bar dates" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("metadata-only Databento cost estimate" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("estimate_h_a2_independent_validation_cost.py" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("create a separate download decision artifact" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.54 post-stress normalization/control import diagnostic is pre-registered" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.53 post-stress normalization/control download is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.49 bounded normal/control exact replay is complete as E1" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.64 cache inventory is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("2025-02-11, direction call" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("mid_pnl -$22.00 and implementable_pnl -$26.56" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("OOS rule evaluation" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.56 post-stress normalization/control exact replay is pre-registered" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("run the bounded H-A2.57 exact replay" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("pre-register the next validation-data or sample-expansion decision" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.49 bounded normal/control exact replay is pre-registered" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("implement and run only this bounded local exact-replay diagnostic" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("write research log 036" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.48 normal/control import diagnostic is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.47 normal/control import diagnostic is pre-registered" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.46 normal/control download is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("pre-register a normal/control sample decision or no-paid validation gap decision" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.45 normal/control paid download decision is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("execute only the approved normal/control pack download" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("rerun `python scripts\\audit_paid_costs.py`" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("do not approve e2, paper trading, operational validation, or real-money trading" in action.lower() for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.62 breakeven-aware train-only diagnostic is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.61 breakeven-aware revised-rule preregistration is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.59 mechanism-revision preregistration is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("h_a2_mechanism_revision_audit` as a local/no-paid E1 diagnostic" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.60 mechanism-revision audit is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.58 decision after two exact replays is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.43 normal/control independent-validation sample decision is pre-registered" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("Next safe H-A2 work is to build or update the metadata-only cost-estimate runner" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.41 one-day independent-validation import/normalization/diagnostic is pre-registered" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.40 one-day independent-validation download is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.39 one-day paid download decision is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.38 independent-validation metadata cost estimate passed" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.37 independent-validation paid-cost estimate plan is pre-registered as E0 control evidence" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.35 independent validation feasibility diagnostic is complete as E1 diagnostic evidence" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.34 original-entry robustness/prioritization review is complete as E1 diagnostic evidence" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.32 original-entry revision diagnostic is complete as E1 diagnostic evidence" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.27 locked-condition signal-attribution audit is complete as E1 diagnostic evidence" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.27 locked-condition signal-attribution audit is pre-registered as E0 control evidence" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.26 revised-condition robustness audit is complete as E1 diagnostic evidence" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.25 revised-condition robustness audit is pre-registered as E0 control evidence" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2 revised opening-followthrough diagnostic is complete as E1 prioritization evidence" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("revised opening-followthrough condition is pre-registered" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("implement and run the local-only revised-condition diagnostic" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("run the local-only analysis of non-risk losing days" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("pre-register H-A2 residual/adverse-day analysis" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("H-G1.24a no-paid local-cache overlap scan is complete and blocked" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("H-G1 remains parked" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("current 2-date gamma intersection" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("do not run a metadata cost check, paid data download, new gamma ablation, strategy use, paper trading, or true net-gamma claim" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("News-Unblock N.7" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-A2.17 IBKR readiness gate rerun is complete and externally blocked" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("no local IBKR API port is listening on 7497/7496/4002/4001" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("start local TWS/Gateway with API enabled" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("do not approve e2, paper trading, operational validation, or real-money trading" in action.lower() for action in result["next_safe_actions"]))
        self.assertFalse(any("Next rerun/clear the IBKR readiness gate" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("Next decide whether to park H-G1" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("the next H-G1-only safe step is a no-paid local-cache overlap scan" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("sample-expansion decision artifact" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-G1.23 decision is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("do not rerun this ablation, add variants, buy data, or claim true market-maker net gamma" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-G1.21 strategy-ablation pre-registration is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("implement the no-paid H-G1 gamma strategy-ablation runner" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-G1.20 acceptance blocker review is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("pre-register H-G1 gamma strategy ablation" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-G1.19 side-aware data-validity diagnostic passed" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("strategy-independent acceptance blocker review" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("before any NOVI/net-gamma strategy filter" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-G1.18 side-aware bucket policy adoption is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("rerun the H-G1 gamma diagnostic on manifest-v3 rows under this policy" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("side-aware policy-adoption artifact" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-G1.17 bucket-policy comparison is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-G1.16 bucket-policy review pre-registration is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("no-paid policy-comparison diagnostic" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-G1.15 manifest-v3 bucket-failure diagnostic is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("all 55 blocked rows inside the five failed buckets are opposite-right ITM rows" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("pre-registered bucket-policy review" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("diagnose the v3 bucket failures" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-G1.14 manifest-v3 diagnostic is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-G1 v3 replacement OI download exists" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("rerun H-G1 enrichment/diagnostic using manifest v3" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("`2023-09-13` replacement OI day" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("controlled one-day OI download only" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-G1.12 is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("Next run a metadata cost check" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("H-G1.10 is complete" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("Next draft policy v2.1" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("policy revision alone is rejected" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("Next investigate the five bucket failures" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("h_g1_bucket_failure_diagnostic.md" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("repair the missing `2023-03-13`/`2023-03-22` SPY bar cache" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("news_gdelt_doc_api_enrichment_scaffold.md" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("alternative timestamp-clean real-news source paths" in action for action in result["next_safe_actions"]))
        self.assertTrue(any("source-decision artifact" in action for action in result["next_safe_actions"]))
        self.assertFalse(any("run a diagnostic gamma aggregation against the policy gates" in action for action in result["next_safe_actions"]))
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

    def test_databento_mo_and_ai_envs_are_tracked_as_supported_keys(self) -> None:
        result = self.auditor.audit_research_readiness(
            process_env={"DATABENTO_API_MO": "x", "DATABENTO_API_AI": "y"},
            user_env_getter=lambda name: None,
        )

        self.assertIn("DATABENTO_API_MO", result["environment"])
        self.assertIn("DATABENTO_API_AI", result["environment"])
        self.assertTrue(result["environment"]["DATABENTO_API_MO"]["process"])
        self.assertTrue(result["environment"]["DATABENTO_API_AI"]["process"])
        self.assertNotIn("requires_databento_api_key_for_aug_2023_live_cost", result["blockers"])

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
