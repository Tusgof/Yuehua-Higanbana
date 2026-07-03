# IMPLEMENT_PLAN.md

## Overview
- **Start state**: The project scaffold is already built: schemas, fixture pipeline, Databento cost/download tooling, normalized SPY/0DTE data flow, macro/VIX coverage, dry-run operational guards, and Exp07 redesign/audit guards exist. The current real strategy evidence is still insufficient: Mar-Dec 2023 in-sample plus Jan-Jun 2024 OOS contains 11,593,672 option quote rows, 166,287 SPY bar rows, 71 candidate days, and 68 closed trades versus the N >= 500 target. Real timestamp-clean news cases are not captured yet, GDELT retries are under HTTP 429 cooldown, and IBKR/order transmission remains blocked.
- **End state**: The project has enough real SPY 0DTE bid/ask evidence to run or explicitly defer the planned experiments, starting from Exp01; each completed experiment has a Thai report and Yuehua research log; Exp07 tests prompt-template families only on real timestamp-clean news; the final research acceptance gate clearly says pass/fail/inconclusive; and operational validation remains separated from real-money launch until research, permission, capital, and user-approval gates pass.
- **Total milestones**: 7
- **Estimated total effort**: XL

---

## Gap Analysis
- The old scaffold roadmap is no longer the right active plan because its core implementation tasks are already complete.
- The main unresolved research gap is sample size: 68 closed trades is far below the baseline N >= 500 requirement.
- The current strategy evidence cannot support final conclusions or live readiness yet.
- OOS data that has already been viewed must not be used for tuning.
- Exp01 and other deterministic baseline experiments should be handled before Exp07 so the LLM layer is measured against a real non-LLM baseline.
- Exp07 needs real timestamp-clean news cases; synthetic/policy fixtures are infrastructure evidence only.
- GDELT is blocked by HTTP 429 cooldown, so live news retries must be controlled one day at a time after cooldown.
- Any completed experiment must produce a Thai research log under `research_log` and pass push-state audit for `https://github.com/Tusgof/Yuehua_Research_log`.
- IBKR execution and real-money launch remain out of scope until research acceptance and external gates pass.

## Dependency Map
- Milestone 1 sets the active research baseline and freezes the next experiment order.
- Milestone 2 expands real SPY 0DTE data and is required before high-confidence experiment conclusions.
- Milestone 3 prepares the real-data experiment runner/report path so Exp01 outputs are not mixed with fixture evidence.
- Milestone 4 runs deterministic non-LLM experiments in order, starting from Exp01.
- Milestone 5 builds the real news archive required for Exp07.
- Milestone 6 runs Exp07 prompt-template and ablation research only after Milestones 4 and 5 provide prerequisites.
- Milestone 7 consolidates conclusions and validates operational readiness without enabling real-money order transmission.

---

## Milestone 1: Research Baseline And Experiment Order
**Goal**: Turn the current project state into a clean research starting point, with Exp01-first ordering and known blockers visible.
**Dependencies**: none

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 1.1 | Regenerate the current readiness snapshot from existing artifacts only | S | ✅ | `python scripts\audit_strategy_data_readiness.py`, `python scripts\audit_research_readiness.py`, and `python scripts\audit_paid_costs.py` produce current reports without live API calls |
| 1.2 | Create an experiment-order map from `backtest_experiments_plan.md` and `experiments\experiment_manifests.json`, explicitly placing Exp01 first | M | ✅ | Generated order document/report lists every experiment, prerequisite data, blockers, and reason for any deferral |
| 1.3 | Mark synthetic Exp07 prompt matrices as infrastructure-only evidence in the active research order | S | ⚠️ | Exp07 order entry requires real news cases and cannot be selected as a completed research experiment |
| 1.4 | Confirm no current task requires IBKR credentials, order transmission, non-SPY symbols, or a new paid provider | S | ⚠️ | Readiness report contains no unauthorized scope expansion |

**Milestone complete when**: The active research order is documented, Exp01 is the first runnable experiment path, and current blockers are reproducible from local audits.

---

