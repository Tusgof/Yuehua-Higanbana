# H-A2 Breakeven-Aware Rule Preregistration

## Purpose

H-A2.61 pre-registers the next H-A2 step after `h_a2_mechanism_revision_audit`.

H-A2.60 showed a specific mechanism problem: both exact-replayed candidates were directionally correct at the SPY underlying level, but both option spreads still lost money after implementable costs because the forced-close price did not reach the long call strike.

The revised question is therefore not simply whether ORB predicts direction. The revised question is whether decision-time information can identify ORB debit vertical candidates whose expected movement is large enough to make the selected strike and cost structure plausible.

## Controlling Evidence

- `reports/diagnostics/h_a2_mechanism_revision_audit.json`
- `reports/diagnostics/h_a2_normal_control_exact_replay.json`
- `reports/diagnostics/h_a2_post_stress_normalization_control_exact_replay.json`
- `experiments/h_a2_post_two_exact_replay_decision.json`

## Revised Hypothesis

H-A2 should be treated as a breakeven-aware conditional continuation hypothesis.

The strategy needs more than correct direction. It needs the underlying to move far enough after entry for the selected vertical to approach or exceed the long strike and overcome debit, bid/ask spread, and per-leg fees before forced close.

## Lookahead Boundary

Post-entry magnitude is a target to explain, not a live input.

Allowed decision-time inputs include:

- opening range geometry available at `09:35 ET`
- entry-time SPY price
- nearest discrete strike mapping at entry
- entry mid debit and implementable debit
- entry bid/ask width or liquidity proxy
- macro/VIX/calendar labels available before entry

Forbidden live inputs include:

- future underlying close
- future post-entry followthrough to close
- forced-close option quote
- same-day realized PnL after entry
- any OOS-selected filter

## Next Diagnostic

Next safe action is H-A2.62:

`h_a2_breakeven_aware_rule_train_diagnostic`

This diagnostic must be local, no-paid, and train-only. It may define and compare candidate rule trials on training data, but it must not select a rule from OOS results.

Required outputs:

- decision-time feature list
- future/leakage exclusion list
- train-only candidate rule trial table
- complete search log
- cost-adjusted strike-reachability target definition
- mid PnL versus implementable PnL interpretation rules
- decision: park H-A2, preregister OOS evaluation of one locked rule, or write a targeted data/regime expansion plan

## Guardrails

This preregistration does not approve:

- paid data
- exact replay expansion
- IBKR request
- live LLM call
- GDELT retry
- OOS filter selection
- paper trading
- operational validation
- real-money trading
- E2 acceptance claim

## Completion Criteria

H-A2.61 is complete when:

- `experiments/h_a2_breakeven_aware_rule_preregistration.json` exists
- this document exists
- `scripts/validate_h_a2_breakeven_aware_rule_preregistration.py` passes
- tests pass
- readiness audit points the next H-A2 action to H-A2.62
