# H-L2 LLM Price-Input Design

## Status
- **Date**: 2026-07-03
- **Hypothesis**: H-L2
- **Evidence tier**: E0 design artifact
- **Execution status**: Dormant design complete; no live LLM calls are allowed for this branch yet.
- **Relationship to H-L1**: Separate branch. H-L2 must not be mixed with news/sentiment prompts.

## Research Question
Can an LLM that sees only chronological price and option-quote context produce parseable, stable exit or hold assessments that improve over fixed TP/SL rules without using future information?

This branch tests dynamic decision assistance, not news interpretation. It must be evaluated against simple deterministic baselines before any strategy claim.

## Allowed Inputs
At each decision timestamp, the prompt may include only data observable at or before that timestamp:
- SPY OHLCV bars up to the decision time,
- option bid/ask/mid snapshots up to the decision time,
- current open position structure,
- entry price and timestamp,
- current unrealized mid PnL and implementable exit estimate,
- time remaining until forced close,
- pre-registered risk limits,
- VIX/macro fields only if already available to the baseline at the same timestamp.

Forbidden inputs:
- final day PnL,
- post-decision high/low/close,
- future option quotes,
- later stop/target outcome,
- labels derived from hindsight,
- H-L1 news/sentiment outputs.

## Candidate Decisions
The model may only emit advisory labels. It must not transmit orders.

Allowed labels:
- `hold`
- `tighten_exit`
- `exit_now`
- `unknown`

The execution simulator must translate these labels through pre-registered rules. For example, `exit_now` uses the same implementable exit model and forced-close discipline as the deterministic backtest.

## Baselines
H-L2 must be tested against simple rules:
- fixed TP/SL grid from existing exit-threshold experiments,
- forced-close-only baseline,
- time-based exit baseline,
- simple trailing mid-PnL rule if pre-registered.

No H-L2 result is useful unless it beats these baselines after implementable costs and search-log correction.

## Prompt Families

| Family | Purpose | Main risk |
|:--|:--|:--|
| `state_summary_json` | Summarize position state and emit one advisory label | May only restate PnL |
| `risk_first_exit_rubric` | Focus on survival, drawdown, and time-to-close | Over-exits profitable trades |
| `counterfactual_paths` | Compare benign/base/stress price paths from current state | Verbose and costly |
| `few_shot_price_only` | Use examples from training period only | Overfits known patterns |
| `self_consistency_price_panel` | Repeated calls to estimate dispersion | Higher cost and latency |

Prompt variants must be selected only on chronological training data. OOS cases must stay untouched until the prompt and parser are fixed.

## Output Schema
Each call must return strict JSON:
- `advisory_label`: one of `hold`, `tighten_exit`, `exit_now`, `unknown`
- `risk_score`: integer from 0 to 10
- `trend_score`: integer from -5 to 5
- `liquidity_score`: integer from 0 to 10
- `time_decay_pressure`: integer from 0 to 10
- `confidence_score`: integer from 0 to 10
- `evidence_fields_used`: list of input field names
- `uncertainty_reason`: string or null

Saved assessment metadata:
- `assessment_id`
- `trade_id`
- `decision_time_et`
- `model_id`
- `provider`
- `prompt_family`
- `prompt_version`
- `call_index`
- `input_hash`
- `output_hash`
- `parse_valid`
- `openrouter_reported_cost_usd` when available

## Validation Design
Chronological split:
- train/design: historical period used to create prompt variants,
- validation: later period used to select among pre-registered prompt families,
- OOS: untouched final period for diagnostic evaluation.

Required controls:
- no random K-fold,
- no same-day future aggregate features,
- no prompt examples from OOS,
- no post-decision labels in prompt,
- all scalers or thresholds fit only inside training windows,
- search log for every prompt family, threshold, and simulation rule.

Required metrics:
- parse-valid rate,
- repeated-call stability,
- trade count,
- implementable PnL,
- mid PnL as a control only,
- cost drag,
- drawdown,
- ES95 / ES99,
- big-day dependency,
- DSR or DSR blocker when multiple prompt/rule trials are compared,
- latency and provider cost.

## Acceptance, Falsification, And Parking Rules
H-L2 remains dormant if:
- H-L1 design is incomplete,
- chronological price/quote manifests are not pre-registered,
- cost guard is not available,
- parser and simulator plumbing do not exist.

H-L2 is parked or killed if:
- parse-valid rate is below the pre-registered threshold,
- chronological controls cannot be proven,
- implementable PnL improvement disappears after cost and DSR adjustment,
- latency makes the advisory unusable before the next decision point.

H-L2 can only become a strategy candidate after:
- deterministic baselines are reported,
- prompt selection is locked before OOS,
- OOS implementable metrics improve for a clear reason,
- operational checks prove the model cannot violate forced close, entry order rules, or user approval gates.

## Verification Commands
Design-only verification:

```powershell
python scripts\validate_hypothesis_registry.py
python scripts\validate_evidence_tiers.py
```

Future execution verification:

```powershell
python -m unittest discover -s tests
python scripts\run_fixture_pipeline.py
```

## Current Blockers
- No run script exists for H-L2.
- No pre-registered chronological price-input case manifest exists.
- No live LLM calls are approved for this branch.
- H-L2 must remain separate from H-L1 news/sentiment measurement.
