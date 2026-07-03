from __future__ import annotations

import argparse
import csv
import html
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CAPTURE_ROOT = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "macro_calendar" / "2026-06-30"

FIELDNAMES = ["source_id", "event_type", "event_date", "release_time_et", "title"]
MONTH_ALIASES = {
    "Jan": "January",
    "Feb": "February",
    "Mar": "March",
    "Apr": "April",
    "Jun": "June",
    "Jul": "July",
    "Aug": "August",
    "Sep": "September",
    "Sept": "September",
    "Oct": "October",
    "Nov": "November",
    "Dec": "December",
}


class MacroCalendarConvertError(ValueError):
    pass


def convert_capture_to_csv(capture_root: Path = DEFAULT_CAPTURE_ROOT, output_path: Path | None = None) -> dict[str, Any]:
    capture_year = _infer_capture_year(capture_root)
    output_path = output_path or _default_output_path(capture_root)
    rows: list[dict[str, str]] = []
    rows.extend(_parse_fomc(capture_root / "federal_reserve_fomc_calendar.html", capture_year))
    rows.extend(_parse_bls(capture_root / "bls_release_calendar.html"))
    rows.extend(_parse_bea(_bea_capture_path(capture_root), capture_year))
    rows.extend(_parse_ism(capture_root / "ism_pmi_release_calendar.html", capture_year))
    rows.extend(_parse_census_retail(_census_capture_path(capture_root), capture_year))
    rows = sorted(_dedupe_rows(rows), key=lambda row: (row["event_date"], row["release_time_et"], row["event_type"], row["title"]))
    if not rows:
        raise MacroCalendarConvertError("no macro calendar rows extracted")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return {
        "output_path": str(output_path),
        "record_count": len(rows),
        "event_types": sorted({row["event_type"] for row in rows}),
        "coverage_start": rows[0]["event_date"],
        "coverage_end": rows[-1]["event_date"],
    }


def _parse_fomc(path: Path, year: int) -> list[dict[str, str]]:
    text = _read(path)
    section = _section_between(text, rf"{year} FOMC Meetings", rf"{year - 1} FOMC Meetings")
    blocks = re.findall(r'<div class="[^"]*fomc-meeting[^"]*"[^>]*>(.*?)</div>\s*</div>', section, flags=re.I | re.S)
    rows: list[dict[str, str]] = []
    for block in blocks:
        month_match = re.search(r'fomc-meeting__month[^>]*>\s*<strong>([^<]+)</strong>', block, flags=re.I)
        date_match = re.search(r'fomc-meeting__date[^>]*>([^<]+)</div>', block, flags=re.I)
        if not month_match or not date_match:
            continue
        month = _final_month_label(_clean(month_match.group(1)))
        day = _last_day_in_range(_clean(date_match.group(1)))
        decision_date = _parse_month_day_year(f"{month} {day}, {year}")
        rows.append(
            {
                "source_id": "federal_reserve_fomc_calendar",
                "event_type": "FOMC_DECISION",
                "event_date": decision_date,
                "release_time_et": "14:00",
                "title": f"FOMC decision {decision_date}",
            }
        )
        minutes_match = re.search(rf"Released\s+([A-Za-z]+\s+\d{{1,2}},\s+{year})", block, flags=re.I)
        if minutes_match:
            minutes_date = _parse_month_day_year(minutes_match.group(1))
            rows.append(
                {
                    "source_id": "federal_reserve_fomc_calendar",
                    "event_type": "FOMC_MINUTES",
                    "event_date": minutes_date,
                    "release_time_et": "14:00",
                    "title": f"FOMC minutes for {decision_date}",
                }
            )
    return rows


def _parse_bls(path: Path) -> list[dict[str, str]]:
    text = _read(path)
    rows = _parse_bls_month_calendar(text)
    if rows:
        return rows

    rows = _parse_bls_yearly_list(text)
    if rows:
        return rows

    raise MacroCalendarConvertError("BLS page missing supported schedule rows")


