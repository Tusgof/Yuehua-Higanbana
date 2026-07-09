from __future__ import annotations

import argparse
import importlib.util
import json
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_2022_spy_bar_source_decision.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "ibkr_spy_bars_readiness_probe_h_a2_2022_10.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "ibkr_spy_bars_readiness_probe_h_a2_2022_10.md"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORTS = (7497, 7496, 4002, 4001)
DEFAULT_PACKAGES = ("ib_insync", "ibapi")


def check_port(host: str, port: int, timeout_seconds: float = 0.5) -> dict[str, Any]:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return {"port": port, "status": "open"}
    except OSError as exc:
        return {"port": port, "status": "closed", "error": exc.__class__.__name__}


def check_package(name: str, package_python: Path | None = None) -> dict[str, Any]:
    if package_python is not None:
        completed = subprocess.run(
            [
                str(package_python),
                "-c",
                f"import importlib.util; raise SystemExit(0 if importlib.util.find_spec({name!r}) else 1)",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        return {
            "package": name,
            "available": completed.returncode == 0,
            "package_python": str(package_python),
        }
    return {"package": name, "available": importlib.util.find_spec(name) is not None}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_readiness_result(
    *,
    decision_path: Path = DEFAULT_DECISION_PATH,
    host: str = DEFAULT_HOST,
    ports: tuple[int, ...] = DEFAULT_PORTS,
    packages: tuple[str, ...] = DEFAULT_PACKAGES,
    package_python: Path | None = None,
    port_checks: list[dict[str, Any]] | None = None,
    package_checks: list[dict[str, Any]] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    decision = _load_json(decision_path)
    port_results = port_checks if port_checks is not None else [check_port(host, port) for port in ports]
    package_results = package_checks if package_checks is not None else [check_package(name, package_python) for name in packages]

    open_ports = [item["port"] for item in port_results if item.get("status") == "open"]
    available_packages = [item["package"] for item in package_results if item.get("available")]
    blockers: list[str] = []
    if decision.get("selected_next_action") != "run_no_paid_ibkr_data_only_probe_if_local_ibkr_setup_is_available":
        blockers.append("h_a2_source_decision_not_locked_to_ibkr_probe")
    if not open_ports:
        blockers.append("no_local_ibkr_api_port_listening")
    if not available_packages:
        blockers.append("missing_ibkr_python_client")

    if open_ports and available_packages and not blockers:
        status = "ready_for_manual_data_probe"
        next_safe_action = (
            "Run a separate explicit IBKR historical-bars data probe for SPY 2022-10 using data-only settings; "
            "do not transmit orders and do not rerun H-A2 until coverage/timestamp validation passes."
        )
    else:
        status = "blocked_local_ibkr_unavailable"
        next_safe_action = (
            "Start local TWS/Gateway with API enabled and confirm market-data permission, then rerun this readiness probe. "
            "If local IBKR cannot be made available, stop for clear user direction before Alpaca or any new paid provider."
        )

    return {
        "schema_version": "ibkr_spy_bars_readiness_probe_v1",
        "generated_at_utc": generated_at_utc or datetime.now(timezone.utc).isoformat(),
        "hypothesis_id": "H-A2",
        "evidence_tier": "E0",
        "status": status,
        "purpose": "Check whether the local machine is ready for a no-paid IBKR data-only SPY 2022-10 historical-bars probe.",
        "decision_path": str(decision_path.relative_to(PROJECT_ROOT)) if decision_path.is_relative_to(PROJECT_ROOT) else str(decision_path),
        "host": host,
        "runtime_python": sys.executable,
        "package_python": str(package_python) if package_python is not None else sys.executable,
        "ports_checked": list(ports),
        "port_checks": port_results,
        "open_ports": open_ports,
        "package_checks": package_results,
        "available_packages": available_packages,
        "blockers": blockers,
        "guardrails": {
            "external_network_used": False,
            "paid_data_used": False,
            "historical_data_requested": False,
            "orders_transmitted": False,
            "broker_execution_enabled": False,
            "new_provider_used": False,
        },
        "forbidden_actions_preserved": [
            "Do not transmit orders.",
            "Do not buy a new paid provider without clear user direction.",
            "Do not buy 2022-09 option data while 2022 underlying bars are unresolved.",
            "Do not rerun H-A2 stress diagnostics until SPY 2022-10 bars pass coverage and timestamp validation.",
        ],
        "next_safe_action": next_safe_action,
        "research_log_required": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
    }


def write_report(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# IBKR SPY Bars Readiness Probe",
        "",
        f"- **Status**: `{result['status']}`",
        f"- **Hypothesis**: `{result['hypothesis_id']}`",
        f"- **Evidence tier**: `{result['evidence_tier']}`",
        f"- **Historical data requested**: `{result['guardrails']['historical_data_requested']}`",
        f"- **Orders transmitted**: `{result['guardrails']['orders_transmitted']}`",
        f"- **Paid data used**: `{result['guardrails']['paid_data_used']}`",
        "",
        "## Port Checks",
        "",
        "| Host | Port | Status | Error |",
        "|:-----|-----:|:-------|:------|",
    ]
    for item in result["port_checks"]:
        lines.append(f"| `{result['host']}` | {item['port']} | `{item['status']}` | `{item.get('error', '')}` |")
    lines.extend(["", "## Python Client Checks", "", "| Package | Available |", "|:--------|:----------|"])
    for item in result["package_checks"]:
        lines.append(f"| `{item['package']}` | `{item['available']}` |")
    lines.extend(["", "## Blockers", ""])
    if result["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in result["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Next Safe Action", "", result["next_safe_action"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe local readiness for an IBKR data-only SPY 2022-10 historical-bars check.")
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--ports", nargs="*", type=int, default=list(DEFAULT_PORTS))
    parser.add_argument(
        "--package-python",
        type=Path,
        default=None,
        help="Optional Python executable used only for IBKR package availability checks.",
    )
    args = parser.parse_args(argv)

    result = build_readiness_result(
        decision_path=args.decision_path,
        host=args.host,
        ports=tuple(args.ports),
        package_python=args.package_python,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    write_report(result, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
