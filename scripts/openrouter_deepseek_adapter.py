from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_m2_contracts import load_schema, validate_record


SCHEMA_VERSION = "m2.0"
DEFAULT_API_KEY_ENV = "HIGANBANA_OPENROUTER_API"
DEFAULT_MODEL_ID = "deepseek/deepseek-v4-flash"
DEFAULT_REASONING_EFFORT = "high"
OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
VALID_REASONING_EFFORTS = {"high", "xhigh"}

PROMPT_VARIANTS = {
    "A": {
        "version": "exp07-prompt-a-tail-risk-v12",
        "text": (
            "You are a conservative SPY 0DTE tail-risk gate. Use the provided preclassified_event_policy first. "
            "If it says decision=unknown, return decision=unknown unless the input also shows systemic or "
            "disorderly tail risk. Use decision=block only for panic, crash, halt, war shock, emergency banking "
            "crisis, disorderly futures, or VIX>=30. Use decision=allow only for quiet/normal markets with no "
            "scheduled event risk and no credible tail-risk catalyst. Return strict JSON with decision, "
            "risk_score_0_to_10, volatility_condition, event_risk_condition, directional_bias, "
            "tail_risk_condition, strategy_suitability, and reasons."
        ),
    },
    "B": {
        "version": "exp07-prompt-b-balanced-score-v12",
        "text": (
            "You are a balanced SPY 0DTE risk classifier. Classify the market gate, not trade edge. Treat "
            "preclassified_event_policy as a hard rule: if it says decision=unknown, the final decision should "
            "be unknown unless systemic/disorderly tail risk requires block. Block only for explicit systemic "
            "risk, panic, emergency banking crisis, war shock, halt/crash risk, or VIX>=30. Allow only when "
            "preclassified_event_policy says allow, volatility is normal, and no tail-risk catalyst is present. "
            "Return strict JSON with decision, risk_score_0_to_10, volatility_condition, event_risk_condition, "
            "directional_bias, tail_risk_condition, strategy_suitability, and reasons."
        ),
    },
    "C": {
        "version": "exp07-prompt-c-structured-assessment-v12",
        "text": (
            "Evaluate five blocks: volatility_condition, event_risk_condition, directional_bias, "
            "tail_risk_condition, and strategy_suitability. Apply preclassified_event_policy before the LLM "
            "judgment: scheduled_or_ambiguous event risk means decision=unknown unless there is systemic tail "
            "risk. Block only for panic, crash, halt, war shock, emergency banking crisis, disorderly futures, "
            "or VIX>=30. Elevated volatility without systemic evidence is unknown, not block. Allow only when "
            "event risk is none and market conditions are quiet/normal. Return strict JSON with decision, "
            "risk_score_0_to_10, volatility_condition, event_risk_condition, directional_bias, "
            "tail_risk_condition, strategy_suitability, and reasons."
        ),
    },
}


class OpenRouterAdapterError(ValueError):
    pass


def build_prompt_input(news_items: list[dict[str, Any]], vix_vxv: dict[str, Any], market_context: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "market_context": market_context or {},
        "news_items": news_items,
        "vix_vxv": vix_vxv,
    }


