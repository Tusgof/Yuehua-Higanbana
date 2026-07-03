# Gamma Aggregation And Validation Policy

## Purpose
This document defines the minimum policy before any Greeks/OI-derived gamma feature may be used in NOVI, net-gamma, volatility-attenuation, or strategy-filter experiments.

Current status: the 2024-01-03 local enrichment probe passed with caveats, but it is not strategy-ready. Gamma-family features may be used only as diagnostic labels until the validation gates below pass.

## Source-Bounded Rationale
- The local LLM Wiki defines market-maker net gamma as a hedging-needs variable from pre-existing option positions, scaled in the source paper as a percentage of equivalent S&P 500 index shares.
- Positive market-maker net gamma can imply counter-cyclical hedging and volatility attenuation, but this is regime-dependent and should not be generalized without checking positioning, gamma sign, liquidity, and identification assumptions.
- Net gamma is not directly observed in the current project data. It depends on reconstructed positions, Greeks, moneyness buckets, and scaling conventions.
- The current project has OPRA open interest and self-computed IV/Delta/Gamma for a subset of SPY 0DTE quote rows. It does not have CBOE open-close volume, dealer/customer side, or vendor-calculated Greeks.

## Current Inputs
Allowed inputs from the current probe:
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

Current probe evidence:
- Target date: `2024-01-03`
- Quote rows: 3,488
- Prior SPY-bar joins: 3,488
- Exact-symbol prior OI joins: 3,488
- Rows with computed IV/Delta/Gamma: 1,750
- Rows blocked by Black-Scholes bracket check: 1,738

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
- gamma proxy divided by underlying notional,
- percentile rank within the available training window,
- bucket-level contribution share.

Until a wider sample exists, percentile ranks must be labeled `probe_only` and may not be used for acceptance-grade strategy conclusions.

## Required Validation Gates
Gamma-family strategy use is blocked until all gates below pass.

### Gate 1: Coverage
- At least 95% of rows needed by a candidate strategy day must have joined underlying price and exact-symbol prior OI.
- At least 70% of rows in the strategy's required moneyness range must have `greeks_status = computed_with_caveats`.
- Rows blocked by Black-Scholes bracket check must be reported by moneyness and right.

### Gate 2: Timestamp Discipline
- OI must be joined only from `ts_recv <= decision timestamp`.
- Underlying price must be joined only from `timestamp_et <= quote_timestamp_et`.
- No row may use future quotes, future underlying bars, future OI, or post-decision macro/news information.

### Gate 3: Stability
The same aggregation code must be run across multiple dates before strategy use:
- one normal/low-volatility day,
- one macro-event day,
- one high-volatility or stress day if local data exists,
- one OOS day.

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

## Forbidden Claims
Do not claim:
- the proxy is true market-maker net gamma,
- a positive proxy proves volatility attenuation,
- the current one-day enrichment probe validates NOVI/net-gamma trading,
- OI alone reveals dealer inventory,
- Black-Scholes self-computed Greeks are production-grade vendor Greeks,
- OOS performance can be selected after viewing OOS gamma buckets.

## First Acceptable Experiment Shape
The first gamma-family experiment should be diagnostic only:

1. Compute bucketed `net_oi_gamma_proxy` for available strategy days.
2. Split existing Sub-System A results into pre-registered gamma proxy buckets.
3. Report active trades, implementable PnL, Sharpe, PSR/MinTRL labels, realized volatility, big-day dependency, and cost drag by bucket.
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
