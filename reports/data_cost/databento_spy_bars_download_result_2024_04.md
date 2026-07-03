# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-04-01T13:30:00+00:00` to `2024-04-30T20:00:00+00:00`
- **Estimated cost USD**: `0.007933884859`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\apr_2024_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 248896
- **SHA-256**: `8ff028a4bf8042ea168b9175c35bc2e3fc8f14cecab22cbc656784de3b47a5a6`
