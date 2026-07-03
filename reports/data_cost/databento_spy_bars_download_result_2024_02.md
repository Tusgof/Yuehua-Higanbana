# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-02-01T14:30:00+00:00` to `2024-02-29T21:00:00+00:00`
- **Estimated cost USD**: `0.006415575743`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\feb_2024_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 199814
- **SHA-256**: `d2ad86488859c51cde7cda6b91991ef50716225133ca1980a3cf3dc4d899fd4e`
