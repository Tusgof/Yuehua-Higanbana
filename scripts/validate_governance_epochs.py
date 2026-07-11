from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import load_json, relative_to_root, write_json


DEFAULT_MANIFEST = PROJECT_ROOT / "config" / "governance_epochs.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "governance_epochs_validation.json"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_FIELDS = {"epoch_id", "date", "status", "kind", "description", "evidence_paths"}
TAG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def validate_governance_epochs(manifest_path: Path = DEFAULT_MANIFEST, output_path: Path = DEFAULT_OUTPUT, write_report: bool = True) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    blockers: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    epochs = manifest.get("epochs")
    if not isinstance(epochs, list) or not epochs:
        blockers.append("epochs must be a non-empty list")
        epochs = []

    rows = []
    for index, epoch in enumerate(epochs):
        row_blockers: list[str] = []
        if not isinstance(epoch, dict):
            blockers.append(f"epoch[{index}] must be object")
            continue
        missing = sorted(REQUIRED_FIELDS - set(epoch))
        row_blockers.extend(f"missing_field:{field}" for field in missing)

        epoch_id = epoch.get("epoch_id")
        if not isinstance(epoch_id, str) or not epoch_id.strip():
            row_blockers.append("epoch_id must be non-empty string")
            epoch_id = f"epoch[{index}]"
        elif epoch_id in seen_ids:
            row_blockers.append(f"duplicate_epoch_id:{epoch_id}")
        seen_ids.add(str(epoch_id))

        date = epoch.get("date")
        if not isinstance(date, str) or not DATE_RE.match(date):
            row_blockers.append("date must use YYYY-MM-DD")

        git_tag = epoch.get("git_tag")
        if git_tag is not None and (not isinstance(git_tag, str) or not TAG_RE.match(git_tag)):
            row_blockers.append("git_tag must be a valid lowercase tag name")

        evidence_paths = epoch.get("evidence_paths")
        existing_paths: list[str] = []
        if not isinstance(evidence_paths, list) or not evidence_paths:
            row_blockers.append("evidence_paths must be non-empty list")
            evidence_paths = []
        for raw_path in evidence_paths:
            if not isinstance(raw_path, str) or not raw_path.strip():
                row_blockers.append("evidence_path must be non-empty string")
                continue
            path = PROJECT_ROOT / raw_path
            if path.exists():
                existing_paths.append(relative_to_root(path, PROJECT_ROOT))
            else:
                row_blockers.append(f"missing_evidence_path:{raw_path}")

        rows.append(
            {
                "epoch_id": epoch_id,
                "status": epoch.get("status"),
                "kind": epoch.get("kind"),
                "git_tag": git_tag,
                "blockers": row_blockers,
                "existing_evidence_paths": existing_paths,
            }
        )
        blockers.extend(f"{epoch_id}:{item}" for item in row_blockers)

    if "technical-dd-remediation-2026-07-09" not in seen_ids:
        blockers.append("missing_required_epoch:technical-dd-remediation-2026-07-09")
    if "gamma-policy-v2" not in seen_ids:
        warnings.append("missing_recommended_epoch:gamma-policy-v2")
    technical_dd = next((item for item in epochs if item.get("epoch_id") == "technical-dd-remediation-2026-07-09"), {})
    if not technical_dd.get("git_tag"):
        blockers.append("technical_dd_epoch_missing_git_tag")

    report: dict[str, Any] = {
        "schema_version": "governance_epochs_validation_v1",
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "warnings": warnings,
        "epoch_count": len(rows),
        "rows": rows,
        "source_path": relative_to_root(manifest_path, PROJECT_ROOT),
    }
    if write_report:
        write_json(output_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Higanbana governance epoch manifest.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = validate_governance_epochs(args.manifest, args.output, write_report=True)
    print(f"{report['status']}: {report['epoch_count']} governance epochs")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
