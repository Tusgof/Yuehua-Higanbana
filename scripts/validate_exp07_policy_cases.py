from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_CASES_PATH = PROJECT_ROOT / "tests" / "fixtures" / "exp07_policy_cases_v12.json"
DEFAULT_POLICY_SPEC_PATH = PROJECT_ROOT / "tests" / "fixtures" / "exp07_policy_spec_v12.json"
VALID_DECISIONS = {"allow", "block", "unknown"}
REQUIRED_PROMPT_INPUT_KEYS = {"market_context", "news_items", "vix_vxv"}
REQUIRED_MARKET_CONTEXT_KEYS = {"scenario", "trade_date", "underlying"}

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from exp07_event_policy import preclassify_event_policy  # noqa: E402


def load_policy_case_rows(path: Path = DEFAULT_POLICY_CASES_PATH) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON array")
    return payload


def load_policy_spec(path: Path = DEFAULT_POLICY_SPEC_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def validate_policy_cases(
    path: Path = DEFAULT_POLICY_CASES_PATH,
    spec_path: Path | None = DEFAULT_POLICY_SPEC_PATH,
) -> list[str]:
    cases = load_policy_case_rows(path)
    errors: list[str] = []
    seen_case_ids: set[str] = set()

    if not cases:
        return ["policy fixture must contain at least one case"]

    for index, case in enumerate(cases):
        prefix = f"case[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix} must be an object")
            continue

        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{prefix}.case_id is required")
            case_label = prefix
        else:
            case_label = case_id
            if case_id in seen_case_ids:
                errors.append(f"{case_label}: duplicate case_id")
            seen_case_ids.add(case_id)

        expected_decision = case.get("expected_decision")
        if expected_decision not in VALID_DECISIONS:
            errors.append(f"{case_label}: expected_decision must be allow, block, or unknown")

        prompt_input = case.get("prompt_input")
        if not isinstance(prompt_input, dict):
            errors.append(f"{case_label}: prompt_input is required")
            continue

        if "preclassified_event_policy" in prompt_input:
            errors.append(f"{case_label}: prompt_input must not embed preclassified_event_policy")

        missing_prompt_keys = sorted(REQUIRED_PROMPT_INPUT_KEYS - set(prompt_input))
        if missing_prompt_keys:
            errors.append(f"{case_label}: prompt_input missing {', '.join(missing_prompt_keys)}")

        errors.extend(_validate_market_context(case_label, prompt_input.get("market_context")))
        errors.extend(_validate_news_items(case_label, prompt_input.get("news_items")))
        errors.extend(_validate_vix_vxv(case_label, prompt_input.get("vix_vxv")))

        if expected_decision in VALID_DECISIONS:
            decision = preclassify_event_policy(_copy_json(prompt_input))["decision"]
            if decision != expected_decision:
                errors.append(
                    f"{case_label}: expected_decision={expected_decision} "
                    f"does not match preclassified decision={decision}"
                )

    if spec_path is not None:
        errors.extend(validate_policy_spec(load_policy_spec(spec_path), cases))

    return errors