def _parse_bls_month_calendar(text: str) -> list[dict[str, str]]:
    year_match = re.search(r"<h1[^>]*>\s*([A-Za-z]+)\s+(\d{4})\s*</h1>", text, flags=re.I)
    if not year_match:
        return []
    year = int(year_match.group(2))
    rows: list[dict[str, str]] = []
    for cell_match in re.finditer(r'<td[^>]*id="d(\d{2})(\d{2})"[^>]*>(.*?)</td>', text, flags=re.I | re.S):
        month = int(cell_match.group(1))
        day = int(cell_match.group(2))
        cell = cell_match.group(3)
        for title, release_time in re.findall(r"<strong>(.*?)<br>\s*</strong>.*?<br>\s*([0-9]{1,2}:[0-9]{2}\s+[AP]M)", cell, flags=re.I | re.S):
            clean_title = _clean(title)
            event_type = {
                "Consumer Price Index": "CPI",
                "Employment Situation": "NFP",
                "Job Openings and Labor Turnover Survey": "JOLTS",
            }.get(clean_title)
            if not event_type:
                continue
            rows.append(
                {
                    "source_id": "bls_release_calendar",
                    "event_type": event_type,
                    "event_date": f"{year:04d}-{month:02d}-{day:02d}",
                    "release_time_et": _to_24h(release_time),
                    "title": clean_title,
                }
            )
    return rows


