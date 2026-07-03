# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2023-03-28T13:30:00+00:00` to `2023-03-31T20:00:00+00:00`
- **Estimated cost USD**: `0.001230418682`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\mar_2023_partial_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 39261
- **SHA-256**: `8c910a5246f9c801bad0933ac1af778b5a8e6528a92cc309b75c18c2f4a4b533`
