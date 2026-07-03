# IMPLEMENT_PLAN.md

## Overview
- **Start state**: The project has a working SPY 0DTE research scaffold, canonical data contracts, Databento cost/download/normalization tooling, macro and VIX/VIX3M inputs, DeepSeek/OpenRouter environment wiring, and real SPY 0DTE pilot artifacts through Dec 31 2024. The latest real-data artifacts contain Mar-Dec 2023 in-sample coverage plus Jan-Dec 2024 OOS coverage. The readiness auditor now reports 21,503,220 normalized option quote rows, 232,513 SPY bar rows, 93 candidate days, and 90 closed trades. This remains `under-sampled` and `underpowered`; no acceptance-grade strategy conclusion exists.
- **End state**: The project reaches **Operationally Ready** status, not Real-Money Ready. All real-data experiment families are run, failed, or explicitly deferred; reports use MinTRL/PSR/power-aware labels, DSR/search-log discipline, big-day dependency checks, mid-vs-implementable PnL, and chronological validation. Completed experiments have Thai research logs. Only after research acceptance does the project validate paper/dry-run operations: order tickets, alerts, logs, forced close, and operator workflow. Real-money launch remains a separate blocked gate requiring IBKR options permission, account feasibility, explicit user approval, kill switch, and final launch checklist pass.
- **Total milestones**: 7
- **Estimated total effort**: XL

---

## Gap Analysis
- The immediate blocker is evidence quality, not basic scaffolding. Current real strategy evidence is still far below the rough N >= 500 prior target and below any MinTRL/PSR-based acceptance claim.
- After the 2026-07-02 grill update, the active posture is Risk-first: validate whether a real edge exists before paper trading, and treat paper trading as a later operational step only after the research is coherent.
- `N >= 500` is no longer a fixed acceptance target. The required sample length must be computed from MinTRL / PSR / power analysis using the actual return distribution, Sharpe null threshold, skewness, kurtosis, and serial correlation.
- The old weekly Databento download path is too slow and too expensive in operator time. The active data plan is now bulk-first: estimate a large coverage block for planning, execute recoverably by month with `daily_union`, then audit trade density before expanding again.
- The project must decide whether the strategy has enough trade density to justify further data spending. If Q4 2024 adds only a few trades, continuing calendar downloads without revising the hypothesis is weak research.
- Broad data acquisition must be evidence-seeking, not completionist. Each new batch must answer: how many tradable days did it add, how much did it cost, which regimes did it cover, and does the projected path to experiment-specific MinTRL still make sense?
- Data expansion must cover more than calendar time. It needs a regime coverage plan across volatility/macro regimes, trend or momentum regimes where feasible, major subperiods, economic-surprise environments where data exists, and gamma/liquidity regimes if data can support them.
- Missing Greeks/gamma/open-interest inputs are an explicit data-source research task, not a reason to permanently drop NOVI/net-gamma experiments. The plan must evaluate whether Databento, another provider, or a defensible proxy can supply these inputs at a reasonable cost.
- Experiment numbers are identifiers only. Execution order must follow dependency: data feasibility -> baseline -> execution realism -> non-LLM filters/parameters -> real-news LLM prompt research -> final acceptance -> operational validation.
- LLM work must answer the real problem: whether language reasoning over timestamp-clean news improves risk control beyond deterministic filters. It must not become a pile of safety policies that merely imitate a rule-based bot.
- LLM work should not claim ordinary backtests can prove black-swan prevention. Near-term LLM research should focus on testable sentiment/market-impact/volatility-relevance scores, assessment stability, and later separate price-input dynamic entry/exit hypotheses.
- LLM prompt templates are independent variables. The plan must compare prompt families such as role-only, structured JSON, evidence-first, few-shot, scenario-branching, self-consistency, and masking/anonymization policies on identical real-news cases.
- Historical LLM tests are vulnerable to training-data contamination. Reports must record model id, known/claimed training cutoff, document timestamp, fetch window, masking policy, and leakage caveat.
- Parameter searches such as TP/SL, VIX ranges, macro filters, strike rules, or entry timing require search logs and trial counts. If a selected-best Sharpe is reported, DSR is required or explicitly blocked.
- Any Sharpe-based claim must include sample length, MinTRL, PSR, power notes, and `under-sampled` / `underpowered` labels when applicable.
- Filtered results must report active trade counts after each filter. A filter that looks good by shrinking the sample is not acceptance-grade unless it survives MinTRL/PSR and robustness checks.
- Every option result must separate `mid_pnl` from `implementable_pnl`; deployable conclusions must use bid/ask, spread, fees, and slippage assumptions.
- Moneyness-grid experiments must use real-chain strike mapping, such as nearest discrete strike rounding, before interpreting PnL.
- Paper trading validates operations only. It cannot prove edge and must not be used to override weak backtest evidence.

