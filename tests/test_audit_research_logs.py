from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_research_logs.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("audit_research_logs", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load research log auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditResearchLogsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = load_auditor()

    def test_current_research_logs_are_present_and_pushed(self) -> None:
        result = self.auditor.audit_research_logs()

        self.assertEqual("pass", result["status"])
        self.assertEqual(11, len(result["required_logs"]))
        summary_ids = {item["summary_id"] for item in result["required_logs"]}
        self.assertIn("subsystem_a_orb_baseline_summary", summary_ids)
        self.assertIn("subsystem_b_put_ratio_feasibility_summary", summary_ids)
        self.assertIn("m4_exit_behavior_diagnostic_summary", summary_ids)
        self.assertIn("h_a2_macro_conditioned_reanalysis_summary", summary_ids)
        self.assertIn("m5_transaction_cost_latency_sensitivity_summary", summary_ids)
        self.assertIn("m5_strike_selection_sensitivity_summary", summary_ids)
        self.assertIn("m5_entry_timing_sensitivity_summary", summary_ids)
        self.assertIn("m5_exit_target_stop_sensitivity_summary", summary_ids)
        self.assertIn("m5_regime_filter_sensitivity_summary", summary_ids)
        self.assertIn("m5_portfolio_construction_diagnostic_summary", summary_ids)
        self.assertIn("m5_structural_break_assessment_summary", summary_ids)
        self.assertTrue(all(item["present"] for item in result["required_logs"]))
        self.assertEqual("012", result["sequence"]["next_log_number"])
        self.assertEqual("012-higanbana-", result["sequence"]["next_filename_prefix"])
        self.assertTrue(result["git"]["clean"])
        self.assertTrue(result["git"]["remote_matches_expected"])
        self.assertEqual(result["git"]["local_head"], result["git"]["remote_head"])

    def test_missing_log_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()
            (experiment_root / "exp01_real_summary.json").write_text(
                json.dumps({"research_log_required": True, "research_log_slug": "higanbana_exp01_real"}),
                encoding="utf-8",
            )

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_research_log:exp01_real_summary", result["blockers"])

    def test_legacy_live_prompt_summary_does_not_require_research_log_without_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()
            (experiment_root / "exp07_prompt_v12_summary.json").write_text(
                json.dumps({"mode": "live_openrouter", "case_count": 43}),
                encoding="utf-8",
            )

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["required_logs"])

    def test_completed_experiment_log_passes_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()
            (experiment_root / "exp01_real_summary.json").write_text(
                json.dumps({"research_log_required": True, "research_log_slug": "higanbana_exp01_real"}),
                encoding="utf-8",
            )
            (log_root / "001-higanbana-exp01-real-baseline.md").write_text("log", encoding="utf-8")

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertEqual("pass", result["status"])
        self.assertEqual(1, len(result["required_logs"]))
        self.assertTrue(result["required_logs"][0]["present"])
        self.assertEqual("002", result["sequence"]["next_log_number"])
        self.assertEqual("002-higanbana-", result["sequence"]["next_filename_prefix"])

    def test_nested_completed_summary_requires_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "reports"
            nested_root = experiment_root / "baselines"
            log_root = root / "research_log"
            nested_root.mkdir(parents=True)
            log_root.mkdir()
            (nested_root / "subsystem_a_orb_baseline_summary.json").write_text(
                json.dumps({"research_log_required": True, "research_log_slug": "higanbana_orb_baseline_real_data"}),
                encoding="utf-8",
            )

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_research_log:subsystem_a_orb_baseline_summary", result["blockers"])

    def test_empty_research_log_directory_starts_at_001(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertEqual("pass", result["status"])
        self.assertEqual("001", result["sequence"]["next_log_number"])
        self.assertEqual("001-higanbana-", result["sequence"]["next_filename_prefix"])

    def test_missing_sequence_number_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()
            (log_root / "001-higanbana-orb-baseline-real-data.md").write_text("log", encoding="utf-8")
            (log_root / "003-higanbana-cost-sensitivity-real-data.md").write_text("log", encoding="utf-8")

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_research_log_number:002", result["blockers"])

    def test_unpushed_log_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()
            (experiment_root / "exp01_real_summary.json").write_text(
                json.dumps({"research_log_required": True, "research_log_slug": "higanbana_exp01_real"}),
                encoding="utf-8",
            )
            (log_root / "001-higanbana-exp01-real-baseline.md").write_text("log", encoding="utf-8")

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.unpushed_git_runner(),
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("research_log_not_pushed", result["blockers"])

    def test_legacy_filename_blocks_even_when_log_matches_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()
            (experiment_root / "exp01_real_summary.json").write_text(
                json.dumps({"research_log_required": True, "research_log_slug": "higanbana_exp01_real"}),
                encoding="utf-8",
            )
            (log_root / "2026-06-30_higanbana_exp01_real.md").write_text("log", encoding="utf-8")

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("invalid_research_log_filename:2026-06-30_higanbana_exp01_real.md", result["blockers"])

    @staticmethod
    def clean_git_runner():
        def run_git(cwd: Path, args: list[str]) -> str:
            command = " ".join(args)
            if command == "status --porcelain":
                return ""
            if command == "remote -v":
                return "origin\thttps://github.com/Tusgof/Yuehua_Research_log (fetch)\n"
            if command == "rev-parse HEAD":
                return "abc123\n"
            if command == "ls-remote origin HEAD":
                return "abc123\tHEAD\n"
            raise AssertionError(args)

        return run_git

    @staticmethod
    def unpushed_git_runner():
        def run_git(cwd: Path, args: list[str]) -> str:
            command = " ".join(args)
            if command == "status --porcelain":
                return ""
            if command == "remote -v":
                return "origin\thttps://github.com/Tusgof/Yuehua_Research_log (fetch)\n"
            if command == "rev-parse HEAD":
                return "local\n"
            if command == "ls-remote origin HEAD":
                return "remote\tHEAD\n"
            raise AssertionError(args)

        return run_git


if __name__ == "__main__":
    unittest.main()
