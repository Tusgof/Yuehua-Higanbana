# H-L1 LLM Measurement Experiment Design

## Status
- **Date**: 2026-07-03
- **Hypothesis**: H-L1
- **Evidence tier**: E0 design artifact
- **Execution status**: Design complete; live LLM research remains blocked until real timestamp-clean news cases exist.
- **Primary model target**: OpenRouter `deepseek/deepseek-v4-flash`
- **API key rule**: Read from user environment variable `HIGANBANA_OPENROUTER_API`; never store the key value in project files.

## Research Question
Can an LLM convert real pre-entry news context into stable, timestamp-clean, trade-relevant measurements that add information beyond deterministic VIX and macro-calendar baselines?

The target is not a production "Go / No-Go bot". The target is a measurement layer:
- sentiment direction,
- expected market impact,
- volatility relevance,
- tail-risk relevance,
- strategy suitability,
- uncertainty and abstention.

Strategy blocking or position sizing may only be tested later, after the measurement layer passes parser, stability, contamination, and incremental-information gates.

## Required Inputs
Every case must be built from real news records that were available before the strategy decision timestamp.

Required fields:
- `case_id`
- `decision_time_et`
- `published_at_et`
- `fetched_at_et`
- `source_name`
- `url`
- `headline`
- `summary_or_body`
- `provider`
- raw archive path
- deterministic baseline fields available at decision time:
  - VIX / VIX3M state,
  - macro calendar flags,
  - same-day strategy candidate flag,
  - SPY pre-entry price context where already allowed by the baseline design.

Forbidden prompt inputs:
- same-day realized PnL,
- post-decision SPY return,
- post-decision volatility,
- later article updates,
- post-event summaries,
- labels such as "crash day", "banking crisis", or known event names when those labels would reveal future outcomes.

## Case Set Design
The case set must be split chronologically. Do not random-shuffle cases.

Minimum case groups:
- quiet non-macro days,
- scheduled macro days,
- high realized intraday volatility days,
- large adverse ORB days,
- large favorable ORB days,
- high VIX or VIX spike days,
- geopolitical or systemic-risk news days,
- false-alarm scary-news days,
- stale-news or conflicting-news days.

Holdout event types must be preserved. A prompt family cannot be selected on every available event type and then claim generalization on the same cases.

## Independent Variables
H-L1 tests prompt behavior. The independent variables are prompt-design choices, not additional safety rules.

Prompt families:

| Family | Purpose | Main risk |
|:--|:--|:--|
| `role_only_market_analyst` | Test whether a concise expert role is enough | Vague confidence |
| `structured_json_classifier` | Test parser discipline and repeatable fields | Becomes a brittle checklist |
| `evidence_first_rubric` | Force claims to cite concrete input evidence | May under-react to latent risk |
| `few_shot_timestamp_clean` | Test whether examples improve ambiguous cases | Example overfit |
| `scenario_branching` | Ask for benign/base/stress interpretations before scoring | Higher cost and verbosity |
| `self_consistency_panel` | Repeat the same prompt/case to estimate dispersion | Higher cost |

Masking policies:

| Policy | What changes | Purpose |
|:--|:--|:--|
| `raw_entities` | Preserve original entities and dates | Baseline readability |
| `masked_unique_entities` | Replace unique company/person/event names with neutral tags | Reduce event memorization |
| `masked_dates_and_entities` | Replace dates and unique identifiers while preserving sequence timing | Stronger contamination control |

The experiment must compare prompt family and masking policy separately. Do not merge them into one untraceable "best prompt".

## Output Schema
Each LLM call must return strict JSON. Saved artifacts must not include hidden chain-of-thought.

Required output fields:
- `decision`: one of `allow`, `block`, `unknown`
- `sentiment_score`: integer from -5 to 5
- `market_impact_score`: integer from 0 to 10
- `volatility_relevance_score`: integer from 0 to 10
- `tail_risk_score`: integer from 0 to 10
- `strategy_suitability_score`: integer from 0 to 10
- `confidence_score`: integer from 0 to 10
- `evidence`: list of short evidence snippets from the input
- `uncertainty_reason`: string or null
- `stale_or_conflicting_news`: boolean

Every saved assessment row must include:
- `assessment_id`
- `case_id`
- `model_id`
- `provider`
- `prompt_family`
- `prompt_version`
- `masking_policy`
- `call_index`
- `created_at_utc`
- `input_hash`
- `output_hash`
- `parse_valid`
- `openrouter_reported_cost_usd` when available

## Stability Protocol
For each prompt-family and masking-policy pair:
- run 5 calls per case where cost allows,
- record dispersion for numeric scores,
- record decision agreement rate,
- record parse-valid rate,
- record `unknown` rate.

Minimum candidate thresholds before strategy ablation:
- parse-valid rate: 100% on the evaluation case set,
- decision agreement: at least 80% within repeated calls,
- no unexplained `block` or `allow` decisions,
- no hidden dependency on unmasked event identity.

If cost forces fewer than 5 calls, the report must label the result `under-sampled` for stability.

## Contamination Controls
Local wiki guidance treats historical LLM financial signals as contamination-prone. H-L1 must record:
- model id,
- provider,
- provider-reported training cutoff if available,
- document timestamps,
- retrieval/fetch window,
- masking policy,
- whether the model may have seen the historical event outcome.

Mandatory probes:
- compare raw-entity versus masked-entity outputs,
- compare masked-date outputs where feasible,
- flag cases where the model refers to facts not present in the prompt,
- reject any prompt family that relies on memorized event labels rather than supplied evidence.

## Evaluation Metrics
Parser and call quality:
- parse-valid rate,
- schema-field completeness,
- cost per case,
- latency per call,
- failure/retry rate.

Measurement quality:
- repeated-call dispersion,
- decision agreement rate,
- `unknown` rate,
- rationale evidence quality,
- masked-vs-raw stability.

Incremental-information tests:
- association between LLM scores and same-day realized volatility,
- association between LLM scores and adverse tail days,
- comparison against VIX-only and macro-calendar-only baselines,
- logistic or rank-correlation diagnostics fit only on chronological training data.

Strategy metrics are not part of the first H-L1 prompt run. They belong to a later ablation after the measurement layer passes.

## Acceptance, Falsification, And Parking Rules
H-L1 remains blocked if:
- real timestamp-clean news cases are unavailable,
- case count is too small for even diagnostic stability,
- parse validity is below 100%,
- masking reveals likely event memorization,
- scores add no information beyond VIX and macro baselines.

H-L1 can move from `active_blocked` to `active_ready_for_e1_run` only when:
- a real timestamp-clean news archive exists,
- a chronological case manifest is pre-registered,
- cost estimate is inside the active guard,
- the run script can store prompt, input hash, output, model id, timestamp, parse result, and cost.

H-L1 can support strategy ablation only after an E1 measurement report shows stable, parse-valid, contamination-controlled scores. Strategy ablation still cannot claim E2 unless sample adequacy, MinTRL/PSR, and no-LLM baselines are satisfied.

## Verification Commands
Design-only verification:

```powershell
python scripts\validate_hypothesis_registry.py
python scripts\validate_evidence_tiers.py
python scripts\audit_research_readiness.py
```

Future execution verification:

```powershell
python scripts\audit_news_coverage.py
python scripts\audit_paid_costs.py
python -m unittest discover -s tests
```

## Current Blockers
- No real timestamp-clean news archive is available yet.
- GDELT per-day API capture is under HTTP 429 cooldown pressure.
- Live OpenRouter research calls are prohibited until the news blocker is removed.