## Dependency Map
- Milestone 1 preserves the research rules and active evidence ledger.
- Milestone 2 determines whether the data path is statistically and economically viable before broad experiments continue.
- Milestone 3 hardens the backtest/reporting engine so later experiments cannot overstate results.
- Milestone 4 runs the base no-LLM strategy evidence for Sub-System A and Sub-System B.
- Milestone 5 tests non-LLM execution, structure, regime, parameter, and portfolio hypotheses.
- Milestone 6 tests real-news and LLM prompt/gate value only after deterministic baselines exist.
- Milestone 7 consolidates research into an acceptance decision and then validates paper/dry-run operations if research passes.

---

## Milestone 1: Research Control And Evidence Ledger
**Goal**: Keep the project aligned with the real research problem and prevent misleading experiment order, weak statistics, leakage, or overfitting.
**Dependencies**: none
**Status**: Mostly complete; maintain as the control layer for all later work.

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 1.1 | Keep `PROJECT_BRAIN.md`, `docs\RESEARCH_CONTROL_PLANE.md`, and this plan aligned on scope, hard boundaries, and experiment-family order | S | RISK | Boot Sequence confirms no conflict across the three documents |
| 1.2 | Treat experiment numbers as identifiers, not execution order | S | OK | `docs\RESEARCH_CONTROL_PLANE.md` maps Exp01-Exp10 into dependency-based families |
| 1.3 | Keep acceptance-grade report requirements mandatory: MinTRL, PSR, power labels, DSR/search logs, big-day dependency, chronological split, mid-vs-implementable PnL, strike mapping | S | RISK | Every experiment template/checklist includes these fields before a run is accepted |
| 1.4 | Keep research-log trigger narrow: only completed real experiments receive Thai research logs, named with `NNN-higanbana-clear-topic-slug.md` | S | OK | `python scripts\audit_research_logs.py` passes after completed experiment reports, rejects legacy filename patterns, and rejects missing sequence numbers |
| 1.5 | Keep cost guard policy current: user-reported actual usage controls already-scoped SPY-only work below $125; estimates remain warning evidence | S | RISK | `python scripts\audit_paid_costs.py` reports current actual usage, remaining room, and known committed estimate |

**Milestone complete when**: The control documents agree, no experiment can be treated as acceptance-grade without the required evidence fields, and the active cost/scope rules are explicit.

---

