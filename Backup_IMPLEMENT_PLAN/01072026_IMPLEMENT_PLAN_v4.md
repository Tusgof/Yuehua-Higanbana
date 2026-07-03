# IMPLEMENT_PLAN.md

## Overview
- **Start state**: The project has a working research scaffold, Databento tooling, canonical contracts, fixture pipeline, macro/VIX coverage, DeepSeek/OpenRouter adapter smoke evidence, and partial real SPY 0DTE data through Sep 30 2024. Current real strategy evidence is still weak: 14,745,863 option quote rows, 199,378 SPY bar rows, 83 candidate days, and 80 closed trades. Evidence is `under-sampled` / `underpowered`; real news archive is missing; GDELT remains blocked by HTTP 429; IBKR live order transmission is out of scope until research and operational gates pass.
- **End state**: The project reaches **Operationally Ready** status: real-data experiment families have been run, failed, or explicitly deferred; reports use MinTRL/PSR/power-aware labels; all completed experiments have Thai research logs; accepted components pass the research acceptance gate; and paper/dry-run operational validation proves workflow, order tickets, alerts, logging, and forced close. Real-money launch remains a separate blocked gate requiring options permission, account feasibility, explicit user approval, and launch checklist pass.
- **Total milestones**: 7
- **Estimated total effort**: XL

---

## Gap Analysis
- The main blocker is not code scaffolding anymore. The blocker is evidence quality: current sample size is far below what can support strong Sharpe, drawdown, or tail-risk conclusions.
- Weekly Databento pulls are too slow. Normal data expansion must use recoverable monthly batches. `daily_union` Databento cost/download requests are now the preferred workflow because they reduce many narrow research windows into one provider request per trading day while preserving a clear daily cost cap.
- The project must not blindly chase N >= 500 if the trade density is too low. After each bulk checkpoint, calculate trades added, cost per closed trade, projected calendar coverage, and projected cost to reach the next evidence threshold.
- Experiment IDs in `backtest_experiments_plan.md` are identifiers, not execution order. The correct order is: baseline and execution realism first, then regime/parameter experiments, then LLM/news, then final acceptance, then paper/dry-run operations.
- Experiment 7 in the old file mixes two different ideas: LLM prompt robustness and transaction-cost sensitivity. In the active plan, LLM prompt research belongs in the LLM/news milestone, while transaction cost/latency belongs in core execution feasibility.
- LLM/news research must use real timestamp-clean news, not synthetic cases. Historical LLM tests must control training-data contamination through point-in-time checkpoints where possible or masking/anonymization plus leakage caveats.
- Parameter/filter searches must keep search logs and trial counts. Any selected-best Sharpe claim requires Deflated Sharpe Ratio (DSR) or a DSR blocker.
- Every Sharpe report must include sample length, MinTRL, PSR, power notes, and `under-sampled` / `underpowered` labels when required.
- Every filtered strategy result must include active trade counts after filtering and a big-day dependency check.
- Every option result must separate `mid_pnl` from `implementable_pnl` using bid/ask and per-leg fee assumptions.
- Moneyness-grid experiments must state the real-chain strike mapping method before interpreting PnL.
- Paper trading is operational validation only. It cannot rescue weak backtest evidence.

## Dependency Map
- Milestone 1 locks research rules and experiment-family order.
- Milestone 2 decides whether the data path is economically and statistically viable before more broad experiments. It must first finish the current OOS 2024 Q4 checkpoint, then decide whether more data acquisition is rational.
- Milestone 3 runs the base strategy and execution-realism experiments that all later experiments depend on.
- Milestone 4 runs non-LLM regime, structure, portfolio, entry, exit, and parameter experiments.
- Milestone 5 runs real-news and LLM prompt/gate experiments only after deterministic baselines exist.
- Milestone 6 consolidates all research into an acceptance decision.
- Milestone 7 validates paper/dry-run operations only after research acceptance.

---

## Milestone 1: Research Control Plane
**Goal**: Preserve the research rules that prevent misleading experiment order, weak statistics, leakage, and overfitting.
**Dependencies**: none
**Status**: Completed 2026-07-01.

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 1.1 | Keep the experiment-family map active and treat experiment numbers as identifiers only | S | OK | `docs\RESEARCH_CONTROL_PLANE.md` maps all 10 experiment IDs into dependency-based families |
| 1.2 | Keep MinTRL/PSR/power labels mandatory for Sharpe-based conclusions | S | RISK | Acceptance checklist requires sample length, MinTRL, PSR, power note, and labels |
| 1.3 | Keep report states explicit: preliminary, under-sampled, underpowered, accepted, failed, inconclusive, deferred | S | OK | Report metadata states are documented in `docs\RESEARCH_CONTROL_PLANE.md` |
| 1.4 | Keep methodology guardrails mandatory: LLM contamination, DSR/search logs, big-day dependency, mid-vs-implementable PnL, strike mapping, chronological split | S | RISK | Guardrail checklist exists and is referenced by later milestones |
| 1.5 | Keep hard boundaries active: SPY only, no entry market orders, no OOS tuning, no random K-fold, no IBKR transmit, no stored secrets | S | RISK | `PROJECT_BRAIN.md` and readiness audits reflect these boundaries |

