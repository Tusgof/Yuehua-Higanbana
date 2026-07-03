# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-08-01T13:30:00+00:00` to `2024-08-02T20:00:00+00:00`
- **Estimated cost USD**: `0.000665903091`
- **Output path**: `data\raw\spy_0dte\databento\spy_bars\aug_2024_chunk1_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `downloaded`
- **Bytes**: 24667
- **SHA-256**: `92f08e8856a01daf12421aa1b4743120a659e19d6fb8433aee6db44470b732e9`
