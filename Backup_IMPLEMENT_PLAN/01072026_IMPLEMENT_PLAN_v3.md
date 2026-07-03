# IMPLEMENT_PLAN.md

## Overview
- **Start state**: The project scaffold is complete: canonical contracts, fixture pipeline, Databento cost/download tooling, normalized SPY 0DTE option quotes and SPY bars, macro/VIX coverage, dry-run operational guards, OpenRouter/DeepSeek adapter smoke evidence, and Exp07 redesign guards exist. The current real strategy evidence is not enough for acceptance: Mar-Dec 2023 in-sample plus Jan-Jul 31 2024 OOS, Aug 1-30 2024 OOS chunks 1-5, and Sep 3-20 2024 OOS chunks 1-3 contains 13,931,013 option quote rows, 196,344 SPY bar rows, 82 candidate days, and 79 closed trades. Weekly Databento chunks are now treated as too slow for the evidence target unless used for recovery after a failed batch; the forward data policy is monthly batch acquisition with multi-month cost planning and explicit trade-density checkpoints. The old fixed N >= 500 language is now treated as a rough prior threshold only; final sample adequacy must use MinTRL/PSR/power diagnostics and label results as `under-sampled` or `underpowered` when required. Real timestamp-clean news cases are still missing, GDELT is under HTTP 429 cooldown, and IBKR/live order transmission remains blocked.
- **End state**: The project reaches **Operationally Ready** status: strategy research has run or explicitly deferred all required experiment families with Thai reports and Yuehua research logs; final conclusions use MinTRL/PSR/power-aware evidence labels; accepted components pass the research acceptance gate; and paper/dry-run operational validation proves order tickets, close workflow, alerts, logging, and operator workflow without treating paper trading as proof of edge. Real-money readiness remains a separate gated extension requiring options permission, capital feasibility, user approval, and launch checklist pass.
- **Total milestones**: 7
- **Estimated total effort**: XL

---

## Gap Analysis
- The old scaffold roadmap is complete enough; the remaining work is research evidence, experiment execution, statistical interpretation, and operational validation.
- Current strategy data is too small for strong conclusions under Sharpe inference; every report must include actual sample length versus MinTRL, PSR, power notes, and `under-sampled` / `underpowered` labels where applicable. The current observed rate of 79 closed trades from the available pilot window is a warning that blindly adding one week at a time may be operationally wasteful.
- Historical LLM news tests carry training-data-contamination risk. LLM prompt experiments must prefer point-in-time model checkpoints where possible, or use entity/date/event masking plus explicit training-cutoff and retrieval-window caveats.
- Parameter and filter sweeps can create multiple-testing overfitting. Experiments that select a best observed Sharpe must preserve search logs/trial counts and report DSR or a DSR blocker.
- Filter-heavy results can be dominated by small samples or a few extreme days. Reports must include active trade count after each filter, MinTRL/PSR, and a big-day dependency check.
- Option PnL must be reported as both `mid_pnl` and `implementable_pnl`; moneyness-grid tests must disclose nearest-strike rounding or interpolation before interpreting real-chain PnL.
- Experiment numbering in `backtest_experiments_plan.md` is only an identifier set. Execution order must follow dependencies, not numeric order.
- Data expansion must serve the experiment being tested: reference/pre-break, in-sample, and OOS should be filled as needed, while preserving no-OOS-tuning discipline. The default Databento unit is now a calendar month; multi-month or quarter-level estimates may be used for planning, but downloads should be normalized, registered, and audited month-by-month until tooling proves stable enough for larger atomic batches.
- Sub-System A and Sub-System B both remain in scope. If Sub-System B is too large for a $1,000 account, it becomes a capital-feasibility and paper-trading validation issue, not a reason to silently remove it.
- News/LLM research must not rely on synthetic or policy-fixture cases. LLM prompt-template experiments require real timestamp-clean news cases and a deterministic no-LLM baseline first.
- Paper trading is operational validation after research pass. It is not evidence of edge and does not make the system real-money ready.
- Future `IMPLEMENT_PLAN.md` replacement should be preceded by a user-visible archive recommendation and approval, not silent auto-archive.

