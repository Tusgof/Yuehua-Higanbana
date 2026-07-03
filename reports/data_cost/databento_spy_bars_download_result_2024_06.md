# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-06-03T13:30:00+00:00` to `2024-06-28T20:00:00+00:00`
- **Estimated cost USD**: `0.006182134151`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\june_2024_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 186973
- **SHA-256**: `e974b64c11b57979d22be6dcab2ae137af08ae227ab4bcc0f274d21c1b53b9ae`
