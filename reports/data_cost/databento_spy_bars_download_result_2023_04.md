# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2023-04-03T13:30:00+00:00` to `2023-04-28T20:00:00+00:00`
- **Estimated cost USD**: `0.006508827209`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\apr_2023_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 196047
- **SHA-256**: `b0a2b20d0ae548ea7729811dc1bcc3e56132713918493a812f55e8ad89879a62`
