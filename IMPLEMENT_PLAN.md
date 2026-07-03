# IMPLEMENT_PLAN.md

## Overview
- **Start state**: Higanbana has a working SPY 0DTE research scaffold, Mar-Dec 2023 in-sample and Jan-Dec 2024 OOS option data, 90 Sub-System A closed trades, Sub-System B feasibility evidence, M4/M5 diagnostic reports, macro/VIX inputs, OPRA OI feasibility/enrichment probes, and one gamma aggregation diagnostic. All current strategy evidence is tier E1 diagnostic at best: under-sampled, underpowered, search-contaminated where applicable, and not deployable.
- **End state**: A hypothesis-led research system that can say which strategy hypotheses are falsified, parked, validated for operational paper/dry-run, or still blocked. Paper trading is allowed only after E2 research acceptance, or as an explicitly labeled E0 operational dry run with no edge claim. Real-money launch remains a separate blocked gate requiring IBKR permission, account feasibility, explicit user approval, kill switch, and final checklist pass.
- **Total tracks**: 7
- **Estimated total effort**: XL

---

## Current Locked Decisions
- Edge validation comes before paper trading.
- Experiment numbers are legacy identifiers, not execution order.
- User-reported Databento usage is now about `$105`; the current `$125` stop threshold leaves about `$20` until real top-up.
- Cap extension is allowed only by real payment on the existing Databento account. Multi-account signup-credit harvesting is prohibited.
- No broad calendar buying. Every data pull must serve a named hypothesis and a named field, regime, window, or falsification gap.
- No live LLM research calls until real timestamp-clean news cases exist.
- No current result may be treated above E1 diagnostic evidence.
- Every hypothesis/report conclusion must use the project labels `ผ่าน`, `ไม่ผ่าน`, or `ยังสรุปไม่ได้`, with evidence tier and blockers stated beside the conclusion.
- Next real experiment research log is `012-higanbana-...`.

---

## Track P-1: Cost-Basis Sync
**Goal**: Make paid-action decisions use the real cost guard before any new purchase.
**Dependencies**: none
**Status**: Complete for the current `$105` update.

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| P-1.1 | Update `reports\data_cost\user_reported_actual_usage.json` to actual usage about `$105` | S | RISK | `python scripts\audit_paid_costs.py` reports `cost_guard_used_usd=105.0` |
| P-1.2 | Add budget policy: cap extension by real payment on the existing Databento account only; prohibit multi-account credit harvesting | S | RISK | `reports\data_cost\paid_cost_audit.md` includes the Budget Policy section |
| P-1.3 | Keep conservative committed estimates as trace evidence, not the controlling guard while actual usage exists | S | OK | `paid_cost_audit.json` includes actual-usage and known-estimate reconciliation |

**Track complete when**: Paid-cost audit passes on actual-usage basis and reports about `$20` remaining under the current `$125` guard.

---

## Track P0: Registry, Evidence Tiers, And Audit Backbone
**Goal**: Move the project from experiment-number sequencing to hypothesis-led execution with machine-checkable evidence tiers and next actions.
**Dependencies**: Track P-1

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| P0.1 | Create `docs\HYPOTHESIS_REGISTRY.md` with H-A1, H-A2, H-B1, H-B2, H-G1, H-L1, and H-L2 seed entries | M | RISK | Complete: document exists and records rationale, predictions, validation/falsification criteria, required data, evidence links, decision logs, and the kill/resurrection rule |
| P0.2 | Create `experiments\hypothesis_registry.json` as the machine-readable registry | M | RISK | Complete: `python scripts\validate_hypothesis_registry.py` reports `status=pass`, `hypothesis_count=7` |
| P0.3 | Add `scripts\validate_hypothesis_registry.py` and tests | M | RISK | Complete: `python -m unittest tests.test_validate_hypothesis_registry` passes |
| P0.4 | Add evidence-tier policy and validator requiring `hypothesis_id`, `evidence_tier`, and `tier_blockers` for experiment summaries | L | RISK | Complete: `python scripts\validate_evidence_tiers.py` passes; tests reject unknown hypothesis IDs, missing metadata on acceptance claims, and acceptance claims below E2 |
| P0.5 | Fix stale `scripts\audit_research_readiness.py` next action after gamma diagnostic exists | M | RISK | Complete: `python -m unittest tests.test_audit_research_readiness` passes and readiness next action now points to H-G1/H-A2 targeted next steps instead of rerunning the completed gamma diagnostic |
| P0.6 | Add read-only `scripts\report_project_state.py` | M | OK | Complete: command reports hypothesis status, tier, blockers, next safe action, cost headroom, and news/GDELT status with no network calls or file writes |
| P0.7 | Wire registry/tier validators into `scripts\run_fixture_pipeline.py` | S | RISK | Complete: `python scripts\run_fixture_pipeline.py` passes and includes `validate_hypothesis_registry` plus `validate_evidence_tiers` |