## Milestone 2: Data Feasibility And Bulk Acquisition Gate
**Goal**: Replace slow weekly pulls with auditable bulk acquisition, complete the near-term Q4 2024 checkpoint, and decide whether more broad data acquisition is rational before spending more time or money.
**Dependencies**: Milestone 1
**Status**: Complete for the Q4 checkpoint; broad acquisition is paused unless a revised hypothesis or explicit data-target decision justifies more paid data. Risk-first planning is captured in `docs\RISK_FIRST_DATA_PLAN.md`, and the first automated Risk-first audit is captured in `reports\risk_first_data_audit.md`.

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 2.1 | Maintain the current evidence ledger through Dec 2024 | S | RISK | `python scripts\audit_strategy_data_readiness.py` reports Mar-Dec 2023 plus Jan-Dec 2024 artifacts and totals 90 closed trades |
| 2.2 | Run paid-cost, strategy-data, and research-readiness audits before any further paid action | S | RISK | `python scripts\audit_paid_costs.py`, `python scripts\audit_strategy_data_readiness.py`, and `python scripts\audit_research_readiness.py` complete and are summarized |
| 2.3 | Use a bulk planning estimate before new expansion | M | RISK | A planning artifact estimates the candidate coverage block, expected provider requests, projected option cost, SPY bar cost, and budget headroom before any download |
| 2.4 | Execute Dec 2024 as the next recoverable monthly `daily_union` batch only if the cost guard passes | L | RISK | Complete: Dec 2024 has option cost artifact, download result, normalization summary, SPY bars, adapter summary, PnL summary, and readiness-audit inclusion |
| 2.5 | Run a Q4 trade-density/cost checkpoint after Dec 2024 | M | RISK | Complete: `docs\DATA_COVERAGE_MATRIX.md` records Q4 added cost, added closed trades, cost per closed trade, projected coverage/cost to N >= 500 and N >= 1,000, and whether blind acquisition remains rational |
| 2.6 | Decide the next data path from checkpoint evidence: continue 2025 OOS, add 2022-2023 in-sample depth, add reference/pre-break data, narrow the signal, or revise the hypothesis | M | RISK | Complete for the next step: pause blind broad acquisition; use current data for engine/reporting hardening and diagnostic baselines; require a revised hypothesis or explicit data-target decision before more broad paid data |
| 2.7 | Preserve OOS discipline while expanding data | S | RISK | Reports show Jan 2024 onward remains OOS and is not used for tuning after results are viewed |
| 2.8 | Stop on scope/cost boundaries | S | RISK | Work stops if actual usage would reach $125, a new paid provider is introduced, symbol universe expands beyond SPY, or broker/order transmission is involved |
| 2.9 | Replace fixed N gate with experiment-specific MinTRL/PSR sample plan | M | RISK | Complete first automation: `reports\risk_first_data_audit.md` computes current inputs and approximation fields: 90 trades, observed Sharpe proxy `0.092203`, skewness `1.221374`, kurtosis `3.09085`, first-order autocorrelation `-0.02181`, PSR about `0.821497` versus Null Sharpe `0`, MinTRL about 285 observations, and observed Sharpe below Null Sharpe `0.5` |
| 2.10 | Build a regime coverage plan before more paid data | M | RISK | Complete first automation: `reports\risk_first_data_audit.md` counts current trades/PnL by VIX bucket, macro bucket, trend bucket, subperiod, and split; blockers remain for missing reference/pre-break trades, missing high-VIX trade coverage, and partial trend-history gaps |
| 2.11 | Research Greeks/gamma/open-interest data sources and proxies | M | RISK | Feasibility, enrichment, and diagnostic aggregation probes complete with caveats: `reports\greeks_oi_feasibility_audit.md` confirms OPRA `OPEN_INTEREST`, exact-symbol OI mapping, prior SPY-bar joins, and one self-computed IV/Delta/Gamma path. `reports\greeks_oi_enrichment_probe_report.md` enriches 3,488 target-date quotes, joins 3,488 prior OI rows and underlying prices, computes IV/Delta/Gamma for 1,750 rows, and blocks 1,738 rows where mid price is outside the Black-Scholes bracket. `docs\GAMMA_AGGREGATION_VALIDATION_POLICY.md` defines proxy formulas, moneyness buckets, scaling, validation gates, and forbidden claims. `reports\diagnostics\gamma_aggregation_diagnostic_summary.json` runs the policy on the one-day enriched set: timestamp discipline and search-log gates pass, but coverage fails at computed Greeks rate `0.50172`, stability is `under-regime-sampled`, and economic-sign validation is blocked until multiple dates exist. Strategy use remains diagnostic-only and blocked |

