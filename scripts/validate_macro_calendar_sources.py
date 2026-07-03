from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PLAN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "macro_calendar_sources_v1.json"
VALID_IMPORTANCE = {"high", "medium", "low"}
VALID_PARSER_STATUS = {"planned", "implemented", "deferred"}
VALID_CAPTURE_MODE = {"single_url", "bea_pce_release_pages"}


def load_source_plan(path: Path = DEFAULT_SOURCE_PLAN_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def validate_source_plan(path: Path = DEFAULT_SOURCE_PLAN_PATH) -> list[str]:
    plan = load_source_plan(path)
    errors: list[str] = []
    required_events = plan.get("minimum_required_event_types")
    sources = plan.get("sources")
    if not isinstance(required_events, list) or not required_events:
        errors.append("minimum_required_event_types must be a non-empty array")
        required_events = []
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty array")
        sources = []
    if plan.get("timezone") != "America/New_York":
        errors.append("timezone must be America/New_York")

    seen_source_ids: set[str] = set()
    covered_events: set[str] = set()
    for index, source in enumerate(sources):
        label = f"source[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label} must be an object")
            continue
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            errors.append(f"{label}.source_id is required")
        elif source_id in seen_source_ids:
            errors.append(f"{source_id}: duplicate source_id")
        else:
            seen_source_ids.add(source_id)
            label = source_id
        for field in ("provider", "source_url", "release_time_et", "license_notes"):
            if not isinstance(source.get(field), str) or not source[field]:
                errors.append(f"{label}.{field} is required")
        if isinstance(source.get("source_url"), str) and not source["source_url"].startswith("https://"):
            errors.append(f"{label}.source_url must be https")
        source_url_template = source.get("source_url_template")
        if source_url_template is not None:
            if not isinstance(source_url_template, str) or not source_url_template.startswith("https://"):
                errors.append(f"{label}.source_url_template must be https when present")
            elif "{year}" not in source_url_template:
                errors.append(f"{label}.source_url_template must contain {{year}} when present")
        output_extension = source.get("output_extension")
        if output_extension is not None and output_extension not in {"html", "xls", "json"}:
            errors.append(f"{label}.output_extension must be html, json, or xls when present")
        capture_mode = source.get("capture_mode", "single_url")
        if capture_mode not in VALID_CAPTURE_MODE:
            errors.append(f"{label}.capture_mode must be one of {sorted(VALID_CAPTURE_MODE)}")
        if source.get("default_importance") not in VALID_IMPORTANCE:
            errors.append(f"{label}.default_importance must be one of {sorted(VALID_IMPORTANCE)}")
        if source.get("parser_status") not in VALID_PARSER_STATUS:
            errors.append(f"{label}.parser_status must be one of {sorted(VALID_PARSER_STATUS)}")
        event_types = source.get("event_types")
        if not isinstance(event_types, list) or not event_types:
            errors.append(f"{label}.event_types must be a non-empty array")
            continue
        for event_type in event_types:
            if not isinstance(event_type, str) or not event_type:
                errors.append(f"{label}.event_types must contain non-empty strings")
                continue
            covered_events.add(event_type)

    for event_type in sorted(set(required_events) - covered_events):
        errors.append(f"missing required macro event type {event_type}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the macro calendar source plan.")
    parser.add_argument("--path", type=Path, default=DEFAULT_SOURCE_PLAN_PATH)
    args = parser.parse_args(argv)

    errors = validate_source_plan(args.path)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    plan = load_source_plan(args.path)
    print(f"validated {len(plan['sources'])} macro calendar sources from {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
