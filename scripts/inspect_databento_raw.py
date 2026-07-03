from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "databento" / "one_month_pilot"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_raw_inspection.md"
DEFAULT_JSON_REPORT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_raw_inspection.json"
OPTION_SYMBOL_RE = re.compile(r"^([A-Z]+)\s+(\d{6})([CP])(\d{8})$")


def inspect_raw_root(raw_root: Path = DEFAULT_RAW_ROOT, max_files: int | None = None) -> dict[str, Any]:
    files = sorted(raw_root.glob("*.dbn.zst"))
    if max_files is not None:
        files = files[:max_files]
    summaries = [inspect_raw_file(path) for path in files]
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "raw_root": str(raw_root),
        "file_count": len(summaries),
        "total_rows": sum(item["row_count"] for item in summaries),
        "total_valid_bid_ask_rows": sum(item["valid_bid_ask_rows"] for item in summaries),
        "total_unique_symbols": sum(item["unique_symbol_count"] for item in summaries),
        "files": summaries,
    }


def inspect_raw_file(path: Path) -> dict[str, Any]:
    import databento as db  # type: ignore

    store = db.DBNStore.from_file(path)
    frame = store.to_df()
    return summarize_frame(
        frame=frame,
        path=path,
        metadata={
            "dataset": str(store.dataset),
            "schema": str(store.schema),
            "start": str(store.start),
            "end": str(store.end),
            "stype_in": str(store.stype_in),
            "symbols": list(store.symbols or []),
        },
    )


def summarize_frame(frame: Any, path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    row_count = int(len(frame))
    columns = list(frame.columns)
    valid_bid_ask_rows = 0
    unique_symbols: list[str] = []
    rights: set[str] = set()
    expirations: set[str] = set()
    strikes: list[float] = []
    ts_recv_start = None
    ts_recv_end = None

    if row_count:
        if getattr(frame, "index", None) is not None:
            ts_recv_start = str(frame.index.min())
            ts_recv_end = str(frame.index.max())
        if "symbol" in frame:
            unique_symbols = sorted(str(value) for value in frame["symbol"].dropna().unique())
            for symbol in unique_symbols:
                parsed = parse_databento_option_symbol(symbol)
                if parsed:
                    rights.add(parsed["right"])
                    expirations.add(parsed["expiration"])
                    strikes.append(parsed["strike"])
        if {"bid_px_00", "ask_px_00"}.issubset(columns):
            valid = frame[(frame["bid_px_00"] > 0) & (frame["ask_px_00"] > 0) & (frame["ask_px_00"] >= frame["bid_px_00"])]
            valid_bid_ask_rows = int(len(valid))

    return {
        "path": str(path),
        "name": path.name,
        "bytes": path.stat().st_size if path.exists() else 0,
        "metadata": metadata,
        "columns": columns,
        "row_count": row_count,
        "valid_bid_ask_rows": valid_bid_ask_rows,
        "ts_recv_start": ts_recv_start,
        "ts_recv_end": ts_recv_end,
        "unique_symbol_count": len(unique_symbols),
        "symbol_examples": unique_symbols[:5],
        "expirations": sorted(expirations),
        "rights": sorted(rights),
        "strike_min": min(strikes) if strikes else None,
        "strike_max": max(strikes) if strikes else None,
    }


def parse_databento_option_symbol(symbol: str) -> dict[str, Any] | None:
    match = OPTION_SYMBOL_RE.match(symbol.strip())
    if not match:
        return None
    underlying, yymmdd, right, strike_raw = match.groups()
    year = 2000 + int(yymmdd[:2])
    expiration = f"{year:04d}-{int(yymmdd[2:4]):02d}-{int(yymmdd[4:6]):02d}"
    return {
        "underlying": underlying,
        "expiration": expiration,
        "right": "call" if right == "C" else "put",
        "strike": int(strike_raw) / 1000,
    }


def render_markdown(inspection: dict[str, Any]) -> str:
    lines = [
        "# Databento Raw Inspection",
        "",
        f"- **Created at UTC**: `{inspection['created_at_utc']}`",
        f"- **Raw root**: `{inspection['raw_root']}`",
        f"- **File count**: {inspection['file_count']}",
        f"- **Total rows**: {inspection['total_rows']}",
        f"- **Total valid bid/ask rows**: {inspection['total_valid_bid_ask_rows']}",
        f"- **Total unique-symbol observations by file**: {inspection['total_unique_symbols']}",
        "",
        "| File | Rows | Valid Bid/Ask | Symbols | Expirations | Rights | Strike Range |",
        "|:--|--:|--:|--:|:--|:--|:--|",
    ]
    for item in inspection["files"]:
        strike_range = (
            f"{item['strike_min']} - {item['strike_max']}"
            if item["strike_min"] is not None and item["strike_max"] is not None
            else "n/a"
        )
        lines.append(
            "| `{name}` | {rows} | {valid} | {symbols} | `{exp}` | `{rights}` | {strike_range} |".format(
                name=item["name"],
                rows=item["row_count"],
                valid=item["valid_bid_ask_rows"],
                symbols=item["unique_symbol_count"],
                exp=", ".join(item["expirations"]),
                rights=", ".join(item["rights"]),
                strike_range=strike_range,
            )
        )
    lines.extend(
        [
            "",
            "## Use Rule",
            "",
            "- This inspection reads local DBN files only.",
            "- Passing this inspection means the raw files are readable and contain bid/ask fields; it is not a strategy result.",
            "- Normalization to canonical `option_quote` records must happen before real backtests.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(inspection: dict[str, Any], report_path: Path, json_report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_markdown(inspection), encoding="utf-8")
    json_report_path.parent.mkdir(parents=True, exist_ok=True)
    json_report_path.write_text(json.dumps(inspection, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect local Databento DBN raw files without calling Databento APIs.")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--max-files", type=int)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--json-report-path", type=Path, default=DEFAULT_JSON_REPORT_PATH)
    args = parser.parse_args()

    inspection = inspect_raw_root(args.raw_root, max_files=args.max_files)
    write_outputs(inspection, args.report_path, args.json_report_path)
    print(json.dumps(inspection, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
