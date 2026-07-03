# IMPLEMENT_PLAN.md

## Overview
- **Start state**: The project scaffold is complete through data contracts, fixture ingestion, strategy intent generation, fixture backtests, reporting, dry-run operational guards, Databento cost/download tooling, macro/VIX imports, and Exp07 redesign guards. Real strategy evidence is still not research-grade: Mar-Dec 2023 in-sample plus Jan-Jun 2024 OOS currently has 71 candidate days and 68 closed trades versus the N >= 500 target. Real timestamp-clean news cases are not captured yet, and GDELT live retries are under HTTP 429 cooldown.
- **End state**: The project has enough real SPY 0DTE bid/ask data to run the planned experiments in order, produces Thai research reports and Yuehua research logs for completed experiments, explicitly passes/fails/defers each hypothesis, validates whether LLM/news adds value beyond deterministic filters, and keeps IBKR/live order transmission blocked until research, permission, capital, and user-approval gates pass.
- **Total milestones**: 7
- **Estimated total effort**: XL

---

## Gap Analysis
- The old milestone plan mostly describes scaffold work that is already done; the active gap is real evidence, not framework creation.
- Strategy-data sample size is too small: 68 closed trades versus the minimum N >= 500 target.
- OOS results from Jan-Jun 2024 have already been seen, so they must remain evaluation evidence only and must not be used for parameter tuning.
- Exp07 must not proceed from synthetic/policy-fixture cases. The corrected research question requires real timestamp-clean news snapshots, prompt-template family comparison, and later no-LLM-vs-LLM strategy ablation.
- GDELT is the current free news path but is blocked by HTTP 429 cooldown; a retry/import loop exists but must be used one day at a time after cooldown.
- Completed experiments require Thai research logs under `research_log` and push verification to `https://github.com/Tusgof/Yuehua_Research_log`.
- IBKR/order-transmission work remains out of scope until research acceptance passes and external permission/capital gates are satisfied.

## Dependency Map
- Milestone 1 rebaselines the plan and keeps audits aligned.
- Milestone 2 expands real SPY 0DTE data coverage; it is required before trusting Exp01+ results.
- Milestone 3 runs non-LLM baseline experiments in order, starting from Exp01, after enough data exists.
- Milestone 4 builds the real-news archive required for Exp07.
- Milestone 5 runs Exp07 only after Milestones 3 and 4 provide baselines and real news cases.
- Milestone 6 consolidates research conclusions, logs, and acceptance gates.
- Milestone 7 remains operational only and cannot enable real-money transmission without research and user gates.

---

## Milestone 1: Rebaseline The Active Plan
**Goal**: Replace the completed scaffold roadmap with a current evidence-first execution plan.
**Dependencies**: none

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 1.1 | [DONE] Rewrite `IMPLEMENT_PLAN.md` around the current verified state instead of the old scaffold milestones | M | OK | Plan starts from the 68 closed-trade / 71 candidate-day state and includes no completed scaffold tasks as future work |
| 1.2 | Update `PROJECT_BRAIN.md` current state and next safe action to point at the rebaselined plan | S | OK | `PROJECT_BRAIN.md` no longer implies the old scaffold roadmap is the active execution plan |
| 1.3 | Run non-live verification after the plan update | S | OK | `python -m unittest discover -s tests`, `python scripts\run_fixture_pipeline.py`, and readiness audits complete or show expected blockers |

**Milestone complete when**: Active project docs agree that the next phase is real data expansion and ordered research experiments, not more scaffold construction.

---

## Milestone 2: Expand Real Strategy Data To Research-Usable Size
**Goal**: Build enough real SPY 0DTE bid/ask evidence to make baseline experiments meaningful.
**Dependencies**: Milestone 1

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 2.1 | Run `audit_paid_costs.py` before each new already-scoped paid Databento pull | S | RISK | Audit status is `pass`, scope is SPY-only, and cumulative actual/estimated cost remains below `$125` |
| 2.2 | Continue OOS Databento acquisition month by month after Jun 2024, starting with Jul 2024 | L | RISK | Each month has live cost reports, download results, normalized option quotes, normalized SPY bars, adapter summary, and PnL summary |
| 2.3 | Continue earlier in-sample/reference coverage only if needed for N >= 500 and structural-break analysis | L | RISK | Added data is tagged by split and does not overwrite existing OOS evidence |
| 2.4 | Update `audit_strategy_data_readiness.py` and related tests after each completed month | M | OK | Readiness audit totals match local artifacts and tests cover the new month |
| 2.5 | Stop expansion or request direction if cost reaches `$125`, provider changes, symbol scope changes, or data quality degrades | S | RISK | Paid-cost audit or data-readiness audit records the blocker explicitly |

