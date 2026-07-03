# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-08-19T13:30:00+00:00` to `2024-08-23T20:00:00+00:00`
- **Estimated cost USD**: `0.001545220613`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\aug_2024_chunk4_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 48114
- **SHA-256**: `28b7d0eac325f207eb2a925d9ed9ae48161e30c416ebf454be43ba5fb572f481`