## Dependency Map
- Milestone 1 defines the research control plane: experiment families, dependencies, evidence labels, and acceptance language.
- Milestone 2 expands and audits data according to experiment needs across reference, in-sample, and OOS windows.
- Milestone 3 runs core strategy and execution-feasibility experiments that do not depend on news/LLM.
- Milestone 4 runs regime, risk, portfolio, entry/exit, and structural-break experiments after enough data exists.
- Milestone 5 runs news and LLM experiments only after deterministic baselines and real news cases exist.
- Milestone 6 consolidates research reports, research logs, and final acceptance.
- Milestone 7 performs operational validation through paper/dry-run only after research acceptance.

---

## Milestone 1: Research Control Plane
**Goal**: Define the active experiment roadmap and evidence standards before more implementation or data pulls.
**Dependencies**: none
**Status**: Completed 2026-07-01. Control artifact: `docs\RESEARCH_CONTROL_PLANE.md`.

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 1.1 | Create an experiment-family map from `backtest_experiments_plan.md`, allowing reorder and rename by dependency | M | OK | Done in `docs\RESEARCH_CONTROL_PLANE.md`; all 10 experiment identifiers are mapped to dependency-based families |
| 1.2 | Add MinTRL/PSR/power reporting requirements to the research acceptance plan | M | RISK | Done in `docs\RESEARCH_CONTROL_PLANE.md`; acceptance-grade checklist requires sample length, MinTRL, PSR, power note, and `under-sampled` / `underpowered` labels |
| 1.3 | Define preliminary versus acceptance-grade report states | S | OK | Done in `docs\RESEARCH_CONTROL_PLANE.md`; report metadata states include `preliminary`, `under-sampled`, `underpowered`, `accepted`, `failed`, `inconclusive`, and `deferred` |
| 1.4 | Add the methodology guardrail checklist for LLM contamination, multiple testing, small samples, big-day dependency, mid-vs-implementable PnL, strike-grid mapping, and chronological splits | M | RISK | Done in `docs\RESEARCH_CONTROL_PLANE.md`; acceptance-grade checklist lists all required guardrail fields |
| 1.5 | Reconfirm hard boundaries: SPY only, no entry market orders, no OOS tuning, no random K-fold for time-series acceptance, no IBKR transmit, no stored secrets | S | RISK | Done in `PROJECT_BRAIN.md` and `docs\RESEARCH_CONTROL_PLANE.md`; readiness audit remains blocked only on expected research/data blockers |
| 1.6 | Record the future plan-replacement rule: recommend archive and request approval before replacing `IMPLEMENT_PLAN.md` | S | OK | Done in `PROJECT_BRAIN.md` decision log and `IMPLEMENT_PLAN.md` execution notes |

**Milestone complete when**: The project has a dependency-based experiment roadmap and statistical evidence standard that prevents Exp numbering, fixed-N shortcuts, or paper-trading confusion.

---

