from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


DEFAULT_DATASET = "OPRA.PILLAR"
DEFAULT_SCHEMA = "cbbo-1m"
DEFAULT_SYMBOL = "SPY.OPT"
DEFAULT_STYPE_IN = "parent"
DEFAULT_API_KEY_ENV = "DATABENTO_API_KEY"
DATABENTO_API_KEY_ENV_ALIASES = ("DATABENTO_SPY0DTE_API",)
DEFAULT_REVIEW_COST_USD = 5.0
DEFAULT_BLOCK_COST_USD = 25.0
SCENARIOS = ["one_day_sample", "one_month_pilot", "oos_2024_2025", "full_research"]
WINDOW_PROFILES = ["entry_close", "intraday_exit_30m"]
COST_GRANULARITIES = ["window", "daily_union"]
ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


@dataclass(frozen=True)
class CostWindow:
    name: str
    start: str
    end: str
    note: str


@dataclass(frozen=True)
class CostRequest:
    dataset: str
    symbols: list[str]
    schema: str
    stype_in: str
    start: str
    end: str
    scenario: str
    window: str
    note: str


def build_cost_requests(
    scenario: str,
    dataset: str = DEFAULT_DATASET,
    schema: str = DEFAULT_SCHEMA,
    symbol: str = DEFAULT_SYMBOL,
    stype_in: str = DEFAULT_STYPE_IN,
    start_date: date | None = None,
    end_date: date | None = None,
    window_profile: str = "entry_close",
    scenario_label: str | None = None,
) -> list[CostRequest]:
    windows = build_windows(scenario, start_date=start_date, end_date=end_date, window_profile=window_profile)
    request_scenario = scenario_label or scenario
    return [
        CostRequest(
            dataset=dataset,
            symbols=[symbol],
            schema=schema,
            stype_in=stype_in,
            start=window.start,
            end=window.end,
            scenario=request_scenario,
            window=window.name,
            note=window.note,
        )
        for window in windows
    ]


def build_windows(
    scenario: str,
    start_date: date | None = None,
    end_date: date | None = None,
    window_profile: str = "entry_close",
) -> list[CostWindow]:
    if scenario == "one_day_sample":
        target = start_date or date(2024, 1, 3)
        return _daily_research_windows(target, window_profile)
    if scenario == "one_month_pilot":
        start = start_date or date(2024, 1, 2)
        end = end_date or date(2024, 1, 31)
        return _daily_range_windows(start, end, window_profile)
    if scenario == "oos_2024_2025":
        start = start_date or date(2024, 1, 1)
        end = end_date or date(2025, 6, 29)
        return _daily_range_windows(start, end, window_profile)
    if scenario == "full_research":
        start = start_date or date(2022, 5, 11)
        end = end_date or date(2026, 6, 29)
        return _daily_range_windows(start, end, window_profile)
    raise ValueError(f"unknown scenario: {scenario}")


def estimate_live_cost(
    requests: list[CostRequest],
    api_key_env: str = DEFAULT_API_KEY_ENV,
    max_live_requests: int = 100,
    planned_request_count: int | None = None,
    cost_granularity: str = "window",
) -> dict[str, Any]:
    if len(requests) > max_live_requests:
        raise RuntimeError(
            f"refusing {len(requests)} live Databento cost calls; "
            f"increase --max-live-requests above {max_live_requests} if intentional"
        )
    api_key = _databento_api_key_from_env(api_key_env)
    if not api_key:
        raise RuntimeError(f"missing Databento API key environment variable: {_databento_env_names(api_key_env)}")
    try:
        import databento as db  # type: ignore
    except ImportError as exc:
        raise RuntimeError("missing Python package: databento") from exc

    client = db.Historical(api_key)
    rows: list[dict[str, Any]] = []
    total = 0.0
    errors: list[dict[str, str]] = []
    for request in requests:
        payload = asdict(request)
        try:
            cost = float(
                client.metadata.get_cost(
                    dataset=request.dataset,
                    symbols=request.symbols,
                    schema=request.schema,
                    stype_in=request.stype_in,
                    start=request.start,
                    end=request.end,
                )
            )
            payload["estimated_cost_usd"] = cost
            total += cost
        except Exception as exc:
            payload["estimated_cost_usd"] = None
            payload["error"] = str(exc)
            errors.append({"window": request.window, "error": str(exc)})
        rows.append(payload)
    return {
        "mode": "live",
        "cost_granularity": cost_granularity,
        "planned_request_count": planned_request_count or len(requests),
        "live_request_count": len(requests),
        "total_estimated_cost_usd": round(total, 6),
        "requests": rows,
        "summary": summarize_requests(requests),
        "errors": errors,
    }