**Track complete when**: Complete. One command can report current project state from the registry and audits, and no experiment artifact can silently claim acceptance-grade evidence without E2 fields.

---

## Track H-A2: Macro-Conditioned ORB Edge
**Goal**: Turn the best current diagnostic clue into a pre-registered, falsifiable hypothesis instead of continuing blind data buying.
**Dependencies**: Track P0
**Priority**: Highest edge track.

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| H-A2.1 | Register H-A1 as falsified-as-stated with a mechanism autopsy, and H-A2 as the new macro-conditioned hypothesis | M | RISK | Registry validator passes and H-A1/H-A2 decision logs are explicit |
| H-A2.2 | Re-analyze the existing M5.5 macro-filter result as H-A2 E1 evidence with inherited 9-trial search contamination and DSR blocker/adjustment | M | RISK | Complete: `reports\experiments\h_a2_macro_conditioned_reanalysis_summary.json` cites the 9 M5.5 trials, labels evidence `E1`, records DSR/sample/regime blockers, and does not claim E2 |
| H-A2.3 | Investigate why cached Aug 2024 VIX-spike windows produced zero high-VIX trades | M | RISK | Complete: `reports\diagnostics\h_a2_high_vix_silence_diagnostic_summary.json` shows complete VIX/market-data coverage and zero ORB candidates on high-VIX dates, so the gap is ORB silence rather than a labeling gap |
| H-A2.4 | If still justified, estimate 2022 H2 top 2-3 VIX months only, before any purchase | S | RISK | Complete: `reports\data_cost\h_a2_2022_h2_stress_purchase_estimate.json` ranks 2022-10 and 2022-09 as top2, estimates base cost `$16.923156` inside `$20` headroom, and marks top3 as requiring live cost or top-up |
| H-A2.5 | Buy 2022 H2 stress data only if the decision tree passes and headroom/top-up allows it | L | RISK | First run live Databento metadata cost check for top2 only; proceed to download only if `audit_paid_costs.py` still passes and live estimate keeps total below `$125` |
| H-A2.6 | Write research log `011-higanbana-...` only if a real experiment or formal deferred/falsification result completes | S | OK | Complete for H-A2.2: `research_log\011-higanbana-macro-conditioned-orb-reanalysis.md` was written and pushed; `python scripts\audit_research_logs.py` passes |

**Track complete when**: H-A2 is either falsified cheaply, remains active with a justified next data target, or earns a clean path toward E2 using untouched validation data.

---

## Track H-B2: Sub-System B At Realistic Scale
**Goal**: Decide whether the put-ratio-with-wing structure has merit at simulated `$10k`/`$25k` scale, without confusing this with tradability on the current `$1k` account.
**Dependencies**: Track P0

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| H-B2.1 | Register H-B1 as falsified for `$300` allocation / `$20` risk and H-B2 as simulated-scale structure test | S | RISK | Registry validator passes |
| H-B2.2 | Pre-register account sizes, wing grid, sizing rule, selection rule, and DSR/search-log handling | M | RISK | Experiment manifest includes fixed grid before run |
| H-B2.3 | Rerun Sub-System B feasibility using already-cached data only | L | RISK | Summary reports `$10k` and `$25k` results, implementable PnL, ES95, drawdown, cost drag, sample labels, and search log |
| H-B2.4 | Decide falsified/active/parked based on pre-registered criteria | S | RISK | Registry decision log updated with report link and tier |

**Track complete when**: The project knows whether Sub-System B is structurally worth keeping for larger capital research, independent of current small-account feasibility.

---

## Track H-G1: Gamma/OI Proxy Validity
**Goal**: Validate or kill the signed-OI gamma proxy as a data signal before any NOVI/net-gamma strategy claim.
**Dependencies**: Track P0 and existing OPRA OI/enrichment probes

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| H-G1.1 | Issue `docs\GAMMA_AGGREGATION_VALIDATION_POLICY.md` v2 before rerun | M | RISK | v1 fail remains preserved; v2 requires dual raw-row and bucket-weighted coverage reporting |
| H-G1.2 | Pre-register a 12-date regime set across low/normal/high volatility, macro/no-macro, trend, train, and OOS buckets | M | RISK | Date-set manifest validates before any OI purchase |
| H-G1.3 | Estimate and buy only the 12 OPRA statistics/OI days if cost guard passes | M | RISK | Estimated cost about `$4.30`; `audit_paid_costs.py` passes before and after |
| H-G1.4 | Rerun enrichment and gamma diagnostic under v2 | L | RISK | Report includes v1 fail record, v2 gates, timestamp discipline, stability, economic-sign relation, and blockers |
| H-G1.5 | Register result as active, falsified, or still blocked | S | RISK | Registry decision log updated; no strategy use unless H-G1 passes |