def _parse_bls_yearly_list(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in re.findall(r"<tr(?:\s[^>]*)?>(.*?)</tr>", text, flags=re.I | re.S):
        clean_row = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", row))).strip()
        title_match = re.search(r"<strong>\s*(.*?)\s*</strong>", row, flags=re.I | re.S)
        title = _clean(title_match.group(1)) if title_match else ""
        event_type = _bls_event_type(title)
        if not event_type:
            continue
        date_match = re.search(r"\b([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})\b", clean_row)
        time_match = re.search(r"\b([0-9]{1,2}:[0-9]{2}\s+[AP]M)\b", clean_row, flags=re.I)
        if not date_match or not time_match:
            continue
        rows.append(
            {
                "source_id": "bls_release_calendar",
                "event_type": event_type,
                "event_date": _parse_month_day_year(date_match.group(0)),
                "release_time_et": _to_24h(time_match.group(1)),
                "title": title,
            }
        )
    return rows


def _bls_event_type(value: str) -> str | None:
    if value == "Consumer Price Index":
        return "CPI"
    if value == "Employment Situation":
        return "NFP"
    if value == "Job Openings and Labor Turnover Survey":
        return "JOLTS"
    return None


def _parse_bea(path: Path, year: int) -> list[dict[str, str]]:
    if path.suffix.lower() == ".json":
        return _parse_bea_release_pages_json(path, year)

    text = _read(path)
    rows: list[dict[str, str]] = []
    pattern = (
        r'<td class="scheduled-date[^"]*"[^>]*>\s*<div class="release-date">([^<]+)</div>\s*'
        r'<small[^>]*>([^<]+)</small>.*?'
        r'<td class="release-title[^"]*"[^>]*>(.*?)</td>'
    )
    for date_text, time_text, title in re.findall(pattern, text, flags=re.I | re.S):
        clean_title = _clean(title)
        if "Personal Income and Outlays" not in clean_title:
            continue
        rows.append(
            {
                "source_id": "bea_release_schedule",
                "event_type": "PCE",
                "event_date": _parse_month_day_year(f"{_clean(date_text)}, {year}"),
                "release_time_et": _to_24h(time_text),
                "title": clean_title,
            }
        )
    return rows


def _parse_bea_release_pages_json(path: Path, year: int) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    for page in payload.get("pages", []):
        text = str(page.get("content", ""))
        title = _clean(str(page.get("title", "")))
        embargo = re.search(r"EMBARGOED\s+UNTIL\s+RELEASE\s+AT\s+([^<]+)", text, flags=re.I)
        if not embargo:
            continue
        release_date, release_time = _parse_bea_embargo(embargo.group(1))
        if not release_date.startswith(f"{year:04d}-"):
            continue
        rows.append(
            {
                "source_id": "bea_release_schedule",
                "event_type": "PCE",
                "event_date": release_date,
                "release_time_et": release_time,
                "title": title or "Personal Income and Outlays",
            }
        )
    return rows


def _parse_bea_embargo(value: str) -> tuple[str, str]:
    cleaned = _clean(value).replace("A.M.", "AM").replace("P.M.", "PM").replace("a.m.", "AM").replace("p.m.", "PM")
    time_match = re.search(r"(\d{1,2}:\d{2})\s*([AP]M)", cleaned, flags=re.I)
    date_match = re.search(r"([A-Za-z]+\s+\d{1,2},\s+\d{4})", cleaned)
    if not time_match or not date_match:
        raise MacroCalendarConvertError(f"BEA embargo timestamp not parseable: {value}")
    return _parse_month_day_year(date_match.group(1)), _to_24h(f"{time_match.group(1)} {time_match.group(2).upper()}")


def _parse_ism(path: Path, year: int) -> list[dict[str, str]]:
    text = _read(path)
    try:
        table = _section_between(text, rf"{year} ISM PMI", r"</tbody>")
    except MacroCalendarConvertError:
        if "Manufacturing and Services ISM PMI" not in text:
            raise
        return _parse_ism_from_release_rule(year)
    rows: list[dict[str, str]] = []
    for month_text, manufacturing_day, services_day in re.findall(
        rf"<tr>\s*<th[^>]*>([A-Za-z]+\s+{year})</th>\s*<td>(.*?)</td>\s*<td>(.*?)</td>",
        table,
        flags=re.I | re.S,
    ):
        month = _clean(month_text).split()[0]
        for event_type, day_text, title in [
            ("ISM_MANUFACTURING", manufacturing_day, "ISM Manufacturing PMI"),
            ("ISM_SERVICES", services_day, "ISM Services PMI"),
        ]:
            day = _first_int(day_text)
            if day is None:
                continue
            rows.append(
                {
                    "source_id": "ism_pmi_release_calendar",
                    "event_type": event_type,
                    "event_date": _parse_month_day_year(f"{month} {day}, {year}"),
                    "release_time_et": "10:00",
                    "title": title,
                }
            )
    return rows


def _parse_ism_from_release_rule(year: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for month in range(1, 13):
        manufacturing_n = 2 if month == 1 else 1
        services_n = 4 if month == 1 else 3
        rows.extend(
            [
                {
                    "source_id": "ism_pmi_release_calendar",
                    "event_type": "ISM_MANUFACTURING",
                    "event_date": _nth_nyse_business_day(year, month, manufacturing_n).isoformat(),
                    "release_time_et": "10:00",
                    "title": "ISM Manufacturing PMI",
                },
                {
                    "source_id": "ism_pmi_release_calendar",
                    "event_type": "ISM_SERVICES",
                    "event_date": _nth_nyse_business_day(year, month, services_n).isoformat(),
                    "release_time_et": "10:00",
                    "title": "ISM Services PMI",
                },
            ]
        )
    return rows


def _parse_census_retail(path: Path, year: int) -> list[dict[str, str]]:
    if path.suffix.lower() == ".xls":
        return _parse_census_retail_xls(path, year)

    text = _read(path)
    section = _section_between(text, r"Advance Monthly Retail Trade Report", r"Monthly Retail Trade Report")
    rows: list[dict[str, str]] = []
    for data_month, release_date in re.findall(
        r"<tr>\s*<td[^>]*>([A-Za-z]+\s+\d{4})</td>\s*<td[^>]*>([A-Za-z]+\s+\d{1,2},\s+\d{4})</td>\s*</tr>",
        section,
        flags=re.I | re.S,
    ):
        rows.append(
            {
                "source_id": "census_retail_release_schedule",
                "event_type": "RETAIL_SALES",
                "event_date": _parse_month_day_year(_clean(release_date)),
                "release_time_et": "08:30",
                "title": f"Advance Monthly Retail Trade Report for {_clean(data_month)}",
            }
        )
    return rows


def _parse_census_retail_xls(path: Path, year: int) -> list[dict[str, str]]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise MacroCalendarConvertError("pandas is required to parse Census retail release-date XLS files") from exc

    frame = pd.read_excel(path, header=None)
    rows: list[dict[str, str]] = []
    month_labels = [str(value).strip() for value in frame.iloc[3, 1:13].tolist()]
    for _, row in frame.iloc[4:].iterrows():
        release_year = _coerce_int(row.iloc[0])
        if release_year != year:
            continue
        for month_index, month_label in enumerate(month_labels, start=1):
            day = _coerce_int(row.iloc[month_index])
            if day is None:
                continue
            release_date = date(year, month_index, day).isoformat()
            rows.append(
                {
                    "source_id": "census_retail_release_schedule",
                    "event_type": "RETAIL_SALES",
                    "event_date": release_date,
                    "release_time_et": "08:30",
                    "title": f"Advance Monthly Retail Trade Report released {month_label} {year}",
                }
            )
    return rows


def _dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (row["source_id"], row["event_type"], row["event_date"], row["title"])
        deduped[key] = row
    return list(deduped.values())


def _infer_capture_year(capture_root: Path) -> int:
    match = re.match(r"(\d{4})", capture_root.name)
    if not match:
        raise MacroCalendarConvertError(f"capture root name must start with YYYY: {capture_root}")
    return int(match.group(1))


def _census_capture_path(capture_root: Path) -> Path:
    xls_path = capture_root / "census_retail_release_schedule.xls"
    if xls_path.exists():
        return xls_path
    return capture_root / "census_retail_release_schedule.html"


def _bea_capture_path(capture_root: Path) -> Path:
    json_path = capture_root / "bea_release_schedule.json"
    if json_path.exists():
        return json_path
    return capture_root / "bea_release_schedule.html"


def _default_output_path(capture_root: Path) -> Path:
    return capture_root / f"official_macro_calendar_{capture_root.name}.csv"


def _section_between(text: str, start_pattern: str, end_pattern: str) -> str:
    start = re.search(start_pattern, text, flags=re.I)
    if not start:
        raise MacroCalendarConvertError(f"section start not found: {start_pattern}")
    end = re.search(end_pattern, text[start.end() :], flags=re.I)
    if not end:
        raise MacroCalendarConvertError(f"section end not found: {end_pattern}")
    return text[start.end() : start.end() + end.start()]


def _read(path: Path) -> str:
    if not path.exists():
        raise MacroCalendarConvertError(f"missing raw capture file: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", value))).strip()


