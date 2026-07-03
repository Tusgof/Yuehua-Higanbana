# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2023-09-01T13:30:00+00:00` to `2023-09-29T20:00:00+00:00`
- **Estimated cost USD**: `0.006397426128`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\sep_2023_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 199015
- **SHA-256**: `d66a11f191f670af7c92b6a9aeb894e239f401862af905422a5c4cefaacecebf`
