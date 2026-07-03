# Data Coverage Matrix

## Purpose

This document is the Milestone 2 planning artifact for experiment-driven data expansion. It records current real-data coverage, blockers, and the next data actions needed before any acceptance-grade experiment.

This matrix must be checked before paid data pulls, experiment execution, or LLM/news runs.

## Latest Read-Only Audit

Commands run:

```powershell
python scripts\audit_paid_costs.py
python scripts\audit_strategy_data_readiness.py
```

Results:

| Audit | Status | Key Result |
|:--|:--|:--|
| Paid cost | `pass` | User-reported actual usage is `$64.64`; stop threshold is `$125`; remaining room is `$60.36` on actual-usage basis. Known committed estimated cost is `$169.551219`, leaving `$-44.551219` before the conservative estimate stop. `cost_guard_reconciliation` reports estimate-only total `$7.150193` and 13 single estimate-only threshold breaches; this conservative basis is trace/warning evidence while actual provider usage is the controlling guard for already-scoped SPY-only work |
| Strategy data readiness | `blocked` | Current real strategy evidence has 90 closed trades versus the rough prior target of 500 trades; `sample_adequacy.evidence_labels` reports `under-sampled` and `underpowered`, with MinTRL/PSR pending experiment return distribution metrics |

The paid-cost audit writes/uses `reports\data_cost\paid_cost_audit.json`. The strategy readiness audit writes/uses `reports\strategy_data_readiness_audit.json`.

## Current Strategy Data Coverage

| Split | Coverage | Quote Rows | SPY Bar Rows | Candidate Days | Closed Trades | Status |
|:--|:--|--:|--:|--:|--:|:--|
| Reference / pre-break | 2019-01-01 to 2022-05-10 | 0 | 0 | 0 | 0 | Missing |
| In-sample | 2023-03-01 to 2023-12-29 | 8,145,550 | 100,365 | 42 | 41 | Present but under-sampled |
| OOS | 2024-01-02 to 2024-12-31 | 13,357,670 | 132,148 | 51 | 49 | Present but under-sampled |
| Total | 2023-03-01 to 2024-12-31, with gaps outside current windows | 21,503,220 | 232,513 | 93 | 90 | Blocked on sample adequacy; `under-sampled` / `underpowered` |

July 2024 OOS coverage is present for `2024-07-01` to `2024-07-31` across the current pilot windows. The latest added dataset is Dec 2024 (`2024-12-02` to `2024-12-31`) using the `daily_union` workflow, which added 2,007,814 option quote rows, 10,836 SPY bar rows, 3 candidate days, and 3 closed pilot trades. The observed 90 closed trades after the current pilot coverage means one-week chunks are no longer an acceptable default path, and blind monthly calendar expansion is weak unless a checkpoint justifies the next data block.

## Non-Strategy Inputs

| Input | Current Status | Notes |
|:--|:--|:--|
| VIX/VXV | Present | Official Cboe VIX/VIX3M coverage passes current audit |
| Macro calendar | Present | Official-source 2022-2026 macro backfill is imported and passes required event-type coverage |
| Real news archive | Blocked | GDELT live captures returned HTTP 429; real timestamp-clean news cases are not captured |
| Exp07 real-news case plan | Blocked | 71 candidate days planned, 0 captured candidate days |
| OpenRouter/DeepSeek env | Available | `HIGANBANA_OPENROUTER_API` visible in process/user env; do not run research prompt experiments before real news cases |
| Databento env | Available | `DATABENTO_SPY0DTE_API` visible in process/user env; continue only inside SPY-only <$125 rule |

## Experiment Family Coverage Matrix

