# Databento SPY 1-Minute Bars Plan

- **Mode**: `plan`
- **Decision**: `pass`
- **Reason**: Download still requires explicit user approval even when the estimated cost is small.
- **Dataset**: `EQUS.MINI`
- **Schema**: `ohlcv-1m`
- **Symbol**: `SPY`
- **Window**: `2024-01-02T14:30:00+00:00` to `2024-01-31T21:00:00+00:00`
- **Estimated cost USD**: `0.006720364094`
- **Output path**: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\data\raw\spy_0dte\databento\spy_bars\jan_2024_spy_ohlcv_1m.dbn.zst`

## Use Rule

- This plan is for SPY underlying bars needed by ORB logic.
- Do not run `--execute` without explicit user approval.
- Reuse the local output file after download; repeated experiments should not query Databento.
