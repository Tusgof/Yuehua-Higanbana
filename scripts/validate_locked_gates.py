from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.integrity import sha256_file
from lib.io import load_jsonl, relative_to_root


DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "experiments" / "locked_gates.jsonl"
MINIMUM_LOCKED_GATE_ENTRIES = 4


def _resolve(relative_path: str) -> Path:
    return PROJECT_ROOT / relative_path


def validate_locked_gates(manifest_path: Path = DEFAULT_MANIFEST_PATH, *, minimum_entries: int | None = None) -> dict[str, Any]:
    blockers: list[str] = []
    entries = load_jsonl(manifest_path) if manifest_path.exists() else []
    seen_gate_ids: set[str] = set()
    entries_by_gate_id: dict[str, dict[str, Any]] = {}
    superseded_by: dict[str, str] = {}
    checked: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        gate_id = str(entry.get("gate_id", ""))
        if not gate_id:
            blockers.append(f"entry_{index}_missing_gate_id")
        elif gate_id in seen_gate_ids:
            blockers.append(f"duplicate_gate_id:{gate_id}")
        seen_gate_ids.add(gate_id)

        if not entry.get("human_approval"):
            blockers.append(f"missing_human_approval:{gate_id or index}")

        supersedes_gate_id = entry.get("supersedes_gate_id")
        if supersedes_gate_id is not None:
            supersedes_gate_id = str(supersedes_gate_id)
            predecessor = entries_by_gate_id.get(supersedes_gate_id)
            if not predecessor:
                blockers.append(f"unknown_or_nonprior_superseded_gate:{gate_id}:{supersedes_gate_id}")
            else:
                if supersedes_gate_id in superseded_by:
                    blockers.append(f"multiple_supersessions:{supersedes_gate_id}")
                if entry.get("artifact_path") != predecessor.get("artifact_path"):
                    blockers.append(f"supersession_artifact_path_changed:{gate_id}")
                if entry.get("validator_path") != predecessor.get("validator_path"):
                    blockers.append(f"supersession_validator_path_changed:{gate_id}")
                if not entry.get("reviewed_by"):
                    blockers.append(f"missing_reviewer:{gate_id}")
                superseded_by[supersedes_gate_id] = gate_id

        entries_by_gate_id[gate_id] = entry

    for entry in entries:
        gate_id = str(entry.get("gate_id", ""))
        if gate_id in superseded_by:
            checked.append(
                {
                    "gate_id": gate_id,
                    "status": "superseded",
                    "superseded_by": superseded_by[gate_id],
                }
            )
            continue

        artifact_path = _resolve(str(entry.get("artifact_path", "")))
        validator_path = _resolve(str(entry.get("validator_path", "")))
        artifact_expected = entry.get("artifact_sha256")
        validator_expected = entry.get("validator_sha256")

        artifact_status = "missing"
        validator_status = "missing"
        artifact_actual = None
        validator_actual = None
        if artifact_path.exists():
            artifact_actual = sha256_file(artifact_path)
            artifact_status = "pass" if artifact_actual == artifact_expected else "hash_mismatch"
        if validator_path.exists():
            validator_actual = sha256_file(validator_path)
            validator_status = "pass" if validator_actual == validator_expected else "hash_mismatch"

        if artifact_status != "pass":
            blockers.append(f"artifact_{artifact_status}:{gate_id}:{entry.get('artifact_path')}")
        if validator_status != "pass":
            blockers.append(f"validator_{validator_status}:{gate_id}:{entry.get('validator_path')}")

        checked.append(
            {
                "gate_id": gate_id,
                "artifact_path": relative_to_root(artifact_path, PROJECT_ROOT),
                "artifact_status": artifact_status,
                "artifact_actual_sha256": artifact_actual,
                "validator_path": relative_to_root(validator_path, PROJECT_ROOT),
                "validator_status": validator_status,
                "validator_actual_sha256": validator_actual,
            }
        )

    if not entries:
        blockers.append("locked_gate_manifest_empty")
    else:
        required_minimum = (
            MINIMUM_LOCKED_GATE_ENTRIES
            if minimum_entries is None and manifest_path.resolve() == DEFAULT_MANIFEST_PATH.resolve()
            else minimum_entries or 0
        )
        if len(entries) < required_minimum:
            blockers.append(f"locked_gate_manifest_below_minimum:{len(entries)}<{required_minimum}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "manifest_path": relative_to_root(manifest_path, PROJECT_ROOT),
        "entry_count": len(entries),
        "checked": checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate append-only locked gate hash manifest.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    args = parser.parse_args()
    result = validate_locked_gates(args.manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