## Milestone 2: Real SPY 0DTE Data Expansion
**Goal**: Increase real bid/ask strategy evidence toward the N >= 500 minimum while preserving split discipline and cost controls.
**Dependencies**: Milestone 1

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 2.1 | Run paid-cost guard before every new Databento estimate/download | S | ⚠️ | `python scripts\audit_paid_costs.py` reports `pass`, uses user-reported actual cost `$49.37`, and remains below the `$125` stop threshold |
| 2.2 | Continue monthly OOS data acquisition after Jun 2024, beginning with Jul 2024 | L | ⚠️ | Each month has live cost reports, download result JSON, raw cache files, normalized option quotes, normalized SPY bars, adapter summary, and PnL summary |
| 2.3 | Add earlier in-sample/reference months only when needed for N >= 500 or structural-break analysis | L | ⚠️ | New artifacts are tagged by split and do not overwrite or retune against viewed OOS data |
| 2.4 | Update readiness inputs and tests after each completed data month | M | ✅ | `audit_strategy_data_readiness.py` totals match artifacts and targeted tests cover the new month |
| 2.5 | Stop and report if cost, data quality, provider scope, or symbol scope violates guardrails | S | ⚠️ | Blocker is recorded in paid-cost/readiness audit before any further paid pull |

**Milestone complete when**: Strategy-data readiness reaches N >= 500 closed trades, or the remaining gap is explicitly documented with cost/data blockers and a user decision point.

---

## Milestone 3: Real-Data Experiment Runner And Report Readiness
**Goal**: Ensure completed experiments are generated from real Databento artifacts, not fixture-only reports.
**Dependencies**: Milestone 2 can begin first; this milestone can proceed when enough data exists for a meaningful Exp01 run

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 3.1 | Separate fixture reports from real experiment outputs in paths and metadata | M | ⚠️ | Real experiment artifacts include data source, coverage window, split, trade count, and raw/normalized provenance |
| 3.2 | Verify Exp01 can consume current real-data summaries and trade logs without OOS tuning | M | ⚠️ | Dry-run or validation command shows train/OOS split policy and parameter source before report generation |
| 3.3 | Confirm required metrics are available for real reports | M | ✅ | Metrics output includes cashflow, equity, drawdown, Sharpe, Sortino, MDD, ES95/ES99, worst-day loss, win rate, payoff ratio, trade count, cost drag, and benchmark comparison |
| 3.4 | Validate Thai report and research-log workflow on a non-completed dry-run artifact | S | ✅ | Report generator and `audit_research_logs.py` can distinguish draft/incomplete work from completed experiments |

**Milestone complete when**: Exp01 can be run on real data with correct provenance, metrics, split metadata, and report/log boundaries.

---

## Milestone 4: Ordered Non-LLM Strategy Experiments
**Goal**: Establish deterministic strategy baselines before testing whether news/LLM adds value.
**Dependencies**: Milestone 3

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 4.1 | Run Exp01 on real data without LLM/news gating | L | ⚠️ | Exp01 report has required metrics, benchmark comparison, trade count, conclusion, failure conditions, and no fixture-only evidence |
| 4.2 | Write and push the Thai Exp01 research log if Exp01 is complete | M | ✅ | `python scripts\audit_research_logs.py` passes and the Yuehua Research Log remote is up to date |
| 4.3 | Continue Exp02 onward only after Exp01 has a conclusion or explicit deferral | XL | ⚠️ | Each experiment has a report, conclusion (`ผ่าน` / `ไม่ผ่าน` / `ยังสรุปไม่ได้`), artifacts, and research log when complete |
| 4.4 | Preserve OOS discipline across all deterministic experiments | M | ⚠️ | Split-enforcement tests and experiment metadata show no OOS-derived parameter changes |
| 4.5 | Explicitly document failed or inconclusive hypotheses before revising them | M | ✅ | Report includes diagnosis, revised hypothesis, and new success criteria where required |

**Milestone complete when**: All non-LLM experiments that can run without real news are completed, failed, or explicitly deferred with evidence.

---

## Milestone 5: Real News Archive For Exp07
**Goal**: Collect timestamp-clean real news cases so Exp07 tests prompt behavior against real events.
**Dependencies**: Milestone 1; should run in parallel with Milestones 2-4 only when GDELT cooldown clears

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 5.1 | Monitor the no-network GDELT capture command plan while retry pressure is `cooldown_recommended` | S | ⚠️ | `python scripts\plan_gdelt_news_capture_commands.py` reports retry status and next unattempted date |
| 5.2 | Retry one candidate day at a time after cooldown clears | M | ⚠️ | Capture status file records success or structured failure; no uncontrolled retry loop occurs |
| 5.3 | Import successful GDELT CSV captures into canonical news records | M | ⚠️ | Import output includes source, URL/headline when available, published/fetched timestamps, decision time, raw provenance, and registry evidence |
| 5.4 | Validate Exp07 real-news case coverage and prompt-family readiness | M | ⚠️ | `python scripts\validate_exp07_real_news_case_plan.py` passes and rejects synthetic cases as research input |
| 5.5 | Escalate a news-source decision if GDELT remains unusable | M | ⚠️ | A source-decision note identifies alternatives, cost, limitations, and requires user approval for any new paid provider |