| Family | Needs Reference | Needs In-Sample | Needs OOS | Needs News | Current Readiness | Next Data Need |
|:--|:--:|:--:|:--:|:--:|:--|:--|
| Structural Break | Yes | Yes | Yes | No | Blocked | Add reference/pre-break coverage before structural-break conclusions |
| Cost And Execution Friction | No | Yes | Yes | No | Blocked | Expand post-2022 data enough to test cost drag and latency with non-trivial trade count |
| Strike Selection | No | Yes | Yes | No | Blocked | Ensure option-chain strike availability and define nearest-strike/interpolation policy |
| Entry Timing | No | Yes | Yes | No | Blocked | Expand intraday quote/bar coverage and preserve OOS lock |
| Exit Rules | No | Yes | Yes | No | Blocked | Expand intraday option quote coverage and log all TP/SL trials for DSR |
| VIX Regime | Optional | Yes | Yes | No | Blocked | Expand post-2022 trade count; current 82 trades is under-sampled after filters |
| Macro Filter | Optional | Yes | Yes | No | Blocked | Expand post-2022 trade count; macro input exists but filtered active trades may shrink below MinTRL |
| NOVI / Net Gamma Proxy | Optional | Yes | Yes | No | Blocked | Confirm proxy inputs from available option quote/volume fields or identify missing open-interest/gamma data |
| Portfolio Construction | No | Yes | Yes | No | Blocked | Needs strategy-level return series from accepted/preliminary Sub-System A and B baselines |
| LLM News Gate | Optional | Yes | Yes | Yes | Blocked | Build real timestamp-clean news archive and contamination-controlled prompt cases |

## Data Expansion Rules

- Do not download data as a blind calendar sweep.
- Before every paid action, run `python scripts\audit_paid_costs.py`.
- Default Databento acquisition unit is a calendar month. Use multi-month or quarter-level estimates for planning where useful, but normalize, register, and audit month-by-month until the tooling is proven reliable for larger atomic batches.
- Weekly chunks are only a recovery fallback after a monthly batch fails or times out; they are not the normal acquisition plan.
- For every new month or recovery chunk, record cost estimate, download result, raw hash, normalization summary, adapter/PnL summary, and split label.
- After every new dataset, run `python scripts\audit_strategy_data_readiness.py`.
- After each 3 added calendar months or 50 newly closed trades, whichever comes first, record a trade-density checkpoint: added closed trades, added provider cost, projected years/cost to reach N >= 500, and whether continued acquisition still makes sense.
- Do not tune on OOS after viewing results.
- Use `docs\RESEARCH_CONTROL_PLANE.md` for methodology guardrails before interpreting new results.

## Q4 2024 Completion Planning

The current OOS completion target is `2024-09-23` to `2024-12-31`.

