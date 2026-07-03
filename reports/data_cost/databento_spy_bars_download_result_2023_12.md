# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2023-12-01T14:30:00+00:00` to `2023-12-29T21:00:00+00:00`
- **Estimated cost USD**: `0.006180882454`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\dec_2023_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 188004
- **SHA-256**: `2cf858f80703ba8998f054dd1e86430c353b2754926ca6cda2b9504a2eddf2fc`
