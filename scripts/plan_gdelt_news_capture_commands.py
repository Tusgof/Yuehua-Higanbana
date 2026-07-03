from __future__ import annotations

import argparse
import json
from datetime import date, datetime, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = PROJECT_ROOT / "reports" / "pilots"
DEFAULT_ADAPTER_SUMMARY_PATHS = [
    PILOT_DIR / "mar_2023_pilot_adapter_summary.json",
    PILOT_DIR / "apr_2023_pilot_adapter_summary.json",
    PILOT_DIR / "may_2023_pilot_adapter_summary.json",
    PILOT_DIR / "jun_2023_pilot_adapter_summary.json",
    PILOT_DIR / "jul_2023_pilot_adapter_summary.json",
    PILOT_DIR / "aug_2023_pilot_adapter_summary.json",
    PILOT_DIR / "sep_2023_pilot_adapter_summary.json",
    PILOT_DIR / "oct_2023_pilot_adapter_summary.json",
    PILOT_DIR / "nov_2023_pilot_adapter_summary.json",
    PILOT_DIR / "dec_2023_pilot_adapter_summary.json",
    PILOT_DIR / "jan_2024_pilot_adapter_summary.json",
    PILOT_DIR / "feb_2024_pilot_adapter_summary.json",
    PILOT_DIR / "mar_2024_pilot_adapter_summary.json",
    PILOT_DIR / "apr_2024_pilot_adapter_summary.json",
    PILOT_DIR / "may_2024_pilot_adapter_summary.json",
    PILOT_DIR / "jun_2024_pilot_adapter_summary.json",
]
DEFAULT_STATUS_INPUT_PATH = PROJECT_ROOT / "reports" / "news_gdelt_capture_status.json"
DEFAULT_STATUS_DIR = PROJECT_ROOT / "reports" / "news_gdelt_capture_status"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "news_gdelt_capture_command_plan.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "news_gdelt_capture_command_plan.md"
COOLDOWN_BLOCKED_STATUS_THRESHOLD = 3
ET = ZoneInfo("America/New_York")


class GdeltNewsCaptureCommandPlanError(ValueError):
    pass


def plan_capture_commands(
    adapter_summary_paths: list[Path] | None = None,
    status_input_path: Path = DEFAULT_STATUS_INPUT_PATH,
    status_dir: Path = DEFAULT_STATUS_DIR,
    max_records: int = 5,
    lookback_hours: int = 24,
) -> dict[str, Any]:
    if max_records <= 0:
        raise GdeltNewsCaptureCommandPlanError("max_records must be positive")
    if lookback_hours <= 0:
        raise GdeltNewsCaptureCommandPlanError("lookback_hours must be positive")

    paths = adapter_summary_paths or DEFAULT_ADAPTER_SUMMARY_PATHS
    candidate_dates = _load_candidate_dates(paths)
    latest_status = _load_latest_status(status_input_path)
    status_by_date = _load_status_by_date(status_dir)
    commands = [
        _build_command(
            trade_date,
            max_records=max_records,
            lookback_hours=lookback_hours,
            latest_status=status_by_date.get(trade_date),
        )
        for trade_date in candidate_dates
    ]

    status = "ready_to_retry" if commands else "blocked"
    blockers: list[str] = []
    if not commands:
        blockers.append("no_candidate_ready_days_found")
    if latest_status.get("status") == "blocked":
        blockers.extend(latest_status.get("blockers", []))

    retry_queue_summary = _summarize_retry_queue(commands)
    retry_pressure = _summarize_retry_pressure(retry_queue_summary)
    return {
        "mode": "dry_run_no_network",
        "status": status,
        "blockers": sorted(set(blockers)),
        "adapter_summary_paths": [str(path) for path in paths],
        "latest_capture_status_path": str(status_input_path),
        "latest_capture_status": latest_status,
        "daily_status_dir": str(status_dir),
        "daily_status_counts": _summarize_daily_statuses(status_by_date),
        "retry_queue_summary": retry_queue_summary,
        "retry_pressure": retry_pressure,
        "candidate_day_count": len(candidate_dates),
        "command_count": len(commands),
        "max_records": max_records,
        "lookback_hours": lookback_hours,
        "commands": commands,
        "next_step": _build_next_step(retry_pressure),
    }


def write_reports(
    result: dict[str, Any],
    json_output: Path = DEFAULT_JSON_OUTPUT,
    report_output: Path = DEFAULT_REPORT_OUTPUT,
) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# GDELT News Capture Command Plan",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Status: `{result['status']}`",
        f"- Candidate days: `{result['candidate_day_count']}`",
        f"- Command count: `{result['command_count']}`",
        f"- Max records per topic: `{result['max_records']}`",
        f"- Lookback hours: `{result['lookback_hours']}`",
        f"- Latest capture status: `{result['latest_capture_status'].get('status', 'missing')}`",
        f"- Daily status files: `{sum(result.get('daily_status_counts', {}).values())}`",
        f"- Not-attempted candidate days: `{result.get('retry_queue_summary', {}).get('not_attempted_count', 0)}`",
        f"- Retry pressure: `{result.get('retry_pressure', {}).get('status', 'unknown')}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = result.get("blockers") or []
    if blockers:
        lines.extend(f"- `{blocker}`" for blocker in blockers)
    else:
        lines.append("- None for planning. Live GDELT availability still must be checked command-by-command.")

    retry_pressure = result.get("retry_pressure", {})
    lines.extend(["", "## Retry Pressure", ""])
    lines.append(f"- Status: `{retry_pressure.get('status', 'unknown')}`")
    reason = retry_pressure.get("reason")
    if reason:
        lines.append(f"- Reason: {reason}")

    retry_queue_summary = result.get("retry_queue_summary", {})
    next_command = retry_queue_summary.get("next_unattempted_command")
    lines.extend(["", "## Next Unattempted Command", ""])
    if next_command:
        lines.extend(["```powershell", str(next_command), "```", ""])
    else:
        lines.append("- None. All planned candidate days already have status files.")

    lines.extend(["", "## Commands", ""])
    for command in result["commands"]:
        lines.extend(
            [
                f"### {command['trade_date']}",
                "",
                "```powershell",
                command["command"],
                "```",
                "",
            ]
        )
    lines.extend(["## Next Step", "", str(result["next_step"])])
    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_candidate_dates(paths: list[Path]) -> list[str]:
    dates: set[str] = set()
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise GdeltNewsCaptureCommandPlanError(f"adapter summary path missing: {missing}")
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        days = payload.get("days")
        if not isinstance(days, list):
            raise GdeltNewsCaptureCommandPlanError(f"{path} missing days array")
        for day in days:
            if not isinstance(day, dict):
                continue
            if day.get("status") != "candidate_ready":
                continue
            trade_date = str(day.get("date", "")).strip()
            if trade_date:
                date.fromisoformat(trade_date)
                dates.add(trade_date)
    return sorted(dates)


