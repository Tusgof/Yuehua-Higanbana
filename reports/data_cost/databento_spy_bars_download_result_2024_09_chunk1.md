# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-09-03T13:30:00+00:00` to `2024-09-06T20:00:00+00:00`
- **Estimated cost USD**: `0.001371860504`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\sep_2024_chunk1_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 45296
- **SHA-256**: `51a973be61d1adb0adfb6200cdf83656f840a98e4215c7dad1c88610072e4cca`
