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
DEFAULT_ACTIVE_REGISTRY = PROJECT_ROOT / "experiments" / "active_wiki_citation_hashes.json"
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
        normalized = value.replace("\\", "/")
        if normalized.endswith(".md") and (
            "wiki/" in normalized
            or normalized.startswith(("concepts/", "sources/", "questions/"))
            or normalized.startswith("${HIGANBANA_WIKI_ROOT}/")
        ):
            found.append(value)
    return found


def _wiki_relative_path(value: str) -> str | None:
    normalized = value.replace("\\", "/")
    token_prefix = "${HIGANBANA_WIKI_ROOT}/"
    if normalized.startswith(token_prefix):
        return normalized[len(token_prefix) :]
    if "wiki/" in normalized:
        return normalized.split("wiki/", 1)[1]
    if normalized.startswith(("concepts/", "sources/", "questions/")):
        return normalized
    return None


def audit_wiki_citation_hashes(
    experiment_root: Path = DEFAULT_EXPERIMENT_ROOT,
    output_path: Path = DEFAULT_OUTPUT,
    wiki_base: Path | None = None,
    active_registry_path: Path | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    base = wiki_base or wiki_root()
    registry_path = active_registry_path
    if registry_path is None and experiment_root.resolve() == DEFAULT_EXPERIMENT_ROOT.resolve():
        registry_path = DEFAULT_ACTIVE_REGISTRY

    if registry_path is not None and registry_path.exists():
        report = _audit_active_registry(registry_path, base)
        if write_report:
            write_json(output_path, report)
        return report

    report = _audit_legacy_experiments(experiment_root, base)
    if write_report:
        write_json(output_path, report)
    return report


def _audit_active_registry(registry_path: Path, base: Path) -> dict[str, Any]:
    registry = load_json(registry_path)
    blockers: list[str] = []
    citations: list[dict[str, Any]] = []
    preregistrations = registry.get("preregistrations", []) if isinstance(registry, dict) else []
    if not isinstance(preregistrations, list) or not preregistrations:
        blockers.append("active_wiki_citation_registry_empty")
        preregistrations = []

    for entry in preregistrations:
        artifact_relative = str(entry.get("artifact_path", ""))
        artifact_path = PROJECT_ROOT / artifact_relative
        expected_artifact_hash = str(entry.get("artifact_sha256", ""))
        if not artifact_path.exists():
            blockers.append(f"active_preregistration_missing:{artifact_relative}")
            continue
        actual_artifact_hash = sha256_file(artifact_path)
        if actual_artifact_hash != expected_artifact_hash:
            blockers.append(f"active_preregistration_hash_mismatch:{artifact_relative}")
        try:
            payload = load_json(artifact_path)
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"active_preregistration_json_error:{artifact_relative}:{type(exc).__name__}")
            continue

        references = {
            relative
            for raw in _walk_values(payload)
            if (relative := _wiki_relative_path(raw)) is not None
        }
        recorded_hashes = entry.get("wiki_citation_hashes", {})
        if not isinstance(recorded_hashes, dict):
            blockers.append(f"wiki_citation_hashes_must_be_object:{artifact_relative}")
            recorded_hashes = {}
        for relative in sorted(references | set(recorded_hashes)):
            wiki_path = base / relative
            expected_wiki_sha256 = recorded_hashes.get(relative)
            actual_wiki_sha256 = sha256_file(wiki_path) if wiki_path.exists() else None
            status = "pass"
            if relative not in references:
                status = "registry_reference_not_in_artifact"
            elif not expected_wiki_sha256:
                status = "wiki_sha256_missing"
            elif actual_wiki_sha256 is None:
                status = "wiki_file_missing"
            elif actual_wiki_sha256 != expected_wiki_sha256:
                status = "wiki_sha256_mismatch"
            if status != "pass":
                blockers.append(f"{status}:{artifact_relative}:{relative}")
            citations.append(
                {
                    "experiment_path": artifact_relative,
                    "artifact_expected_sha256": expected_artifact_hash,
                    "artifact_actual_sha256": actual_artifact_hash,
                    "wiki_relative_path": relative,
                    "wiki_sha256_expected": expected_wiki_sha256,
                    "wiki_sha256_actual": actual_wiki_sha256,
                    "status": status,
                }
            )

    return {
        "audit_id": "wiki_citation_hash_audit",
        "schema_version": "active_wiki_citation_hash_audit_v1",
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "active_registry_path": relative_to_root(registry_path, PROJECT_ROOT),
        "active_preregistration_count": len(preregistrations),
        "citation_count": len(citations),
        "hash_missing_count": sum(1 for item in citations if item["status"] == "wiki_sha256_missing"),
        "hash_recorded_count": sum(1 for item in citations if item["status"] == "pass"),
        "wiki_root": str(base),
        "citations": citations,
        "interpreter": interpreter_metadata(),
    }


def _audit_legacy_experiments(experiment_root: Path, base: Path) -> dict[str, Any]:
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
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit wiki citation content hashes in experiment JSON files.")
    parser.add_argument("--experiment-root", type=Path, default=DEFAULT_EXPERIMENT_ROOT)
    parser.add_argument("--active-registry", type=Path, default=DEFAULT_ACTIVE_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = audit_wiki_citation_hashes(
        args.experiment_root,
        args.output,
        active_registry_path=args.active_registry,
        write_report=True,
    )
    print(
        f"{report['status']}: {report['citation_count']} citations, "
        f"{report['hash_missing_count']} missing hashes"
    )
    return 0 if report["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
