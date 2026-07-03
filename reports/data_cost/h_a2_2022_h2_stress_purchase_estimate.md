# H-A2 2022 H2 Stress Purchase Estimate

## Status
- Mode: `projection_no_databento_api_call`
- No new paid data: `True`
- Remaining before stop: `$20.0`
- Recommendation: `live_cost_check_top2_only`
- Reason: Top2 is the only candidate that plausibly fits the current headroom on base projection; top3 likely requires top-up.

## Ranked 2022 H2 Months
| Rank | Month | Trading days | Avg VIX | Max VIX | High>=25 days | Stress>=30 days |
|--:|:--|--:|--:|--:|--:|--:|
| 1 | `2022-10` | 21 | 30.0057 | 33.63 | 21 | 11 |
| 2 | `2022-09` | 21 | 27.4062 | 32.6 | 17 | 5 |
| 3 | `2022-07` | 20 | 24.8685 | 27.54 | 9 | 0 |
| 4 | `2022-11` | 21 | 23.4362 | 26.09 | 5 | 0 |
| 5 | `2022-08` | 23 | 22.1696 | 26.21 | 4 | 0 |
| 6 | `2022-12` | 21 | 21.7843 | 25.0 | 1 | 0 |

## Purchase Candidates
| Candidate | Months | Projected cost low/base/high | Headroom status | Projected candidates base |
|:--|:--|:--|:--|--:|
| `top2` | `2022-10, 2022-09` | $12.256252 / $16.923156 / $25.343452 | `fits_base_projection` | 8.44 |
| `top3` | `2022-10, 2022-09, 2022-07` | $18.384378 / $25.384734 / $38.015178 | `requires_live_cost_or_topup` | 12.45 |

## Cost Model
```json
{
  "comparable_month_costs": {
    "2023-09": 6.128126,
    "2023-10": 7.271917,
    "2023-11": 6.722094,
    "2023-12": 6.601407,
    "2024-02": 8.605623,
    "2024-03": 7.101296,
    "2024-04": 7.480666,
    "2024-05": 7.848551,
    "2024-06": 7.091976,
    "2024-07": 8.362379,
    "2024-08": 9.285274,
    "2024-09": 9.187169,
    "2024-10": 12.671726,
    "2024-11": 11.060765,
    "2024-12": 11.504703
  },
  "comparable_month_count": 15,
  "per_month_base_usd": 8.461578,
  "per_month_high_usd": 12.671726,
  "per_month_low_usd": 6.128126,
  "source": "existing Databento download_result artifacts; projection only, not a live Databento quote"
}
```

## Trade Density Model
```json
{
  "aug_2024_candidate_rate": 0.090909,
  "note": "Candidate density is uncertain in 2022 because option data is not downloaded yet; use this only as a pre-purchase density warning.",
  "observed_candidate_ready_days": 93,
  "observed_month_count": 22,
  "observed_trade_days": 463,
  "overall_candidate_rate": 0.200864,
  "source": "existing pilot adapter summaries; projection only"
}
```
