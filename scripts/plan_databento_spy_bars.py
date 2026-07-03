from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API_KEY_ENV = "DATABENTO_API_KEY"
DATABENTO_API_KEY_ENV_ALIASES = ("DATABENTO_SPY0DTE_API",)
DEFAULT_DATASET = "EQUS.MINI"
DEFAULT_SCHEMA = "ohlcv-1m"
DEFAULT_SYMBOL = "SPY"
DEFAULT_STYPE_IN = "raw_symbol"
DEFAULT_START = "2024-01-02T14:30:00+00:00"
DEFAULT_END = "2024-01-31T21:00:00+00:00"
DEFAULT_PLAN_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_spy_bars_plan.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_spy_bars_plan.md"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "databento" / "spy_bars" / "jan_2024_spy_ohlcv_1m.dbn.zst"


def build_plan(
    dataset: str = DEFAULT_DATASET,
    schema: str = DEFAULT_SCHEMA,
    symbol: str = DEFAULT_SYMBOL,
    stype_in: str = DEFAULT_STYPE_IN,
    start: str = DEFAULT_START,
    end: str = DEFAULT_END,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    estimated_cost_usd: float | None = None,
) -> dict[str, Any]:
    status = "review" if estimated_cost_usd is None else ("pass" if estimated_cost_usd < 1 else "review")
    return {
        "mode": "plan",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "decision": {
            "status": status,
            "reason": "Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.",
            "review_cost_usd": 1.0,
        },
        "request": {
            "dataset": dataset,
            "schema": schema,
            "symbols": [symbol],
            "stype_in": stype_in,
            "start": start,
            "end": end,
            "output_path": str(output_path),
            "estimated_cost_usd": estimated_cost_usd,
        },
    }


def add_live_cost(plan: dict[str, Any], api_key_env: str = DEFAULT_API_KEY_ENV) -> dict[str, Any]:
    api_key = _databento_api_key_from_env(api_key_env)
    if not api_key:
        raise RuntimeError(f"missing Databento API key environment variable: {_databento_env_names(api_key_env)}")
    import databento as db  # type: ignore

    request = plan["request"]
    client = db.Historical(api_key)
    cost = client.metadata.get_cost(
        dataset=request["dataset"],
        symbols=request["symbols"],
        schema=request["schema"],
        stype_in=request["stype_in"],
        start=request["start"],
        end=request["end"],
    )
    return build_plan(
        dataset=request["dataset"],
        schema=request["schema"],
        symbol=request["symbols"][0],
        stype_in=request["stype_in"],
        start=request["start"],
        end=request["end"],
        output_path=Path(request["output_path"]),
        estimated_cost_usd=float(cost),
    )


def execute_download(plan: dict[str, Any], api_key_env: str = DEFAULT_API_KEY_ENV) -> dict[str, Any]:
    api_key = _databento_api_key_from_env(api_key_env)
    if not api_key:
        raise RuntimeError(f"missing Databento API key environment variable: {_databento_env_names(api_key_env)}")
    import databento as db  # type: ignore

    request = plan["request"]
    output_path = Path(request["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    source = "cache"
    if output_path.exists() and output_path.stat().st_size == 0:
        output_path.unlink()
    if not output_path.exists():
        temp_path = output_path.with_name(f"{output_path.name}.download")
        if temp_path.exists():
            temp_path.unlink()
        client = db.Historical(api_key)
        client.timeseries.get_range(
            dataset=request["dataset"],
            symbols=request["symbols"],
            schema=request["schema"],
            stype_in=request["stype_in"],
            start=request["start"],
            end=request["end"],
            path=temp_path,
        )
        temp_path.replace(output_path)
        source = "downloaded"
    result = dict(plan)
    result["mode"] = "download_complete"
    result["downloaded"] = {
        "source": source,
        "output_path": str(output_path),
        "bytes": output_path.stat().st_size,
        "sha256": sha256(output_path),
    }
    return result


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


def render_markdown(plan: dict[str, Any]) -> str:
    request = plan["request"]
    lines = [
        "# Databento SPY 1-Minute Bars Plan",
        "",
        f"- **Mode**: `{plan['mode']}`",
        f"- **Decision**: `{plan['decision']['status']}`",
        f"- **Reason**: {plan['decision']['reason']}",
        f"- **Dataset**: `{request['dataset']}`",
        f"- **Schema**: `{request['schema']}`",
        f"- **Symbol**: `{request['symbols'][0]}`",
        f"- **Window**: `{request['start']}` to `{request['end']}`",
        f"- **Estimated cost USD**: `{request['estimated_cost_usd']}`",
        f"- **Output path**: `{request['output_path']}`",
        "",
        "## Use Rule",
        "",
        "- This plan is for SPY underlying bars needed by ORB logic.",
        "- Low-cost Databento SPY-only research pulls may run after cost logging.",
        "- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.",
        "- Reuse the local output file after download; repeated experiments should not query Databento.",
        "",
    ]
    if "downloaded" in plan:
        downloaded = plan["downloaded"]
        lines.extend(
            [
                "## Downloaded",
                "",
                f"- **Source**: `{downloaded['source']}`",
                f"- **Bytes**: {downloaded['bytes']}",
                f"- **SHA-256**: `{downloaded['sha256']}`",
                "",
            ]
        )
    return "\n".join(lines)


def write_outputs(plan: dict[str, Any], plan_path: Path, report_path: Path) -> None:
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_markdown(plan), encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan or execute Databento SPY 1-minute bar retrieval.")
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA)
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--stype-in", default=DEFAULT_STYPE_IN)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--live-cost", action="store_true")
    parser.add_argument("--execute", action="store_true", help="Download data after cost logging within the approved low-cost Databento scope.")
    args = parser.parse_args()

    plan = build_plan(args.dataset, args.schema, args.symbol, args.stype_in, args.start, args.end, args.output_path)
    if args.live_cost or args.execute:
        plan = add_live_cost(plan, args.api_key_env)
    if args.execute:
        plan = execute_download(plan, args.api_key_env)
    write_outputs(plan, args.plan_path, args.report_path)
    print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