**Milestone complete when**: The project has a clear data-feasibility decision based on real batch evidence, including whether continuing data acquisition is statistically and economically justified, and the next expansion path is chosen before any additional blind calendar pull. Current decision: Q4 2024 trade density does not justify blind broad acquisition; the Risk-first automation still blocks broad buying. The OPRA OI plus self-computed IV/Greeks enrichment path is feasible with caveats, and the first gamma aggregation diagnostic is now complete but blocked by policy gates. The next data action must be targeted: add enough gamma/OI dates across normal, macro-event, high-vol/stress, and OOS regimes to test coverage/stability/economic sign; choose missing pre-break/high-VIX/major-regime strategy coverage; or revise the strategy hypothesis toward higher trade density.

---

## Milestone 3: Backtest And Reporting Engine Hardening
**Goal**: Make the real-data experiment engine capable of producing evidence that cannot be confused with optimistic pilot output.
**Dependencies**: Milestone 2
**Status**: Complete. The closure audit `python scripts\audit_m3_backtest_reporting_hardening.py` passes and confirms the current artifacts cover implementable PnL, sample labels, big-day dependency, search logs/DSR blocker, chronological metadata, and strike mapping.

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 3.1 | Add or confirm report support for both `mid_pnl` and `implementable_pnl` | M | RISK | First pass complete: `reports\pilots\dec_2024_daily_union_pilot_pnl_m3_report.md` shows mid PnL, implementable PnL, bid/ask liquidation treatment, `$0.64` per-contract fee, and cost drag |
| 3.2 | Add MinTRL/PSR/power-aware reporting for Sharpe-based claims | M | RISK | First pass complete: the M3 sample report labels insufficient evidence as `under-sampled` / `underpowered` and keeps MinTRL/PSR as pending until an experiment return distribution exists |
| 3.3 | Add DSR/search-log plumbing for parameter and filter searches | M | RISK | First pass complete: `scripts\run_jan2024_pilot_sensitivity.py` writes `reports\experiments\search_logs\jan_2024_pilot_sensitivity_search_log.jsonl`, saves `trial_count=10`, `parameter_grid`, selection metadata, and `DSR blocked` in the summary/report |
| 3.4 | Add big-day dependency checks to report generation | M | RISK | First pass complete: the M3 sample report removes top/bottom 5% trades by implementable PnL and reports retained PnL and Sharpe proxy |
| 3.5 | Enforce chronological split and no-OOS-tuning metadata | M | RISK | Complete first pass: `python scripts\validate_m3_experiment_guardrails.py` validates train/OOS windows, parameter lock, no random split, no OOS tuning, and decision-time fit discipline |
| 3.6 | Define real-chain strike mapping for moneyness-grid experiments | S | RISK | Complete first pass: `experiments\m3_experiment_guardrails.json` sets `nearest_discrete_strike_rounding` with a report-disclosure requirement, and the validator rejects unsupported/interpolated default methods |
| 3.7 | Run the full local test suite after engine/report changes | S | OK | Complete after M3 closure: `python -m unittest discover -s tests` passes 259 tests and `python scripts\run_fixture_pipeline.py` returns `status=pass` |

**Milestone complete when**: Complete. A real-data report can be generated and audited with implementable PnL, statistical labels, robustness checks, search logs, and chronological metadata.

---