| Artifact | Status | Evidence |
|:--|:--|:--|
| Option quote dry-run | Complete | `reports\data_cost\databento_cost_oos_2024_q4_completion_intraday_exit_30m_dryrun.json` planned 980 OPRA request windows |
| Option quote projected cost | Complete for planning, not a provider quote | `reports\data_cost\databento_cost_projection_oos_2024_q4_completion_intraday_exit_30m.json` projects `$28.545538` from Sep 2024 chunk3 live cost, using `$0.0291281` average cost per window |
| Option quote exact live cost | Complete for Sep remainder through `daily_union` | `reports\data_cost\databento_cost_oos_2024_sep_remainder_intraday_exit_30m_daily_union.json` planned 84 research windows, coalesced them into 6 daily provider requests, estimated `$3.419502`, and passed. This is exact for the daily superset request, not the sum of narrow-window requests |
| Sep remainder option quote download | Complete | `reports\data_cost\databento_download_result_oos_2024_09_remainder_daily_union.json` downloaded 6 daily files for `2024-09-23` to `2024-09-30` |
| Sep remainder SPY bars | Complete | `reports\data_cost\databento_spy_bars_download_result_2024_09_remainder.json` downloaded bars at estimated cost `$0.001898825169`; normalized output has 3,034 rows |
| Sep remainder adapter/PnL | Complete | `reports\pilots\sep_2024_remainder_daily_union_pilot_pnl_summary.json` reports 1 candidate day, 1 closed trade, and total net PnL `$-8.00`; this is diagnostic evidence only |
| SPY bars live-cost plan | Complete | `reports\data_cost\databento_spy_bars_plan_oos_2024_q4_completion.json` estimates `$0.022813439369` for `2024-09-23T13:30:00+00:00` to `2024-12-31T21:00:00+00:00` |
| Oct 2024 option quote cost | Complete | `reports\data_cost\databento_cost_oos_2024_10_intraday_exit_30m_daily_union.json` planned 322 research windows, coalesced them into 23 daily provider requests, estimated `$12.671726`, and received `review` status only because it exceeded the legacy `$5` review threshold |
| Oct 2024 option quote download | Complete | `reports\data_cost\databento_download_result_oos_2024_10_daily_union.json` downloaded 23 daily files for `2024-10-01` to `2024-10-31` under the user-approved `$125` actual-usage guard |
| Oct 2024 SPY bars | Complete | `reports\data_cost\databento_spy_bars_download_result_2024_10.json` downloaded bars at estimated cost `$0.007642865181`; normalized output has 12,212 rows |
| Oct 2024 adapter/PnL | Complete | `reports\pilots\oct_2024_daily_union_pilot_pnl_summary.json` reports 2 candidate days, 2 closed trades, and total net PnL `$135.00`; this is diagnostic evidence only |
| Nov 2024 option quote cost | Complete | `reports\data_cost\databento_cost_oos_2024_11_intraday_exit_30m_daily_union.json` planned 280 research windows, coalesced them into 20 daily provider requests, estimated `$11.060765`, and received `review` status only because it exceeded the legacy `$5` review threshold |
| Nov 2024 option quote download | Complete | `reports\data_cost\databento_download_result_oos_2024_11_daily_union.json` downloaded 20 daily files for `2024-11-01` to `2024-11-29` under the user-approved `$125` actual-usage guard |
| Nov 2024 SPY bars | Complete | `reports\data_cost\databento_spy_bars_download_result_2024_11.json` downloaded bars at estimated cost `$0.006312936544`; normalized output has 10,087 rows |
| Nov 2024 adapter/PnL | Complete | `reports\pilots\nov_2024_daily_union_pilot_pnl_summary.json` reports 5 candidate days, 5 closed trades, total net PnL `$-152.00`, and 0 skipped trades; this is diagnostic evidence only |
| Dec 2024 option quote cost | Complete | `reports\data_cost\databento_cost_oos_2024_12_intraday_exit_30m_daily_union.json` planned 294 research windows, coalesced them into 21 daily provider requests, estimated `$11.504703`, and received `review` status only because it exceeded the legacy `$5` review threshold |
| Dec 2024 option quote download | Complete | `reports\data_cost\databento_download_result_oos_2024_12_daily_union.json` downloaded 21 daily files for `2024-12-02` to `2024-12-31` under the user-approved `$125` actual-usage guard |
| Dec 2024 SPY bars | Complete | `reports\data_cost\databento_spy_bars_download_result_2024_12.json` downloaded bars at estimated cost `$0.006781697273`; normalized output has 10,836 rows |
| Dec 2024 adapter/PnL | Complete | `reports\pilots\dec_2024_daily_union_pilot_pnl_summary.json` reports 3 candidate days, 3 closed trades, total net PnL `$229.00`, and 0 skipped trades; this is diagnostic evidence only |

Planning implication: Sep remainder proved the `daily_union` workflow can replace slow narrow-window cost calls, and Oct-Dec 2024 proved the full-month daily-union path is operationally usable. The data-acquisition problem is no longer tooling speed; it is trade density. Do not continue broad calendar acquisition until the next data block is justified by a revised hypothesis, a higher-density signal target, or a specific experiment need.

## Q4 2024 Trade-Density / Cost Checkpoint

| Window | Option Cost | SPY Bar Cost | Total Cost | Candidate Days | Closed Trades | Cost / Closed Trade | Decision |
|:--|--:|--:|--:|--:|--:|--:|:--|
| Sep remainder-Dec 2024 | `$38.656696` | `$0.022636` | `$38.679332` | 11 | 11 | `$3.516303` | Pause blind broad acquisition |

