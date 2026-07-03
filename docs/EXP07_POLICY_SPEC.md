# Experiment 7 Event Policy Spec v12

## Purpose

This document is the human-readable companion to `tests/fixtures/exp07_policy_spec_v12.json`.
The JSON file is the machine-checked source for category coverage. This Markdown file explains the same policy in a form that can be reviewed before another live prompt matrix.

The policy is only for the Experiment 7 guarded LLM pre-experiment. It must not be treated as a production LLM gate or integrated into strategy/live paths yet.

## Decision Meanings

| Decision | Meaning |
|:--|:--|
| `allow` | No same-day scheduled catalyst, no systemic stress, and no elevated volatility rule hit. This only means the event policy does not block the case. |
| `unknown` | Same-day scheduled/ambiguous event risk or unclear elevated volatility. The guarded layer should prevent raw LLM confidence from turning this into `allow`. |
| `block` | Systemic, disorderly, SPY/index halt, war, crash, panic, or VIX>=30 risk. |

## Categories

### quiet_or_normal_market

Expected decision: `allow`

Rules:

- VIX below 25 unless another explicit `unknown` or `block` rule fires.
- VIX/VXV term structure is not inverted by the v12 threshold.
- News context is quiet, already digested, future-dated, after close, non-market operational wording, or explicitly de-escalatory.

Cases:

- `quiet_vix18_normal_term_structure`
- `very_quiet_vix13_no_news`
- `earnings_next_week_no_catalyst_vix16`
- `fed_remarks_yesterday_no_data_vix17`
- `earnings_after_close_vix16`
- `cpi_tomorrow_vix16`
- `stress_contained_vix18`
- `panic_bid_defensives_vix17`
- `fomc_minutes_next_week_vix16`
- `treasury_auction_yesterday_vix17`
- `emergency_drill_vix14`
- `single_stock_halt_after_close_vix16`
- `powell_tomorrow_no_major_data_vix17`
- `cpi_yesterday_digested_vix18`
- `treasury_auction_tomorrow_vix16`
- `normal_vix24_vxv25_no_news`
- `no_war_risk_eased_vix17`
- `limit_down_drill_vix15`
- `near_inversion_below_threshold_vix20`

### scheduled_or_ambiguous_event

Expected decision: `unknown`

Rules:

- Same-day CPI, PCE, jobs, ISM, JOLTS, retail sales, FOMC, Powell, Fed decision, Treasury auction, or earnings-heavy references are `unknown`.
- Future-dated references are `allow` unless same-day markers keep a relevant event active.
- Prior-day scheduled references are `allow` unless another rule fires.

Cases:

- `major_fed_event_vix21`
- `cpi_release_pending_vix22`
- `jobs_report_pending_vix19`
- `earnings_heavy_calendar_vix20`
- `pce_inflation_pending_vix18`
- `treasury_auction_pending_vix18`
- `cpi_next_week_fed_today_vix19`
- `bank_stress_contained_fed_today_vix21`
- `cpi_today_earnings_next_month_vix18`
- `ism_services_today_vix18`
- `jolts_today_vix18`
- `retail_sales_today_vix18`

### elevated_volatility_unclear

Expected decision: `unknown`

Rules:

- VIX>=25 is `unknown` unless a `block` rule fires.
- VIX>=20 and VIX/VXV>=1.05 is `unknown` unless a `block` rule fires.

Cases:

- `high_vol_no_clear_news_vix27`
- `high_vol_no_news_vix26`
- `vix_vxv_inversion_vix24`

### systemic_or_disorderly_tail_risk

Expected decision: `block`

Rules:

- VIX>=30 is `block`.
- Systemic banking crisis, war shock, market panic, circuit breaker risk, index futures halt, or SPY ETF halt risk is `block`.
- Non-systemic or future/after-close halt references may be `allow` when explicitly scoped away from SPY intraday risk.

Cases:

- `systemic_banking_panic_vix34`
- `war_shock_futures_limit_vix42`
- `regional_bank_halt_vix24`
- `market_panic_vix28`
- `banking_stress_spreads_systemic_vix24`
- `futures_halt_rumor_vix29`
- `spy_etf_halt_risk_vix23`
- `war_risk_escalates_vix22`
- `circuit_breaker_risk_vix24`

## Current v12 Evidence

The controlled live v12 matrix produced:

- 43 cases
- 129 OpenRouter/DeepSeek assessments
- 129/129 parse-valid outputs
- 35/43 raw-stable cases
- 43/43 guarded-stable cases
- 0 raw expected-decision mismatches
- 0 guarded expected-decision mismatches
- 13 raw unknown-policy violations
- 0 guarded unknown-policy violations

The result supports continued guarded-policy testing, but raw LLM decisions remain not ready for production.

## Next Use

Before a later live matrix, add new cases to `tests/fixtures/exp07_policy_cases_v12.json` and assign them to exactly one category in `tests/fixtures/exp07_policy_spec_v12.json`, or create a new versioned fixture/spec pair.
Then run:

```powershell
python scripts\validate_exp07_policy_cases.py
python -m unittest tests.test_validate_exp07_policy_cases tests.test_exp07_prompt_experiment tests.test_openrouter_deepseek_adapter
```