**Milestone complete when**: Exp07 has enough real timestamp-clean news cases to test prompt-template families, or the news-source blocker is formally escalated.

---

## Milestone 6: Exp07 Prompt-Template And LLM Ablation Research
**Goal**: Test whether LLM/news improves decisions beyond deterministic baselines, using real news only.
**Dependencies**: Milestones 4 and 5

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 6.1 | Finalize Exp07 independent variables around prompt-template families and role definitions | M | ⚠️ | Exp07 design names prompt families, controls, dependent metrics, false-block/false-allow criteria, and expected failure modes |
| 6.2 | Run a tiny guarded DeepSeek/OpenRouter smoke to verify parser and cost metadata | S | ⚠️ | Output records model id `deepseek/deepseek-v4-flash`, prompt variant, input hash, parse-valid decision, and provider cost metadata where available |
| 6.3 | Run prompt-family experiment on real timestamp-clean news cases | L | ⚠️ | Prompt report compares template families, stability, evidence use, false-block/false-allow behavior, latency, and cost |
| 6.4 | Run no-LLM versus LLM-gated strategy ablation only after prompt results are reviewed | L | ⚠️ | Ablation report compares trade count, skip rate, PnL, Sharpe, Sortino, MDD, ES95/ES99, worst-day loss, cost drag, and benchmark performance |
| 6.5 | Write and push the Thai Exp07 research log if Exp07 is complete | M | ✅ | `python scripts\audit_research_logs.py` passes and remote push state is clean |

**Milestone complete when**: Exp07 concludes `ผ่าน`, `ไม่ผ่าน`, or `ยังสรุปไม่ได้` from real-news prompt evidence and strategy ablation.

---

## Milestone 7: Final Acceptance And Operational Gate
**Goal**: Decide whether the researched system is accepted, rejected, or still inconclusive, then validate operations only if research justifies it.
**Dependencies**: Milestones 4 and 6

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 7.1 | Regenerate final research review from real experiment reports | M | ⚠️ | Final review cites real experiment artifacts and separates fixture/scaffold evidence from strategy evidence |
| 7.2 | Run final research acceptance gate | M | ⚠️ | Gate blocks unless N, OOS Sharpe, max drawdown, implementable PnL, tail metrics, post-2022 analysis, and benchmark comparison meet criteria |
| 7.3 | Document accepted, rejected, and inconclusive components | M | ✅ | Final review includes failure conditions, evidence that would overturn conclusions, and next hypotheses where needed |
| 7.4 | Validate paper/dry-run operations only if research acceptance justifies moving forward | M | ⚠️ | Tickets, kill switch, entry-limit-only behavior, buying-power checks, alerts, and 3:45 PM ET close workflow pass without live transmission |
| 7.5 | Keep real-money launch blocked until external gates pass | S | ⚠️ | Launch checklist records research pass, options permission, cash-account feasibility, user approval, and no stored secrets |

**Milestone complete when**: The project has a documented research decision and either remains blocked with exact reasons or proceeds only to safe operational validation without real-money transmission.

---

## Execution Notes
- **Blocked items**: N >= 500 real closed trades is not met; real timestamp-clean news archive is missing; GDELT retry pressure is `cooldown_recommended`; IBKR options permission/capital/live approval are not ready; real-money order transmission is blocked.
- **Decision points**: Whether to keep paying for Databento month-by-month under the `$125` cap; whether to add earlier/reference months after OOS expansion; whether to switch news source if GDELT remains blocked; whether each failed experiment gets a revised hypothesis or is abandoned.
- **Risk checkpoints**: After each paid data month, before Exp01 completion, before Exp07, after Exp07 ablation, and before any operational validation beyond dry-run.
- **Cost policy**: Continue already-scoped SPY-only Databento/OpenRouter work without per-run approval while cumulative actual/estimated cost stays below `$125`; current user-reported provider actual usage is `$49.37`.
- **Research log policy**: After each completed experiment, write a Thai log using `RESEARCH_LOG_FORMAT.md`, save under `research_log`, push to `https://github.com/Tusgof/Yuehua_Research_log`, and run `python scripts\audit_research_logs.py`.
- **Verification loop**: After each milestone, run the operating checks from `PROJECT_BRAIN.md`, including `python -m unittest discover -s tests`; for scaffold-impacting changes also run `python scripts\run_fixture_pipeline.py` and relevant readiness audits.
