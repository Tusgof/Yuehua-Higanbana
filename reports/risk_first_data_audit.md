# Risk-First Data Audit

- Status: `blocked`
- Trade sample: 90
- Observed Sharpe: `0.092203`
- Skewness: `1.221374`
- Kurtosis: `3.09085`
- First-order autocorrelation: `-0.02181`
- Labels: `under-sampled`, `underpowered`
- Next safe action: Do not buy broad calendar data yet. The local Greeks/OI enrichment probe passed with caveats; next define gamma aggregation/scaling and validation policy, or choose a targeted sample/regime expansion for pre-break, high-VIX, or major-macro coverage.

## Blockers

- `requires_mintrl_psr_sample_adequacy`
- `regime_coverage:missing_reference_pre_break_regime_trades`
- `regime_coverage:missing_high_vix_trade_coverage`
- `regime_coverage:trend_bucket_has_insufficient_prior_bar_history`
- `greeks_data_probe:normalized_option_quotes_missing_vendor_greeks`
- `greeks_data_probe:normalized_option_quotes_missing_open_interest`

## PSR / MinTRL Approximation

| Null Sharpe | PSR | MinTRL required | Actual N | Status |
|--:|--:|--:|--:|:--|
| 0.0 | 0.821497 | 285 | 90 | `under-sampled` |
| 0.5 | 2.3e-05 | None | 90 | `blocked_observed_sharpe_not_above_null` |

## Regime Coverage

### vix_bucket

| Bucket | Trades | PnL | Win rate |
|:--|--:|--:|--:|
| `vix_low_lt15|term_normal` | 46 | 687.24 | 0.3696 |
| `vix_normal_15_25|term_normal` | 44 | -141.64 | 0.2727 |

### macro_bucket

| Bucket | Trades | PnL | Win rate |
|:--|--:|--:|--:|
| `high_importance_macro_same_day` | 6 | -218.36 | 0.0 |
| `major_macro_same_day` | 20 | -56.2 | 0.25 |
| `no_same_day_macro` | 55 | 597.2 | 0.3636 |
| `other_macro_same_day` | 9 | 222.96 | 0.4444 |

### trend_bucket

| Bucket | Trades | PnL | Win rate |
|:--|--:|--:|--:|
| `spy_downtrend_below_sma20` | 19 | -211.64 | 0.2105 |
| `spy_neutral_near_sma20` | 13 | 657.72 | 0.6154 |
| `spy_uptrend_above_sma20` | 53 | 227.32 | 0.3208 |
| `trend_insufficient_prior_bars` | 5 | -127.8 | 0.0 |

### subperiod_bucket

| Bucket | Trades | PnL | Win rate |
|:--|--:|--:|--:|
| `oos_2024_plus` | 49 | -78.44 | 0.3061 |
| `post_break_train` | 41 | 624.04 | 0.3415 |

### split

| Bucket | Trades | PnL | Win rate |
|:--|--:|--:|--:|
| `in_sample` | 41 | 624.04 | 0.3415 |
| `oos` | 49 | -78.44 | 0.3061 |

## Greeks / OI Feasibility

- Status: `blocked`
- Sampled quote files: 32
- Sampled quote rows: 3200
- Observed quote fields: `ask`, `ask_size`, `bid`, `bid_size`, `databento_symbol`, `databento_window`, `dte`, `expiration_date`, `provider`, `quote_timestamp_et`, `record_type`, `right`, `schema_version`, `source`, `strike`, `underlying`
- Vendor Greek fields present: none
- Open-interest fields present: none
- Self-computed Greeks feasibility: `passed_local_iv_delta_gamma_probe_with_caveats`
- OI/Greeks feasibility report: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\greeks_oi_feasibility_audit.json`
- OI/Greeks enrichment report: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\greeks_oi_enrichment_probe_summary.json`

## Note

Read-only Risk-first audit from existing local artifacts; no live Databento or OpenRouter calls.
