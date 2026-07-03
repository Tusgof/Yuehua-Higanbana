# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-12-02T14:30:00+00:00` to `2024-12-31T21:00:00+00:00`
- **Estimated cost USD**: `0.006781697273`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\dec_2024_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 211558
- **SHA-256**: `7ba8a2d7d66a918bedba4a836626fe8b8a857307817ce137b62ae06c4714b7f3`
