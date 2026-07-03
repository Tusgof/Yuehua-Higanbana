from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "ibkr.example.json"
DEFAULT_KILL_SWITCH = PROJECT_ROOT / "config" / "kill_switch.json"


class OperationalBridgeError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_order_ticket(
    intent: dict[str, Any],
    legs: list[dict[str, Any]],
    limit_price: float,
    order_type: str = "LIMIT",
    transmit: bool = False,
) -> dict[str, Any]:
    if order_type != "LIMIT":
        raise OperationalBridgeError("Entry orders must be LIMIT orders")
    if transmit:
        raise OperationalBridgeError("Ticket builder cannot enable transmit")
    _validate_defined_risk_legs(legs)
    return {
        "ticket_id": f"ticket-{intent['intent_id']}",
        "intent_id": intent["intent_id"],
        "strategy_id": intent["strategy_id"],
        "order_type": order_type,
        "limit_price": limit_price,
        "transmit": False,
        "legs": legs,
        "close_plan": close_workflow(intent["entry_time_et"]),
    }


def pre_transmit_validate(
    ticket: dict[str, Any],
    config: dict[str, Any],
    account_state: dict[str, Any],
    kill_switch: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if kill_switch.get("enabled", True):
        errors.append(f"kill switch active: {kill_switch.get('reason', 'no reason')}")
    if ticket.get("transmit") is True:
        errors.append("ticket transmit must remain false before launch gate")
    if config.get("transmit_enabled") is not True:
        errors.append("config transmit_enabled is false")
    if config.get("mode") == "live" and config.get("options_permission_confirmed") is not True:
        errors.append("live mode requires confirmed options permission")
    if account_state.get("open_positions", 0) >= config.get("max_open_positions", 1):
        errors.append("max open positions reached")
    if account_state.get("estimated_max_loss", 0) > config.get("max_risk_usd", 0):
        errors.append("estimated max loss exceeds configured max risk")
    if not ticket.get("close_plan"):
        errors.append("ticket missing forced close plan")
    return errors


def paper_trade_dry_run(ticket: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "paper",
        "would_submit": False,
        "ticket_id": ticket["ticket_id"],
        "validated_legs": len(ticket["legs"]),
        "close_plan_steps": len(ticket["close_plan"]),
        "journal_note": "Paper dry-run only; not evidence of trading edge.",
    }


def email_alert_payload(kind: str, subject: str, body: str, to: str) -> dict[str, Any]:
    return {
        "dry_run": True,
        "kind": kind,
        "to": to,
        "subject": subject,
        "body": body,
    }


def close_workflow(entry_time_et: str) -> list[dict[str, str]]:
    trade_date = entry_time_et.split("T")[0]
    return [
        {"time_et": f"{trade_date}T15:40:00{_offset(entry_time_et)}", "action": "send_closing_limit_order"},
        {"time_et": f"{trade_date}T15:43:00{_offset(entry_time_et)}", "action": "cancel_limit_and_send_market_close_if_unfilled"},
        {"time_et": f"{trade_date}T15:45:00{_offset(entry_time_et)}", "action": "backup_forced_close_must_be_active"},
    ]


def launch_checklist_status(checklist: dict[str, Any]) -> dict[str, Any]:
    required = [
        "research_acceptance_passed",
        "options_permission_approved",
        "cash_account_constraints_documented",
        "defined_risk_only_confirmed",
        "user_real_money_approval_recorded",
        "kill_switch_tested",
        "forced_close_tested",
        "backup_close_order_plan_tested",
    ]
    missing = [key for key in required if checklist.get(key) is not True]
    return {"status": "pass" if not missing else "blocked", "missing": missing}


def _validate_defined_risk_legs(legs: list[dict[str, Any]]) -> None:
    if not legs:
        raise OperationalBridgeError("ticket requires option legs")
    for leg in legs:
        if leg["side"] == "sell":
            matching_wings = [
                candidate for candidate in legs
                if candidate["side"] == "buy"
                and candidate["right"] == leg["right"]
                and candidate["expiration_date"] == leg["expiration_date"]
                and (
                    (leg["right"] == "put" and candidate["strike"] < leg["strike"])
                    or (leg["right"] == "call" and candidate["strike"] > leg["strike"])
                )
            ]
            if not matching_wings:
                raise OperationalBridgeError("short option leg requires protective wing")


def _offset(timestamp_et: str) -> str:
    if timestamp_et.endswith("-05:00"):
        return "-05:00"
    if timestamp_et.endswith("-04:00"):
        return "-04:00"
    return "-05:00"


if __name__ == "__main__":
    print(json.dumps({
        "config": load_json(DEFAULT_CONFIG),
        "kill_switch": load_json(DEFAULT_KILL_SWITCH),
    }, ensure_ascii=False, indent=2, sort_keys=True))
