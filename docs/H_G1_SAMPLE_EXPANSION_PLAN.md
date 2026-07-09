# H-G1 Sample-Expansion Plan

## Status
- **Hypothesis**: `H-G1`
- **Artifact**: `experiments/h_g1_sample_expansion_plan.json`
- **Evidence tier**: `E0`
- **Conclusion**: ยังสรุปไม่ได้
- **Network / paid data**: none
- **Strategy use allowed**: no
- **Paper trading allowed**: no

## Why This Exists
H-G1.22 did not falsify the economic idea behind the `signed-OI gamma proxy`, but it also did not produce usable strategy evidence. Only 2 of 90 baseline Sub-System A closed trades intersected the available gamma-proxy dates, and every gamma-filtered variant had 0 active trades.

The current blocker is therefore sample overlap and statistical power. More H-G1 work is allowed only as a sample-expansion planning problem first, not as another strategy test or data purchase.

## Locked Sequence
1. Run a no-paid local-cache overlap scan.
   - Use only existing baseline trades, cached quote days, macro/VIX labels, and existing gamma artifacts.
   - Report expected trade overlap, train/OOS split, volatility buckets, macro/no-macro coverage, and remaining gaps.

2. Run a MinTRL/PSR feasibility gate.
   - Do not use a fixed universal N.
   - State the Sharpe null threshold and whether the expanded return series can estimate skewness, kurtosis, and first-order autocorrelation.
   - If the expected sample remains too small, keep H-G1 parked.

3. Run a targeted cost gate only if the overlap scan passes.
   - Estimate cost only for named dates and named fields.
   - Do not buy broad calendar data.
   - Do not introduce a new provider without user approval.

4. Create a new preregistered ablation only after data-validity gates pass.
   - Lock variants, chronological split, search log/DSR policy, MinTRL/PSR reporting, implementable PnL, and big-day dependency before reviewing strategy PnL.

## Required Coverage
- Chronological train and OOS split.
- Low, normal, and high volatility buckets where data exists.
- Macro and no-macro days.
- Stress or high-volatility subperiods where available.
- Trend or momentum labels when already available without lookahead.
- Gamma/liquidity buckets only when the proxy passes timestamp and coverage gates.

## Forbidden Actions
- Do not use H-G1 as a trading filter from this plan.
- Do not approve paper trading from this plan.
- Do not buy paid data from this plan alone.
- Do not claim true market-maker net gamma or dealer net gamma from the signed-OI gamma proxy.
- Do not add new gamma variants or tune OOS before a new preregistered ablation.
- Do not buy broad calendar data.

## References
- `wiki/concepts/minimum-track-record-length.md`
- `wiki/concepts/probabilistic-sharpe-ratio.md`
- `wiki/concepts/deflated-sharpe-ratio.md`
- `wiki/concepts/regime-filtering-for-zero-dte.md`
- `wiki/concepts/market-maker-net-gamma.md`
