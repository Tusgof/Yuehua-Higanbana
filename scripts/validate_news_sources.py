from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PLAN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "news_sources_v1.json"
VALID_ACCESS_STATUS = {"free_no_key", "key_required"}
VALID_ARCHIVE_STATUS = {"candidate", "deferred", "supplement_only"}
VALID_PARSER_STATUS = {"planned", "implemented", "deferred"}
VALID_SOURCE_ROLES = {
    "primary_archive_candidate",
    "optional_market_news_supplement",
    "fallback_paid_archive_candidate",
    "structured_regulatory_supplement",
}


def load_source_plan(path: Path = DEFAULT_SOURCE_PLAN_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def validate_source_plan(path: Path = DEFAULT_SOURCE_PLAN_PATH) -> list[str]:
    plan = load_source_plan(path)
    errors: list[str] = []

    if plan.get("plan_version") != "news-sources-v1":
        errors.append("plan_version must be news-sources-v1")
    if plan.get("timezone") != "America/New_York":
        errors.append("timezone must be America/New_York")

    topics = plan.get("minimum_required_topics")
    if not isinstance(topics, list) or not topics:
        errors.append("minimum_required_topics must be a non-empty array")
        topics = []

    anti_leakage = plan.get("anti_leakage_rules")
    if not isinstance(anti_leakage, dict):
        errors.append("anti_leakage_rules must be an object")
        anti_leakage = {}
    _validate_anti_leakage_rules(anti_leakage, errors)

    sources = plan.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty array")
        sources = []

    primary_source_id = plan.get("primary_source_id")
    seen_source_ids: set[str] = set()
    covered_topics: set[str] = set()
    implemented_or_planned_primary = False
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"source[{index}] must be an object")
            continue
        label = _validate_source(index, source, seen_source_ids, errors)
        if source.get("source_id") == primary_source_id:
            implemented_or_planned_primary = (
                source.get("source_role") == "primary_archive_candidate"
                and source.get("access_status") == "free_no_key"
                and source.get("archive_status") == "candidate"
                and source.get("parser_status") in {"planned", "implemented"}
            )
        for topic in source.get("allowed_topics", []):
            if isinstance(topic, str):
                covered_topics.add(topic)
        if source.get("access_status") == "key_required" and source.get("archive_status") == "candidate":
            errors.append(f"{label}: key_required sources must be deferred until explicitly approved")

    if primary_source_id not in seen_source_ids:
        errors.append("primary_source_id must match a source_id")
    if not implemented_or_planned_primary:
        errors.append("primary source must be a free candidate with planned or implemented parser")
    for topic in sorted(set(topics) - covered_topics):
        errors.append(f"missing required news topic {topic}")
    return errors


def _validate_anti_leakage_rules(rules: dict[str, Any], errors: list[str]) -> None:
    required_flags = [
        "published_at_must_be_lte_decision_time",
        "fetched_at_must_be_lte_decision_time_for_live_replay",
        "raw_snapshot_required_before_strategy_use",
    ]
    for flag in required_flags:
        if rules.get(flag) is not True:
            errors.append(f"anti_leakage_rules.{flag} must be true")
    if rules.get("decision_time_field") != "decision_time_et":
        errors.append("anti_leakage_rules.decision_time_field must be decision_time_et")
    required_item_fields = rules.get("required_item_fields")
    if not isinstance(required_item_fields, list):
        errors.append("anti_leakage_rules.required_item_fields must be an array")
        return
    for field in ("published_at_et", "fetched_at_et", "source_name", "headline", "url", "provider"):
        if field not in required_item_fields:
            errors.append(f"anti_leakage_rules.required_item_fields missing {field}")


def _validate_source(index: int, source: dict[str, Any], seen_source_ids: set[str], errors: list[str]) -> str:
    label = f"source[{index}]"
    source_id = source.get("source_id")
    if not isinstance(source_id, str) or not source_id:
        errors.append(f"{label}.source_id is required")
    elif source_id in seen_source_ids:
        errors.append(f"{source_id}: duplicate source_id")
    else:
        seen_source_ids.add(source_id)
        label = source_id

    for field in ("provider", "source_url", "api_url_template", "license_notes", "query_notes"):
        if not isinstance(source.get(field), str) or not source[field]:
            errors.append(f"{label}.{field} is required")
    if isinstance(source.get("source_url"), str) and not source["source_url"].startswith("https://"):
        errors.append(f"{label}.source_url must be https")
    if isinstance(source.get("api_url_template"), str) and not source["api_url_template"].startswith("https://"):
        errors.append(f"{label}.api_url_template must be https")
    if source.get("source_role") not in VALID_SOURCE_ROLES:
        errors.append(f"{label}.source_role must be one of {sorted(VALID_SOURCE_ROLES)}")
    if source.get("access_status") not in VALID_ACCESS_STATUS:
        errors.append(f"{label}.access_status must be one of {sorted(VALID_ACCESS_STATUS)}")
    if source.get("archive_status") not in VALID_ARCHIVE_STATUS:
        errors.append(f"{label}.archive_status must be one of {sorted(VALID_ARCHIVE_STATUS)}")
    if source.get("parser_status") not in VALID_PARSER_STATUS:
        errors.append(f"{label}.parser_status must be one of {sorted(VALID_PARSER_STATUS)}")
    topics = source.get("allowed_topics")
    if not isinstance(topics, list) or not topics:
        errors.append(f"{label}.allowed_topics must be a non-empty array")
    elif any(not isinstance(topic, str) or not topic for topic in topics):
        errors.append(f"{label}.allowed_topics must contain non-empty strings")
    return label


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the news source plan.")
    parser.add_argument("--path", type=Path, default=DEFAULT_SOURCE_PLAN_PATH)
    args = parser.parse_args(argv)

    errors = validate_source_plan(args.path)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    plan = load_source_plan(args.path)
    print(f"validated {len(plan['sources'])} news sources from {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