## Milestone 4: Baseline Strategy Evidence
**Goal**: Learn whether the base no-news/no-LLM strategies have any research value before adding more filters or LLM complexity.
**Dependencies**: Milestones 2-3

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 4.1 | Run the Sub-System A ORB baseline on available real data without news/LLM filters | L | RISK | Complete: `reports\baselines\subsystem_a_orb_baseline_summary.json` and `.md` report 90 closed trades, mid PnL `$1089.50`, implementable PnL `$545.60`, OOS implementable PnL `$-78.44`, `under-sampled` / `underpowered` labels, big-day dependency, and conclusion `ยังสรุปไม่ได้` |
| 4.2 | Run Sub-System B capped-risk put ratio baseline where data and account feasibility allow | L | RISK | Complete: `reports\baselines\subsystem_b_put_ratio_feasibility_summary.json` and `.md` report 412 closed trades, implementable PnL `$-5973.44`, OOS implementable PnL `$-3866.76`, min/median/max defined loss `$366/$566/$773`, 0 trades fit the `$300` Sub-System B allocation or `$20` risk budget, `under-sampled` / `underpowered` labels, and conclusion `ไม่ผ่าน` for current sizing |
| 4.3 | Compare forced-close-only versus currently implemented target/stop behavior as diagnostics, not OOS tuning | M | RISK | Complete: `reports\baselines\m4_exit_behavior_diagnostic_summary.json` and `.md` compare `forced_close_only` versus `target_stop_25_50` on identical Sub-System A candidate days. Result is `ยังสรุปไม่ได้`; target/stop improves OOS and downside metrics but worsens overall PnL by `$-436.68`, remains `under-sampled` / `underpowered`, and no exit model is selected from OOS |
| 4.4 | Confirm no entry market orders, skipped unfilled entries, and no position held past 3:45 PM ET | M | RISK | Complete: `reports\baselines\m4_execution_rule_compliance_audit.json` and `.md` pass with 0 blockers. The audit checked 96 component summary files, 273 closed trades, 546 entry fill rows, and 546 close timestamp rows; no entry market evidence or close timestamp after 15:45 ET was found. A synthetic probe confirms missing entry quote/fill evidence skips the trade. |
| 4.5 | Write Thai research logs for completed baseline experiments only, using running-number filenames | M | OK | Baseline logs complete and pushed: `research_log\001-higanbana-orb-baseline-real-data.md`, `research_log\002-higanbana-put-ratio-feasibility-real-data.md`, and `research_log\003-higanbana-exit-behavior-diagnostic-real-data.md`; `python scripts\audit_research_logs.py` passes and next filename prefix is `004-higanbana-` |

**Milestone complete when**: Complete. The project has baseline evidence for Sub-System A, Sub-System B, exit behavior diagnostics, execution-rule compliance, and Thai research logs for completed baseline experiments. Current conclusions remain diagnostic: Sub-System A and exit behavior are `ยังสรุปไม่ได้`; Sub-System B current-sizing feasibility is `ไม่ผ่าน`.

---

