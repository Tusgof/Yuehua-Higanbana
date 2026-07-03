# Experiment 7 Acceptance Criteria

## Purpose

This document defines the acceptance gate for Experiment 7 prompt-matrix outputs before any LLM gate is considered for strategy integration.

The machine-readable source is `tests/fixtures/exp07_acceptance_criteria_v1.json`. The evaluator is `scripts/evaluate_exp07_acceptance.py`.

## Gate Levels

### Raw LLM Gate

Raw LLM decisions pass only when all of these are true:

- The summary is from live OpenRouter mode.
- Case count is at least 40.
- Assessment count equals case count times 3 prompt variants.
- Parse-valid rate is 100%.
- Raw expected-decision mismatches are 0.
- Raw unknown-policy violations are 0.
- Raw decisions are stable across all prompt variants for every case.

The current v12 result fails this gate because raw decisions are stable for only 35 of 43 cases and still have 13 unknown-policy violations.

### Guarded Policy Candidate

Guarded policy decisions pass the controlled prompt-matrix candidate gate only when all of these are true:

- The shared live matrix checks pass.
- Guarded expected-decision mismatches are 0.
- Guarded unknown-policy violations are 0.
- Guarded decisions are stable across all prompt variants for every case.

The current v12 result passes this controlled candidate gate: 43 of 43 guarded cases are stable, with 0 guarded mismatches and 0 guarded unknown-policy violations.

### Strategy Integration

Passing the guarded candidate gate is not enough to integrate the LLM gate into strategy research or live trading.

Strategy integration remains blocked until these items are satisfied:

- Real strategy backtest ablation comparing with and without the guarded LLM policy, not only the blocked readiness runner.
- Real news archive source, not only fixture headlines.
- Real macro calendar archive from official source snapshots, not only fixture rows. This is now satisfied by the 2022-2026 official-source canonical macro archive.
- Wider SPY 0DTE data coverage sufficient for research conclusions.

## Current v12 Evaluation

Artifacts:

- `reports/experiments/exp07_prompt_v12_summary.json`
- `reports/experiments/exp07_acceptance_evaluation.json`
- `reports/experiments/exp07_acceptance_evaluation.md`

Current statuses:

- Raw LLM gate: `fail`
- Guarded policy candidate: `pass`
- Strategy integration: `blocked`

## Commands

```powershell
python scripts\evaluate_exp07_acceptance.py
python -m unittest tests.test_evaluate_exp07_acceptance
```