**Track complete when**: The gamma proxy either passes data-validity gates under v2, fails cleanly, or remains blocked with exact missing evidence.

---

## Track H-L1 / H-L2: LLM Measurement Design
**Goal**: Prepare clean LLM research without running live prompt experiments before real timestamp-clean news exists.
**Dependencies**: Track P0; real news archive for execution

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| L.1 | Create `docs\LLM_MEASUREMENT_EXPERIMENT_DESIGN.md` for H-L1 | M | RISK | Design covers prompt families, masking, repeated calls, stability metrics, contamination probe, cost/latency, and no Go/No-Go-only framing |
| L.2 | Create `docs\H_L2_PRICE_INPUT_DESIGN.md` as a separate dormant branch | M | RISK | Design enforces chronological price/quote inputs and separation from news/sentiment |
| L.3 | Add pointers from existing Exp07 docs to the new H-L1/H-L2 designs | S | OK | `rg` finds no active instruction to run live LLM research before timestamp-clean news |
| L.4 | Keep GDELT/new-news provider work blocked on source policy | S | RISK | `docs\M6_NEWS_SOURCE_DECISION_NOTE.md` remains the controlling source-decision note |

**Track complete when**: LLM research is designed and pre-registered, but no live LLM research run has occurred without real timestamp-clean news cases.

---

## Track News-Unblock
**Goal**: Unblock real timestamp-clean news cases without treating provider changes as automatic.
**Dependencies**: Track P0

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| N.1 | Preserve GDELT cooldown discipline after HTTP 429 pressure | S | OK | Command plan continues to record blocked/not-attempted/cooldown status |
| N.2 | Evaluate GDELT bulk raw-file path as a possible free archive route | M | RISK | Source-decision note compares bulk raw files with current GDELT API path before implementation |
| N.3 | Ask user before any new paid news provider or new access method capture | S | RISK | No new provider artifacts exist without explicit approval |

**Track complete when**: The project either has real timestamp-clean news cases or a documented blocker/source decision.

---

## Track Acceptance And Operations
**Goal**: Convert E2 evidence, if any, into operational validation without making real-money claims.
**Dependencies**: At least one strategy hypothesis reaches E2 or an E0 operational dry-run is explicitly chosen.

| # | Task | Effort | Risk | Verification |
|:--|:-----|:------:|:----:|:-------------|
| A.1 | Add `scripts\evaluate_research_acceptance.py` | L | RISK | Reads machine summaries and returns `approved_for_operational_validation`, `blocked`, or `scope_restricted` |
| A.2 | Require MinTRL/PSR/DSR, big-day survival, implementable PnL, regime coverage, and benchmark comparison for E2 | M | RISK | Acceptance tests reject current E1 artifacts |
| A.3 | If E2 exists, validate paper/dry-run tickets and operator workflow | L | RISK | Dry-run config has no live transmit and rejects entry market orders, undefined risk, missing forced close, and excessive buying power |
| A.4 | Keep real-money launch blocked | S | RISK | Launch checklist still requires research pass, IBKR permission, account feasibility, explicit approval, and kill switch |

**Track complete when**: Either a strategy hypothesis is approved for operational validation with scope restrictions, or the project remains blocked with exact missing research gates.

---

## Execution Notes
- **Active track**: H-A2 after P0 completion.
- **Immediate next safe action**: Continue H-A2 with H-A2.5 pre-download gate: run a live Databento metadata cost check for top2 only (`2022-10`, `2022-09`) before any download. Do not buy top3 unless the user tops up or live cost proves top3 remains under the current guard.
- **Blocked paid actions**: 2022 H2 stress data download requires live metadata estimate plus `audit_paid_costs.py` pass before and after. Any new provider still requires explicit user approval.
- **Current cost basis**: User-reported actual usage `$105.0`; stop threshold `$125`; current headroom `$20.0`.
- **Risk checkpoints**: Before every paid pull, after every validator/audit change, before H-A2 stress purchase, before H-G1 12-date OI purchase, before any LLM call, before acceptance, and before paper/dry-run.
- **Archive policy**: Before replacing this plan again, archive the current `IMPLEMENT_PLAN.md` under `Backup_IMPLEMENT_PLAN\` and state why.
- **Verification loop**: After each track-level implementation, run `python -m unittest discover -s tests`; for scaffold-impacting changes also run `python scripts\run_fixture_pipeline.py` and relevant readiness audits.
