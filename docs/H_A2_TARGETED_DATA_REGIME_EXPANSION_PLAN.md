# H-A2 Targeted Data/Regime Expansion Plan

## Purpose

H-A2.62 showed that the current train artifacts are not enough to lock a true `breakeven-aware` SPY 0DTE ORB debit vertical rule. The problem is not simply "not enough data". The missing part is specific option payoff geometry across the train distribution.

This plan pre-registers what data is needed before any paid download or OOS rule evaluation.

## Controlling Result

H-A2.62 conclusion: `ยังสรุปไม่ได้`.

Reason: current local train rows can run surrogate followthrough trials, but they do not contain the per-candidate fields needed to compute whether a selected option spread could realistically reach breakeven after costs.

Missing fields:

- nearest discrete long strike for each candidate
- short strike width
- entry mid debit
- entry implementable debit
- entry bid/ask width
- quote size or liquidity proxy
- forced-close spread value
- cost-adjusted strike-reachability target

## Hypothesis-First Data Rule

Do not buy broad calendar data.

Every future data request must answer one of these questions:

1. Can a candidate's entry-time option chain map the ORB signal to a tradable discrete spread?
2. Is the entry debit and bid/ask width small enough that the trade has plausible breakeven reach?
3. Does the forced-close quote prove implementable PnL separately from mid PnL?
4. Does the rule survive across volatility, macro, calendar, trend, and liquidity regimes?
5. Is the sample long enough under MinTRL/PSR, or must it be labeled `under-sampled` / `underpowered`?

## Minimum Fields

### Underlying Bars

Required fields:

- `symbol`
- `timestamp_utc`
- `timestamp_et`
- `open`
- `high`
- `low`
- `close`
- `volume`

Required windows:

- 09:30-09:35 ET opening range
- 09:35 ET decision timestamp
- 15:45 ET forced close timestamp
- full regular session only if stop/target path is later introduced

### Entry Option Chain

Required fields:

- `raw_symbol`
- `underlying`
- `expiration`
- `right`
- `strike`
- `timestamp_utc`
- `timestamp_et`
- `bid_px`
- `ask_px`
- `bid_sz`
- `ask_sz`

Required window:

- 09:34-09:36 ET entry chain snapshot

Strike scope:

- same-day SPY option strikes from 0.97x to 1.03x of entry underlying price
- widen only if the nearest-discrete strike audit shows missed candidates

### Forced-Close Option Quotes

Required fields:

- selected-leg quote at 15:44-15:46 ET
- bid/ask prices
- bid/ask sizes

Purpose:

- compute mid PnL
- compute implementable PnL
- compute cost drag

### Regime Labels

Required labels:

- VIX bucket
- macro-event flag and type
- day of week
- trend proxy bucket
- stress subperiod label
- liquidity bucket from entry quotes

## Target Sets

### 1. Train Candidate Geometry Backfill

Priority: highest.

Goal: backfill option payoff geometry for existing train candidate/non-risk days before selecting any revised rule.

Expected current count from H-A2.62: 30 train non-risk trade days.

Allowed next step: cache inventory and grouped cost estimate.

Paid download: not allowed by this plan.

### 2. Normal/Control Geometry Pack

Goal: use already downloaded 2025 normal/control packs to validate parser, strike mapping, and breakeven target logic before larger spend.

Allowed next step: local parser or inventory work only.

Paid download: not allowed by this plan.

### 3. Stress-Regime Geometry Pack

Goal: add high-VIX/stress geometry only after train geometry can be computed.

Status: blocked until underlying-bar source/cache inventory passes.

Paid download: not allowed by this plan.

### 4. OOS Locked-Rule Evaluation Pack

Goal: reserve OOS data for a single future pre-registered locked rule.

Status: future preregistration only.

Paid download: not allowed by this plan.

## Statistical Requirements Before Acceptance

No H-A2 acceptance claim is allowed until future reports include:

- active trade count after each filter
- MinTRL
- PSR
- DSR if any best trial is selected
- big-day dependency check
- mid PnL
- implementable PnL
- cost drag
- regime coverage
- `under-sampled` label if actual N is below MinTRL
- `underpowered` label if statistical power is too low

## Cost Policy

The next step may estimate cost only. It may not download data.

Allowed key pool for later already-scoped Databento work:

- `DATABENTO_API_MO`
- `DATABENTO_API_AI`

The selected key env must be logged before paid action. Each key stays under `$100`, and the combined MO/AI pool stays under `$200`.

## Next Artifact

Next safe step: H-A2.64 `h_a2_targeted_geometry_cache_inventory_and_cost_estimate`.

Required outputs:

- cache coverage by target set
- missing field/window table
- candidate date count by split and regime
- grouped request plan
- selected key env for estimate if a live estimate is run
- estimated cost and cap headroom
- explicit no-download status

## Forbidden

- No paid download from H-A2.63 alone
- No broad calendar buying
- No OOS rule evaluation
- No threshold selection
- No paper trading approval
- No operational validation
- No real-money trading
- No E2 claim

