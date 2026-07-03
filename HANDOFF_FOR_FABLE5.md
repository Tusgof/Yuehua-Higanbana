# Higanbana Handoff For Fable 5

## Purpose
This document is for Fable 5 working through chat only. The project is being pushed to GitHub so Fable can inspect the repo without local CLI access. The goal of the Fable session is a major planning and research-foundation upgrade, not immediate experiment execution.

GitHub target:
`https://github.com/Tusgof/Yuehua-Higanbana`

Local project root:
`D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana`

## Read First
Use these as the authoritative project state:

1. `PROJECT_BRAIN.md`
2. `IMPLEMENT_PLAN.md`
3. `AGENTS.md`
4. `RESEARCH_LOG_FORMAT.md`

Do not duplicate those files in a new plan. Reference them and propose precise changes.

## User Intent
The user wants the project to become much more rigorous. The main correction is to stop treating experiment IDs as the plan and instead rebuild the roadmap around hypotheses, edge logic, falsification criteria, sample adequacy, regime coverage, and data reliability.

The user has repeatedly clarified:
- Find and validate edge before paper trading.
- Paper trading is operational validation, not edge validation.
- `N >= 500` is not a universal rule; required N should come from MinTRL / PSR / power analysis.
- Data expansion must cover market regimes, not just calendar time.
- LLM experiments should test prompt/template variables and measurable sentiment/impact/volatility judgments, not just pile safety rules into a bot.
- Historical LLM news tests must address training-data contamination.
- Sub-System A and Sub-System B both remain in scope.
- Gamma/OI gaps should trigger data-source/proxy research, not silent cancellation.

## Current State Summary
See `PROJECT_BRAIN.md section 9 Current Verified State` and `IMPLEMENT_PLAN.md Execution Notes` for the exact state.

Short version:
- M1 complete/maintained: research control.
- M2 complete for Q4 checkpoint; broad data acquisition paused.
- M3 complete: backtest/reporting hardening.
- M4 complete: baseline strategy evidence, mostly inconclusive or failed.
- M5 complete/deferred: deterministic experiments completed as diagnostic evidence; structural-break testing deferred because pre-break/reference SPY 0DTE option data is missing.
- M6 active but blocked: real LLM/news work cannot proceed until real timestamp-clean news cases exist. GDELT is blocked by HTTP 429/cooldown.
- M7 not reached.

Current real strategy evidence is still under-sampled/underpowered. Current Sub-System A evidence has 90 closed trades.

## Latest Important Artifact: Gamma Diagnostic
Recent Codex work added and verified:

- `scripts\run_gamma_aggregation_diagnostic.py`
- `tests\test_gamma_aggregation_diagnostic.py`
- `reports\diagnostics\gamma_aggregation_diagnostic_summary.json`

Result:
- 3,488 quote rows.
- 1,750 computed Greeks rows.
- 3,488 underlying joins.
- 3,488 exact-symbol OI joins.
- Timestamp discipline gate passes.
- Search-log gate passes because no threshold/best bucket was selected.
- Coverage gate fails: computed Greeks rate is `0.50172`, below the 70% policy threshold.
- Stability gate fails: only `2024-01-03` is available.
- Economic-sign gate is blocked: multiple dates are required for realized-volatility/PnL comparison.

Conclusion: gamma/OI proxy is diagnostic-only. Do not use it as a NOVI/net-gamma strategy filter.

Known stale follow-up:
- `scripts\audit_research_readiness.py` still says the next safe action is to run gamma diagnostic. That action is now stale because the diagnostic exists. It should be updated to recommend targeted regime/data expansion, gamma coverage improvement, or hypothesis revision.

## Files Worth Reviewing
Core control:
- `PROJECT_BRAIN.md`
- `IMPLEMENT_PLAN.md`
- `docs\RISK_FIRST_DATA_PLAN.md`
- `docs\GAMMA_AGGREGATION_VALIDATION_POLICY.md`
- `docs\M6_NEWS_SOURCE_DECISION_NOTE.md`
- `docs\EXP07_PROMPT_REDESIGN.md`
- `docs\DATA_COVERAGE_MATRIX.md`

