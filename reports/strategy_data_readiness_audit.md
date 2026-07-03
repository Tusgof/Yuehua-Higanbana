# Strategy Data Readiness Audit

- Status: `blocked`
- Minimum trade count: 500
- Total closed trades: 90
- Total candidate days: 93
- Total quote rows: 21503220
- Total SPY bar rows: 232513
- Evidence labels: `under-sampled`, `underpowered`
- MinTRL status: `pending_experiment_return_distribution`
- PSR status: `pending_experiment_return_distribution`
- Power status: `underpowered`

## Blockers

- `requires_minimum_trade_count_500`

## Datasets

| Dataset | Split | Status | Candidate days | Closed trades | Quote rows | SPY bar rows | Source |
|:--|:--|:--|--:|--:|--:|--:|:--|
| in_sample_2023_mar_dec | in_sample | `present` | 42 | 41 | 8145550 | 100365 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\insample_2023_mar_dec_multimonth_summary.json` |
| oos_2024_01 | oos | `present` | 6 | 4 | 83125 | 10738 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\jan_2024_pilot_pnl_summary.json` |
| oos_2024_02 | oos | `present` | 3 | 3 | 669424 | 10251 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\feb_2024_pilot_pnl_summary.json` |
| oos_2024_03 | oos | `present` | 4 | 4 | 725580 | 10741 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\mar_2024_pilot_pnl_summary.json` |
| oos_2024_04 | oos | `present` | 5 | 5 | 647966 | 12677 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\apr_2024_pilot_pnl_summary.json` |
| oos_2024_05 | oos | `present` | 6 | 6 | 636064 | 11637 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\may_2024_pilot_pnl_summary.json` |
| oos_2024_06 | oos | `present` | 5 | 5 | 685963 | 9878 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\jun_2024_pilot_pnl_summary.json` |
| oos_2024_07_partial | oos | `present` | 1 | 1 | 269772 | 4177 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\jul_2024_partial_pilot_pnl_summary.json` |
| oos_2024_07_chunk3 | oos | `present` | 1 | 1 | 172638 | 2541 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\jul_2024_chunk3_pilot_pnl_summary.json` |
| oos_2024_07_chunk4 | oos | `present` | 2 | 2 | 150398 | 2625 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\jul_2024_chunk4_pilot_pnl_summary.json` |
| oos_2024_07_chunk5 | oos | `present` | 1 | 1 | 108142 | 1541 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\jul_2024_chunk5_pilot_pnl_summary.json` |
| oos_2024_08_chunk1 | oos | `present` | 0 | 0 | 72280 | 1064 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\aug_2024_chunk1_pilot_pnl_summary.json` |
| oos_2024_08_chunk2 | oos | `present` | 0 | 0 | 244084 | 2880 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\aug_2024_chunk2_pilot_pnl_summary.json` |
| oos_2024_08_chunk3 | oos | `present` | 1 | 1 | 304688 | 2702 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\aug_2024_chunk3_pilot_pnl_summary.json` |
| oos_2024_08_chunk4 | oos | `present` | 0 | 0 | 241026 | 2469 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\aug_2024_chunk4_pilot_pnl_summary.json` |
| oos_2024_08_chunk5 | oos | `present` | 1 | 1 | 207944 | 2606 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\aug_2024_chunk5_pilot_pnl_summary.json` |
| oos_2024_09_chunk1 | oos | `present` | 1 | 1 | 150676 | 2192 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\sep_2024_chunk1_pilot_pnl_summary.json` |
| oos_2024_09_chunk2 | oos | `present` | 1 | 1 | 190791 | 2642 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\sep_2024_chunk2_pilot_pnl_summary.json` |
| oos_2024_09_chunk3 | oos | `present` | 2 | 2 | 224902 | 2618 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\sep_2024_chunk3_pilot_pnl_summary.json` |
| oos_2024_09_remainder | oos | `present` | 1 | 1 | 814850 | 3034 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\sep_2024_remainder_daily_union_pilot_pnl_summary.json` |
| oos_2024_10 | oos | `present` | 2 | 2 | 2480933 | 12212 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\oct_2024_daily_union_pilot_pnl_summary.json` |
| oos_2024_11 | oos | `present` | 5 | 5 | 2268610 | 10087 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\nov_2024_daily_union_pilot_pnl_summary.json` |
| oos_2024_12 | oos | `present` | 3 | 3 | 2007814 | 10836 | `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\pilots\dec_2024_daily_union_pilot_pnl_summary.json` |

## Note

Read-only audit from existing Databento pilot artifacts; no live API calls.
