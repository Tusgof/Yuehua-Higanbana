# Hypothesis Registry

## Purpose

This registry is the control document for hypothesis-led research in Higanbana. Experiment IDs such as Exp01-Exp10 and M4/M5 reports are now evidence sources, not the execution order.

Every hypothesis must state why the edge should exist, what would validate it, what would falsify it, and which evidence tier currently supports it.

## Evidence Tiers

| Tier | Meaning | Allowed Claim |
|:--|:--|:--|
| E0 | Infrastructure, fixtures, parser, prompt plumbing | The machinery works |
| E1 | Real data but under-sampled, underpowered, search-contaminated, or gate-blocked | Hypothesis-generating only |
| E2 | Validation-grade research evidence | Edge exists in the tested scope |
| E3 | E2 plus operational validation and launch gates | May trade only after explicit user approval |

No current Higanbana strategy result is above E1.

## Kill And Resurrection Rule

A hypothesis can be killed only when its pre-registered statistical falsification criteria are hit and a written mechanism autopsy explains where the economic rationale broke. The mechanism matters, but numbers cannot be overridden by belief.

Resurrection is allowed only as a new registry entry with at least one new testable prediction the dead hypothesis did not make. Re-activating the same entry because the idea still feels plausible is prohibited.

## Registry Entries

### H-A1: Legacy Unconditional ORB

- **Family**: `subsystem_a`
- **Status**: `falsified-as-stated`
- **Statement**: Post-2022 SPY 0DTE ORB debit verticals beat SPY buy-and-hold risk-adjusted without conditioning on macro or regime state.
- **Economic rationale**: Opening-range breakouts may reflect early order-flow imbalance after the 0DTE listing expansion.
- **Current evidence**: 90 Sub-System A closed trades, OOS implementable PnL `-$78.44`, observed Sharpe proxy below every meaningful null, and benchmark-null validation undefined.
- **Conclusion**: `ไม่ผ่าน` for the unconditional form.
- **Mechanism autopsy**: The unconditional version likely mixes different market mechanisms: ordinary order-flow imbalance days, scheduled macro repricing days, and stress windows. If these states behave differently, a single unconditional ORB rule dilutes the intended edge and makes blind calendar expansion misleading.
- **Successor**: H-A2.

### H-A2: Macro-Conditioned ORB

- **Family**: `subsystem_a`
- **Status**: `parked`
- **Statement**: The ORB edge, if it exists, is macro-conditioned: excluding high-importance scheduled macro days should improve implementable risk-adjusted OOS returns because non-macro breakout days reflect cleaner order-flow imbalance.
- **Economic rationale**: On scheduled macro days, the opening range can be dominated by anticipatory positioning and post-release repricing rather than persistent intraday imbalance. Removing those days is a mechanism claim, not merely a fitted filter.
- **Testable predictions**:
  - Macro-day trades remain weak or negative in fresh data.
  - Retained no-macro trades remain positive after cost and big-day removal.
  - The effect is not concentrated in one VIX/trend bucket unless the hypothesis is explicitly scope-restricted.
- **Validation criteria**: E2 requires untouched validation data or DSR accounting for the inherited 9-trial M5.5 search, MinTRL/PSR against `SR0=0` and same-trade-calendar SPY, implementable PnL, big-day survival, and regime coverage or explicit scope restriction.
- **Falsification criteria**: H-A2 is killed if fresh retained no-macro trades have implementable PnL `<= 0` after reaching `MinTRL_falsify`, or if the macro-day/no-macro mechanism reverses in fresh data.
- **Current evidence**: M5.5 `exclude_high_importance_macro_same_day` has E1 diagnostic evidence only: 64 closed trades, implementable PnL `$820.16`, OOS `$240.96`, and inherited 9-trial selection contamination.
- **Conclusion**: `ยังสรุปไม่ได้`.

### H-B1: Put Ratio At Current Small-Account Sizing

- **Family**: `subsystem_b`
- **Status**: `falsified`
- **Statement**: Capped-risk put ratio spreads are feasible and profitable under `$300` allocation and `$20` risk budget on a `$1,000` account.
- **Economic rationale**: Selling short-dated downside skew may have premium edge if tail risk is capped by a protective wing.
- **Current evidence**: M4.2 produced 412 closed trades, implementable PnL `-$5,973.44`, OOS implementable PnL `-$3,866.76`, and 0 trades fit the `$300` allocation or `$20` risk budget.
- **Conclusion**: `ไม่ผ่าน`.
- **Mechanism autopsy**: The structure may be too large and fee-heavy for the current account constraints; strike granularity and defined-risk width dominate the intended skew-premium mechanism.
- **Successor**: H-B2.

### H-B2: Put Ratio Structure At Realistic Scale