Checkpoint interpretation:

- The Q4 completion path added only 11 closed pilot trades despite using recoverable monthly `daily_union` batches.
- At the observed checkpoint density, adding the remaining 410 trades needed to reach the rough N >= 500 floor would project to about `$1,441.68` of similar data cost before accounting for time, failures, or provider-side differences.
- The projected cost to collect 500 or 1,000 trades at this density is about `$1,758.15` and `$3,516.30`, respectively.
- This does not mean the strategy fails. It means broad calendar acquisition is not the right next default action.
- Next data spending should be tied to a revised hypothesis, a higher-density signal design, a specific in-sample/reference need, or a narrower experiment whose expected trade yield is known before purchase.

## Priority Order

1. Preserve cost guardrail and audit state before new paid work.
2. Pause further blind broad calendar acquisition after Q4 2024 because the checkpoint trade density is too low to justify simply buying more of the same data.
3. Use the current real-data set for engine/report hardening and diagnostic baseline reporting without acceptance-grade claims.
4. Add reference/pre-break data only when preparing structural-break analysis or when a revised hypothesis explicitly needs it.
5. Defer LLM/news research until real timestamp-clean news cases exist.
6. Defer paper/dry-run operational validation until research acceptance explicitly allows it.

## Immediate Next Candidate Actions

| Priority | Action | Rationale | Guardrail |
|:--|:--|:--|:--|
| 1 | Re-run `audit_paid_costs.py` immediately before any Databento live estimate/download | Confirms remaining budget under `$125` | Stop if threshold would be reached |
| 2 | Treat Q4 2024 checkpoint as a pause signal for blind acquisition | Q4 added 11 closed trades for about `$38.68`, which projects poorly to N >= 500 | Do not continue 2025 broad pulls without a revised hypothesis or explicit data-target decision |
| 3 | Move to backtest/reporting hardening and diagnostic baseline work using current real data | This makes progress without buying low-yield data blindly | Every report must remain `under-sampled` / `underpowered` until MinTRL/PSR evidence says otherwise |
| 4 | Plan reference/pre-break coverage separately before structural-break testing | Structural-break testing needs 2019-2022 data | Estimate cost first; do not mix with OOS tuning |
| 5 | Pause GDELT `--execute` retries until 429 pressure clears | Avoid wasting requests and producing blocked status files | Retry one candidate day at a time |

## Milestone 2 Progress

- Task 2.1 is complete for this session: paid-cost and strategy-readiness audits were run before further data action.
- Task 2.2 is complete for this session: this matrix records required inputs, current coverage, and coverage gaps by experiment family.
- Task 2.3 is complete for the Q4 checkpoint: Sep 2024 remainder, Oct 2024, Nov 2024, and Dec 2024 OOS coverage through `2024-12-31` were estimated with `daily_union`, downloaded, normalized, and converted into adapter/PnL summaries for the cost/execution and no-LLM baseline evidence path.
- Task 2.4 is complete for the Q4 checkpoint: `scripts\audit_strategy_data_readiness.py` now includes July partial, July chunks 3-5, Aug chunks 1-5, Sep chunks 1-3, Sep remainder, Oct 2024, Nov 2024, and Dec 2024, reports 90 closed trades, and writes `sample_adequacy` labels. Current labels are `under-sampled` and `underpowered`; MinTRL/PSR remain pending until an experiment report provides return distribution metrics.
- Task 2.5 is active: `scripts\audit_paid_costs.py` now writes `cost_guard_reconciliation` and includes pending SPY bars plans as estimate-only. Cost-basis decision is resolved for already-scoped SPY-only work: actual provider usage is the controlling guard when available; conservative known-estimate totals remain trace/warning evidence.
- Task 2.6 is resolved for the next step: Q4 trade density makes blind OOS 2025 expansion impractical as the default. The next work should use the current real-data set for engine/reporting hardening and diagnostic baselines, while future paid data expansion must be tied to a revised hypothesis or explicit data-target decision.
