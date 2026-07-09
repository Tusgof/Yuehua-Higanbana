# H-G1 Bucket Failure Diagnostic

- Status: `diagnostic_complete_h_g1_still_blocked`
- Paid data used: `False`
- Network used: `False`
- Total rows: `2834`
- Failed buckets reviewed: `5`
- Interpretation: Most failures need policy review, but at least one failed bucket also has weak OI-notional coverage; H-G1 should remain blocked until that date/bucket is repaired or replaced.

## Failed Buckets

### 2023-07-12 otm_put

- Rows: `22`; computed: `12`; blocked: `10`
- Computed row rate: `0.545455`
- Computed OI-notional share: `0.662545`
- Blocked status counts: `{"blocked_mid_outside_black_scholes_bracket": 10}`
- Moneyness range: `{"max": 0.994, "min": 0.971613}`

| right | strike | moneyness | mid | open_interest | oi_notional | greeks_status |
|:--|--:|--:|--:|--:|--:|:--|
| call | 441.0 | 0.987284 | 5.545 | 12839 | 573492452.0 | blocked_mid_outside_black_scholes_bracket |
| call | 443.0 | 0.991761 | 3.64 | 12612 | 563352816.0 | blocked_mid_outside_black_scholes_bracket |
| call | 440.0 | 0.985045 | 6.54 | 11869 | 530164492.0 | blocked_mid_outside_black_scholes_bracket |
| call | 442.0 | 0.989523 | 4.565 | 11240 | 502068320.0 | blocked_mid_outside_black_scholes_bracket |
| call | 439.0 | 0.982806 | 7.525 | 6108 | 272832144.0 | blocked_mid_outside_black_scholes_bracket |

### 2023-08-09 otm_call

- Rows: `24`; computed: `12`; blocked: `12`
- Computed row rate: `0.5`
- Computed OI-notional share: `0.939224`
- Blocked status counts: `{"blocked_mid_outside_black_scholes_bracket": 12}`
- Moneyness range: `{"max": 1.029687, "min": 1.005171}`

| right | strike | moneyness | mid | open_interest | oi_notional | greeks_status |
|:--|--:|--:|--:|--:|--:|:--|
| put | 451.0 | 1.005171 | 2.28 | 2897 | 129982596.0 | blocked_mid_outside_black_scholes_bracket |
| put | 453.0 | 1.009628 | 4.09 | 2546 | 114233928.0 | blocked_mid_outside_black_scholes_bracket |
| put | 452.0 | 1.007399 | 3.135 | 2171 | 97408428.0 | blocked_mid_outside_black_scholes_bracket |
| put | 455.0 | 1.014086 | 6.065 | 469 | 21043092.0 | blocked_mid_outside_black_scholes_bracket |
| put | 454.0 | 1.011857 | 5.07 | 349 | 15658932.0 | blocked_mid_outside_black_scholes_bracket |

### 2024-01-03 otm_put

- Rows: `17`; computed: `6`; blocked: `11`
- Computed row rate: `0.352941`
- Computed OI-notional share: `0.906923`
- Blocked status counts: `{"blocked_mid_outside_black_scholes_bracket": 11}`
- Moneyness range: `{"max": 0.992941, "min": 0.971679}`

| right | strike | moneyness | mid | open_interest | oi_notional | greeks_status |
|:--|--:|--:|--:|--:|--:|:--|
| call | 465.0 | 0.988689 | 5.285 | 2503 | 117721096.0 | blocked_mid_outside_black_scholes_bracket |
| call | 467.0 | 0.992941 | 3.335 | 479 | 22528328.0 | blocked_mid_outside_black_scholes_bracket |
| call | 460.0 | 0.978057 | 10.225 | 176 | 8277632.0 | blocked_mid_outside_black_scholes_bracket |
| call | 466.0 | 0.990815 | 4.255 | 144 | 6772608.0 | blocked_mid_outside_black_scholes_bracket |
| call | 462.0 | 0.98231 | 8.135 | 40 | 1881280.0 | blocked_mid_outside_black_scholes_bracket |

### 2024-05-21 otm_call

- Rows: `18`; computed: `9`; blocked: `9`
- Computed row rate: `0.5`
- Computed OI-notional share: `0.984773`
- Blocked status counts: `{"blocked_mid_outside_black_scholes_bracket": 9}`
- Moneyness range: `{"max": 1.029467, "min": 1.0068}`

| right | strike | moneyness | mid | open_interest | oi_notional | greeks_status |
|:--|--:|--:|--:|--:|--:|:--|
| put | 533.0 | 1.0068 | 3.52 | 619 | 32769860.0 | blocked_mid_outside_black_scholes_bracket |
| put | 534.0 | 1.008689 | 4.465 | 105 | 5558700.0 | blocked_mid_outside_black_scholes_bracket |
| put | 536.0 | 1.012467 | 6.48 | 58 | 3070520.0 | blocked_mid_outside_black_scholes_bracket |
| put | 540.0 | 1.020023 | 10.48 | 28 | 1482320.0 | blocked_mid_outside_black_scholes_bracket |
| put | 535.0 | 1.010578 | 5.48 | 26 | 1376440.0 | blocked_mid_outside_black_scholes_bracket |

### 2024-12-18 otm_call

- Rows: `30`; computed: `17`; blocked: `13`
- Computed row rate: `0.566667`
- Computed OI-notional share: `0.965892`
- Blocked status counts: `{"blocked_mid_outside_black_scholes_bracket": 13}`
- Moneyness range: `{"max": 1.028929, "min": 1.005733}`

| right | strike | moneyness | mid | open_interest | oi_notional | greeks_status |
|:--|--:|--:|--:|--:|--:|:--|
| put | 609.0 | 1.009047 | 5.385 | 2056 | 124087824.0 | blocked_mid_outside_black_scholes_bracket |
| put | 610.0 | 1.010704 | 6.315 | 876 | 52870104.0 | blocked_mid_outside_black_scholes_bracket |
| put | 611.0 | 1.01236 | 7.275 | 76 | 4586904.0 | blocked_mid_outside_black_scholes_bracket |
| put | 613.0 | 1.015674 | 9.27 | 32 | 1931328.0 | blocked_mid_outside_black_scholes_bracket |
| put | 612.0 | 1.014017 | 8.28 | 26 | 1569204.0 | blocked_mid_outside_black_scholes_bracket |

## Next Safe Action

Review whether the v2 policy should use OI-notional coverage as the primary bucket gate, or replace the low-notional failed dates with a v3 pre-registered date set. Do not claim H-G1 pass yet.
