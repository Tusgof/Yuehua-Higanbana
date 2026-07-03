# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-03-01T14:30:00+00:00` to `2024-03-29T20:00:00+00:00`
- **Estimated cost USD**: `0.00672224164`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\mar_2024_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 204715
- **SHA-256**: `cabc4c047fc8a9e20dc4e6acfa256944e794f404272089688fd430d7d7c024f6`
