from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from tests.tiers import state_audit


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

    @state_audit(("research_log", PROJECT_ROOT / "research_log"))
    def test_current_research_logs_are_present_and_sequence_is_current(self) -> None:
        result = self.auditor.audit_research_logs()

        self.assertEqual("pass", result["status"])
        self.assertEqual(41, len(result["required_logs"]))
        summary_ids = {item["summary_id"] for item in result["required_logs"]}
        self.assertIn("subsystem_a_orb_baseline_summary", summary_ids)
        self.assertIn("subsystem_b_put_ratio_feasibility_summary", summary_ids)
        self.assertIn("m4_exit_behavior_diagnostic_summary", summary_ids)
        self.assertIn("h_a2_macro_conditioned_reanalysis_summary", summary_ids)
        self.assertIn("h_g1_gamma_regime_diagnostic_summary", summary_ids)
        self.assertIn("h_g1_gamma_regime_diagnostic_summary_v3", summary_ids)
        self.assertIn("h_g1_manifest_v3_bucket_failure_diagnostic", summary_ids)
        self.assertIn("h_g1_bucket_policy_comparison", summary_ids)
        self.assertIn("h_g1_gamma_strategy_ablation_summary", summary_ids)
        self.assertIn("h_a2_2022_10_coarse_stress_review", summary_ids)
        self.assertIn("h_a2_lower_resolution_proxy_summary", summary_ids)
        self.assertIn("h_a2_proxy_first_robustness_summary", summary_ids)
        self.assertIn("h_l1_macro_event_proxy_baseline_summary", summary_ids)
        self.assertIn("h_a2_residual_adverse_day_analysis", summary_ids)
        self.assertIn("h_a2_revised_opening_followthrough_condition_summary", summary_ids)
        self.assertIn("h_a2_locked_condition_signal_attribution_summary", summary_ids)
        self.assertIn("h_a2_delayed_entry_condition_summary", summary_ids)
        self.assertIn("h_a2_original_entry_revision_summary", summary_ids)
        self.assertIn("h_a2_original_entry_robustness_prioritization_summary", summary_ids)
        self.assertIn("h_a2_independent_validation_feasibility", summary_ids)
        self.assertIn("h_a2_independent_validation_import_diagnostic", summary_ids)
        self.assertIn("h_a2_normal_control_import_diagnostic", summary_ids)
        self.assertIn("h_a2_normal_control_exact_replay", summary_ids)
        self.assertIn("h_a2_post_stress_normalization_control_import_diagnostic", summary_ids)
        self.assertIn("h_a2_post_stress_normalization_control_exact_replay", summary_ids)
        self.assertIn("h_a2_mechanism_revision_audit", summary_ids)
        self.assertIn("h_a2_breakeven_aware_rule_train_diagnostic", summary_ids)
        self.assertIn("h_a2_2022_10_stress_exact_replay_summary", summary_ids)
        self.assertIn("h_b2_falsification_review", summary_ids)
        self.assertIn("m5_transaction_cost_latency_sensitivity_summary", summary_ids)
        self.assertIn("m5_strike_selection_sensitivity_summary", summary_ids)
        self.assertIn("m5_entry_timing_sensitivity_summary", summary_ids)
        self.assertIn("m5_exit_target_stop_sensitivity_summary", summary_ids)
        self.assertIn("m5_regime_filter_sensitivity_summary", summary_ids)
        self.assertIn("m5_portfolio_construction_diagnostic_summary", summary_ids)
        self.assertIn("m5_structural_break_assessment_summary", summary_ids)
        self.assertTrue(all(item["present"] for item in result["required_logs"]))
        self.assertEqual("042", result["sequence"]["next_log_number"])
        self.assertEqual("042-higanbana-", result["sequence"]["next_filename_prefix"])
        self.assertTrue(result["sequence"]["contiguous_from_001"])
        self.assertEqual([], result["git"]["blockers"])
        self.assertTrue(result["git"]["remote_matches_expected"])
        self.assertFalse(result["git"]["nested_repo_present"])
        self.assertEqual(41, result["git"]["tracked_log_count"])
        self.assertEqual([], result["git"]["untracked_logs"])

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
            (log_root / "001-higanbana-exp01-real-baseline.md").write_text(
                self.valid_log_text(),
                encoding="utf-8",
            )

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

    def test_completed_experiment_summary_with_utf8_bom_passes_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()
            (experiment_root / "exp01_real_summary.json").write_text(
                json.dumps({"research_log_required": True, "research_log_slug": "higanbana_exp01_real"}),
                encoding="utf-8-sig",
            )
            (log_root / "001-higanbana-exp01-real-baseline.md").write_text(
                self.valid_log_text(),
                encoding="utf-8",
            )

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertEqual("pass", result["status"])
        self.assertEqual(1, len(result["required_logs"]))

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
            (log_root / "001-higanbana-orb-baseline-real-data.md").write_text(
                self.valid_log_text(),
                encoding="utf-8",
            )
            (log_root / "003-higanbana-cost-sensitivity-real-data.md").write_text(
                self.valid_log_text(),
                encoding="utf-8",
            )

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_research_log_number:002", result["blockers"])

    def test_log_not_tracked_by_main_repo_blocks(self) -> None:
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
            (log_root / "001-higanbana-exp01-real-baseline.md").write_text(
                self.valid_log_text(),
                encoding="utf-8",
            )

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.untracked_git_runner(),
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn(
            "research_log_not_tracked_by_main_repo:001-higanbana-exp01-real-baseline.md",
            result["blockers"],
        )

    def test_nested_research_log_repo_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()
            (log_root / ".git").mkdir()

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("research_log_nested_git_repo_present", result["blockers"])

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
            (log_root / "2026-06-30_higanbana_exp01_real.md").write_text(
                self.valid_log_text(),
                encoding="utf-8",
            )

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("invalid_research_log_filename:2026-06-30_higanbana_exp01_real.md", result["blockers"])

    def test_missing_quick_read_section_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()
            (log_root / "001-higanbana-exp01-real-baseline.md").write_text(
                "# บันทึกการวิจัย: Test\n\n## 2. วัตถุประสงค์\n\nไม่มีสรุปอ่านเร็ว\n",
                encoding="utf-8",
            )

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn(
            "research_log_readability_issue:001-higanbana-exp01-real-baseline.md:missing_quick_read_section",
            result["blockers"],
        )

    def test_mojibake_marker_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()
            (log_root / "001-higanbana-exp01-real-baseline.md").write_text(
                self.valid_log_text() + "\nข้อความเพี้ยน: เธเธฑเธเธ—เธถเธ\n",
                encoding="utf-8",
            )

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn(
            "research_log_readability_issue:001-higanbana-exp01-real-baseline.md:mojibake_marker:เธ",
            result["blockers"],
        )

    def test_log_042_requires_new_research_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()
            (log_root / "042-higanbana-new-question.md").write_text(self.valid_log_text(), encoding="utf-8")

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        self.assertIn(
            "research_log_readability_issue:042-higanbana-new-question.md:research_format_v2_section_mismatch",
            result["blockers"],
        )

    def test_log_042_accepts_six_sections_and_research_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()
            (log_root / "042-higanbana-bounded-question.md").write_text(
                self.valid_v2_log_text(),
                encoding="utf-8",
            )

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        issues = [item["issue"] for item in result["readability_issues"]]
        self.assertNotIn("research_format_v2_section_mismatch", issues)
        self.assertFalse(any(issue.startswith("research_format_v2_missing_label:") for issue in issues))

    def test_log_042_rejects_empty_scope_and_overlong_question(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root = root / "experiments"
            log_root = root / "research_log"
            experiment_root.mkdir()
            log_root.mkdir()
            text = self.valid_v2_log_text().replace(
                "คำถามวิจัย: กฎที่กำหนดให้ผลตามเกณฑ์หรือไม่",
                f"คำถามวิจัย: {'ก' * 301}",
            ).replace("ขอบเขต: SPY ในข้อมูล OOS ที่ล็อกไว้", "ขอบเขต:")
            (log_root / "042-higanbana-unbounded-question.md").write_text(text, encoding="utf-8")

            result = self.auditor.audit_research_logs(
                log_root,
                experiment_root,
                git_runner=self.clean_git_runner(),
            )

        issues = [item["issue"] for item in result["readability_issues"]]
        self.assertIn("research_format_v2_empty_label:ขอบเขต:", issues)
        self.assertIn("research_format_v2_question_too_long", issues)

    @staticmethod
    def valid_log_text() -> str:
        return "# บันทึกการวิจัย: Test\n\n## 2. วัตถุประสงค์\n\n### อ่านแบบเร็ว\n\nอ่านง่าย\n"

    @staticmethod
    def valid_v2_log_text() -> str:
        return """# บันทึกการวิจัย: Test

## 1. ข้อมูลพื้นฐาน

### อ่านแบบเร็ว

สรุปแบบสั้น

## 2. ปัญหา (คำถาม) และสมมติฐาน

คำถามวิจัย: กฎที่กำหนดให้ผลตามเกณฑ์หรือไม่
ขอบเขต: SPY ในข้อมูล OOS ที่ล็อกไว้
สมมติฐาน: ผลหลังต้นทุนเป็นบวก

## 3. ขั้นตอนการทดลอง

1. ทดสอบตามกฎ

## 4. ผลลัพธ์

รายงานผล

## 5. อภิปรายผล ปัญหา และข้อจำกัด

อภิปรายข้อจำกัด

## 6. สรุปผลการทดลองและแนวทางพัฒนาต่อ

ข้อสรุป: ยังสรุปไม่ได้
"""

    @staticmethod
    def clean_git_runner():
        def run_git(cwd: Path, args: list[str]) -> str:
            command = " ".join(args)
            if command == "remote -v":
                return "origin\thttps://github.com/Tusgof/Yuehua-Higanbana.git (fetch)\n"
            if command == "ls-files -- research_log":
                log_root = cwd / "research_log"
                return "\n".join(f"research_log/{path.name}" for path in sorted(log_root.glob("*.md")))
            raise AssertionError(args)

        return run_git

    @staticmethod
    def untracked_git_runner():
        def run_git(cwd: Path, args: list[str]) -> str:
            command = " ".join(args)
            if command == "ls-files -- research_log":
                return ""
            return AuditResearchLogsTests.clean_git_runner()(cwd, args)

        return run_git


if __name__ == "__main__":
    unittest.main()
