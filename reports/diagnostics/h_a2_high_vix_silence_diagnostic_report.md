# H-A2 High-VIX Silence Diagnostic

## Status
- Hypothesis: `H-A2`
- Evidence tier: `E1`
- Conclusion: ยังสรุปไม่ได้
- Diagnostic result: `genuine_orb_silence_during_high_vix_window`
- No new paid data: `True`

## Counts
```json
{
  "aug_2024_trade_days": 22,
  "candidate_ready_days": 2,
  "candidate_ready_on_prior_high_vix": 0,
  "candidate_ready_on_prior_stress_vix": 0,
  "candidate_ready_on_same_day_high_vix": 0,
  "candidate_ready_on_same_day_stress_vix": 0,
  "prior_high_vix_days": 3,
  "prior_stress_vix_days": 1,
  "same_day_high_vix_days": 3,
  "same_day_stress_vix_days": 1
}
```

## Date Sets
```json
{
  "candidate_ready_dates": [
    "2024-08-12",
    "2024-08-28"
  ],
  "missing_market_data_on_high_vix_dates": [],
  "missing_vix_dates": [],
  "prior_high_vix_dates": [
    "2024-08-06",
    "2024-08-07",
    "2024-08-08"
  ],
  "prior_stress_vix_dates": [
    "2024-08-06"
  ],
  "same_day_high_vix_dates": [
    "2024-08-05",
    "2024-08-06",
    "2024-08-07"
  ],
  "same_day_stress_vix_dates": [
    "2024-08-05"
  ]
}
```

## Interpretation
- labeling_gap: `False`
- orb_silence_during_high_vix: `True`
- prior_close_shift_note: `The 2024-08-05 VIX spike is visible in same-day close, but M5.5 prior-close policy cannot know it before entry. The ex-ante high-VIX label shifts to later dates after the spike is already observed.`
- research_implication: `Aug 2024 does not currently provide high-VIX ORB trade outcomes; it only shows that the ORB trigger produced no candidate trades during the cached high-VIX stress window.`

## Daily Rows
| Date | Adapter status | Same-day VIX | Prior VIX date | Prior VIX | Same-day high | Prior high | Option rows | SPY bars |
|:--|:--|--:|:--|--:|:--:|:--:|--:|--:|
| 2024-08-01 | `no_trade` | 18.59 | 2024-07-31 | 16.36 | False | False | 33638 | 554 |
| 2024-08-02 | `no_trade` | 23.39 | 2024-08-01 | 18.59 | False | False | 38642 | 510 |
| 2024-08-05 | `no_trade` | 38.57 | 2024-08-02 | 23.39 | True | False | 37808 | 522 |
| 2024-08-06 | `no_trade` | 27.71 | 2024-08-05 | 38.57 | True | True | 41978 | 652 |
| 2024-08-07 | `no_trade` | 27.85 | 2024-08-06 | 27.71 | True | True | 51430 | 622 |
| 2024-08-08 | `no_trade` | 23.79 | 2024-08-07 | 27.85 | False | True | 54210 | 601 |
| 2024-08-09 | `no_trade` | 20.37 | 2024-08-08 | 23.79 | False | False | 58658 | 483 |
| 2024-08-12 | `candidate_ready` | 20.71 | 2024-08-09 | 20.37 | False | False | 54766 | 443 |
| 2024-08-13 | `no_trade` | 18.12 | 2024-08-12 | 20.71 | False | False | 57824 | 558 |
| 2024-08-14 | `no_trade` | 16.19 | 2024-08-13 | 18.12 | False | False | 53932 | 585 |
| 2024-08-15 | `no_trade` | 15.23 | 2024-08-14 | 16.19 | False | False | 51708 | 610 |
| 2024-08-16 | `no_trade` | 14.8 | 2024-08-15 | 15.23 | False | False | 86458 | 506 |
| 2024-08-19 | `no_trade` | 14.65 | 2024-08-16 | 14.8 | False | False | 66164 | 455 |
| 2024-08-20 | `no_trade` | 15.88 | 2024-08-19 | 14.65 | False | False | 41422 | 517 |
| 2024-08-21 | `no_trade` | 16.27 | 2024-08-20 | 15.88 | False | False | 44202 | 514 |
| 2024-08-22 | `no_trade` | 17.55 | 2024-08-21 | 16.27 | False | False | 44202 | 524 |
| 2024-08-23 | `no_trade` | 15.86 | 2024-08-22 | 17.55 | False | False | 45036 | 459 |
| 2024-08-26 | `no_trade` | 16.15 | 2024-08-23 | 15.86 | False | False | 40588 | 468 |
| 2024-08-27 | `no_trade` | 15.43 | 2024-08-26 | 16.15 | False | False | 40588 | 516 |
| 2024-08-28 | `candidate_ready` | 17.11 | 2024-08-27 | 15.43 | False | False | 40588 | 624 |
| 2024-08-29 | `no_trade` | 15.65 | 2024-08-28 | 17.11 | False | False | 40588 | 556 |
| 2024-08-30 | `no_trade` | 15.0 | 2024-08-29 | 15.65 | False | False | 45592 | 442 |