## Milestone 5: Non-LLM Experiment Families
**Goal**: Test deterministic strategy, execution, regime, parameter, and portfolio hypotheses before using LLM/news as a gate.
**Dependencies**: Milestones 3-4

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 5.1 | Run transaction-cost and execution-latency sensitivity as its own experiment family | L | RISK | Complete: `reports\experiments\m5_transaction_cost_latency_sensitivity_summary.json` and `.md` compare 8 cost/latency scenarios with search log, DSR blocker, mid-vs-implementable PnL, cost drag, and sample labels. Baseline half-spread + `$0.64` fee + 0 latency has implementable PnL `$545.60` and OOS `$-78.44`; 1-minute latency reduces the comparable scenario to `$169.60`; worst stress is `$-141.00`. Conclusion remains `ยังสรุปไม่ได้`. |
| 5.2 | Run strike-selection experiments: delta versus moneyness with explicit discrete-strike mapping | L | RISK | Complete with delta blocker: `reports\experiments\m5_strike_selection_sensitivity_summary.json` and `.md` compare 5 moneyness/target-gap scenarios using nearest discrete strike rounding, no interpolation, search log, DSR blocker, EV/trade, gap breach rate, and implementable PnL. Delta-based selection is explicitly blocked because current normalized option quotes contain no Greeks. Best diagnostic scenario is target gap `$0.25` with implementable PnL `$632.60`; baseline-like target gap `$1.48` has `$558.60`; all OOS results remain negative and conclusion remains `ยังสรุปไม่ได้`. |
| 5.3 | Run entry-timing sensitivity for Sub-System A and B with search logs | L | RISK | Complete: `reports\experiments\m5_entry_timing_sensitivity_summary.json` and `.md` compare 12 timing trials with a search log and DSR blocker. Sub-System A recomputes ORB breakout timing from 09:35 to 10:00; 09:35 remains the best diagnostic scenario with implementable PnL `$539.60`, while all Sub-System A OOS results are negative. Sub-System B tests exact 09:55-10:00 put snapshots; 09:59 is least bad at `$-5827.44`, but 0 trades fit the `$300` allocation or `$20` risk budget. Conclusion remains `ยังสรุปไม่ได้`. |
| 5.4 | Run exit target/stop sensitivity with search logs | XL | RISK | Complete: `reports\experiments\m5_exit_target_stop_sensitivity_summary.json` and `.md` compare 7 TP/SL trials with a search log and DSR blocker. Forced close remains best by total implementable PnL at `$545.60`; `tp_100_stop_100` has best OOS diagnostic PnL at `$262.56` but cannot be selected from OOS; `tp_10_stop_25` lowers max drawdown to `-0.153230` but total PnL is `-$93.08`. Conclusion remains `ยังสรุปไม่ได้`. |
| 5.5 | Run VIX/VXV, macro-event, and NOVI/net-gamma-proxy filters | XL | RISK | Complete: `reports\experiments\m5_regime_filter_sensitivity_summary.json` and `.md` compare 9 VIX/VXV and macro-event filter trials with a search log and DSR blocker. VIX uses previous available close before trade date; macro uses scheduled same-day events. `exclude_high_importance_macro_same_day` is best diagnostic scenario with 64 closed trades, implementable PnL `$820.16`, and OOS `$240.96`; `exclude_major_macro_same_day` has 70 closed trades, implementable PnL `$601.80`, and OOS `$95.72`. NOVI/net-gamma is explicitly blocked because current option quotes lack Greeks, open interest, dealer inventory, or position reconstruction inputs. Conclusion remains `ยังสรุปไม่ได้`. |
| 5.6 | Run portfolio construction tests after Sub-System A/B returns exist | L | RISK | Complete: `reports\experiments\m5_portfolio_construction_diagnostic_summary.json` and `.md` compare 5 allocation trials with a search log and DSR blocker. A-only is the only scenario not blocked by Sub-System B sizing and has total PnL `$545.60`, OOS `$-78.44`, and max drawdown `-0.370769`; B-only is worst at `-$5973.44`; equal weight, inverse-volatility risk parity, and inverse-ES95 parity remain blocked for current sizing/fractional-contract reasons. Conclusion remains `ยังสรุปไม่ได้`. |
| 5.7 | Run structural-break testing around May 11 2022 only when reference/pre-break data exists | L | RISK | Deferred with evidence: `reports\experiments\m5_structural_break_assessment_summary.json` and `.md` show 0 reference/pre-break SPY 0DTE option datasets and 0 closed trades before `2022-05-11`, so no structural-break performance statistic was run. Post-break train has 41 closed trades from `2023-03-01` to `2023-12-29`; OOS has 49 closed trades from `2024-01-02` to `2024-12-31`; total remains below N >= 500. Conclusion remains `ยังสรุปไม่ได้`. |
| 5.8 | Write Thai research logs for completed deterministic experiment families with readable running-number filenames | M | OK | Current deterministic logs `001`-`010` are present and pushed; `python scripts\audit_research_logs.py` must pass after each completed/deferred family and the next completed real experiment log must start with `011-higanbana-` |

**Milestone complete when**: Complete/deferred. Deterministic experiments are completed, failed, or explicitly deferred with search-aware statistics and sample-size-aware conclusions. M5.7 is deferred until reference/pre-break SPY 0DTE option coverage exists.

---

