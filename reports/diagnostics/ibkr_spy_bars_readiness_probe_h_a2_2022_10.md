# IBKR SPY Bars Readiness Probe

- **Status**: `ready_for_manual_data_probe`
- **Hypothesis**: `H-A2`
- **Evidence tier**: `E0`
- **Historical data requested**: `False`
- **Orders transmitted**: `False`
- **Paid data used**: `False`

## Port Checks

| Host | Port | Status | Error |
|:-----|-----:|:-------|:------|
| `127.0.0.1` | 7496 | `open` | `` |

## Python Client Checks

| Package | Available |
|:--------|:----------|
| `ib_insync` | `True` |
| `ibapi` | `True` |

## Blockers

- none

## Next Safe Action

Run a separate explicit IBKR historical-bars data probe for SPY 2022-10 using data-only settings; do not transmit orders and do not rerun H-A2 until coverage/timestamp validation passes.
