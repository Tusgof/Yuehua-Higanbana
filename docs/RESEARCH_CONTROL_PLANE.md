# Research Control Plane

## Purpose

This document is the Milestone 1 control artifact for SPY 0DTE - Higanbana. It defines how experiments are grouped, what must be verified before results can be treated as acceptance-grade evidence, and which guardrails block research from moving forward.

This document controls research execution before additional data pulls, LLM prompt experiments, strategy acceptance, or paper/dry-run operational validation.

## Source Inputs

- `PROJECT_BRAIN.md`
- `IMPLEMENT_PLAN.md`
- `AGENTS.md`
- `backtest_experiments_plan.md`
- Local LLM Wiki concepts:
  - `minimum-track-record-length.md`
  - `probabilistic-sharpe-ratio.md`
  - `deflated-sharpe-ratio.md`
  - `backtest-validation-protocol.md`
  - `llm-training-data-contamination.md`
  - `implementable-option-pnl.md`
  - `0dte-trading-rules.md`

## Experiment Family Map

Experiment numbers are identifiers, not execution order. Execution follows dependency and data readiness.

| Original ID | Working Family | Primary Question | Depends On | Required Inputs | Status |
|:--|:--|:--|:--|:--|:--|
| Exp05 | Structural Break | Did the daily 0DTE listing expansion change strategy behavior? | Data coverage matrix | Reference/pre-break, post-2022 in-sample, OOS, SPY bars, option quotes | Deferred until coverage matrix |
| Exp07 | Cost And Execution Friction | Does bid/ask, per-leg fee, spread model, or latency erase edge? | Base strategy mechanics | SPY bars, option quotes, fills, mid and implementable PnL | Deferred until base baseline |
| Exp04 | Strike Selection | Does moneyness-based selection beat delta-based selection under real discrete strikes? | Cost/friction standard | Option chain with strikes, delta if available, strike mapping policy | Deferred until base baseline |
| Exp08 | Entry Timing | Which entry timestamp is robust after costs and no OOS tuning? | Cost/friction standard | Intraday SPY bars, option quotes, trade construction | Deferred until base baseline |
| Exp09 | Exit Rules | Which TP/SL/forced-close rule survives costs, search bias, and tail risk? | Cost/friction standard | Intraday option quotes, exit path assumptions, search log | Deferred until base baseline |
| Exp06 | VIX Regime | Which VIX ranges are useful without selection-biased Sharpe? | Base baseline, VIX/VXV coverage | VIX/VXV, SPY bars, option quotes, trial count | Deferred until base baseline |
| Exp10 | Macro Filter | Which event blocks reduce tail risk without under-sampling? | Base baseline, macro coverage | Macro calendar, SPY bars, option quotes, pre/post-filter counts | Deferred until base baseline |
| Exp01 | NOVI / Net Gamma Proxy | Does market-maker gamma proxy improve risk-adjusted returns? | Base baseline, proxy definition | Option quotes, volume/open-interest proxy if available, SPY bars | Deferred until base baseline |
| Exp03 | Portfolio Construction | Does risk parity improve survival versus equal weight? | Strategy-level returns | Sub-System A/B returns, ES contribution, account constraints | Deferred until strategy-level evidence |
| Exp02 | LLM News Gate | Does LLM/news add value beyond deterministic filters? | No-LLM baseline, real news archive, contamination controls | Real timestamp-clean news, deterministic baseline, prompt logs | Blocked on real news cases |

## Execution Order

1. Build the data coverage matrix for the experiment families.
2. Run the no-LLM/no-news base strategy baseline.
3. Establish cost, execution, strike mapping, and exit-path standards.
4. Test non-LLM strategy variables: strike, entry, exit, VIX, macro, NOVI, portfolio construction, structural break.
5. Build real timestamp-clean news cases.
6. Run LLM prompt-family tests with contamination controls.
7. Run no-LLM versus LLM-gated ablation.
8. Run final research acceptance.
9. Move to paper/dry-run operational validation only if research acceptance explicitly allows it.

## Report States