## Milestone 6: Real News And LLM Prompt/Gate Research
**Goal**: Test whether LLM/news adds value beyond deterministic filters using real timestamp-clean news and prompt templates as the independent variables.
**Dependencies**: Milestones 3-5; real news archive availability

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 6.1 | Build or unblock a real news archive for candidate days | L | RISK | In progress but blocked on real archive: latest single-day retry for `2023-04-13` returned GDELT HTTP 429, command plan now shows 5 blocked per-day captures and 0 captured candidate days. Canonical `news_item` schema/import tooling now requires and preserves `decision_time_et`; fixture/offline imports verify `published_at_et` and `fetched_at_et` are not after `decision_time_et`. Real records still must include `published_at`, `fetched_at`, source, URL/headline/body where available, decision timestamp, and raw provenance |
| 6.2 | If GDELT remains blocked, write a source-decision note before any provider change or paid news use | M | RISK | First note complete: `docs\M6_NEWS_SOURCE_DECISION_NOTE.md` records that GDELT remains the free primary candidate but rapid retries should pause; user approval is still required before a new paid source or provider scope change |
| 6.3 | Define LLM prompt-template families as experiment variables | M | RISK | Prompt plan includes role-only, structured JSON, evidence-first, few-shot, scenario-branching, self-consistency, sentiment/impact scoring, stability via repeated calls where cost allows, and masking/anonymization variants or justified exclusions |
| 6.4 | Add historical-contamination controls | M | RISK | Every LLM run records model id, known/claimed training cutoff, news timestamp, fetch window, masking policy, and leakage caveat |
| 6.5 | Run DeepSeek/OpenRouter prompt-family experiments on identical real-news cases | L | RISK | Report compares parse validity, sentiment/impact/volatility-relevance score stability, repeated-call dispersion or consensus, false-block/false-allow review rate, evidence grounding, latency, and cost |
| 6.6 | Run deterministic baseline versus LLM-gated strategy ablation only after prompt-family review | L | RISK | Report compares baseline and LLM-gated PnL, Sharpe/PSR, ES, drawdown, skipped trades, cost, and big-day dependency |
| 6.7 | Write Thai research logs for completed LLM/news experiments with readable running-number filenames | M | OK | `python scripts\audit_research_logs.py` passes and Yuehua Research Log push state is clean |
| 6.8 | Design a separate price-input dynamic entry/exit LLM hypothesis before any run | M | RISK | A pre-registered design separates price-input prompts from news/sentiment prompts, defines chronological inputs, ablation variants, forbidden leakage, success metrics, and stop conditions |

**Milestone complete when**: The LLM/news layer has a clear conclusion: `ผ่าน`, `ไม่ผ่าน`, or `ยังสรุปไม่ได้`, with contamination caveats and sample-size labels where required.

---

## Milestone 7: Research Acceptance And Paper/Dry-Run Operations
**Goal**: Convert research evidence into a final decision, then validate operations only if the research gate allows it.
**Dependencies**: Milestones 4-6

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 7.1 | Regenerate final research review from real experiment reports only | M | RISK | Final review separates fixture/scaffold evidence from real strategy evidence and cites every completed report |
| 7.2 | Run research acceptance gate with MinTRL/PSR/power-aware labels | M | RISK | Gate returns `approved_for_operational_validation`, `blocked`, or `inconclusive` without overstating weak samples |
| 7.3 | Confirm every completed experiment has a Thai research log | S | OK | `python scripts\audit_research_logs.py` passes |
| 7.4 | If research passes, recheck IBKR permission, cash-account constraints, and paper-trading availability | S | RISK | Status is documented without storing credentials and without enabling live transmit |
| 7.5 | Validate paper/dry-run order tickets for accepted strategy components only | M | RISK | Tickets reject entry market orders, undefined risk, missing protective wing, excess buying power, missing 3:45 PM close plan, and live transmit |
| 7.6 | Validate daily operator workflow, alerts, journal, and forced-close sequence | M | RISK | Paper/dry-run logs show pre-open checks, no-go reasons, staging, alerts, close workflow, and manual fallback |
| 7.7 | Keep real-money launch as a separate blocked gate | S | RISK | Launch checklist still requires research pass, options permission, account feasibility, explicit user approval, kill switch, and no stored secrets |

**Milestone complete when**: The system is operationally ready for approved paper/dry-run validation, or remains blocked with exact missing research or operational gates. It is not real-money ready unless the separate launch checklist later passes.

---

