# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-07-15T13:30:00+00:00` to `2024-07-19T20:00:00+00:00`
- **Estimated cost USD**: `0.001590281725`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\jul_2024_chunk3_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 50423
- **SHA-256**: `2f4fcae3c38b5a015ec3f065e3af66d03213feb8ecd9340718bc6841c68be5a6`