**Milestone complete when**: The control plane remains current and every later milestone can point to it as the source of research discipline.

---

## Milestone 2: Data Feasibility And Bulk Acquisition Gate
**Goal**: Stop slow blind acquisition, obtain enough real data for the next decision, and decide whether broad data expansion is worth continuing.
**Dependencies**: Milestone 1
**Status**: Active.

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 2.1 | Run paid-cost, strategy-data, and research-readiness audits before any paid action | S | RISK | `python scripts\audit_paid_costs.py`, `python scripts\audit_strategy_data_readiness.py`, and `python scripts\audit_research_readiness.py` complete and are summarized in `PROJECT_BRAIN.md` |
| 2.2 | Use the `daily_union` Databento workflow for option quote cost/download batches unless a narrower recovery unit is needed | M | RISK | Cost artifacts record `cost_granularity=daily_union`, planned research windows, live provider requests, total estimated cost, and the note that the cost is exact for the daily superset request |
| 2.3 | Replace weekly pulls with recoverable monthly batches, using quarter-level planning only for cost/scope decisions | L | RISK | For each month, option quotes and SPY bars are downloaded, normalized, registered, converted into adapter/PnL summaries, and audited without corrupting prior data |
| 2.4 | Complete the first bulk target: OOS 2024 Q4 completion after Sep remainder, starting with Oct 2024 then Nov/Dec 2024 if cost/readiness audits still pass | L | RISK | Readiness audit reports added rows, candidate days, closed trades, cost, and sample labels for each completed monthly batch and for the full Q4 checkpoint |
| 2.5 | Run a trade-density checkpoint after Q4 completion, or earlier if 50 new closed trades are added first | M | RISK | `docs\DATA_COVERAGE_MATRIX.md` records added closed trades, added cost, cost per closed trade, projected months/years and cost to reach N >= 500 and preferred N >= 1,000 |
| 2.6 | Decide the next data path after the checkpoint: continue 2025 OOS, add 2022-2023 in-sample depth, add reference/pre-break data, narrow the strategy, or revise the strategy hypothesis | M | RISK | A written decision is added to `PROJECT_BRAIN.md` and `docs\DATA_COVERAGE_MATRIX.md` before further broad acquisition |
| 2.7 | Maintain stop rules for cost, provider, symbol universe, and scope | S | RISK | Work stops if actual usage would reach $125, a new paid provider is needed, symbol universe expands beyond SPY, or broker/order transmission is involved |

**Milestone complete when**: The project has a real-data coverage decision based on batch evidence, not a slow weekly loop, and either enough data to run core experiments with honest labels or a documented reason to revise the hypothesis before paying for more data.

---

## Milestone 3: Baseline Strategy And Execution Realism
**Goal**: Establish whether the base strategy mechanics survive realistic option execution before testing extra filters.
**Dependencies**: Milestones 1-2

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 3.1 | Run the no-news, no-LLM baseline for Sub-System A and Sub-System B where data supports it | L | RISK | Report includes trade log, skipped trades, cashflow, equity curve, drawdown, benchmark comparison, MinTRL/PSR labels, and conclusion |
| 3.2 | Separate mid PnL from implementable PnL for every option leg and strategy | M | RISK | Report contains `mid_pnl`, `implementable_pnl`, bid/ask treatment, per-leg fee assumptions, and cost drag |
| 3.3 | Test transaction cost and execution latency sensitivity as its own core experiment | L | RISK | Report compares half-spread/full-spread, fee assumptions, limit retry, latency delays, friction drag, break-even cost, and conclusion |
| 3.4 | Test forced-close and unfilled-limit behavior in the backtest | M | RISK | Logs prove no entry market order, skipped unfilled entries, and no position held past 3:45 PM ET |
| 3.5 | Test Sub-System B defined-risk and $1,000 account feasibility without deleting it from scope | M | RISK | Report distinguishes research viability, buying-power feasibility, paper-trading feasibility, and any capital-size blocker |
| 3.6 | Write Thai research logs only for completed real-data experiments | M | OK | `python scripts\audit_research_logs.py` passes and Yuehua Research Log push state is clean |

