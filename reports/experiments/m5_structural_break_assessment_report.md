# M5.7 Structural-Break Assessment

## Status
- Status: `deferred`
- Conclusion: ยังสรุปไม่ได้
- Reason: Structural-break testing around 2022-05-11 is deferred because current local SPY 0DTE option coverage has no reference/pre-break observations before 2022-05-11.
- Evidence type: real-data coverage assessment, not a structural-break performance test.
- No paid API call or data download was performed.

## Methodology
```json
{
  "data_policy": "Read-only coverage audit from existing strategy-data readiness artifact; no paid API calls and no new data download.",
  "decision_rule": "Run structural-break statistics only if all three chronological periods have real option coverage and closed trades.",
  "scope": "Assess whether the May 11 2022 structural-break test can be run from existing local real-data artifacts.",
  "split_policy": {
    "forbid_oos_tuning": true,
    "forbid_random_split": true,
    "oos": {
      "end": "current_available",
      "start": "2024-01-01"
    },
    "post_break_train": {
      "end": "2023-12-31",
      "start": "2022-05-11"
    },
    "reference_pre_break": {
      "end": "2022-05-10",
      "start": "2019-01-01"
    }
  }
}
```

## Period Coverage
| Period | Required window | Actual window | Datasets | Candidate days | Closed trades | Quote rows | SPY bar rows |
|:--|:--|:--|--:|--:|--:|--:|--:|
| `reference_pre_break` | 2019-01-01 to 2022-05-10 | none | 0 | 0 | 0 | 0 | 0 |
| `post_break_train` | 2022-05-11 to 2023-12-31 | 2023-03-01 to 2023-12-29 | 1 | 42 | 41 | 8145550 | 100365 |
| `oos` | 2024-01-01 to current_available | 2024-01-02 to 2024-12-31 | 22 | 51 | 49 | 13357670 | 132148 |

## Blockers

- `requires_minimum_trade_count_500`
- `requires_reference_pre_break_closed_trades`
- `requires_reference_pre_break_option_coverage`

## Interpretation
- The May 11 2022 structural-break question cannot be answered from current local option artifacts because the reference/pre-break period has zero local SPY 0DTE option datasets and zero closed trades.
- Running a comparison with only post-2022 data would not test the stated structural-break hypothesis.
- The correct action is to defer M5.7 until pre-break coverage exists, or explicitly revise the hypothesis away from a pre/post 2022 break test.

## Next Requirements

1. Add or acquire SPY 0DTE option coverage for 2019-01-01 to 2022-05-10 before running a structural-break claim.
2. Backfill the missing post-break training window from 2022-05-11 to 2023-02-28 if the test requires full post-break coverage.
3. Re-run strategy-data readiness and this M5.7 assessment after coverage changes.
4. Keep Jan-Dec 2024 OOS untouched for final evaluation; do not tune M5.7 rules on OOS diagnostics.
