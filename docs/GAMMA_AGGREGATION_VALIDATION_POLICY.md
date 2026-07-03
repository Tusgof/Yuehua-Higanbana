# Gamma Aggregation And Validation Policy

## Version
- **Policy version**: v2
- **Issued**: 2026-07-03
- **Hypothesis**: H-G1
- **Status**: Diagnostic-only. No NOVI, net-gamma, or gamma-filter strategy use is allowed until the gates in this policy pass.

## Purpose
This document defines the minimum policy before any Greeks/OI-derived gamma feature may be used in NOVI, net-gamma, volatility-attenuation, or strategy-filter experiments.

The v1 one-day diagnostic on `2024-01-03` remains permanently preserved as a failed diagnostic gate:

- Report: `reports\diagnostics\gamma_aggregation_diagnostic_summary.json`
- V1 status: `blocked`
- V1 blockers: coverage, stability, and economic-sign validation
- V1 reason: one date is not enough, and raw computed-Greeks coverage was only `0.50172`

Policy v2 does not erase the v1 failure. It improves measurement so the next diagnostic can distinguish between two different problems:

1. raw-row chain coverage is weak, and
2. economically important moneyness buckets are weak.

## Source-Bounded Rationale
- The local LLM Wiki defines market-maker net gamma as a hedging-needs variable from pre-existing option positions, scaled in the source paper as a percentage of equivalent S&P 500 index shares.
- Positive market-maker net gamma can imply counter-cyclical hedging and volatility attenuation, but this is regime-dependent and must not be generalized without checking positioning, gamma sign, liquidity, and identification assumptions.
- Net gamma is not directly observed in the current project data. It depends on reconstructed positions, Greeks, moneyness buckets, and scaling conventions.
- The current project has OPRA open interest and self-computed IV/Delta/Gamma for a subset of SPY 0DTE quote rows. It does not have CBOE open-close volume, dealer/customer side, or vendor-calculated Greeks.

## Allowed Inputs
Allowed row-level inputs:

- `databento_symbol`
- `quote_timestamp_et`
- `right`
- `strike`
- `bid`
- `ask`
- `mid`
- `underlying_price`
- `open_interest`
- `implied_volatility`
- `delta`
- `gamma`
- `greeks_status`

Required join discipline:

- OI must be the latest available OPRA statistics/open-interest row with `ts_recv <= decision timestamp`.
- Underlying price must be the latest available SPY bar with `timestamp_et <= quote_timestamp_et`.
- No post-decision option quote, SPY bar, macro event, news item, or OI row may enter a decision-time feature.

## Feature Definitions
### Per-contract local gamma exposure
For each option row with `greeks_status = computed_with_caveats`:

```text
local_gamma_exposure = gamma * open_interest * contract_multiplier * underlying_price
```

Default:

- `contract_multiplier = 100`

This is a proxy for curvature exposure magnitude, not a proven dealer net-gamma estimate.

### Signed open-interest gamma proxy
Because current data does not identify dealer/customer side, signed gamma must be labeled as a proxy:

```text
call_gamma_proxy = +local_gamma_exposure for calls
put_gamma_proxy = -local_gamma_exposure for puts
net_oi_gamma_proxy = sum(call_gamma_proxy + put_gamma_proxy)
```

This sign convention is a research convention only. It must not be described as actual market-maker net gamma unless validated against side-aware flow or an accepted external benchmark.

### Moneyness buckets
Every gamma report must aggregate by moneyness bucket:

```text
moneyness = strike / underlying_price
```

Minimum buckets:

- `deep_put`: `moneyness < 0.97`
- `otm_put`: `0.97 <= moneyness < 0.995`
- `atm`: `0.995 <= moneyness <= 1.005`
- `otm_call`: `1.005 < moneyness <= 1.03`
- `deep_call`: `moneyness > 1.03`

### Scaling
Every aggregate must report at least:

- raw summed gamma proxy,
- signed gamma proxy,
- gamma proxy divided by underlying notional,
- percentile rank within the available training window,
- bucket-level contribution share.

Until a wider sample exists, percentile ranks must be labeled `probe_only` and may not be used for acceptance-grade strategy conclusions.

## V2 Coverage Policy
The v1 coverage test used a single raw-row computed-Greeks rate. That remains required, but v2 adds bucket-weighted coverage.

### Raw-row coverage
Report these rates for every date and for the full date set:

- underlying join rate,
- exact-symbol prior OI join rate,
- computed-Greeks raw-row rate,
- blocked rows by moneyness bucket and option right.

Minimum raw-row gates:

- underlying join rate >= `0.95`
- prior OI join rate >= `0.95`
- computed-Greeks raw-row rate >= `0.70`

