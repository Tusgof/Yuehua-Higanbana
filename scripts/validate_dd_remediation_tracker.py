from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import load_json
DEFAULT_TRACKER = PROJECT_ROOT / "experiments" / "dd_remediation_tracker.json"
VALID_STATUSES = {"not_started", "in_progress", "done", "blocked"}
VALID_WORKSTREAMS = {"WS1", "WS2", "WS3", "WS4", "WS5"}
FORBIDDEN_ABSOLUTE_PATH = re.compile(r"(?i)\b[A-Z]:[/\\]Fogust\b")


def validate_tracker(path: Path = DEFAULT_TRACKER, *, run_expensive: bool = False) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        payload = load_json(path)
    except FileNotFoundError:
        blockers.append(f"tracker_missing:{path}")
        payload = None
    except json.JSONDecodeError as exc:
        blockers.append(f"tracker_invalid_json:{exc}")
        payload = None
    if payload is not None and not isinstance(payload, dict):
        blockers.append(f"tracker_must_be_json_object:{path}")
        payload = None
    if payload is None:
        return _result("fail", path, blockers, [])

    workstreams = payload.get("workstreams")
    if not isinstance(workstreams, list):
        blockers.append("workstreams_must_be_list")
        return _result("fail", path, blockers, [])

    seen_ids: set[str] = set()
    done_artifacts_checked: list[dict[str, str]] = []
    for index, entry in enumerate(workstreams):
        if not isinstance(entry, dict):
            blockers.append(f"workstream_{index}_must_be_object")
            continue
        ws_id = str(entry.get("id", ""))
        if ws_id not in VALID_WORKSTREAMS:
            blockers.append(f"invalid_workstream_id:{ws_id or index}")
        if ws_id in seen_ids:
            blockers.append(f"duplicate_workstream_id:{ws_id}")
        seen_ids.add(ws_id)

        status = entry.get("status")
        if status not in VALID_STATUSES:
            blockers.append(f"{ws_id}:invalid_status:{status}")

        required_artifacts = entry.get("required_artifacts")
        if not isinstance(required_artifacts, list):
            blockers.append(f"{ws_id}:required_artifacts_must_be_list")
            continue
        for artifact in required_artifacts:
            if not isinstance(artifact, dict):
                blockers.append(f"{ws_id}:artifact_must_be_object")
                continue
            artifact_path = artifact.get("path")
            must = artifact.get("must")
            if not isinstance(artifact_path, str) or not artifact_path:
                blockers.append(f"{ws_id}:artifact_missing_path")
            if not isinstance(must, str) or not must:
                blockers.append(f"{ws_id}:artifact_missing_must")

        if status == "done":
            for artifact in required_artifacts:
                if not isinstance(artifact, dict):
                    continue
                artifact_path = str(artifact.get("path", ""))
                must = str(artifact.get("must", ""))
                artifact_blockers = _validate_done_artifact(ws_id, artifact_path, must, run_expensive=run_expensive)
                if artifact_blockers:
                    blockers.extend(artifact_blockers)
                else:
                    done_artifacts_checked.append({"workstream": ws_id, "path": artifact_path, "must": must})

    missing = VALID_WORKSTREAMS - seen_ids
    for ws_id in sorted(missing):
        blockers.append(f"missing_workstream:{ws_id}")

    return _result("fail" if blockers else "pass", path, blockers, done_artifacts_checked)


