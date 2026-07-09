# IBKR SPY Bars Readiness Probe

- **Status**: `blocked_local_ibkr_unavailable`
- **Hypothesis**: `H-A2`
- **Evidence tier**: `E0`
- **Historical data requested**: `False`
- **Orders transmitted**: `False`
- **Paid data used**: `False`

## Port Checks

| Host | Port | Status | Error |
|:-----|-----:|:-------|:------|
| `127.0.0.1` | 7497 | `closed` | `TimeoutError` |
| `127.0.0.1` | 7496 | `closed` | `TimeoutError` |
| `127.0.0.1` | 4002 | `closed` | `TimeoutError` |
| `127.0.0.1` | 4001 | `closed` | `TimeoutError` |

## Python Client Checks

| Package | Available |
|:--------|:----------|
| `ib_insync` | `True` |
| `ibapi` | `True` |

## Blockers

- `no_local_ibkr_api_port_listening`

## Next Safe Action

Start local TWS/Gateway with API enabled and confirm market-data permission, then rerun this readiness probe. If local IBKR cannot be made available, stop for clear user direction before Alpaca or any new paid provider.