- **Family**: `subsystem_b`
- **Status**: `active`
- **Statement**: The put-ratio-with-wing structure may have positive expectancy at simulated `$10k` to `$25k` scale where strike granularity and premium-to-account ratios stop binding.
- **Economic rationale**: If short-dated downside skew is overpriced, a capped-risk structure may monetize it at sufficient account size while preserving survival through the protective wing.
- **Testable predictions**:
  - Cost drag is not the dominant share of gross edge at all wing widths.
  - Implementable PnL and ES95-adjusted return are not negative at both simulated scales.
  - Results are not dependent on fractional contracts or hidden undefined risk.
- **Validation criteria**: Pre-registered account sizes, wing grid, sizing rule, search log, DSR or DSR blocker, implementable PnL, ES95, drawdown, and sample labels.
- **Falsification criteria**: H-B2 is killed if implementable PnL and ES95-adjusted return are negative at both simulated scales with adequate falsification sample, or if cost drag exceeds 60% of gross at all wing widths.
- **Current evidence**: `reports/experiments/h_b2_subsystem_b_scale_summary.json` is E1 diagnostic evidence. The 8 pre-registered trials found zero scenarios with both positive total implementable PnL and positive OOS implementable PnL. H-B2 is parked pending MinTRL_falsify review, with no deployment or paper-trading edge claim allowed.
- **Conclusion**: `ยังสรุปไม่ได้`.

### H-G1: Signed-OI Gamma Proxy Validity

- **Family**: `gamma`
- **Status**: `active`
- **Statement**: A signed-OI gamma proxy aggregated from OPRA open interest and self-computed Greeks carries economic signal: high positive proxy days should exhibit attenuated realized intraday volatility.
- **Economic rationale**: Positive aggregate dealer-style gamma exposure can damp realized volatility through hedging flows, while negative gamma can amplify moves. Higanbana cannot claim true dealer inventory yet, so this is a proxy-validity hypothesis.
- **Testable predictions**:
  - Proxy terciles show monotonic or sign-consistent realized variance differences.
  - The relationship survives across at least 10 dates and at least 3 regimes.
  - Coverage passes the pre-registered v2 policy without retroactively passing v1.
- **Validation criteria**: `GAMMA_AGGREGATION_VALIDATION_POLICY.md` v2, dual raw-row and bucket-weighted coverage reporting, timestamp discipline, stability, economic-sign validation, and no strategy use before data-validity pass.
- **Falsification criteria**: H-G1 is killed if there is no monotonic or sign-consistent relation between proxy tercile and realized 10:00-15:45 SPY variance across the pre-registered multi-regime date set.
- **Current evidence**: One-day 2024-01-03 gamma diagnostic is E1 diagnostic and blocked: timestamp/search-log gates pass, coverage fails at raw computed-Greeks rate `0.50172`, stability is under-regime-sampled, and economic-sign validation is blocked.
- **Conclusion**: `ยังสรุปไม่ได้`.

### H-L1: LLM News Measurement

- **Family**: `llm_news`
- **Status**: `active_blocked`
- **Statement**: LLM sentiment, market-impact, and volatility-relevance scores over timestamp-clean pre-entry news are stable across repeated calls/prompt families and add information beyond VIX plus macro calendar.
- **Economic rationale**: Language models may compress qualitative news context into continuous sentiment/impact/volatility scores that deterministic calendars cannot capture, but only if stability and contamination controls pass first.
- **Testable predictions**:
  - Repeated calls have acceptable dispersion for the selected prompt family.
  - Masking/anonymization reduces event memorization without destroying signal.
  - Scores correlate with same-day realized volatility or adverse tails after controlling for VIX and macro calendar.
- **Validation criteria**: Real timestamp-clean news cases, prompt-family comparison, 5-call stability where cost allows, contamination probe, model/cutoff/fetch metadata, and incremental information tests before any strategy ablation.
- **Falsification criteria**: H-L1 is killed or parked if real cases remain unavailable, parse validity is unreliable, repeated-call dispersion is too high, or scores add no information beyond VIX/macro baselines.
- **Current evidence**: Blocked on real timestamp-clean news. Old Exp07 prompt matrices are E0 infrastructure only.
- **Conclusion**: `ยังสรุปไม่ได้`.

### H-L2: LLM Price-Input Exit Assistance

- **Family**: `llm_price`
- **Status**: `proposed`
- **Statement**: LLM prompts fed only chronological price/quote context may improve exit timing versus fixed TP/SL rules.
- **Economic rationale**: A model might summarize intraday price/quote context into a dynamic exit assessment, but this must be separated from H-L1 and tested against strict chronological controls.
- **Testable predictions**:
  - Parse validity stays above the pre-registered threshold.
  - Any improvement survives ablation against fixed TP/SL grids.
  - No future same-day aggregate or post-decision data enters the prompt.
- **Validation criteria**: Separate pre-registration, strict timestamp controls, search log, cost guard, and no mixing with news/sentiment prompts.
- **Falsification criteria**: H-L2 is killed or parked if parse validity is below threshold, chronological controls cannot be proven, or cost/latency makes the branch impractical.
- **Current evidence**: Design-only branch; no live research run.
- **Conclusion**: `ยังสรุปไม่ได้`.
