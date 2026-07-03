# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2023-11-01T13:30:00+00:00` to `2023-11-30T21:00:00+00:00`
- **Estimated cost USD**: `0.006614595652`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\nov_2023_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 199525
- **SHA-256**: `46e0ea4c6781a519d09a5089bc10804f7d58ac114e642bda4e1771d39f3a3ffa`