**Milestone complete when**: The project knows whether the base strategies are even worth filtering, and all later experiments use realistic execution assumptions instead of mid-price optimism.

---

## Milestone 4: Non-LLM Strategy Experiments
**Goal**: Test regime, structure, portfolio, entry, exit, and structural-break variables before adding LLM/news complexity.
**Dependencies**: Milestone 3

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 4.1 | Test Market-Maker Net Gamma / NOVI proxy activation versus baseline | L | RISK | Report compares Sharpe/PSR, drawdown, Sub-System A win rate, false-breakout behavior, ES95/ES99, and active trade count |
| 4.2 | Test VIX regime and macro-event filters with active-trade counts after each filter | L | RISK | Report includes filter-by-filter trade counts, MinTRL/PSR labels, ES, drawdown, benchmark comparison, and DSR if ranges were searched |
| 4.3 | Test portfolio construction: equal weight, risk parity, and feasible capital allocation | L | RISK | Report compares Sortino, max drawdown, ES contribution, Sub-System A/B risk contribution, and $1,000 account feasibility |
| 4.4 | Test strike selection: delta versus moneyness with explicit real-chain strike mapping | L | RISK | Report states nearest discrete strike rounding, interpolation, or another justified method before PnL interpretation |
| 4.5 | Test entry timing and exit target/stop sensitivity with full search logging | XL | RISK | Report records every parameter trial, selected result, trial count, DSR or DSR blocker, and no-OOS-tuning evidence |
| 4.6 | Test structural break around May 11 2022 using chronological splits only | L | RISK | Report separates reference/pre-break, post-2022 in-sample, and OOS evidence without shuffled validation |
| 4.7 | Run big-day dependency checks for all accepted-looking variants | M | RISK | Removing the top/bottom 5% extreme days/trades does not invalidate any acceptance-grade conclusion, or the report says it fails robustness |
| 4.8 | Write Thai research logs for completed experiment families | M | OK | `audit_research_logs.py` passes after each completed family |

**Milestone complete when**: All non-news/LLM experiment families are completed, failed, or explicitly deferred with MinTRL-aware conclusions and search-aware statistics.

---

## Milestone 5: Real News And LLM Gate Research
**Goal**: Test whether LLM/news adds value beyond deterministic filters, using real timestamp-clean news and prompt families as independent variables.
**Dependencies**: Milestones 1, 3, and 4; real news archive availability

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 5.1 | Build or unblock a real news archive for candidate days | L | RISK | Imported news records include `published_at`, `fetched_at`, source, URL/headline/body where available, decision time, and raw provenance |
| 5.2 | If GDELT remains blocked, write a source-decision note before any new paid news provider | M | RISK | User approval is recorded before changing provider or adding paid news cost |
| 5.3 | Define prompt-template families as the independent variable | M | RISK | Prompt plan includes role-only, structured JSON, evidence-first, few-shot, scenario-branching, and self-consistency or approved alternatives |
| 5.4 | Add contamination controls for historical news tests | M | RISK | Each run records model id, known/claimed training cutoff, document timestamp, retrieval window, masking policy, and leakage caveat |
| 5.5 | Run DeepSeek/OpenRouter prompt experiments on identical real-news cases | L | RISK | Report compares parse validity, stability, false-block/false-allow review rate, evidence grounding, latency, and provider cost |
| 5.6 | Run deterministic no-LLM versus LLM-gated strategy ablation only after prompt review | L | RISK | Report compares baseline versus LLM-gated PnL, Sharpe/PSR, ES, drawdown, skipped trades, cost, and big-day dependency |
| 5.7 | Write Thai research logs for completed LLM/news experiments | M | OK | `audit_research_logs.py` passes and remote push state is clean |

**Milestone complete when**: The LLM/news layer has a real-news conclusion: `ผ่าน`, `ไม่ผ่าน`, or `ยังสรุปไม่ได้`, with under-sampled/underpowered labels where evidence is insufficient.

---

## Milestone 6: Research Acceptance And Final Reporting
**Goal**: Convert experiment evidence into a final research decision without overstating weak samples.
**Dependencies**: Milestones 3-5

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 6.1 | Regenerate final research review from real experiment reports only | M | RISK | Final review separates fixture/scaffold evidence from real strategy evidence and cites every completed report |
| 6.2 | Run the research acceptance gate with MinTRL/PSR/power-aware labels | M | RISK | Gate blocks or labels results when evidence is `under-sampled` or `underpowered` |
| 6.3 | Apply DSR/search-log requirements to selected-best parameter or filter claims | M | RISK | Reports include DSR or a DSR blocker when trial count/search log is incomplete |
| 6.4 | Document accepted, failed, inconclusive, and deferred components | M | OK | Final review includes hypothesis, evidence, conclusion, failure conditions, overturning evidence, diagnosis, and next hypotheses |
| 6.5 | Confirm every completed experiment has a Thai research log pushed to Yuehua Research Log | S | OK | `python scripts\audit_research_logs.py` passes |
| 6.6 | Decide whether research justifies operational validation | S | RISK | Final gate explicitly says `approved_for_operational_validation`, `blocked`, or `inconclusive` |