## Milestone 2: Data Coverage And Evidence Adequacy
**Goal**: Expand real data only where needed for the active experiment families, while tracking sample adequacy and cost.
**Dependencies**: Milestone 1
**Status**: Active. Tasks 2.1 and 2.2 completed 2026-07-01. Tasks 2.3 and 2.4 are in progress after adding Sep 2024 OOS chunk3 coverage through `2024-09-20`. The plan is now changed from weekly chunk continuation to monthly batch acquisition with trade-density checkpoints. Coverage artifact: `docs\DATA_COVERAGE_MATRIX.md`.

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 2.1 | Run paid-cost and readiness audits before each paid data action | S | RISK | Done for this session: `python scripts\audit_paid_costs.py` passed and reports `cost_guard_reconciliation`; actual-usage remaining is `$60.36`, conservative known-estimate remaining is `$-5.871886`, estimate-only total is `$7.150193`, and `python scripts\audit_strategy_data_readiness.py` reported current strategy evidence as blocked with 79 closed trades |
| 2.2 | Build a data-coverage matrix for reference, in-sample, and OOS windows by experiment family | M | RISK | Done in `docs\DATA_COVERAGE_MATRIX.md`; matrix shows required SPY bars, option quotes, VIX/VXV, macro, news, NOVI/proxy, and current coverage gaps |
| 2.3 | Replace weekly Databento chunks with monthly batch acquisition for post-2022 baseline coverage | L | RISK | In progress: Q4 completion dry-run planned 980 OPRA windows and projection from Sep chunk3 estimates option quotes at `$28.545538`; Q4 SPY bars exact live-cost plan estimates `$0.022813439369`. Exact option quote live cost for Sep remainder did not finish and produced no artifact, so the next action is to resolve exact batch cost estimation before any download |
| 2.4 | Add data-quality, sample-adequacy, and trade-density checkpoints after each monthly batch | M | RISK | In progress: readiness audit includes July partial, July chunks 3-5, Aug chunks 1-5, and Sep chunks 1-3, reports 79 closed trades, and writes `sample_adequacy` labels. After every 3 new calendar months or 50 new closed trades, project the trade count/cost needed for N >= 500 and stop blind acquisition if the path is impractical |
| 2.5 | Stop or escalate if cost, provider, symbol universe, data quality, or scope guardrails are violated | S | RISK | Active: `cost_guard_reconciliation` now separates actual-usage and conservative known-estimate bases. Cost-basis decision is resolved for already-scoped SPY-only work: user-reported actual provider usage is controlling when available; conservative known estimate remains trace/warning evidence |
| 2.6 | Decide whether to continue broad data acquisition or revise the research hypothesis after the first bulk checkpoint | M | RISK | Verification requires a written checkpoint in `docs\DATA_COVERAGE_MATRIX.md`: current trade density, added trades per dollar, projected years/cost to N >= 500, and whether to continue OOS 2025 expansion, add reference/pre-break coverage, or revise strategy/prompt/filter hypotheses before paying for more data. This decision cannot happen until Q4 data is actually downloaded, normalized, and audited |

**Milestone complete when**: The project has a documented, experiment-driven data matrix, a cost-aware monthly acquisition trail, and either enough real data to run the next experiment family with correct evidence labels or a documented decision that current trade density makes blind acquisition impractical.

---

## Milestone 3: Core Strategy And Execution Feasibility Experiments
**Goal**: Test the base strategy mechanics before adding regime, portfolio, or LLM layers.
**Dependencies**: Milestones 1-2

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 3.1 | Run the base no-LLM, no-news strategy baseline for Sub-System A and Sub-System B where data allows | L | RISK | Report includes mid PnL, implementable bid/ask PnL, benchmark comparison, trade logs, skipped trades, MinTRL/PSR labels, big-day dependency check, and conclusion |
| 3.2 | Test transaction cost and execution latency sensitivity before relying on any edge claim | L | RISK | Report quantifies mid PnL versus implementable PnL, half-spread/full-spread, per-leg fee assumptions, limit-retry assumptions, latency thresholds, friction drag, and negative-edge breakpoints |
| 3.3 | Test Sub-System B defined-risk feasibility and $1,000 account constraints | M | RISK | Report distinguishes research viability, paper-trading feasibility, buying-power constraints, and any needed portfolio-size experiment |
| 3.4 | Write Thai research logs for completed core experiments only | M | OK | `python scripts\audit_research_logs.py` passes and Yuehua Research Log remote is up to date |

**Milestone complete when**: The base strategy and execution assumptions have preliminary or acceptance-grade evidence, and no later experiment is using an untested execution model.

---

