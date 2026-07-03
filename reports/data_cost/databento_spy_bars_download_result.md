# Databento SPY 1-Minute Bars Plan

- **Mode**: `download_complete`
- **Decision**: `pass`
- **Reason**: Low-cost Databento SPY-only research pull is inside the approved scope after cost logging.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-01-02T14:30:00+00:00` to `2024-01-31T21:00:00+00:00`
- **Estimated cost USD**: `0.006720364094`
- **Output path**: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\data\raw\spy_0dte\databento\spy_bars\jan_2024_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Low-cost Databento SPY-only research pulls may run after cost logging.
- Stop before `--execute` if the request changes provider, symbol universe, or exceeds the project stop threshold.
- Reuse the local output file after download; repeated experiments should not query Databento.

## Downloaded

- **Source**: `cache`
- **Bytes**: 208471
- **SHA-256**: `763a594054f21cc9abb820042122e8cc67d4da51b5e071d897a7e4faeb771e53`