**Milestone complete when**: Strategy-data readiness reaches at least N >= 500 closed trades, or the remaining gap is explicitly documented with cost/data blockers.

---

## Milestone 3: Run Ordered Non-LLM Strategy Experiments
**Goal**: Establish deterministic baseline evidence before any LLM/news layer is allowed to influence strategy conclusions.
**Dependencies**: Milestone 2

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 3.1 | Re-read `backtest_experiments_plan.md` and map the experiment order to current manifests, starting with Exp01 | S | OK | Experiment manifest/order report lists Exp01 first and flags unavailable prerequisites |
| 3.2 | Run Exp01 on real data with implementable bid/ask fills and no LLM/news gate | L | RISK | Exp01 report contains trade count, cashflow, equity, drawdown, Sharpe, Sortino, ES95/ES99, win rate, payoff ratio, cost drag, and benchmark comparison |
| 3.3 | Write and push the Thai research log for Exp01 if the experiment is complete | M | OK | `audit_research_logs.py` passes and Yuehua Research Log remote is up to date |
| 3.4 | Continue Exp02 onward only after each prior experiment has a conclusion or explicit deferral | XL | RISK | Each completed experiment has a report, conclusion, artifacts, and research log |
| 3.5 | Keep OOS tuning locked: any parameter changes must be based on in-sample/pre-registered logic only | M | RISK | Split-enforcement tests and experiment metadata show no OOS-derived tuning |

**Milestone complete when**: Non-LLM baseline experiments that do not require real news are completed, failed, or explicitly deferred with evidence.

---

## Milestone 4: Build Real News Archive For Exp07
**Goal**: Capture and import timestamp-clean real news cases before running prompt-template research.
**Dependencies**: Milestone 2; can overlap with Milestone 3 when GDELT cooldown clears

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 4.1 | Monitor the GDELT command plan without live calls while retry pressure is `cooldown_recommended` | S | RISK | `plan_gdelt_news_capture_commands.py` reports retry status and next unattempted date |
| 4.2 | Retry one candidate day at a time after cooldown clears, starting from the current next unattempted date | M | RISK | Capture status records success or structured HTTP/API blocker without uncontrolled retries |
| 4.3 | Import successful GDELT CSV captures through the offline importer | M | RISK | Canonical news JSONL records include source, timestamp, fetched_at, URL/title/body fields where available, and raw provenance |
| 4.4 | Validate Exp07 real-news case coverage against required fields, case groups, and prompt-template families | M | RISK | `validate_exp07_real_news_case_plan.py` passes without allowing synthetic research cases |
| 4.5 | If GDELT remains blocked, prepare a source-decision note before introducing any new paid news provider | M | RISK | User approval is recorded before any new paid provider or non-GDELT path is used |

**Milestone complete when**: Exp07 has enough real timestamp-clean candidate-day news cases to run a controlled prompt-family experiment, or the news-source blocker is explicitly escalated.

---

## Milestone 5: Run Exp07 LLM Prompt And Ablation Research
**Goal**: Test whether an LLM adds measurable value beyond deterministic strategy filters, using real news only.
**Dependencies**: Milestones 3 and 4

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 5.1 | Finalize the Exp07 research question, variable design, and prompt-template families from `docs\EXP07_PROMPT_REDESIGN.md` | M | RISK | Exp07 design states independent variables, dependent metrics, controls, and failure criteria |
| 5.2 | Run a tiny guarded DeepSeek/OpenRouter smoke only to confirm parsing and provider cost metadata | S | RISK | Output includes model id, prompt variant, input hash, parse-valid decision, and `openrouter_actual_cost_usd` where available |
| 5.3 | Run the prompt-family experiment on real timestamp-clean news cases | L | RISK | Prompt matrix report compares template families, false-block/false-allow behavior, stability, and cost |
| 5.4 | Run no-LLM vs LLM strategy ablation only after prompt-family results are reviewed | L | RISK | Ablation report shows baseline versus LLM-gated PnL, drawdown, tail metrics, trade count, and benchmark comparison |
| 5.5 | Write and push the Thai Exp07 research log only after Exp07 is complete | M | OK | `audit_research_logs.py` passes and remote push state is clean |