### Bucket-weighted coverage
Report coverage by the buckets that can materially affect the H-G1 signal:

- `otm_put`
- `atm`
- `otm_call`

For each required bucket, report:

- row count,
- computed count,
- computed rate,
- absolute raw gamma exposure share,
- OI notional share.

Minimum bucket-weighted gates:

- each required bucket computed rate >= `0.60`
- combined absolute gamma exposure share represented by computed rows >= `0.80`
- no required bucket may be missing entirely on a candidate day

Deep buckets must still be reported. They may not be silently ignored, but they are not allowed to dominate pass/fail if their OI/gamma exposure share is economically tiny. If a deep bucket carries more than `0.20` of absolute gamma exposure, it becomes a required bucket for that date.

## Required Validation Gates
Gamma-family strategy use is blocked until all gates below pass.

### Gate 1: Coverage
Coverage must pass both raw-row and bucket-weighted gates under the v2 coverage policy.

If raw-row coverage fails but bucket-weighted coverage passes, the result may be labeled `diagnostic_data_collection_candidate`, not `validated`.

If bucket-weighted coverage fails, the feature remains blocked.

### Gate 2: Timestamp Discipline
- OI must be joined only from `ts_recv <= decision timestamp`.
- Underlying price must be joined only from `timestamp_et <= quote_timestamp_et`.
- No row may use future quotes, future underlying bars, future OI, or post-decision macro/news information.

Any timestamp violation blocks strategy use.

### Gate 3: Stability
The same aggregation code must be run across the pre-registered 12-date regime set before strategy use.

The date set must include:

- at least 3 low-volatility dates,
- at least 3 normal-volatility dates,
- at least 3 high-volatility or stress dates,
- at least 4 scheduled high-importance macro dates,
- at least 4 no-high-importance-macro dates,
- at least 4 in-sample dates,
- at least 4 OOS dates.

If the current local dataset cannot satisfy these regimes, the report must mark the gamma feature `under-regime-sampled`.

### Gate 4: Economic Sign Check
Before using gamma as a filter, report whether high positive proxy-gamma days actually show lower realized intraday volatility than low/negative proxy-gamma days in the available data.

Required comparison:

- next 10-minute realized volatility after decision time,
- full-day realized volatility from decision time to forced close,
- ORB strategy PnL split by gamma proxy bucket.

If the sign is unstable or contradicted, gamma may remain a diagnostic label but not a gate.

### Gate 5: No Best-Bucket Selection Without Search Log
Any threshold such as "trade only in top gamma quartile" is a parameter search.

Required:

- record every tested threshold,
- record trial count,
- report DSR or mark DSR as blocked,
- keep OOS untouched by threshold selection.

## H-G1 12-Date Pre-Registration
The controlling manifest is:

- `experiments\h_g1_gamma_regime_date_set_preregistration.json`

The manifest must validate before any new OPRA statistics/OI purchase. The selected dates may not be changed after viewing gamma proxy results. If a date is unavailable from Databento or fails OI schema/cost checks, replacement requires a new manifest version and a decision-log entry before rerun.

## Forbidden Claims
Do not claim:

- the proxy is true market-maker net gamma,
- a positive proxy proves volatility attenuation,
- the current one-day enrichment probe validates NOVI/net-gamma trading,
- OI alone reveals dealer inventory,
- Black-Scholes self-computed Greeks are production-grade vendor Greeks,
- OOS performance can be selected after viewing OOS gamma buckets,
- bucket-weighted coverage pass is equivalent to strategy validation.

## First Acceptable Experiment Shape
The first gamma-family experiment remains diagnostic only:

1. Compute bucketed `net_oi_gamma_proxy` for the pre-registered 12-date set.
2. Split existing Sub-System A results into pre-registered gamma proxy terciles.
3. Report active trades, implementable PnL, Sharpe, PSR/MinTRL labels, realized volatility, big-day dependency, and cost drag by tercile.
4. Conclude only one of:
   - `ยังสรุปไม่ได้`: sample or validation gates are insufficient.
   - `ไม่ผ่าน`: proxy sign is unstable, contradictory, or economically weak.
   - `ผ่านเฉพาะ diagnostic`: proxy behaves consistently enough to justify broader data collection, not live use.

## Promotion Rule
Gamma-family features may become a strategy filter only after:

- coverage, timestamp, stability, economic sign, and search-log gates pass,
- the feature is tested on enough sample to satisfy MinTRL/PSR requirements,
- OOS is not used for threshold selection,
- the final report separates mid PnL and implementable PnL,
- the result survives big-day dependency checks.

Until then, gamma features are regime diagnostics only.