## Execution Notes
- **Active milestone**: Milestone 6.
- **Immediate next safe action**: Use `reports\risk_first_data_audit.md`, `reports\greeks_oi_enrichment_probe_report.md`, `docs\GAMMA_AGGREGATION_VALIDATION_POLICY.md`, and `reports\diagnostics\gamma_aggregation_diagnostic_summary.json` as the pre-purchase checkpoint. Do not buy broad calendar data yet. The one-day gamma aggregation diagnostic is complete but not strategy-ready: exact-symbol OI and underlying joins are 100%, timestamp discipline passes, no gamma threshold was selected, but computed Greeks coverage is only `0.50172`, stability is `under-regime-sampled`, and economic-sign validation needs multiple dates. Next choose one targeted action: add gamma/OI/Greeks coverage for a small pre-registered regime set; add missing reference/pre-break and high-VIX/major-regime strategy data; add newer OOS only if it improves regime coverage; or revise the strategy hypothesis toward higher trade density. Milestone 6 remains active but blocked for real LLM research until real timestamp-clean news cases exist; GDELT was retried once for `2023-04-13` on 2026-07-02 and again returned HTTP 429; `reports\news_gdelt_capture_command_plan.json` now shows 5 blocked per-day captures, 66 not-attempted days, and `cooldown_recommended`. Do not run DeepSeek/OpenRouter prompt-family experiments as research until real timestamp-clean news cases exist.
- **Current cost basis**: User-reported actual usage is `$64.64`; stop threshold is `$125`; remaining room is `$60.36` before including any provider-side account refresh. Dec 2024 added estimated Databento cost of `$11.504703` for option quotes plus `$0.006782` for SPY bars. The working projected actual usage after Dec is about `$76.15`, still below `$125`; provider-reported actual usage should be refreshed when available.
- **Data policy**: Use a three-step workflow only after the Risk-first plan identifies the target sample/regime/field gap. Step 1: estimate a targeted block for planning, such as a pre-break block, high-VIX/stress window, newer OOS validation block, or provider field test. Step 2: execute recoverably by monthly `daily_union` or another auditable batch unit so failures do not corrupt the whole dataset. Step 3: run a trade-density, regime-coverage, field-coverage, and cost checkpoint after each 3 added months or 50 newly closed trades, whichever comes first. Use smaller chunks for provider field probes and recovery.
- **Data continuation rule**: The Q4 checkpoint shows poor trade density and an impractical blind path under the old fixed N>=500 framing. Calendar expansion is paused. `reports\risk_first_data_audit.md` confirms this with sample/regime/field evidence: current N is 90 versus approximate MinTRL 285 even against Null Sharpe `0`, observed Sharpe is below Null Sharpe `0.5`, reference/pre-break and high-VIX coverage are missing, and current normalized quotes lack vendor Greeks/OI.
- **Experiment policy**: Do not run Exp02/LLM before real timestamp-clean news cases and deterministic baselines exist. Do not run parameter searches without search logs and DSR planning. Do not treat OOS diagnostics as tuning input.
- **Blocked items**: Real news archive is missing; GDELT has persistent HTTP 429 pressure with 5 blocked per-day capture attempts; current strategy evidence is under-sampled/underpowered; reference/pre-break data is missing so M5.7 remains deferred; gamma-family strategy use remains blocked because the first diagnostic aggregation passes timestamp/search-log gates but fails coverage, stability, and economic-sign gates; IBKR options permission and real-money approval remain external gates.
- **Decision points**: Before any new broad paid data, choose whether to revise trade conditions, target a higher-density signal, add 2022-2023 in-sample depth, add reference/pre-break data for structural break testing, add high-VIX/stress coverage, add 2025 or other OOS regimes, buy/change news provider, or buy/proxy Greeks/gamma/open-interest data. New paid providers still require user approval.
- **Risk checkpoints**: Before every paid pull, after each monthly batch, after Q4 completion, before any parameter search, before any LLM prompt experiment, before final acceptance, and before paper/dry-run validation.
- **Archive policy**: Before replacing `IMPLEMENT_PLAN.md` again, recommend archiving the current plan and get user approval unless the user has already explicitly instructed replacement in that turn.
- **Verification loop**: After every milestone, run the operating checks from `PROJECT_BRAIN.md`, including `python -m unittest discover -s tests`; for scaffold-impacting changes also run `python scripts\run_fixture_pipeline.py` and relevant readiness audits.