| State | Meaning | May Support Operational Validation? |
|:--|:--|:--:|
| `preliminary` | Useful diagnostic, but not enough evidence for acceptance | No |
| `under-sampled` | Actual observations are below MinTRL or too few for the claim | No |
| `underpowered` | Test power is too low to accept or reject the hypothesis reliably | No |
| `accepted` | Evidence passes statistical, cost, timing, and methodology guardrails | Yes, if all other gates pass |
| `failed` | Hypothesis is rejected or performance is not economically usable | No |
| `inconclusive` | Evidence is mixed or blocked by data/method limits | No |
| `deferred` | Experiment is intentionally postponed due dependency or blocker | No |

## Acceptance-Grade Checklist

Every acceptance-grade report must include all applicable fields below.

### Statistical Evidence

- Trade count and observation unit.
- Sharpe and Sortino.
- Sample length versus MinTRL.
- PSR against the chosen null Sharpe threshold.
- Power note where available.
- `under-sampled` label if actual sample length is below MinTRL.
- `underpowered` label if the test cannot support a reliable decision.

### Multiple Testing And Search Bias

- Search log or trial count for every parameter/filter/prompt family search.
- DSR when selecting a best observed Sharpe from multiple trials.
- Explicit `DSR blocked` note if trial count or return matrix is missing.
- No report may highlight only the winning parameter without showing the search breadth.

### Time And Leakage Discipline

- Chronological split only.
- No random or shuffled K-fold for time-series strategy acceptance.
- Fit features, scalers, thresholds, prompt selection, and allocation rules only on pre-decision information.
- No tuning on OOS after results are viewed.
- Every feature must be available at the decision timestamp.

### LLM Training-Data Contamination

Required for LLM/news experiments:

- Model id.
- Known or claimed training cutoff if available.
- Retrieval and fetch window.
- Document timestamps.
- Masking/anonymization policy for historical entities, dates, event names, and company identifiers.
- Contamination caveat if point-in-time checkpoint is unavailable.
- No synthetic or policy-fixture news may count as research evidence.

### Option Implementability

- `mid_pnl` as a comparison control.
- `implementable_pnl` after bid/ask, per-leg fees, slippage assumptions, and spread model.
- Cost drag from mid to implementable PnL.
- Entry limit-fill/skip logic.
- Forced close at 3:45 PM ET.
- No entry market orders.

### Robustness

- Big-day dependency check by removing top/bottom 5% extreme close days or trades.
- Subperiod/regime split where applicable.
- Tail metrics: ES95, ES99, worst-day loss, max drawdown.
- Benchmark comparison against same-period SPY/S&P 500 buy-and-hold.

### Strike Mapping

Required for moneyness-grid or strike-selection experiments:

- Method: nearest discrete strike rounding, interpolation, or another justified method.
- Rounding direction and tie-breaking policy.
- Whether the mapped strike existed in the actual historical option chain.
- Sensitivity to mapping choice if material.

## Hard Boundaries

- SPY only.
- No entry market orders.
- No undefined-risk or naked short structures.
- No IBKR order transmission.
- No stored secrets.
- No OOS tuning.
- No random/shuffled K-fold for time-series acceptance.
- No treating paper trading as proof of edge.
- No treating unmasked historical LLM output as clean evidence without contamination controls.

## Research Log Trigger

This control-plane document is not an experiment result. No research log is required for creating it.

After each completed experiment round:

1. Write a Thai research log under `research_log/` using `RESEARCH_LOG_FORMAT.md`.
2. Commit and push the log to `https://github.com/Tusgof/Yuehua_Research_log`.
3. Run `python scripts\audit_research_logs.py`.

## Milestone 1 Completion Evidence

Milestone 1 is complete when:

- This control-plane document exists.
- All 10 experiment identifiers are mapped to dependency-based families.
- Report states are defined.
- Acceptance-grade checklist covers MinTRL/PSR/power, DSR/search log, LLM contamination, chronological split, big-day dependency, mid-vs-implementable PnL, strike mapping, and hard boundaries.
- `PROJECT_BRAIN.md` and `IMPLEMENT_PLAN.md` point to this artifact.
- Unit tests and readiness audit are run after updates.