def _validate_done_artifact(ws_id: str, artifact_path: str, must: str, *, run_expensive: bool) -> list[str]:
    target = (PROJECT_ROOT / artifact_path).resolve()
    blockers: list[str] = []
    if must == "exist":
        if not target.exists():
            blockers.append(f"{ws_id}:missing_artifact:{artifact_path}")
    elif must in {"pass_in_hermetic_tier", "pass_hermetic_tier"}:
        if not target.exists():
            blockers.append(f"{ws_id}:missing_artifact:{artifact_path}")
        elif test_module := _test_module_from_path(artifact_path):
            completed = subprocess.run(
                [sys.executable, "-m", "unittest", test_module],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                blockers.append(f"{ws_id}:hermetic_test_failed:{artifact_path}")
        elif run_expensive:
            completed = subprocess.run(
                [sys.executable, "scripts/run_test_tier.py", "hermetic", "--verbosity", "0"],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                blockers.append(f"{ws_id}:hermetic_tier_failed:{artifact_path}")
        else:
            blockers.append(f"{ws_id}:requires_expensive_hermetic_run:{artifact_path}")
    elif must == "grep_no_forbidden_absolute_paths":
        blockers.extend(_grep_no_forbidden_absolute_paths(ws_id))
    elif must == "document_kurtosis_convention":
        if not target.exists():
            blockers.append(f"{ws_id}:missing_artifact:{artifact_path}")
        elif "kurtosis" not in target.read_text(encoding="utf-8", errors="ignore").lower():
            blockers.append(f"{ws_id}:missing_kurtosis_convention:{artifact_path}")
    elif must == "retention_policy_user_approved":
        if not target.exists():
            blockers.append(f"{ws_id}:missing_artifact:{artifact_path}")
        elif not re.search(r"(?im)^- \*\*User-approved\*\*:\s*`true`\s*$", target.read_text(encoding="utf-8")):
            blockers.append(f"{ws_id}:retention_policy_not_user_approved:{artifact_path}")
    elif must == "hermetic_lib_unit_tests_exist":
        if not _any_test_contains("lib."):
            blockers.append(f"{ws_id}:missing_hermetic_lib_unit_tests")
    elif must == "locked_gate_hash_meta_test_exists":
        if not _any_test_contains("locked_gates"):
            blockers.append(f"{ws_id}:missing_locked_gate_hash_meta_test")
    elif must == "governance_tag_exists":
        tags = subprocess.run(
            ["git", "tag", "--list", "technical-dd-remediation-*"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if tags.returncode != 0 or not tags.stdout.strip():
            blockers.append(f"{ws_id}:missing_governance_tag")
    elif must.startswith("contains:"):
        needle = must.split(":", 1)[1].lower()
        if not _path_contains(target, needle):
            blockers.append(f"{ws_id}:missing_text:{artifact_path}:{needle}")
    else:
        blockers.append(f"{ws_id}:unknown_artifact_rule:{must}")
    return blockers


def _test_module_from_path(artifact_path: str) -> str | None:
    path = Path(artifact_path)
    if path.parts[:1] != ("tests",) or path.suffix != ".py" or not path.name.startswith("test_"):
        return None
    return ".".join(path.with_suffix("").parts)


def _grep_no_forbidden_absolute_paths(ws_id: str) -> list[str]:
    roots = [PROJECT_ROOT / "scripts", PROJECT_ROOT / "tests", PROJECT_ROOT / "experiments"]
    offenders: list[str] = []
    for root in roots:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".json", ".jsonl", ".md"}:
                text = path.read_text(encoding="utf-8", errors="ignore")
                if FORBIDDEN_ABSOLUTE_PATH.search(text):
                    offenders.append(str(path.relative_to(PROJECT_ROOT)))
    return [f"{ws_id}:forbidden_absolute_path:{path}" for path in offenders]


def _any_test_contains(needle: str) -> bool:
    tests = PROJECT_ROOT / "tests"
    if not tests.exists():
        return False
    needle_lower = needle.lower()
    for path in tests.rglob("test_*.py"):
        if needle_lower in path.read_text(encoding="utf-8", errors="ignore").lower():
            return True
    return False


def _path_contains(path: Path, needle: str) -> bool:
    if path.is_file():
        return needle in path.read_text(encoding="utf-8", errors="ignore").lower()
    if path.is_dir():
        for child in path.rglob("*"):
            if child.is_file() and child.suffix in {".py", ".json", ".jsonl", ".md"}:
                if needle in child.read_text(encoding="utf-8", errors="ignore").lower():
                    return True
    return False


def _result(status: str, path: Path, blockers: list[str], done_artifacts_checked: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "status": status,
        "tracker_path": str(path),
        "blockers": blockers,
        "done_artifacts_checked": done_artifacts_checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the DD remediation tracker and all done claims.")
    parser.add_argument("--tracker", type=Path, default=DEFAULT_TRACKER)
    parser.add_argument("--run-expensive", action="store_true", help="Run expensive artifact checks such as the hermetic tier.")
    args = parser.parse_args()
    result = validate_tracker(args.tracker, run_expensive=args.run_expensive)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
