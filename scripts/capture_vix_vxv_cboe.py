from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PLAN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "vix_vxv_sources_v1.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "vix_vxv"


class VixVxvCaptureError(ValueError):
    pass


def build_capture_plan(
    as_of_date: date,
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    plan = _load_source_plan(source_plan_path)
    source = _primary_source(plan)
    output_dir = output_root / as_of_date.isoformat()
    return {
        "mode": "dry_run",
        "as_of_date": as_of_date.isoformat(),
        "source_plan": str(source_plan_path),
        "output_dir": str(output_dir),
        "requests": [
            {
                "series": "VIX",
                "source_id": source["source_id"],
                "provider": source["provider"],
                "source_url": source["vix_url"],
                "output_path": str(output_dir / "cboe_vix_history.csv"),
            },
            {
                "series": "VIX3M",
                "source_id": source["source_id"],
                "provider": source["provider"],
                "source_url": source["vxv_url"],
                "output_path": str(output_dir / "cboe_vix3m_history.csv"),
            },
        ],
    }


def capture_vix_vxv(
    as_of_date: date,
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    execute: bool = False,
) -> dict[str, Any]:
    capture_plan = build_capture_plan(as_of_date, source_plan_path, output_root)
    if not execute:
        return capture_plan

    output_dir = Path(capture_plan["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    captured = []
    for request in capture_plan["requests"]:
        payload = _fetch_bytes(request["source_url"])
        output_path = Path(request["output_path"])
        output_path.write_bytes(payload)
        captured.append(
            {
                **request,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    manifest = {
        "as_of_date": capture_plan["as_of_date"],
        "source_plan": capture_plan["source_plan"],
        "captured": captured,
    }
    manifest_path = output_dir / "capture_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "mode": "execute",
        "as_of_date": capture_plan["as_of_date"],
        "output_dir": str(output_dir),
        "manifest_path": str(manifest_path),
        "captured_count": len(captured),
        "captured": captured,
    }


def _fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Higanbana research data capture"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise VixVxvCaptureError(f"Cboe volatility index request failed with HTTP {exc.code}: {url}") from exc
    except urllib.error.URLError as exc:
        raise VixVxvCaptureError(f"Cboe volatility index request failed: {exc.reason}") from exc


def _load_source_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise VixVxvCaptureError(f"{path} must contain a JSON object")
    return payload


def _primary_source(plan: dict[str, Any]) -> dict[str, Any]:
    primary_id = plan["primary_source_id"]
    for source in plan["sources"]:
        if source["source_id"] == primary_id:
            return source
    raise VixVxvCaptureError(f"primary source {primary_id!r} not found")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture official Cboe VIX/VIX3M history CSVs for offline import.")
    parser.add_argument("--as-of-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--source-plan-path", type=Path, default=DEFAULT_SOURCE_PLAN_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)

    result = capture_vix_vxv(args.as_of_date, args.source_plan_path, args.output_root, args.execute)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
