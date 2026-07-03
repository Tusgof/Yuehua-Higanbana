# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-08-26T13:30:00+00:00` to `2024-08-30T20:00:00+00:00`
- **Estimated cost USD**: `0.001630961895`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\aug_2024_chunk5_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 50593
- **SHA-256**: `97c8347df424da703272f63512634f8384bead4eeeada091244838d3b9cf6a9f`