def validate_policy_spec(spec: dict[str, Any], cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    categories = spec.get("categories")
    if not isinstance(categories, list) or not categories:
        return ["policy spec categories must be a non-empty array"]

    cases_by_id = {case.get("case_id"): case for case in cases if isinstance(case, dict)}
    spec_case_ids: list[str] = []
    seen_categories: set[str] = set()
    for index, category in enumerate(categories):
        label = f"category[{index}]"
        if not isinstance(category, dict):
            errors.append(f"{label} must be an object")
            continue
        category_id = category.get("category_id")
        if not isinstance(category_id, str) or not category_id:
            errors.append(f"{label}.category_id is required")
            category_label = label
        else:
            category_label = category_id
            if category_id in seen_categories:
                errors.append(f"{category_label}: duplicate category_id")
            seen_categories.add(category_id)
        expected_decision = category.get("expected_decision")
        if expected_decision not in VALID_DECISIONS:
            errors.append(f"{category_label}: expected_decision must be allow, block, or unknown")
        if not isinstance(category.get("description"), str) or not category["description"]:
            errors.append(f"{category_label}: description is required")
        if not isinstance(category.get("rules"), list) or not category["rules"]:
            errors.append(f"{category_label}: rules must be a non-empty array")
        case_ids = category.get("case_ids")
        if not isinstance(case_ids, list) or not case_ids:
            errors.append(f"{category_label}: case_ids must be a non-empty array")
            continue
        for case_id in case_ids:
            if not isinstance(case_id, str) or not case_id:
                errors.append(f"{category_label}: case_ids must contain non-empty strings")
                continue
            spec_case_ids.append(case_id)
            case = cases_by_id.get(case_id)
            if case is None:
                errors.append(f"{category_label}: unknown case_id {case_id}")
            elif case.get("expected_decision") != expected_decision:
                errors.append(
                    f"{category_label}: {case_id} expected_decision={case.get('expected_decision')} "
                    f"does not match category decision={expected_decision}"
                )

    duplicate_case_ids = sorted({case_id for case_id in spec_case_ids if spec_case_ids.count(case_id) > 1})
    for case_id in duplicate_case_ids:
        errors.append(f"policy spec duplicate case_id {case_id}")

    fixture_case_ids = set(cases_by_id)
    spec_case_id_set = set(spec_case_ids)
    for case_id in sorted(fixture_case_ids - spec_case_id_set):
        errors.append(f"policy spec missing case_id {case_id}")
    for case_id in sorted(spec_case_id_set - fixture_case_ids):
        errors.append(f"policy spec extra case_id {case_id}")

    return errors


def _validate_market_context(case_label: str, market_context: Any) -> list[str]:
    if not isinstance(market_context, dict):
        return [f"{case_label}: market_context must be an object"]
    errors: list[str] = []
    missing = sorted(REQUIRED_MARKET_CONTEXT_KEYS - set(market_context))
    if missing:
        errors.append(f"{case_label}: market_context missing {', '.join(missing)}")
    if market_context.get("underlying") != "SPY":
        errors.append(f"{case_label}: market_context.underlying must be SPY")
    for field in ("scenario", "trade_date"):
        if not isinstance(market_context.get(field), str) or not market_context[field]:
            errors.append(f"{case_label}: market_context.{field} must be a non-empty string")
    return errors


def _validate_news_items(case_label: str, news_items: Any) -> list[str]:
    if not isinstance(news_items, list) or not news_items:
        return [f"{case_label}: news_items must be a non-empty array"]
    errors: list[str] = []
    for index, item in enumerate(news_items):
        item_label = f"{case_label}.news_items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_label} must be an object")
            continue
        for field in ("headline", "published_at_et", "source_name"):
            if not isinstance(item.get(field), str) or not item[field]:
                errors.append(f"{item_label}.{field} must be a non-empty string")
    return errors


def _validate_vix_vxv(case_label: str, vix_vxv: Any) -> list[str]:
    if not isinstance(vix_vxv, dict):
        return [f"{case_label}: vix_vxv must be an object"]
    errors: list[str] = []
    for field in ("vix_close", "vxv_close"):
        value = vix_vxv.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{case_label}: vix_vxv.{field} must be numeric")
    return errors


def _copy_json(value: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(value))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Exp07 deterministic policy fixture cases.")
    parser.add_argument("--path", type=Path, default=DEFAULT_POLICY_CASES_PATH)
    parser.add_argument("--spec-path", type=Path, default=DEFAULT_POLICY_SPEC_PATH)
    args = parser.parse_args(argv)

    errors = validate_policy_cases(args.path, args.spec_path)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"validated {len(load_policy_case_rows(args.path))} Exp07 policy cases from {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
