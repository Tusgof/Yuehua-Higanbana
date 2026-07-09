# Experiment 7 Prompt Redesign

## 2026-07-03 v2 Pointer

This document is superseded for active execution by:

- `docs\LLM_MEASUREMENT_EXPERIMENT_DESIGN.md` for H-L1 news/sentiment/impact measurement.
- `docs\H_L2_PRICE_INPUT_DESIGN.md` for the separate dormant price-input branch.

Exp07 remains historical context. Do not run live OpenRouter/DeepSeek prompt research from this document alone. Active execution must follow the H-L1/H-L2 design documents, the hypothesis registry, and the real timestamp-clean news blocker.

## Why The Old Direction Is Not Enough

The previous Exp07 prompt matrix tested whether an LLM could reproduce a hand-written event policy on synthetic cases. That is not the real research question.

If the expected answer is already encoded in a deterministic policy, adding more prompt rules only creates a slower and more fragile rule bot. It does not prove that the LLM adds information beyond VIX, macro calendar, and explicit rule filters.

The partial `exp07_prompt_v15_*` run is stopped and must not be used as an experiment result. It produced only two assessments before the run was interrupted, has no summary, no report, and no research log requirement.

## Correct Research Question

The LLM is useful only if it can read real pre-entry news context and identify qualitative risk that the quantitative filters miss.

The correct question is:

> Can an LLM classify real, timestamp-clean market news into trade-relevant risk states that improve tail-risk control without simply blocking too many normal days?

The target is not sentiment. The target is pre-entry risk interpretation for SPY 0DTE trading.

## Why Real News Is Required

Synthetic headlines are useful for parser tests and infrastructure smoke tests only. They are not sufficient for research because they do not include:

- Real ambiguity.
- Source credibility differences.
- Time ordering and stale-news problems.
- Multi-headline context conflicts.
- Market narrative drift through the morning.
- Events that were not anticipated by the policy writer.

An Exp07 research run requires archived real news snapshots with `published_at`, `fetched_at`, source, URL, and decision time. Any prompt experiment without real news must be labeled infrastructure-only.

## Intended LLM Role

The LLM should not decide trade edge. It should produce a risk interpretation layer that can be compared against a no-LLM baseline.

Allowed roles:

- News risk interpreter.
- Tail-risk scenario assessor.
- Context summarizer for real news snapshots.
- Uncertainty estimator when news is ambiguous or stale.

Disallowed roles:

- Price predictor.
- Strategy optimizer.
- Rule replacement for VIX or macro calendar filters.
- Final live-trade authority.

## Prompt Template Families To Test

The independent variable should be prompt template family, not another list of blocked keywords.

Initial families:

| Family | Purpose | Expected Failure Mode |
|:--|:--|:--|
| Role-only analyst | Test whether a simple expert role is enough | Overconfident and vague |
| Structured JSON classifier | Test parser stability and field discipline | Can become a rule checklist |
| Few-shot real-news examples | Test whether examples improve ambiguous classification | Overfits examples |
| Evidence-first rubric | Force each decision to cite concrete news evidence | May underweight latent risk |
| Scenario-branching prompt | Ask for benign/base/stress interpretations before decision | Higher cost and possible verbosity |
| Self-consistency ensemble | Run the same input multiple times or across variants and compare agreement | Higher cost and slower decisions |

The prompt must not expose hidden chain-of-thought in saved artifacts. Store concise rationale fields only.

## Dataset Design

Exp07 needs real event cases, split by time and event type.

Minimum case groups:

- Normal quiet days.
- Scheduled macro days.
- Large intraday move days.
- Volatility spike days.
- Geopolitical shock or war-risk days.
- Banking/liquidity stress days.
- Index/ETF/futures microstructure disruption days.
- False alarm days where scary language did not become trade-relevant.

Each case must use only information available before the strategy decision time. Later realized outcome can be used only for evaluation labels, not as prompt input.

## Metrics

Primary prompt metrics:

- Parse-valid rate.
- Costed assessment coverage.
- Decision stability across prompt families.
- False-allow rate on adverse risk days.
- False-block rate on normal days.
- Unknown/abstain rate.
- Rationale evidence quality.
- Sensitivity to stale or conflicting news.

Strategy metrics are a later ablation step:

- Change in ES99.
- Change in worst-day loss.
- Change in trade count.
- Change in Sharpe/Sortino.
- Cost drag from LLM calls.

## Correct Experiment Order

Exp07 must not be used before the no-LLM strategy baseline is meaningful.

Safe order:

1. Build real data coverage and validate implementable option PnL.
2. Run no-LLM quantitative baselines and execution-cost checks.
3. Build real timestamp-clean news case archive.
4. Run prompt-family pre-experiment on real news cases.
5. Only if prompt evidence is useful, run strategy ablation with and without the LLM risk layer.

This means the previous synthetic prompt matrices do not justify strategy integration.

## Acceptance Bar

A prompt family is only a candidate if:

- It uses real news snapshots.
- It is timestamp-clean.
- It has 100% parse-valid output.
- It reports provider cost for all live calls or clearly flags unpriced rows.
- It reduces false-allow risk on adverse cases without excessive false blocks.
- Its rationale cites concrete evidence from the input, not generic caution.
- It remains useful on holdout event types not used to design the prompt.

Passing this prompt bar still does not approve the LLM for strategy use. Strategy use requires a separate ablation against a no-LLM baseline.
