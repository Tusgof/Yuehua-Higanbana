# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-07-29T13:30:00+00:00` to `2024-07-31T20:00:00+00:00`
- **Estimated cost USD**: `0.000964432955`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\jul_2024_chunk5_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 32518
- **SHA-256**: `9f55b03a75db49adbf5dd43a7320f1fe81fd58e5a43bac42415204748950accb`