def coalesce_cost_requests(requests: list[CostRequest], granularity: str = "window") -> list[CostRequest]:
    if granularity not in COST_GRANULARITIES:
        raise ValueError(f"unknown cost granularity: {granularity}")
    if granularity == "window":
        return list(requests)

    grouped: dict[tuple[str, str, tuple[str, ...], str, str, str], list[CostRequest]] = {}
    for request in requests:
        trade_date = request.window.split("_", 1)[0]
        key = (
            request.scenario,
            request.dataset,
            tuple(request.symbols),
            request.schema,
            request.stype_in,
            trade_date,
        )
        grouped.setdefault(key, []).append(request)

    coalesced: list[CostRequest] = []
    for (scenario, dataset, symbols, schema, stype_in, trade_date), items in sorted(grouped.items()):
        first_start = min(item.start for item in items)
        last_end = max(item.end for item in items)
        coalesced.append(
            CostRequest(
                dataset=dataset,
                symbols=list(symbols),
                schema=schema,
                stype_in=stype_in,
                start=first_start,
                end=last_end,
                scenario=scenario,
                window=f"{trade_date}_daily_union",
                note=(
                    f"Daily union cost cap for {len(items)} planned research window(s); "
                    "exact for this superset request, not a narrow-window sum."
                ),
            )
        )
    return coalesced


def render_plan(requests: list[CostRequest]) -> dict[str, Any]:
    return {
        "mode": "dry_run",
        "warning": (
            "This is a request plan only. Use --live with DATABENTO_API_KEY to call "
            "Databento metadata.get_cost. Parent symbol SPY.OPT is an upper-bound request."
        ),
        "requests": [asdict(request) for request in requests],
        "summary": summarize_requests(requests),
    }


def _databento_api_key_from_env(api_key_env: str = DEFAULT_API_KEY_ENV) -> str | None:
    api_key = os.environ.get(api_key_env)
    if api_key or api_key_env != DEFAULT_API_KEY_ENV:
        return api_key
    for alias in DATABENTO_API_KEY_ENV_ALIASES:
        api_key = os.environ.get(alias)
        if api_key:
            return api_key
    return None


def _databento_env_names(api_key_env: str = DEFAULT_API_KEY_ENV) -> str:
    if api_key_env != DEFAULT_API_KEY_ENV:
        return api_key_env
    return " or ".join((DEFAULT_API_KEY_ENV, *DATABENTO_API_KEY_ENV_ALIASES))


def render_markdown_report(result: dict[str, Any]) -> str:
    summary = result.get("summary") or summarize_requests(_requests_from_result(result))
    lines = [
        "# Databento Cost Estimate Report",
        "",
        f"- **Mode**: `{result.get('mode', 'unknown')}`",
        f"- **Total request count**: {summary['total_request_count']}",
    ]
    if "planned_request_count" in result:
        lines.append(f"- **Planned research windows**: {result['planned_request_count']}")
    if "live_request_count" in result:
        lines.append(f"- **Live cost request count**: {result['live_request_count']}")
    if result.get("cost_granularity"):
        lines.append(f"- **Cost granularity**: `{result['cost_granularity']}`")
    if "total_estimated_cost_usd" in result:
        lines.append(f"- **Total estimated cost**: `${result['total_estimated_cost_usd']}`")
    else:
        lines.append("- **Total estimated cost**: not available in dry-run mode")
    if result.get("warning"):
        lines.append(f"- **Warning**: {result['warning']}")
    if result.get("decision"):
        decision = result["decision"]
        lines.extend(
            [
                f"- **Decision**: `{decision['status']}`",
                f"- **Decision reason**: {decision['reason']}",
            ]
        )
    if result.get("errors"):
        lines.append(f"- **Errors**: {len(result['errors'])} request window(s) need review")

    lines.extend(
        [
            "",
            "## Scenario Summary",
            "",
            "| Scenario | Requests | First Start UTC | Last End UTC | Dataset | Schema | Symbol |",
            "|:--|--:|:--|:--|:--|:--|:--|",
        ]
    )
    for scenario, data in sorted(summary["scenarios"].items()):
        symbols = ", ".join(data["symbols"])
        lines.append(
            f"| `{scenario}` | {data['request_count']} | `{data['first_start']}` | "
            f"`{data['last_end']}` | `{data['dataset']}` | `{data['schema']}` | `{symbols}` |"
        )

    lines.extend(
        [
            "",
            "## Decision Rule",
            "",
            "- Start with `one_day_sample --live` only.",
            "- Move to `one_month_pilot --live` only if the one-day estimate is acceptable.",
            "- Do not run OOS/full live estimates until the smaller estimates are reviewed.",
            "- Do not download data from Databento until cost, coverage, and schema are explicitly accepted.",
            "",
        ]
    )
    return "\n".join(lines)


