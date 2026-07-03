from __future__ import annotations

from typing import Any


SCHEDULED_EVENT_TERMS = {
    "cpi",
    "earnings",
    "earnings-heavy",
    "fed decision",
    "fed remarks",
    "fomc",
    "inflation data",
    "ism",
    "ism manufacturing",
    "ism services",
    "jobs report",
    "jolts",
    "mega-cap",
    "nonfarm payroll",
    "payrolls",
    "pce",
    "powell",
    "retail sales",
    "treasury auction",
}

SYSTEMIC_TAIL_TERMS = {
    "banking crisis",
    "circuit breaker",
    "crash",
    "disorderly futures",
    "emergency",
    "futures near limit down",
    "halt",
    "limit down",
    "panic",
    "systemic panic",
    "systemic risk",
    "war",
}


def preclassify_event_policy(prompt_input: dict[str, Any]) -> dict[str, Any]:
    text = _policy_text(prompt_input)
    vix_vxv = prompt_input.get("vix_vxv", {})
    vix = float(vix_vxv.get("vix_close", 0.0))
    vxv = float(vix_vxv.get("vxv_close", 0.0))
    systemic_hits = _filter_non_systemic_tail_hits(
        sorted(term for term in SYSTEMIC_TAIL_TERMS if term in text),
        text,
    )
    scheduled_hits = _filter_non_actionable_scheduled_hits(
        sorted(term for term in SCHEDULED_EVENT_TERMS if term in text),
        text,
    )
    if vix >= 30 or systemic_hits:
        return {
            "decision": "block",
            "event_risk_condition": "systemic_or_disorderly",
            "matched_terms": systemic_hits + (["vix>=30"] if vix >= 30 else []),
        }
    if scheduled_hits:
        return {
            "decision": "unknown",
            "event_risk_condition": "scheduled_or_ambiguous",
            "matched_terms": scheduled_hits,
        }
    if vxv > 0 and vix >= 20 and vix / vxv >= 1.05:
        return {
            "decision": "unknown",
            "event_risk_condition": "elevated_volatility_unclear",
            "matched_terms": ["vix/vxv>=1.05"],
        }
    if vix >= 25:
        return {
            "decision": "unknown",
            "event_risk_condition": "elevated_volatility_unclear",
            "matched_terms": ["vix>=25"],
        }
    return {
        "decision": "allow",
        "event_risk_condition": "none",
        "matched_terms": [],
    }


def _policy_text(prompt_input: dict[str, Any]) -> str:
    text_parts = []
    text_parts.extend(str(item.get("headline", "")) for item in prompt_input.get("news_items", []))
    market_context = prompt_input.get("market_context", {})
    text_parts.extend(str(value) for value in market_context.values())
    return " ".join(text_parts).lower()


def _filter_non_actionable_scheduled_hits(scheduled_hits: list[str], text: str) -> list[str]:
    filtered = set(scheduled_hits)
    if "next week" in text or "next month" in text:
        filtered.difference_update({
            "earnings",
            "earnings-heavy",
            "mega-cap",
        })
        if not _has_same_day_marker(text):
            filtered.difference_update({"cpi", "pce", "inflation data"})
        if not _has_same_day_marker(text):
            filtered.difference_update({"fed decision", "fed remarks", "fomc", "powell"})
    if "tomorrow" in text:
        filtered.difference_update({
            "cpi",
            "fed decision",
            "fed remarks",
            "fomc",
            "inflation data",
            "jobs report",
            "nonfarm payroll",
            "payrolls",
            "pce",
            "powell",
            "treasury auction",
        })
    if "after the close" in text:
        filtered.difference_update({"earnings", "earnings-heavy", "mega-cap"})
    if "yesterday" in text or "last week" in text:
        filtered.difference_update(SCHEDULED_EVENT_TERMS)
    if "no major data due today" in text:
        filtered.difference_update(SCHEDULED_EVENT_TERMS)
    return sorted(filtered)


def _has_same_day_marker(text: str) -> bool:
    return any(marker in text for marker in ("today", "later today", "this afternoon", "this morning"))


def _filter_non_systemic_tail_hits(systemic_hits: list[str], text: str) -> list[str]:
    filtered = set(systemic_hits)
    if "emergency drill" in text:
        filtered.discard("emergency")
    if "limit down drill" in text or "circuit breaker drill" in text:
        filtered.discard("limit down")
        filtered.discard("circuit breaker")
    if "no war" in text or "without war" in text:
        filtered.discard("war")
    if "after the close" in text and ("single stock halt" in text or "one stock halt" in text):
        filtered.discard("halt")
    non_systemic_panic_phrases = ("no panic", "without panic", "panic bid", "panic buying")
    if "panic" in filtered and any(phrase in text for phrase in non_systemic_panic_phrases):
        filtered.remove("panic")
    return sorted(filtered)
