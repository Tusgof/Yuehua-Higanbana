# H-G1 Manifest V3 Candidate Selection

- **Status**: pass
- **Network used**: false
- **Paid data used**: false
- **Removed date**: `2023-07-12`
- **Selected replacement**: `2023-09-13`

## Ranking Table

| Rank | Date | VIX | VIX diff | Macro | Quote cache | SPY bar cache |
|:--|:--|--:|--:|:--|:--:|:--:|
| 1 | 2023-09-13 | 13.48 | 0.06 | CPI | yes | yes |
| 2 | 2023-11-14 | 14.16 | 0.62 | CPI | yes | yes |
| 3 | 2023-06-13 | 14.61 | 1.07 | CPI | yes | yes |
| 4 | 2023-12-12 | 12.07 | 1.47 | CPI | yes | yes |
| 5 | 2023-08-31 | 13.57 | 0.03 | PCE | yes | yes |
| 6 | 2023-06-30 | 13.59 | 0.05 | PCE | yes | yes |
| 7 | 2023-07-28 | 13.33 | 0.21 | PCE | yes | yes |
| 8 | 2023-06-14 | 13.88 | 0.34 | FOMC_DECISION | yes | yes |
| 9 | 2023-07-26 | 13.19 | 0.35 | FOMC_DECISION | yes | yes |
| 10 | 2023-08-01 | 13.93 | 0.39 | JOLTS | yes | yes |
| 11 | 2023-12-22 | 13.03 | 0.51 | PCE | yes | yes |
| 12 | 2023-11-30 | 12.92 | 0.62 | PCE | yes | yes |
| 13 | 2023-12-05 | 12.85 | 0.69 | JOLTS | yes | yes |
| 14 | 2023-08-29 | 14.45 | 0.91 | JOLTS | yes | yes |
| 15 | 2023-12-13 | 12.19 | 1.35 | FOMC_DECISION | yes | yes |

## Guardrails

- Candidate selection used only macro event type, same-day VIX close, and local cache presence.
- Gamma/OI result, strategy PnL, and post-decision realized volatility were not used.
- The next allowed action is metadata cost check for the one replacement OPRA statistics/OI day after manifest validation passes.