def add_cost_decision(
    result: dict[str, Any],
    review_cost_usd: float = DEFAULT_REVIEW_COST_USD,
    block_cost_usd: float = DEFAULT_BLOCK_COST_USD,
) -> dict[str, Any]:
    decision = evaluate_cost_decision(result, review_cost_usd, block_cost_usd)
    updated = dict(result)
    updated["decision"] = decision
    return updated


def evaluate_cost_decision(
    result: dict[str, Any],
    review_cost_usd: float = DEFAULT_REVIEW_COST_USD,
    block_cost_usd: float = DEFAULT_BLOCK_COST_USD,
) -> dict[str, Any]:
    cost = result.get("total_estimated_cost_usd")
    error_count = len(result.get("errors", []))
    if cost is None:
        return {
            "status": "review",
            "reason": "Dry-run has no dollar estimate. Run one_day_sample --live before any download.",
            "review_cost_usd": review_cost_usd,
            "block_cost_usd": block_cost_usd,
        }
    if error_count:
        return {
            "status": "review",
            "reason": f"Estimated cost ${cost} has {error_count} request error(s); review coverage before download.",
            "review_cost_usd": review_cost_usd,
            "block_cost_usd": block_cost_usd,
        }
    if cost >= block_cost_usd:
        status = "block"
        reason = f"Estimated cost ${cost} is at or above block threshold ${block_cost_usd}."
    elif cost >= review_cost_usd:
        status = "review"
        reason = f"Estimated cost ${cost} is at or above review threshold ${review_cost_usd}."
    else:
        status = "pass"
        reason = f"Estimated cost ${cost} is below review threshold ${review_cost_usd}."
    return {
        "status": status,
        "reason": reason,
        "review_cost_usd": review_cost_usd,
        "block_cost_usd": block_cost_usd,
    }


def summarize_requests(requests: list[CostRequest]) -> dict[str, Any]:
    scenarios: dict[str, dict[str, Any]] = {}
    for request in requests:
        item = scenarios.setdefault(
            request.scenario,
            {
                "request_count": 0,
                "first_start": request.start,
                "last_end": request.end,
                "dataset": request.dataset,
                "schema": request.schema,
                "symbols": request.symbols,
                "stype_in": request.stype_in,
            },
        )
        item["request_count"] += 1
        item["first_start"] = min(item["first_start"], request.start)
        item["last_end"] = max(item["last_end"], request.end)
    return {
        "total_request_count": len(requests),
        "scenarios": scenarios,
    }


def _requests_from_result(result: dict[str, Any]) -> list[CostRequest]:
    requests: list[CostRequest] = []
    for row in result.get("requests", []):
        requests.append(
            CostRequest(
                dataset=row["dataset"],
                symbols=list(row["symbols"]),
                schema=row["schema"],
                stype_in=row["stype_in"],
                start=row["start"],
                end=row["end"],
                scenario=row["scenario"],
                window=row["window"],
                note=row["note"],
            )
        )
    return requests


def _daily_range_windows(start: date, end: date, window_profile: str = "entry_close") -> list[CostWindow]:
    windows: list[CostWindow] = []
    current = start
    while current <= end:
        if is_market_session_date(current):
            windows.extend(_daily_research_windows(current, window_profile))
        current += timedelta(days=1)
    return windows


def is_market_session_date(target: date) -> bool:
    return target.weekday() < 5 and target not in us_equity_market_holidays(target.year)


def us_equity_market_holidays(year: int) -> set[date]:
    holidays = {
        _observed_fixed_holiday(year, 1, 1),
        _nth_weekday(year, 1, 0, 3),   # Martin Luther King Jr. Day
        _nth_weekday(year, 2, 0, 3),   # Presidents Day
        _good_friday(year),
        _last_weekday(year, 5, 0),     # Memorial Day
        _observed_fixed_holiday(year, 6, 19),
        _observed_fixed_holiday(year, 7, 4),
        _nth_weekday(year, 9, 0, 1),   # Labor Day
        _nth_weekday(year, 11, 3, 4),  # Thanksgiving
        _observed_fixed_holiday(year, 12, 25),
    }
    return {holiday for holiday in holidays if holiday.year == year}