## Milestone 4: Regime, Risk, Portfolio, Entry, And Exit Experiments
**Goal**: Test the non-LLM strategy variables that determine whether the portfolio can survive and outperform.
**Dependencies**: Milestone 3

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 4.1 | Test Market-Maker Net Gamma / NOVI proxy activation versus baseline | L | RISK | Report compares Sharpe/PSR, drawdown, false-breakout behavior, Sub-System A win rate, and tail risk |
| 4.2 | Test VIX regime and macro-event filter sensitivity | L | RISK | Report compares VIX ranges, macro-event groups, pre/post-filter trade count, MinTRL/PSR labels, ES95/ES99, drawdown, benchmark-relative performance, and DSR if ranges were searched |
| 4.3 | Test portfolio construction and sizing choices, including risk parity versus equal weight | L | RISK | Report compares drawdown, Sortino, ES contribution, Sub-System A/B capital use, $1,000 account feasibility, and big-day dependency |
| 4.4 | Test strike-selection, entry-timing, and exit-rule sensitivity | XL | RISK | Report covers moneyness versus delta, nearest-strike rounding or interpolation policy, ORB/volatility entry times, target/stop rules, forced close, cost drag, search log/trial count, DSR, and OOS-tuning guard |
| 4.5 | Test structural-break behavior around daily 0DTE listing expansion | L | RISK | Report separates reference/pre-break, post-2022 in-sample, and OOS evidence with chronological split only and without tuning on viewed OOS |
| 4.6 | Write Thai research logs for each completed experiment family | M | OK | `audit_research_logs.py` passes after each completed report |

**Milestone complete when**: All non-news/LLM experiment families are completed, failed, or explicitly deferred with MinTRL-aware conclusions.

---

## Milestone 5: Real News And LLM Gate Research
**Goal**: Test whether LLM/news adds value beyond deterministic filters using real timestamp-clean news only.
**Dependencies**: Milestones 1, 3, and 4; GDELT or alternate news source availability

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 5.1 | Build or unblock the real news archive for candidate days | L | RISK | Imported news records include published_at, fetched_at, source, URL/headline/body where available, decision_time_et, and raw provenance |
| 5.2 | If GDELT remains blocked, prepare a source-decision note before any new paid provider | M | RISK | User approval is recorded before using a new paid news provider or changing source policy |
| 5.3 | Design prompt-template families as independent variables, not as accumulating safety rules | M | RISK | Prompt design lists role-only, structured JSON, few-shot, evidence-first, scenario-branching, and self-consistency style variants or approved alternatives, plus a masking/anonymization policy |
| 5.4 | Run guarded DeepSeek/OpenRouter prompt experiments on real news cases with contamination controls | L | RISK | Report compares parser validity, stability, false-block/false-allow, evidence grounding, latency, provider cost, model id, known/claimed training cutoff, retrieval window, masking policy, and contamination caveat |
| 5.5 | Run no-LLM versus LLM-gated strategy ablation only after prompt results are reviewed | L | RISK | Ablation report compares deterministic baseline versus LLM-gated outcomes using PnL, Sharpe/PSR, ES, drawdown, skipped trades, and cost |
| 5.6 | Write Thai research logs for completed LLM/news experiments | M | OK | `audit_research_logs.py` passes and remote push state is clean |

**Milestone complete when**: The LLM/news layer has a real-news conclusion: `ผ่าน`, `ไม่ผ่าน`, or `ยังสรุปไม่ได้`, with under-sampled/underpowered labels if evidence is insufficient.

---

## Milestone 6: Research Acceptance And Reporting
**Goal**: Convert experiment evidence into a final research decision without overstating weak samples.
**Dependencies**: Milestones 3-5

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 6.1 | Regenerate final research review from real experiment reports only | M | RISK | Final review separates fixture/scaffold evidence from real strategy evidence and cites all completed reports |
| 6.2 | Run the research acceptance gate with MinTRL/PSR/power-aware labels and search-aware Sharpe interpretation | M | RISK | Gate blocks or labels results when evidence is `under-sampled` or `underpowered`; reports DSR for searched best-Sharpe claims or blocks if search log/trial count is missing |
| 6.3 | Document accepted, failed, inconclusive, and deferred components | M | OK | Review includes hypothesis, evidence, conclusion, failure conditions, overturning evidence, diagnosis, and next hypotheses |
| 6.4 | Verify every acceptance-grade report includes applicable methodology guardrails | M | RISK | Final review confirms LLM contamination controls, chronological split, big-day dependency, mid-vs-implementable PnL, strike mapping, and DSR/search-log fields where applicable |
| 6.5 | Verify every completed experiment has a Thai research log pushed to Yuehua Research Log | S | OK | `python scripts\audit_research_logs.py` passes and remote matches expected repository |
| 6.6 | Decide whether research justifies moving to operational validation | S | RISK | Final gate explicitly says `approved_for_operational_validation`, `blocked`, or `inconclusive` |

