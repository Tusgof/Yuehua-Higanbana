# H-G1 Manifest V3 Bucket Failure Diagnostic

- Status: `diagnostic_complete_h_g1_still_blocked`
- Conclusion: ยังสรุปไม่ได้
- Evidence tier: `E1`
- Paid data used: `False`
- Network used: `False`
- Failed buckets reviewed: `5`
- Primary diagnosis: All blocked rows inside failed buckets are opposite-right ITM options created by moneyness-only buckets. The failure is primarily a bucket-definition/policy problem, not an OI join or timestamp problem.

## Summary

- Blocked rows in failed buckets: `55`
- Opposite-right blocked rows: `55`
- Opposite-right blocked row share: `1.0`
- Minimum computed OI-notional share among failed buckets: `0.880098`

## Failed Buckets

### 2023-08-09 otm_call

- Rows: `24`; computed: `12`; blocked: `12`
- Computed row rate: `0.5`
- Computed OI-notional share: `0.939224`
- Blocked side alignment: `{"opposite_right_for_bucket": 12}`
- Blocked spread pct/mid: `{"max": 0.02934, "median": 0.012532, "min": 0.008772}`
- Blocked mid minus intrinsic: `{"max": -0.04, "median": -0.255, "min": -0.265}`

| right | strike | moneyness | mid | bid | ask | spread_pct_mid | mid_minus_intrinsic | open_interest | side_alignment | greeks_status |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|:--|:--|
| put | 451.0 | 1.005171 | 2.28 | 2.27 | 2.29 | 0.008772 | -0.04 | 2897 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| put | 453.0 | 1.009628 | 4.09 | 4.03 | 4.15 | 0.02934 | -0.23 | 2546 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| put | 452.0 | 1.007399 | 3.135 | 3.12 | 3.15 | 0.009569 | -0.185 | 2171 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| put | 455.0 | 1.014086 | 6.065 | 6.01 | 6.12 | 0.018137 | -0.255 | 469 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| put | 454.0 | 1.011857 | 5.07 | 5.01 | 5.13 | 0.023669 | -0.25 | 349 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |

### 2023-09-13 otm_put

- Rows: `22`; computed: `12`; blocked: `10`
- Computed row rate: `0.545455`
- Computed OI-notional share: `0.880098`
- Blocked side alignment: `{"opposite_right_for_bucket": 10}`
- Blocked spread pct/mid: `{"max": 0.035264, "median": 0.017996, "min": 0.011669}`
- Blocked mid minus intrinsic: `{"max": -0.06, "median": -0.165, "min": -0.175}`

| right | strike | moneyness | mid | bid | ask | spread_pct_mid | mid_minus_intrinsic | open_interest | side_alignment | greeks_status |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|:--|:--|
| call | 440.0 | 0.984274 | 6.875 | 6.8 | 6.95 | 0.021818 | -0.155 | 13182 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| call | 443.0 | 0.990985 | 3.97 | 3.9 | 4.04 | 0.035264 | -0.06 | 2442 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| call | 442.0 | 0.988748 | 4.92 | 4.85 | 4.99 | 0.028455 | -0.11 | 888 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| call | 441.0 | 0.986511 | 5.895 | 5.82 | 5.97 | 0.025445 | -0.135 | 612 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| call | 439.0 | 0.982037 | 7.865 | 7.79 | 7.94 | 0.019072 | -0.165 | 115 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |

### 2024-01-03 otm_put

- Rows: `17`; computed: `6`; blocked: `11`
- Computed row rate: `0.352941`
- Computed OI-notional share: `0.906923`
- Blocked side alignment: `{"opposite_right_for_bucket": 11}`
- Blocked spread pct/mid: `{"max": 0.095238, "median": 0.05379, "min": 0.030552}`
- Blocked mid minus intrinsic: `{"max": 0.015, "median": -0.09, "min": -0.185}`

| right | strike | moneyness | mid | bid | ask | spread_pct_mid | mid_minus_intrinsic | open_interest | side_alignment | greeks_status |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|:--|:--|
| call | 465.0 | 0.988689 | 5.285 | 5.05 | 5.52 | 0.088931 | -0.035 | 2503 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| call | 467.0 | 0.992941 | 3.335 | 3.28 | 3.39 | 0.032984 | 0.015 | 479 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| call | 460.0 | 0.978057 | 10.225 | 9.95 | 10.5 | 0.05379 | -0.095 | 176 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| call | 466.0 | 0.990815 | 4.255 | 4.19 | 4.32 | 0.030552 | -0.065 | 144 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| call | 462.0 | 0.98231 | 8.135 | 7.83 | 8.44 | 0.074985 | -0.185 | 40 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |

### 2024-05-21 otm_call

- Rows: `18`; computed: `9`; blocked: `9`
- Computed row rate: `0.5`
- Computed OI-notional share: `0.984773`
- Blocked side alignment: `{"opposite_right_for_bucket": 9}`
- Blocked spread pct/mid: `{"max": 0.069429, "median": 0.042453, "min": 0.02391}`
- Blocked mid minus intrinsic: `{"max": -0.08, "median": -0.12, "min": -0.135}`

| right | strike | moneyness | mid | bid | ask | spread_pct_mid | mid_minus_intrinsic | open_interest | side_alignment | greeks_status |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|:--|:--|
| put | 533.0 | 1.0068 | 3.52 | 3.46 | 3.58 | 0.034091 | -0.08 | 619 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| put | 534.0 | 1.008689 | 4.465 | 4.31 | 4.62 | 0.069429 | -0.135 | 105 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| put | 536.0 | 1.012467 | 6.48 | 6.3 | 6.66 | 0.055556 | -0.12 | 58 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| put | 540.0 | 1.020023 | 10.48 | 10.3 | 10.66 | 0.034351 | -0.12 | 28 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| put | 535.0 | 1.010578 | 5.48 | 5.3 | 5.66 | 0.065693 | -0.12 | 26 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |

### 2024-12-18 otm_call

- Rows: `30`; computed: `17`; blocked: `13`
- Computed row rate: `0.566667`
- Computed OI-notional share: `0.965892`
- Blocked side alignment: `{"opposite_right_for_bucket": 13}`
- Blocked spread pct/mid: `{"max": 0.027397, "median": 0.020401, "min": 0.01512}`
- Blocked mid minus intrinsic: `{"max": -0.075, "median": -0.245, "min": -0.25}`

| right | strike | moneyness | mid | bid | ask | spread_pct_mid | mid_minus_intrinsic | open_interest | side_alignment | greeks_status |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|:--|:--|
| put | 609.0 | 1.009047 | 5.385 | 5.34 | 5.43 | 0.016713 | -0.075 | 2056 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| put | 610.0 | 1.010704 | 6.315 | 6.26 | 6.37 | 0.017419 | -0.145 | 876 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| put | 611.0 | 1.01236 | 7.275 | 7.22 | 7.33 | 0.01512 | -0.185 | 76 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| put | 613.0 | 1.015674 | 9.27 | 9.17 | 9.37 | 0.021575 | -0.19 | 32 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |
| put | 612.0 | 1.014017 | 8.28 | 8.18 | 8.38 | 0.024155 | -0.18 | 26 | opposite_right_for_bucket | blocked_mid_outside_black_scholes_bracket |

## Decision

Do not use NOVI/net-gamma as a strategy filter yet. Review the bucket policy because the failed row-rate cells are driven by opposite-right ITM rows inside moneyness-only buckets; then choose between a pre-registered side-aware bucket gate, an OI/gamma-notional gate, or another replacement/repair path.
