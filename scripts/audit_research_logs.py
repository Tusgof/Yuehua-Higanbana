from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESEARCH_LOG_ROOT = PROJECT_ROOT / "research_log"
DEFAULT_EXPERIMENT_ROOT = PROJECT_ROOT / "reports"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "research_log_audit.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "research_log_audit.md"
EXPECTED_REMOTE = "https://github.com/Tusgof/Yuehua-Higanbana.git"
QUICK_READ_HEADINGS = ("### อ่านแบบเร็ว", "### เธญเนเธฒเธเนเธเธเน€เธฃเนเธง")
LOG_FILENAME_RE = re.compile(r"^\d{3}-higanbana-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
MOJIBAKE_MARKERS = ("เธ", "เน€", "เน", "เน", "โ€", "�")
LEGACY_DIRECTORY_NAME = "legacy_format"
RESEARCH_FORMAT_V2_HEADINGS = (
    "## 1. ข้อมูลพื้นฐาน",
    "## 2. ปัญหา (คำถาม) และสมมติฐาน",
    "## 3. ขั้นตอนการทดลอง",
    "## 4. ผลลัพธ์",
    "## 5. อภิปรายผล ปัญหา และข้อจำกัด",
    "## 6. สรุปผลการทดลองและแนวทางพัฒนาต่อ",
)
RESEARCH_FORMAT_V2_REQUIRED_LABELS = ("คำถามวิจัย:", "ขอบเขต:", "สมมติฐาน:")
RESEARCH_QUESTION_MAX_LENGTH = 300


GitRunner = Callable[[Path, list[str]], str]


def audit_research_logs(
    research_log_root: Path = DEFAULT_RESEARCH_LOG_ROOT,
    experiment_root: Path = DEFAULT_EXPERIMENT_ROOT,
    expected_remote: str = EXPECTED_REMOTE,
    git_runner: GitRunner | None = None,
) -> dict[str, Any]:
    required_logs = _required_completed_experiment_logs(experiment_root, research_log_root)
    missing_logs = [item for item in required_logs if not item["present"]]
    naming_issues = _research_log_naming_issues(research_log_root)
    readability_issues = _research_log_readability_issues(research_log_root)
    sequence_status = _research_log_sequence_status(research_log_root)
    git_status = _git_status(research_log_root, expected_remote, git_runner or _run_git)
    blockers = [f"missing_research_log:{item['summary_id']}" for item in missing_logs]
    blockers.extend(f"invalid_research_log_filename:{name}" for name in naming_issues)
    blockers.extend(f"research_log_readability_issue:{item['name']}:{item['issue']}" for item in readability_issues)
    blockers.extend(sequence_status["blockers"])
    blockers.extend(git_status["blockers"])

    return {
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "research_log_root": str(research_log_root),
        "experiment_root": str(experiment_root),
        "naming_convention": "NNN-higanbana-clear-topic-slug.md",
        "invalid_log_filenames": naming_issues,
        "readability_issues": readability_issues,
        "sequence": sequence_status,
        "required_logs": required_logs,
        "git": git_status,
    }


def write_reports(result: dict[str, Any], json_output: Path = DEFAULT_JSON_OUTPUT, report_output: Path = DEFAULT_REPORT_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Research Log Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Blocker count: {len(result['blockers'])}",
        f"- Research log root: `{result['research_log_root']}`",
        f"- Naming convention: `{result['naming_convention']}`",
        "",
        "## Required Logs",
        "",
        "| Summary | Log pattern | Present |",
        "|:--|:--|:--:|",
    ]
    for item in result["required_logs"]:
        lines.append(f"| `{item['summary_id']}` | `{item['expected_pattern']}` | {item['present']} |")

    lines.extend(
        [
            "",
            "## Filename Issues",
            "",
        ]
    )
    if result["invalid_log_filenames"]:
        lines.extend(f"- `{name}`" for name in result["invalid_log_filenames"])
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Readability Issues",
            "",
        ]
    )
    if result["readability_issues"]:
        lines.extend(f"- `{item['name']}`: `{item['issue']}`" for item in result["readability_issues"])
    else:
        lines.append("- None")

    sequence = result["sequence"]
    lines.extend(
        [
            "",
            "## Sequence",
            "",
            f"- Existing log count: {sequence['existing_log_count']}",
            f"- Next log number: `{sequence['next_log_number']}`",
            f"- Next filename prefix: `{sequence['next_filename_prefix']}`",
            f"- Contiguous from 001: `{sequence['contiguous_from_001']}`",
        ]
    )
    if sequence["sequence_issues"]:
        lines.extend(f"- `{issue}`" for issue in sequence["sequence_issues"])
    else:
        lines.append("- Sequence issues: None")

    git_status = result["git"]
    lines.extend(
        [
            "",
            "## Git",
            "",
            f"- Is git repo: `{git_status['is_repo']}`",
            f"- Remote matches expected: `{git_status['remote_matches_expected']}`",
            f"- Nested research-log repo present: `{git_status['nested_repo_present']}`",
            f"- Tracked log count: `{git_status['tracked_log_count']}`",
            f"- Current-format log count: `{git_status['current_log_count']}`",
            f"- Legacy-format log count: `{git_status['legacy_log_count']}`",
            f"- Untracked logs: `{git_status['untracked_logs']}`",
        ]
    )
    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _required_completed_experiment_logs(experiment_root: Path, research_log_root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not experiment_root.exists():
        return items
    for path in sorted(experiment_root.glob("**/*.json")):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            continue
        if payload.get("research_log_required") is not True:
            continue
        slug = payload.get("research_log_slug")
        if not slug:
            raise ValueError(f"{path} sets research_log_required=true but lacks research_log_slug")
        pattern = f"???-{str(slug).replace('_', '-')}*.md"
        matches = sorted(research_log_root.glob(pattern)) if research_log_root.exists() else []
        legacy_root = research_log_root / LEGACY_DIRECTORY_NAME
        if legacy_root.exists():
            matches.extend(sorted(legacy_root.glob(pattern)))
        items.append(
            {
                "summary_id": path.stem,
                "summary_path": _relative(path),
                "expected_pattern": pattern,
                "present": bool(matches),
                "matched_logs": [_relative(match) for match in matches],
            }
        )
    return items


def _research_log_naming_issues(research_log_root: Path) -> list[str]:
    if not research_log_root.exists():
        return []
    return sorted(path.name for path in research_log_root.glob("*.md") if not LOG_FILENAME_RE.match(path.name))


def _research_log_readability_issues(research_log_root: Path) -> list[dict[str, str]]:
    if not research_log_root.exists():
        return []
    issues: list[dict[str, str]] = []
    for path in sorted(research_log_root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not any(heading in text for heading in QUICK_READ_HEADINGS):
            issues.append({"name": path.name, "issue": "missing_quick_read_section"})
        for marker in MOJIBAKE_MARKERS:
            if marker in text:
                issues.append({"name": path.name, "issue": f"mojibake_marker:{marker}"})
                break
        stripped_lines = tuple(line.strip() for line in text.splitlines())
        headings = tuple(line.strip() for line in text.splitlines() if line.startswith("## "))
        if headings != RESEARCH_FORMAT_V2_HEADINGS:
            issues.append({"name": path.name, "issue": "research_format_v2_section_mismatch"})
        for label in RESEARCH_FORMAT_V2_REQUIRED_LABELS:
            matching_lines = [line for line in stripped_lines if line.startswith(label)]
            if not matching_lines:
                issues.append({"name": path.name, "issue": f"research_format_v2_missing_label:{label}"})
            elif not matching_lines[0][len(label):].strip():
                issues.append({"name": path.name, "issue": f"research_format_v2_empty_label:{label}"})
        question_lines = [line for line in stripped_lines if line.startswith("คำถามวิจัย:")]
        if question_lines:
            question = question_lines[0].removeprefix("คำถามวิจัย:").strip()
            if len(question) > RESEARCH_QUESTION_MAX_LENGTH:
                issues.append({"name": path.name, "issue": "research_format_v2_question_too_long"})
    return issues


def _research_log_sequence_status(research_log_root: Path) -> dict[str, Any]:
    log_names = sorted(path.name for path in research_log_root.glob("*.md")) if research_log_root.exists() else []
    valid_numbers = sorted(
        int(name.split("-", 1)[0])
        for name in log_names
        if LOG_FILENAME_RE.match(name)
    )
    expected_numbers = list(range(1, len(valid_numbers) + 1))
    missing_numbers = [number for number in expected_numbers if number not in valid_numbers]
    out_of_sequence_numbers = [number for number in valid_numbers if number not in expected_numbers]
    issues = []
    issues.extend(f"missing_research_log_number:{number:03d}" for number in missing_numbers)
    issues.extend(f"out_of_sequence_research_log_number:{number:03d}" for number in out_of_sequence_numbers)
    next_number = len(valid_numbers) + 1 if not issues else None
    return {
        "existing_log_count": len(valid_numbers),
        "valid_log_numbers": [f"{number:03d}" for number in valid_numbers],
        "contiguous_from_001": not issues,
        "next_log_number": f"{next_number:03d}" if next_number is not None else None,
        "next_filename_prefix": f"{next_number:03d}-higanbana-" if next_number is not None else None,
        "sequence_issues": issues,
        "blockers": issues,
    }


def _git_status(root: Path, expected_remote: str, run_git: GitRunner) -> dict[str, Any]:
    repo_root = root.parent
    try:
        remote_output = run_git(repo_root, ["remote", "-v"])
        tracked_output = run_git(repo_root, ["ls-files", "--", "research_log"])
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        return {
            "is_repo": False,
            "remote_matches_expected": False,
            "nested_repo_present": (root / ".git").exists(),
            "tracked_log_count": 0,
            "current_log_count": 0,
            "legacy_log_count": 0,
            "untracked_logs": [],
            "blockers": [f"research_log_git_unavailable:{type(exc).__name__}"],
        }

    log_paths = sorted(path for path in root.glob("*.md")) if root.exists() else []
    legacy_paths = sorted(path for path in (root / LEGACY_DIRECTORY_NAME).glob("*.md")) if root.exists() else []
    tracked_paths = {line.strip().replace("\\", "/") for line in tracked_output.splitlines() if line.strip()}
    untracked_logs = [
        path.name for path in log_paths if f"research_log/{path.name}" not in tracked_paths
    ]
    nested_repo_present = (root / ".git").exists()
    remote_matches = expected_remote in remote_output
    blockers = []
    if nested_repo_present:
        blockers.append("research_log_nested_git_repo_present")
    blockers.extend(f"research_log_not_tracked_by_main_repo:{name}" for name in untracked_logs)
    if not remote_matches:
        blockers.append("research_log_remote_mismatch")
    return {
        "is_repo": True,
        "remote_matches_expected": remote_matches,
        "nested_repo_present": nested_repo_present,
        "tracked_log_count": len([path for path in tracked_paths if path.endswith(".md")]),
        "current_log_count": len(log_paths),
        "legacy_log_count": len(legacy_paths),
        "untracked_logs": untracked_logs,
        "blockers": blockers,
    }


def _run_git(cwd: Path, args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit completed experiment research logs in the main Higanbana repository.")
    parser.add_argument("--research-log-root", type=Path, default=DEFAULT_RESEARCH_LOG_ROOT)
    parser.add_argument("--experiment-root", type=Path, default=DEFAULT_EXPERIMENT_ROOT)
    parser.add_argument("--expected-remote", default=EXPECTED_REMOTE)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = audit_research_logs(args.research_log_root, args.experiment_root, args.expected_remote)
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