**Milestone complete when**: The project has a defensible research decision and a documented path either to operational validation or back to revised hypotheses.

---

## Milestone 7: Paper/Dry-Run Operational Validation
**Goal**: Validate operational workflow after research pass, without treating paper trading as evidence of edge or enabling real-money launch.
**Dependencies**: Milestone 6

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 7.1 | Recheck IBKR permission, cash-account constraints, and paper-trading availability | S | RISK | Status is documented without storing credentials and without enabling live transmit |
| 7.2 | Validate paper/dry-run order tickets for accepted strategy components only | M | RISK | Tickets reject entry market orders, undefined risk, missing protective wing, excess buying power, and missing 3:45 PM ET close plan |
| 7.3 | Validate daily operator workflow, alerts, journal, and forced-close sequence | M | RISK | Paper/dry-run logs show pre-open checks, no-go reasons, order staging, alerts, close workflow, and manual fallback path |
| 7.4 | Run portfolio-size and operational feasibility checks if Sub-System B or capital constraints remain uncertain | M | RISK | Report distinguishes operational feasibility from edge evidence and lists any capital-size blockers |
| 7.5 | Keep real-money launch as a separate blocked gate | S | RISK | Launch checklist still requires research pass, options permission, cash-account feasibility, user approval, kill switch, and no stored secrets |

**Milestone complete when**: The system is operationally ready for the approved paper/dry-run workflow, or remains blocked with exact missing operational gates. It is not real-money ready unless the separate launch checklist later passes.

---

## Execution Notes
- **Active milestone**: Milestone 2.
- **Immediate next safe action**: Continue Milestone 2 by estimating and, if the cost guard passes, downloading Oct 2024 option quotes with `daily_union`, then SPY bars, normalization, adapter/PnL conversion, and readiness audit. Do not resume weekly chunks unless a monthly batch fails and needs recovery.
- **Current cost basis**: User-reported actual provider usage is `$64.64`; break threshold is `$125`; actual remaining budget is `$60.36`. Conservative known-estimate totals remain warning evidence, not the controlling stop basis while actual provider usage is available.
- **Data acquisition policy**: Do not continue weekly chunks by default. Use monthly option quote and SPY bar batches, with quarter-level planning for cost only. Normalize, register, and audit after each month. Use smaller chunks only as recovery units if a monthly batch fails.
- **Trade-density policy**: After Q4 completion, and thereafter after each 3 added calendar months or 50 new closed trades, calculate added closed trades, added cost, cost per closed trade, projected calendar years, and projected cost to N >= 500 and N >= 1,000. If the projection is impractical, stop blind acquisition and revise the hypothesis.
- **Blocked items**: Real timestamp-clean news archive is missing; GDELT is under HTTP 429 cooldown; current evidence is under-sampled/underpowered; Q4 2024 is not complete; IBKR options permission and real-money approval remain blocked.
- **Decision points**: Continue into 2025 OOS or add 2022-2023 depth after Q4 checkpoint; add reference/pre-break data for structural-break testing; revise strategy frequency if trade density stays too low; switch or pay for a news provider if GDELT remains blocked; define capital-size experiment if Sub-System B is feasible in research but not in a $1,000 account.
- **Risk checkpoints**: Before paid data pulls, after every monthly batch, after Q4 completion, after core execution tests, before any LLM/news ablation, before final acceptance, and before paper/dry-run validation.
- **Archive policy**: Before replacing `IMPLEMENT_PLAN.md` again, tell the user that the current plan should be archived and ask for approval. Do not silently archive or replace it.
- **Research log policy**: After each completed experiment, write a Thai log using `RESEARCH_LOG_FORMAT.md`, save it under `research_log`, push it to `https://github.com/Tusgof/Yuehua_Research_log`, and run `python scripts\audit_research_logs.py`.
- **Verification loop**: After each milestone, run operating checks from `PROJECT_BRAIN.md`, including `python -m unittest discover -s tests`; for scaffold-impacting changes also run `python scripts\run_fixture_pipeline.py` and relevant readiness audits.