def _observed_fixed_holiday(year: int, month: int, day: int) -> date:
    holiday = date(year, month, day)
    if holiday.weekday() == 5:
        return holiday - timedelta(days=1)
    if holiday.weekday() == 6:
        return holiday + timedelta(days=1)
    return holiday


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    current = date(year, month, 1)
    while current.weekday() != weekday:
        current += timedelta(days=1)
    return current + timedelta(days=7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    current = date(year, month + 1, 1) - timedelta(days=1)
    while current.weekday() != weekday:
        current -= timedelta(days=1)
    return current


def _good_friday(year: int) -> date:
    return _western_easter(year) - timedelta(days=2)


def _western_easter(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _daily_research_windows(target: date, window_profile: str = "entry_close") -> list[CostWindow]:
    if window_profile not in WINDOW_PROFILES:
        raise ValueError(f"unknown window_profile: {window_profile}")
    windows = [
        _window(target, time(9, 30), time(9, 40), "entry_a_0935", "10-minute window around 9:35 AM ET"),
        _window(target, time(9, 55), time(10, 5), "entry_b_1000", "10-minute window around 10:00 AM ET"),
    ]
    if window_profile == "intraday_exit_30m":
        windows.extend(
            _window_around(
                target,
                check_time,
                f"exit_check_{check_time:%H%M}",
                f"10-minute window around {check_time:%H:%M} ET for target/stop checks",
            )
            for check_time in [
                time(10, 30),
                time(11, 0),
                time(11, 30),
                time(12, 0),
                time(12, 30),
                time(13, 0),
                time(13, 30),
                time(14, 0),
                time(14, 30),
                time(15, 0),
                time(15, 30),
            ]
        )
    windows.append(_window(target, time(15, 40), time(15, 50), "forced_close_1545", "10-minute window around 3:45 PM ET"))
    return windows


def _window(target: date, start_time: time, end_time: time, name: str, note: str) -> CostWindow:
    start = datetime.combine(target, start_time, ET).astimezone(UTC).isoformat()
    end = datetime.combine(target, end_time, ET).astimezone(UTC).isoformat()
    return CostWindow(name=f"{target.isoformat()}_{name}", start=start, end=end, note=note)


def _window_around(target: date, center_time: time, name: str, note: str) -> CostWindow:
    center = datetime.combine(target, center_time, ET)
    start = (center - timedelta(minutes=5)).astimezone(UTC).isoformat()
    end = (center + timedelta(minutes=5)).astimezone(UTC).isoformat()
    return CostWindow(name=f"{target.isoformat()}_{name}", start=start, end=end, note=note)


def parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate Databento OPRA historical data cost before downloading.")
    parser.add_argument("--scenario", choices=[*SCENARIOS, "all"], default="one_day_sample")
    parser.add_argument("--scenario-label", help="Optional report label when custom dates override the scenario range.")
    parser.add_argument("--start-date", help="Override scenario start date, YYYY-MM-DD.")
    parser.add_argument("--end-date", help="Override scenario end date, YYYY-MM-DD.")
    parser.add_argument("--window-profile", choices=WINDOW_PROFILES, default="entry_close")
    parser.add_argument("--live-cost-granularity", choices=COST_GRANULARITIES, default="window")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA)
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--stype-in", default=DEFAULT_STYPE_IN)
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--max-live-requests", default=100, type=int)
    parser.add_argument("--review-cost-usd", default=DEFAULT_REVIEW_COST_USD, type=float)
    parser.add_argument("--block-cost-usd", default=DEFAULT_BLOCK_COST_USD, type=float)
    parser.add_argument("--report-path", type=Path, help="Optional Markdown report output path.")
    parser.add_argument("--json-report-path", type=Path, help="Optional JSON report output path.")
    parser.add_argument("--live", action="store_true", help="Call Databento metadata.get_cost. Default is dry-run only.")
    args = parser.parse_args()

    scenarios = SCENARIOS if args.scenario == "all" else [args.scenario]
    if args.scenario == "all" and args.scenario_label:
        parser.error("--scenario-label cannot be used with --scenario all")
    requests: list[CostRequest] = []
    for scenario in scenarios:
        requests.extend(
            build_cost_requests(
                scenario=scenario,
                dataset=args.dataset,
                schema=args.schema,
                symbol=args.symbol,
                stype_in=args.stype_in,
                start_date=parse_date(args.start_date),
                end_date=parse_date(args.end_date),
                window_profile=args.window_profile,
                scenario_label=args.scenario_label,
            )
        )
    live_requests = coalesce_cost_requests(requests, args.live_cost_granularity) if args.live else requests
    result = (
        estimate_live_cost(
            live_requests,
            args.api_key_env,
            args.max_live_requests,
            planned_request_count=len(requests),
            cost_granularity=args.live_cost_granularity,
        )
        if args.live
        else render_plan(requests)
    )
    result = add_cost_decision(result, args.review_cost_usd, args.block_cost_usd)
    if args.json_report_path:
        args.json_report_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    if args.report_path:
        args.report_path.parent.mkdir(parents=True, exist_ok=True)
        args.report_path.write_text(render_markdown_report(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