**Milestone complete when**: Exp07 concludes `ผ่าน`, `ไม่ผ่าน`, or `ยังสรุปไม่ได้` based on real news, prompt-family evidence, and strategy ablation.

---

## Milestone 6: Final Research Review And Acceptance Gate
**Goal**: Decide which strategy components are accepted, rejected, or still inconclusive before any operational launch path.
**Dependencies**: Milestones 3 and 5

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 6.1 | Regenerate the final research review from completed experiment reports | M | RISK | Final review cites experiment artifacts and does not use fixture-only evidence as real strategy proof |
| 6.2 | Run the research acceptance gate on real experiment outputs | M | RISK | Gate blocks unless OOS Sharpe, MDD, N, implementable PnL, tail metrics, and benchmark comparison satisfy criteria |
| 6.3 | Document failed/inconclusive hypotheses and next measurable hypotheses | M | OK | Final review includes diagnosis, revised hypothesis, and success criteria for each failed/inconclusive result |
| 6.4 | Verify every completed experiment has a Thai research log pushed to Yuehua Research Log | S | OK | `audit_research_logs.py` passes |

**Milestone complete when**: The project has a clear research decision: accepted for operational validation, rejected, or inconclusive with a next research plan.

---

## Milestone 7: Operational Validation Gate
**Goal**: Validate operations only after research justifies the path, while keeping real-money transmission blocked until all external gates pass.
**Dependencies**: Milestone 6

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| 7.1 | Recheck IBKR options permission and cash-account feasibility | S | RISK | Permission/capital status is documented without storing credentials |
| 7.2 | Run paper-trading or dry-run operational validation if research passes but live readiness is still blocked | M | RISK | Tickets, close workflow, alerts, and journals validate without claiming edge |
| 7.3 | Revalidate kill switch, entry-limit-only behavior, max risk, max position count, and 3:45 PM ET close workflow | M | RISK | Operational tests pass and no simulated/live order violates guardrails |
| 7.4 | Require explicit user approval before any real-money launch step | S | RISK | Launch checklist records user approval and all gates are true |

**Milestone complete when**: Operational readiness is validated, or real-money launch remains explicitly blocked with the exact missing gate.

---

## Execution Notes
- **Active next action**: Complete Milestone 1 by updating `PROJECT_BRAIN.md` to reference this rebaselined plan, then run non-live verification.
- **Blocked items**: Real news archive capture is blocked by GDELT HTTP 429 cooldown; IBKR order transmission is blocked by research acceptance, options permission, capital feasibility, and explicit user approval.
- **Decision points**: Whether to keep expanding Databento month by month after cost/readiness audits; whether to introduce a new news source if GDELT remains blocked; whether any failed experiment deserves a revised hypothesis.
- **Risk checkpoints**: After every paid data month, after Exp01, before Exp07, after Exp07, and before any operational validation beyond dry-run.
- **Cost policy**: Continue already-scoped SPY-only Databento/OpenRouter work without per-run approval while cumulative actual/estimated cost remains below `$125`; current user-reported provider actual usage is `$49.37`.
- **Research log policy**: After each completed experiment, write a Thai log using `RESEARCH_LOG_FORMAT.md`, save under `research_log`, push to `https://github.com/Tusgof/Yuehua_Research_log`, and run `audit_research_logs.py`.
- **Operating rule**: Re-read `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, and `AGENTS.md` before each milestone. Use `python -m unittest discover -s tests`, `python scripts\run_fixture_pipeline.py`, and relevant readiness audits after changes.