**Milestone complete when**: The project has a clear research decision and a documented path either to operational validation or back to revised hypotheses.

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
- **Blocked items**: Real timestamp-clean news archive; GDELT HTTP 429 cooldown; insufficient MinTRL/PSR evidence for strong strategy acceptance; IBKR options permission; real-money launch approval.
- **Decision points**: Whether to adjust the Databento exact-cost estimator workflow after Sep remainder live estimate stalled without an artifact, whether the next bulk path should first complete OOS `2024-09-23` to `2024-12-31`, whether to continue into 2025 OOS after the first trade-density checkpoint, whether to add reference/pre-break data for structural-break analysis, whether to pause Databento acquisition and revise the strategy hypothesis if projected N >= 500 is impractical, whether to buy or switch news sources if GDELT remains blocked, whether Sub-System B requires a portfolio-size experiment, and whether each inconclusive result gets more data or a revised hypothesis.
- **Risk checkpoints**: Before paid data pulls, after each monthly data expansion, after each 3 calendar months or 50 newly closed trades, after core strategy/execution tests, before LLM/news ablation, before final acceptance, and before paper/dry-run validation. At each research checkpoint, verify contamination controls, chronological split, trial/search log, DSR need, MinTRL/PSR labels, big-day dependency, mid-vs-implementable PnL, and strike-mapping disclosure where applicable.
- **Archive policy**: Before replacing `IMPLEMENT_PLAN.md` again, tell the user that the current plan should be archived and ask for approval. Do not silently archive or replace it.
- **Data acquisition policy**: Do not continue one-week chunks as the default. Use monthly Databento batches for normal acquisition; use multi-month or quarter-level estimates for planning; normalize/register/audit month-by-month until larger atomic batches are proven reliable. Do not run parallel paid downloads against the same output path. SPY bars and option quotes may be planned together, but a failed component must be recoverable without corrupting the registry. Projection artifacts can support planning, but option quote downloads still need an accepted exact cost artifact or a recoverable estimator workflow before execution.
- **Trade-density policy**: After each 3 added calendar months or 50 newly closed trades, whichever comes first, calculate added closed trades, added cost, projected calendar years and projected cost needed to reach N >= 500. If the projection is impractical, stop blind acquisition and revise the strategy hypothesis, signal frequency, or experiment target before more paid pulls.
- **Cost policy**: Continue already-scoped SPY-only Databento/OpenRouter work without per-run approval while cumulative actual provider usage stays below `$125`; current user-reported provider actual usage is `$64.64`, with `$60.36` remaining on actual-usage basis. Known committed estimated cost is `$130.871886` and conservative known-estimate remaining is `$-5.871886`; keep this as trace/warning evidence through `cost_guard_reconciliation`. Stop if actual provider usage would reach `$125`, if no actual-usage basis exists and known committed estimate would reach `$125`, if the paid provider changes, if the symbol universe changes beyond SPY, or if the task would move into broker/order-transmission work.
- **Research log policy**: After each completed experiment, write a Thai log using `RESEARCH_LOG_FORMAT.md`, save under `research_log`, push to `https://github.com/Tusgof/Yuehua_Research_log`, and run `python scripts\audit_research_logs.py`.
- **Verification loop**: After each milestone, run operating checks from `PROJECT_BRAIN.md`, including `python -m unittest discover -s tests`; for scaffold-impacting changes also run `python scripts\run_fixture_pipeline.py` and relevant readiness audits.
