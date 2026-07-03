# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-09-23T13:30:00+00:00` to `2024-09-30T21:00:00+00:00`
- **Estimated cost USD**: `0.001898825169`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\sep_2024_remainder_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 56015
- **SHA-256**: `1cb522543e5cbc36e9cda25e917acb67d7a77df63018e9054818e71b0b152f2e`