def _last_day_in_range(value: str) -> int:
    cleaned = re.sub(r"[^0-9-]", "", value)
    return int(cleaned.split("-")[-1])


def _final_month_label(value: str) -> str:
    month = value.split("/")[-1].strip()
    return MONTH_ALIASES.get(month, month)


def _first_int(value: str) -> int | None:
    match = re.search(r"\d+", _clean(value))
    return int(match.group(0)) if match else None


def _coerce_int(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


def _parse_month_day_year(value: str) -> str:
    return datetime.strptime(value, "%B %d, %Y").date().isoformat()


def _to_24h(value: str) -> str:
    return datetime.strptime(_clean(value).upper(), "%I:%M %p").strftime("%H:%M")


def _nth_nyse_business_day(year: int, month: int, n: int) -> date:
    current = date(year, month, 1)
    holidays = _us_equity_market_holidays(year)
    count = 0
    while current.month == month:
        if current.weekday() < 5 and current not in holidays:
            count += 1
            if count == n:
                return current
        current += timedelta(days=1)
    raise MacroCalendarConvertError(f"month {year}-{month:02d} has fewer than {n} NYSE business days")


def _us_equity_market_holidays(year: int) -> set[date]:
    holidays = {
        _observed_fixed_holiday(year, 1, 1),
        _nth_weekday(year, 1, 0, 3),
        _nth_weekday(year, 2, 0, 3),
        _good_friday(year),
        _last_weekday(year, 5, 0),
        _observed_fixed_holiday(year, 6, 19),
        _observed_fixed_holiday(year, 7, 4),
        _nth_weekday(year, 9, 0, 1),
        _nth_weekday(year, 11, 3, 4),
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert archived official macro calendar source pages into importer CSV shape.")
    parser.add_argument("--capture-root", type=Path, default=DEFAULT_CAPTURE_ROOT)
    parser.add_argument("--output-path", type=Path)
    args = parser.parse_args(argv)

    result = convert_capture_to_csv(args.capture_root, args.output_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
