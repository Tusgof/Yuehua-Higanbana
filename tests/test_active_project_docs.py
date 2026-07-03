from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ActiveProjectDocsTests(unittest.TestCase):
    def test_active_docs_exist(self) -> None:
        required = [
            "PROJECT_BRAIN.md",
            "IMPLEMENT_PLAN.md",
            "0dte_trading_system_design.md",
            "backtest_experiments_plan.md",
            "docs/DATA_SOURCE_AUDIT.md",
            "docs/PROVIDER_SAMPLE_SPEC.md",
            "docs/NEXT_USER_INPUTS.md",
            "docs/RUNBOOK.md",
            "docs/RESEARCH_ARCHITECTURE.md",
            "docs/REAL_MONEY_GUARDRAILS.md",
            ".env.example",
            "schemas/m2_contracts.schema.json",
            "scripts/validate_m2_contracts.py",
            "scripts/audit_databento_cache.py",
            "scripts/estimate_databento_cost.py",
            "scripts/project_databento_cost.py",
            "scripts/download_databento_data.py",
            "scripts/inspect_databento_raw.py",
            "scripts/normalize_databento_options.py",
            "scripts/plan_databento_spy_bars.py",
            "scripts/normalize_databento_spy_bars.py",
            "scripts/run_jan2024_pilot_adapter.py",
            "scripts/run_jan2024_pilot_pnl.py",
            "scripts/run_jan2024_pilot_sensitivity.py",
            "scripts/import_m3_fixture.py",
            "scripts/import_provider_sample.py",
            "scripts/strategy_spec_m4.py",
            "scripts/backtest_engine_m5.py",
            "scripts/experiment_runner_m6.py",
            "scripts/operational_bridge_m7.py",
            "scripts/provider_adapters.py",
            "scripts/audit_paid_costs.py",
            "scripts/audit_strategy_data_readiness.py",
            "scripts/audit_research_readiness.py",
            "scripts/audit_m3_backtest_reporting_hardening.py",
            "scripts/run_m4_subsystem_a_baseline.py",
            "scripts/run_m4_subsystem_b_feasibility.py",
            "scripts/run_m4_exit_behavior_diagnostic.py",
            "scripts/audit_m4_execution_rule_compliance.py",
            "scripts/run_m5_transaction_cost_latency_sensitivity.py",
            "scripts/run_m5_strike_selection_sensitivity.py",
            "scripts/run_m5_entry_timing_sensitivity.py",
            "scripts/run_m5_exit_target_stop_sensitivity.py",
            "scripts/run_m5_regime_filter_sensitivity.py",
            "scripts/run_m5_portfolio_construction_diagnostic.py",
            "scripts/run_m5_structural_break_assessment.py",
            "scripts/plan_exp07_real_news_cases.py",
            "scripts/validate_exp07_real_news_case_plan.py",
            "scripts/plan_gdelt_news_capture_commands.py",
            "scripts/import_gdelt_news_capture_directory.py",
            "scripts/run_fixture_pipeline.py",
            "data/raw/spy_0dte/m3_fixture_raw.json",
            "data/registry/datasets.jsonl",
            "experiments/experiment_manifests.json",
            "reports/final_research_review.md",
            "reports/data_cost/databento_cost_dry_run.md",
            "reports/data_cost/databento_cost_plan.md",
            "reports/data_cost/databento_cost_plan.json",
            "reports/data_cost/databento_cost_projection.md",
            "reports/data_cost/databento_cost_projection.json",
            "reports/data_cost/databento_download_plan.json",
            "reports/data_cost/databento_cache_audit.md",
            "reports/data_cost/databento_cache_audit.json",
            "reports/data_cost/databento_raw_inspection.md",
            "reports/data_cost/databento_raw_inspection.json",
            "reports/data_cost/databento_normalization_summary.json",
            "reports/data_cost/databento_spy_bars_plan.md",
            "reports/data_cost/databento_spy_bars_plan.json",
            "reports/data_cost/databento_spy_bars_download_result.md",
            "reports/data_cost/databento_spy_bars_download_result.json",
            "reports/data_cost/databento_spy_bars_normalization_summary.json",
            "reports/data_cost/paid_cost_audit.md",
            "reports/data_cost/paid_cost_audit.json",
            "reports/strategy_data_readiness_audit.md",
            "reports/strategy_data_readiness_audit.json",
            "reports/news_gdelt_capture_status.json",
            "reports/news_gdelt_capture_command_plan.md",
            "reports/news_gdelt_capture_command_plan.json",
            "reports/news_gdelt_capture_directory_import_summary.md",
            "reports/news_gdelt_capture_directory_import_summary.json",
            "reports/research_readiness_audit.md",
            "reports/research_readiness_audit.json",
            "reports/m3_backtest_reporting_hardening_audit.md",
            "reports/m3_backtest_reporting_hardening_audit.json",
            "reports/baselines/subsystem_a_orb_baseline_summary.json",
            "reports/baselines/subsystem_a_orb_baseline_report.md",
            "reports/baselines/subsystem_b_put_ratio_feasibility_summary.json",
            "reports/baselines/subsystem_b_put_ratio_feasibility_report.md",
            "reports/baselines/m4_exit_behavior_diagnostic_summary.json",
            "reports/baselines/m4_exit_behavior_diagnostic_report.md",
            "reports/baselines/m4_execution_rule_compliance_audit.json",
            "reports/baselines/m4_execution_rule_compliance_audit.md",
            "reports/experiments/m5_transaction_cost_latency_sensitivity_summary.json",
            "reports/experiments/m5_transaction_cost_latency_sensitivity_report.md",
            "reports/experiments/search_logs/m5_transaction_cost_latency_sensitivity_search_log.jsonl",
            "reports/experiments/m5_strike_selection_sensitivity_summary.json",
            "reports/experiments/m5_strike_selection_sensitivity_report.md",
            "reports/experiments/search_logs/m5_strike_selection_sensitivity_search_log.jsonl",
            "reports/experiments/m5_entry_timing_sensitivity_summary.json",
            "reports/experiments/m5_entry_timing_sensitivity_report.md",
            "reports/experiments/search_logs/m5_entry_timing_sensitivity_search_log.jsonl",
            "reports/experiments/m5_exit_target_stop_sensitivity_summary.json",
            "reports/experiments/m5_exit_target_stop_sensitivity_report.md",
            "reports/experiments/search_logs/m5_exit_target_stop_sensitivity_search_log.jsonl",
            "reports/experiments/m5_regime_filter_sensitivity_summary.json",
            "reports/experiments/m5_regime_filter_sensitivity_report.md",
            "reports/experiments/search_logs/m5_regime_filter_sensitivity_search_log.jsonl",
            "reports/experiments/m5_portfolio_construction_diagnostic_summary.json",
            "reports/experiments/m5_portfolio_construction_diagnostic_report.md",
            "reports/experiments/search_logs/m5_portfolio_construction_diagnostic_search_log.jsonl",
            "reports/experiments/m5_structural_break_assessment_summary.json",
            "reports/experiments/m5_structural_break_assessment_report.md",
            "reports/experiments/exp07_real_news_case_plan.md",
            "reports/experiments/exp07_real_news_case_plan.json",
            "reports/pilots/jan_2024_pilot_adapter_summary.json",
            "reports/pilots/jan_2024_pilot_adapter_report.md",
            "reports/pilots/jan_2024_pilot_pnl_summary.json",
            "reports/pilots/jan_2024_pilot_pnl_report.md",
            "reports/pilots/jan_2024_pilot_sensitivity_summary.json",
            "reports/pilots/jan_2024_pilot_sensitivity_report.md",
            "data/normalized/spy_0dte/databento/one_month_pilot/option_quote.jsonl",
            "data/normalized/spy_0dte/databento/one_month_pilot/spy_bar.jsonl",
        ]
        for relative_path in required:
            with self.subTest(path=relative_path):
                self.assertTrue((PROJECT_ROOT / relative_path).exists())

    def test_active_scope_is_spy_0dte(self) -> None:
        brain = (PROJECT_ROOT / "PROJECT_BRAIN.md").read_text(encoding="utf-8")
        self.assertIn("SPY 0DTE - Higanbana", brain)
        self.assertIn("Interactive Brokers", brain)
        self.assertIn("Survival first", brain)

    def test_thai_conclusion_labels_are_readable(self) -> None:
        for relative_path in ["PROJECT_BRAIN.md", "IMPLEMENT_PLAN.md", "docs/NEXT_USER_INPUTS.md"]:
            with self.subTest(path=relative_path):
                text = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn("ผ่าน", text)
                self.assertIn("ไม่ผ่าน", text)
                self.assertIn("ยังสรุปไม่ได้", text)
                self.assertNotIn("เธ", text)
                self.assertNotIn("เน", text)

    def test_real_money_guardrails_block_early_transmit(self) -> None:
        guardrails = (PROJECT_ROOT / "docs" / "REAL_MONEY_GUARDRAILS.md").read_text(encoding="utf-8")
        self.assertIn("No IBKR order transmission before research acceptance", guardrails)
        self.assertIn("Paper trading is an operational validation bridge", guardrails)
        self.assertIn("No SPY option position may remain open past 3:45 PM ET", guardrails)

    def test_runbook_documents_safe_fixture_pipeline(self) -> None:
        runbook = (PROJECT_ROOT / "docs" / "RUNBOOK.md").read_text(encoding="utf-8")
        self.assertIn("python scripts\\run_fixture_pipeline.py", runbook)
        self.assertIn("gate must remain blocked", runbook)
        self.assertIn("Do not write real secrets", runbook)

    def test_env_example_contains_no_secret_values(self) -> None:
        env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertIn("IBKR_TRANSMIT_ENABLED=false", env_example)
        self.assertIn("OPENROUTER_DEEPSEEK_MODEL_ID=deepseek/deepseek-v4-flash", env_example)
        self.assertNotIn("<local secret>", env_example)
        self.assertNotIn("<confirm-openrouter-model-id>", env_example)
        self.assertNotIn("sk-", env_example)


if __name__ == "__main__":
    unittest.main()