def _load_latest_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing", "blockers": ["no_prior_gdelt_capture_status"]}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GdeltNewsCaptureCommandPlanError(f"{path} must contain a JSON object")
    return payload


def _load_status_by_date(status_dir: Path) -> dict[str, dict[str, Any]]:
    if not status_dir.exists():
        return {}
    statuses: dict[str, dict[str, Any]] = {}
    for path in sorted(status_dir.glob("*.json")):
        try:
            trade_date = date.fromisoformat(path.stem).isoformat()
        except ValueError:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise GdeltNewsCaptureCommandPlanError(f"{path} must contain a JSON object")
        statuses[trade_date] = payload
    return statuses


def _summarize_daily_statuses(status_by_date: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for payload in status_by_date.values():
        status = str(payload.get("status", "missing"))
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _summarize_retry_queue(commands: list[dict[str, Any]]) -> dict[str, Any]:
    attempted_count = 0
    blocked_count = 0
    next_unattempted: dict[str, Any] | None = None
    for command in commands:
        status = str(command.get("latest_status", {}).get("status", "not_attempted"))
        if status == "not_attempted":
            if next_unattempted is None:
                next_unattempted = command
            continue
        attempted_count += 1
        if status == "blocked":
            blocked_count += 1

    return {
        "attempted_status_file_count": attempted_count,
        "blocked_status_file_count": blocked_count,
        "not_attempted_count": len(commands) - attempted_count,
        "next_unattempted_trade_date": next_unattempted.get("trade_date") if next_unattempted else None,
        "next_unattempted_command": next_unattempted.get("command") if next_unattempted else None,
    }


def _summarize_retry_pressure(retry_queue_summary: dict[str, Any]) -> dict[str, Any]:
    blocked_count = int(retry_queue_summary.get("blocked_status_file_count", 0))
    if blocked_count >= COOLDOWN_BLOCKED_STATUS_THRESHOLD:
        return {
            "status": "cooldown_recommended",
            "threshold": COOLDOWN_BLOCKED_STATUS_THRESHOLD,
            "reason": (
                f"{blocked_count} per-day GDELT capture attempts are blocked; wait before the next --execute retry "
                "or switch to an offline/alternate news archive path."
            ),
        }
    return {
        "status": "normal_retry",
        "threshold": COOLDOWN_BLOCKED_STATUS_THRESHOLD,
        "reason": "Blocked per-day status count is below the cooldown threshold.",
    }


def _build_next_step(retry_pressure: dict[str, Any]) -> str:
    if retry_pressure.get("status") == "cooldown_recommended":
        return (
            "GDELT 429 pressure is persistent. Pause live GDELT --execute retries before trying the next candidate day, "
            "then import and audit only after a real CSV capture succeeds."
        )
    return "Run one command at a time with --execute only after GDELT 429 pressure clears, then import and audit the real news archive."


def _build_command(
    trade_date: str,
    max_records: int,
    lookback_hours: int,
    latest_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decision_time = datetime.combine(date.fromisoformat(trade_date), time(9, 30), tzinfo=ET).isoformat(timespec="seconds")
    output_path = Path("data") / "raw" / "spy_0dte" / "news" / "gdelt" / f"{trade_date}.csv"
    status_path = Path("reports") / "news_gdelt_capture_status" / f"{trade_date}.json"
    command = (
        "python scripts\\capture_gdelt_news_snapshots.py "
        f"--decision-time-et {decision_time} "
        f"--lookback-hours {lookback_hours} "
        f"--max-records {max_records} "
        f"--output-path {output_path} "
        f"--status-output-path {status_path} "
        "--execute"
    )
    return {
        "trade_date": trade_date,
        "decision_time_et": decision_time,
        "output_path": str(output_path),
        "status_output_path": str(status_path),
        "latest_status": latest_status or {"status": "not_attempted"},
        "command": command,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan GDELT news capture commands from candidate-ready pilot dates without network calls.")
    parser.add_argument("--adapter-summary-path", action="append", type=Path, dest="adapter_summary_paths")
    parser.add_argument("--status-input-path", type=Path, default=DEFAULT_STATUS_INPUT_PATH)
    parser.add_argument("--status-dir", type=Path, default=DEFAULT_STATUS_DIR)
    parser.add_argument("--max-records", type=int, default=5)
    parser.add_argument("--lookback-hours", type=int, default=24)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = plan_capture_commands(
        args.adapter_summary_paths,
        args.status_input_path,
        args.status_dir,
        args.max_records,
        args.lookback_hours,
    )
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