Key reports:
- `reports\risk_first_data_audit.md`
- `reports\diagnostics\gamma_aggregation_diagnostic_summary.json`
- `reports\baselines\subsystem_a_orb_baseline_summary.json`
- `reports\baselines\subsystem_b_put_ratio_feasibility_summary.json`
- `reports\experiments\m5_regime_filter_sensitivity_summary.json`
- `reports\experiments\m5_structural_break_assessment_summary.json`
- `reports\research_readiness_audit.json`
- `reports\data_cost\paid_cost_audit.json`
- `reports\news_gdelt_capture_command_plan.json`

Research logs:
- The local `research_log\` folder is a separate nested Git repo / publication flow and is intentionally ignored by this Higanbana repo to avoid creating a broken submodule.
- Use `reports\research_log_audit.json`, `reports\research_log_audit.md`, and the experiment summaries to understand which logs exist.
- Current completed logs are numbered `001` through `010`; the next completed real experiment log should start with `011-higanbana-`.

Note: Raw/normalized market data is intentionally excluded from GitHub via `.gitignore` because it is large paid/provider data.

## What Fable 5 Should Improve
1. Build a hypothesis registry.
   - For each strategy family, state why the edge should exist.
   - Define what would validate it and what would falsify it.
   - Separate diagnostic evidence, validation-grade evidence, and deployment-grade evidence.

2. Rebuild the implementation plan around dependency and evidence quality.
   - Experiment numbers are identifiers only.
   - The plan should not imply that finishing M7 automatically means real-money ready.
   - Paper trading should appear only after research acceptance or as an explicitly limited operational dry run.

3. Create a sample and regime decision framework.
   - Use MinTRL / PSR / power analysis, not fixed N.
   - Define minimum regime coverage for volatility, macro-event, trend, major subperiod, and gamma/liquidity regimes where data supports it.
   - Define when to buy more data and when to revise the hypothesis instead.

4. Decide how to handle Sub-System A and B.
   - Sub-System A has weak OOS evidence but remains worth studying if the logical hypothesis is sharpened.
   - Sub-System B fails current account sizing but should be tested with larger simulated portfolio assumptions before being discarded.

5. Redesign LLM research.
   - Treat prompt template, role framing, evidence-first structure, few-shot examples, self-consistency, and masking policy as independent variables.
   - Near-term LLM outputs should be sentiment, market impact, volatility relevance, strategy suitability, and stability/dispersion over repeated calls.
   - Tail-risk blocking should be caveated because historical news may be contaminated by model training data.
   - Price-input dynamic entry/exit should be a separate hypothesis branch with chronological controls.

6. Create clearer audit automation requirements.
   - Update stale next-action detection.
   - Add a single current-state summary command if useful.
   - Ensure reports and audits cannot overstate diagnostic results as accepted edge.

## Suggested Skills
- `grill-me`: Use if the user needs to choose between edge priority, data-buy path, or LLM role.
- `llm-wiki-inspect`: Use to inspect the local LLM Wiki for MinTRL, PSR, DSR, backtest validation, and LLM contamination before rewriting methodology.
- `visual-plan`: Use if a visual dependency map would help explain the new research architecture.
- `handoff`: Use after Fable finishes the planning pass so Codex can resume implementation cleanly.

## Do Not Do
- Do not run live LLM prompt experiments until real timestamp-clean news cases exist.
- Do not buy broad calendar data just to increase N.
- Do not treat gamma proxy as a passed strategy filter.
- Do not write research logs for infrastructure/data diagnostics.
- Do not store API keys, credentials, or local environment values.
- Do not push raw/normalized `data/` artifacts to GitHub.

## Recommended Output From Fable 5
Produce a concise but rigorous improvement proposal:

- revised research architecture,
- revised milestone structure,
- data acquisition decision tree,
- hypothesis registry format,
- LLM prompt experiment design,
- acceptance gate for research-to-paper-trading,
- exact files that should be changed by Codex afterward.

If recommending a replacement `IMPLEMENT_PLAN.md`, remind the user to archive the current plan first according to project policy.
