# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-10-01T13:30:00+00:00` to `2024-10-31T21:00:00+00:00`
- **Estimated cost USD**: `0.007642865181`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\oct_2024_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 233917
- **SHA-256**: `19484210c7bb24a340f25e9e633aef24e25949b51424b2d2daf2f400b82efe25`
