from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import interpreter_metadata, wiki_root
from lib.integrity import sha256_file
from lib.io import load_json, relative_to_root, write_json


DEFAULT_EXPERIMENT_ROOT = PROJECT_ROOT / "experiments"
DEFAULT_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "wiki_citation_hash_audit.json"


def _walk_values(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for item in value.values():
            found.extend(_walk_values(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_walk_values(item))
    elif isinstance(value, str):
        if "wiki/" in value or value.endswith(".md") and ("minimum-track" in value or "sharpe" in value):
            found.append(value)
    return found


def _wiki_relative_path(value: str) -> str | None:
    normalized = value.replace("\\", "/")
    if "wiki/" in normalized:
        return normalized.split("wiki/", 1)[1]
    if normalized.startswith(("concepts/", "sources/", "questions/")):
        return normalized
    return None


def audit_wiki_citation_hashes(
    experiment_root: Path = DEFAULT_EXPERIMENT_ROOT,
    output_path: Path = DEFAULT_OUTPUT,
    wiki_base: Path | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    base = wiki_base or wiki_root()
    citations: list[dict[str, Any]] = []
    for path in sorted(experiment_root.glob("*.json")):
        try:
            payload = load_json(path)
        except Exception as exc:  # noqa: BLE001
            citations.append(
                {
                    "experiment_path": relative_to_root(path, PROJECT_ROOT),
                    "status": "blocked_json_read_error",
                    "error": type(exc).__name__,
                }
            )
            continue
        embedded_hashes = payload.get("wiki_citation_hashes", {}) if isinstance(payload, dict) else {}
        if not isinstance(embedded_hashes, dict):
            embedded_hashes = {}
        for raw in sorted(set(_walk_values(payload))):
            relative = _wiki_relative_path(raw)
            if relative is None:
                continue
            wiki_path = base / relative
            actual_hash = sha256_file(wiki_path) if wiki_path.exists() else None
            embedded_hash = embedded_hashes.get(relative)
            status = "missing_file"
            if actual_hash is not None and embedded_hash == actual_hash:
                status = "hash_recorded"
            elif actual_hash is not None and embedded_hash:
                status = "hash_mismatch"
            elif actual_hash is not None:
                status = "hash_missing"
            citations.append(
                {
                    "experiment_path": relative_to_root(path, PROJECT_ROOT),
                    "wiki_relative_path": relative,
                    "status": status,
                    "actual_sha256": actual_hash,
                    "embedded_sha256": embedded_hash,
                }
            )

    blockers = [
        f"{item['status']}:{item.get('experiment_path')}:{item.get('wiki_relative_path')}"
        for item in citations
        if item.get("status") in {"missing_file", "hash_mismatch"}
    ]
    report: dict[str, Any] = {
        "audit_id": "wiki_citation_hash_audit",
        "status": "blocked" if blockers else "pass_with_missing_hashes",
        "blockers": blockers,
        "citation_count": len(citations),
        "hash_missing_count": sum(1 for item in citations if item.get("status") == "hash_missing"),
        "hash_recorded_count": sum(1 for item in citations if item.get("status") == "hash_recorded"),
        "wiki_root": str(base),
        "citations": citations,
        "interpreter": interpreter_metadata(),
    }
    if write_report:
        write_json(output_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit wiki citation content hashes in experiment JSON files.")
    parser.add_argument("--experiment-root", type=Path, default=DEFAULT_EXPERIMENT_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = audit_wiki_citation_hashes(args.experiment_root, args.output, write_report=True)
    print(
        f"{report['status']}: {report['citation_count']} citations, "
        f"{report['hash_missing_count']} missing hashes"
    )
    return 0 if report["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