def build_chat_payload(
    prompt_input: dict[str, Any],
    prompt_variant: str,
    model_id: str = DEFAULT_MODEL_ID,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
) -> dict[str, Any]:
    prompt = _prompt(prompt_variant)
    if reasoning_effort not in VALID_REASONING_EFFORTS:
        raise OpenRouterAdapterError(f"reasoning_effort must be one of {sorted(VALID_REASONING_EFFORTS)}")
    return {
        "model": model_id,
        "messages": [
            {"role": "system", "content": prompt["text"]},
            {"role": "user", "content": json.dumps(prompt_input, ensure_ascii=False, sort_keys=True)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": 1200,
        "reasoning": {"effort": reasoning_effort, "exclude": True},
    }


def dry_run_prompt_variant(
    prompt_input: dict[str, Any],
    prompt_variant: str,
    created_at_et: str,
    model_id: str = DEFAULT_MODEL_ID,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
) -> dict[str, Any]:
    payload = build_chat_payload(prompt_input, prompt_variant, model_id, reasoning_effort)
    output = _rule_based_fixture_output(prompt_input)
    return assessment_from_output(
        prompt_input=prompt_input,
        prompt_variant=prompt_variant,
        created_at_et=created_at_et,
        model_id=model_id,
        output_text=json.dumps(output, ensure_ascii=False, sort_keys=True),
        payload=payload,
    )


def live_prompt_variant(
    prompt_input: dict[str, Any],
    prompt_variant: str,
    created_at_et: str,
    api_key_env: str = DEFAULT_API_KEY_ENV,
    model_id: str = DEFAULT_MODEL_ID,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    transport: Any | None = None,
) -> dict[str, Any]:
    payload = build_chat_payload(prompt_input, prompt_variant, model_id, reasoning_effort)
    raw_response = (transport or _openrouter_transport)(payload, api_key_env)
    output_text = extract_message_content(raw_response)
    response_metadata = extract_response_usage_cost(raw_response)
    return assessment_from_output(
        prompt_input=prompt_input,
        prompt_variant=prompt_variant,
        created_at_et=created_at_et,
        model_id=model_id,
        output_text=output_text,
        payload=payload,
        response_metadata=response_metadata,
    )


def assessment_from_output(
    prompt_input: dict[str, Any],
    prompt_variant: str,
    created_at_et: str,
    model_id: str,
    output_text: str,
    payload: dict[str, Any] | None = None,
    response_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prompt = _prompt(prompt_variant)
    input_blob = json.dumps(prompt_input, ensure_ascii=False, sort_keys=True)
    decision = parse_decision(output_text)
    assessment = {
        "record_type": "llm_assessment",
        "schema_version": SCHEMA_VERSION,
        "assessment_id": _stable_id("llm", "|".join([input_blob, created_at_et, model_id, prompt["version"], output_text])),
        "created_at_et": created_at_et,
        "provider": "OpenRouter/DeepSeek",
        "model": model_id,
        "prompt_version": prompt["version"],
        "input_hash": _sha256_text(input_blob),
        "prompt_text": prompt["text"],
        "output_text": output_text,
        "decision": decision,
    }
    if payload is not None:
        assessment["_request_model"] = payload["model"]
        assessment["_reasoning_effort"] = payload.get("reasoning", {}).get("effort")
    if response_metadata:
        for key, value in response_metadata.items():
            assessment[f"_{key}"] = value
    return assessment


def parse_decision(output_text: str) -> str:
    try:
        parsed = json.loads(output_text)
    except json.JSONDecodeError:
        return "unknown"
    raw_decision = str(parsed.get("decision", "")).strip().lower().replace("-", "_")
    if raw_decision in {"allow", "go"}:
        return "allow"
    if raw_decision in {"block", "no_go", "no go", "nogo"}:
        return "block"
    risk_score = parsed.get("risk_score_0_to_10", parsed.get("risk_score"))
    if isinstance(risk_score, (int, float)):
        normalized_score = risk_score / 10 if 10 < risk_score <= 100 else risk_score
        if normalized_score >= 7:
            return "block"
        if normalized_score <= 4:
            return "allow"
    return "unknown"


def extract_message_content(openrouter_response: dict[str, Any]) -> str:
    choices = openrouter_response.get("choices")
    if not choices:
        raise OpenRouterAdapterError("OpenRouter response has no choices")
    message = choices[0].get("message", {})
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise OpenRouterAdapterError("OpenRouter response has empty message content")
    return content


def extract_response_usage_cost(openrouter_response: dict[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    usage = openrouter_response.get("usage")
    if isinstance(usage, dict):
        clean_usage = {
            key: value
            for key, value in usage.items()
            if key in {"prompt_tokens", "completion_tokens", "total_tokens"} and isinstance(value, int)
        }
        if clean_usage:
            metadata["usage"] = clean_usage
        cost = _numeric_value(usage.get("cost"))
        if cost is None:
            cost = _numeric_value(usage.get("total_cost"))
        if cost is not None:
            metadata["cost_usd"] = cost
    for key in ["cost", "total_cost", "total_cost_usd"]:
        cost = _numeric_value(openrouter_response.get(key))
        if cost is not None:
            metadata["cost_usd"] = cost
            break
    return metadata


def validate_assessment(assessment: dict[str, Any]) -> list[str]:
    canonical = {key: value for key, value in assessment.items() if not key.startswith("_")}
    return validate_record(canonical, load_schema())


def api_key_status(api_key_env: str = DEFAULT_API_KEY_ENV) -> dict[str, Any]:
    return {
        "api_key_env": api_key_env,
        "configured": bool(_secret_from_env(api_key_env)),
    }


def build_headers(api_key_env: str = DEFAULT_API_KEY_ENV) -> dict[str, str]:
    api_key = _secret_from_env(api_key_env)
    if not api_key:
        raise OpenRouterAdapterError(f"missing OpenRouter API key environment variable: {api_key_env}")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "SPY 0DTE - Higanbana",
    }


def append_assessment_jsonl(path: str | Path, assessment: dict[str, Any]) -> None:
    canonical = {key: value for key, value in assessment.items() if not key.startswith("_")}
    errors = validate_assessment(canonical)
    if errors:
        raise OpenRouterAdapterError("\n".join(errors))
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(canonical, ensure_ascii=False, sort_keys=True) + "\n")


def run_dry_prompt_matrix(
    news_items: list[dict[str, Any]],
    vix_vxv: dict[str, Any],
    created_at_et: str,
    market_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    prompt_input = build_prompt_input(news_items, vix_vxv, market_context)
    return [dry_run_prompt_variant(prompt_input, variant, created_at_et) for variant in sorted(PROMPT_VARIANTS)]


def _prompt(prompt_variant: str) -> dict[str, str]:
    key = prompt_variant.upper()
    if key not in PROMPT_VARIANTS:
        raise OpenRouterAdapterError(f"unknown prompt variant: {prompt_variant}")
    return PROMPT_VARIANTS[key]


def _rule_based_fixture_output(prompt_input: dict[str, Any]) -> dict[str, Any]:
    news_text = " ".join(str(item.get("headline", "")).lower() for item in prompt_input.get("news_items", []))
    vix = float(prompt_input.get("vix_vxv", {}).get("vix_close", 0.0))
    panic_terms = {"panic", "war", "banking crisis", "emergency", "systemic"}
    tail_risk = vix >= 30 or any(term in news_text for term in panic_terms)
    return {
        "decision": "block" if tail_risk else "allow",
        "risk_score_0_to_10": 8 if tail_risk else 3,
        "volatility_condition": "elevated" if vix >= 25 else "acceptable",
        "directional_bias": "unknown",
        "tail_risk_condition": "high" if tail_risk else "normal",
        "strategy_suitability": "avoid" if tail_risk else "allowed_for_research",
        "reasons": ["dry-run rule; no live OpenRouter API call was made"],
    }


def _openrouter_transport(payload: dict[str, Any], api_key_env: str) -> dict[str, Any]:
    request = urllib.request.Request(
        OPENROUTER_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=build_headers(api_key_env),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise OpenRouterAdapterError(f"OpenRouter transport failed: {type(exc).__name__}") from exc


def _stable_id(prefix: str, text: str) -> str:
    return f"{prefix}-{_sha256_text(text)[:16]}"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _numeric_value(value: Any) -> float | None:
    if isinstance(value, int | float):
        return round(float(value), 8)
    if isinstance(value, str):
        try:
            return round(float(value), 8)
        except ValueError:
            return None
    return None


def _secret_from_env(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value
    return _get_user_env(name)


def _get_user_env(name: str) -> str | None:
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value)
    except OSError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run OpenRouter DeepSeek prompt variants without calling the live API.")
    parser.add_argument("--created-at-et", default=datetime.now().astimezone().isoformat())
    parser.add_argument("--output-path", default="")
    parser.add_argument("--output-jsonl", default="")
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--live", action="store_true", help="Call OpenRouter live. Default is dry-run only.")
    parser.add_argument("--prompt-variant", choices=sorted(PROMPT_VARIANTS), default="")
    args = parser.parse_args()
    prompt_input = build_prompt_input(
        news_items=[{"headline": "Quiet market before open"}],
        vix_vxv={"vix_close": 18.0, "vxv_close": 19.0},
        market_context={"underlying": "SPY", "experiment": "exp07_prompt_pre_experiment"},
    )
    variants = [args.prompt_variant] if args.prompt_variant else sorted(PROMPT_VARIANTS)
    if args.live:
        assessments = [
            live_prompt_variant(prompt_input, variant, args.created_at_et, api_key_env=args.api_key_env)
            for variant in variants
        ]
    else:
        assessments = [
            dry_run_prompt_variant(prompt_input, variant, args.created_at_et)
            for variant in variants
        ]
    for assessment in assessments:
        errors = validate_assessment(assessment)
        if errors:
            raise OpenRouterAdapterError("\n".join(errors))
        if args.output_jsonl:
            append_assessment_jsonl(args.output_jsonl, assessment)
    result = {
        "api_key": api_key_status(args.api_key_env),
        "mode": "live_openrouter" if args.live else "dry_run_no_network",
        "model": DEFAULT_MODEL_ID,
        "reasoning_effort": DEFAULT_REASONING_EFFORT,
        "output_jsonl": args.output_jsonl,
        "assessments": assessments,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output_path:
        Path(args.output_path).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
