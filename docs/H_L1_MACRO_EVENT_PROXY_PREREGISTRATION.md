# H-L1 Macro-Event Proxy Preregistration

## Purpose

This artifact pre-registers a deterministic macro-event and VIX/VXV baseline for H-L1 before waiting on GDELT again or running live LLM calls.

H-L1 asks whether LLM measurements from real pre-entry news add information beyond deterministic baselines. Since real timestamp-clean news cases are still blocked, the correct next step is to measure the deterministic baseline first.

This is not LLM evidence and not news evidence.

## Research Question

Do already-available timestamp-clean macro-calendar labels and VIX/VXV regimes explain adverse ORB or trade conditions enough to form a baseline that future LLM/news scores must beat?

## Baseline Definition

Macro labels:

- scheduled high-importance macro event day,
- scheduled FOMC event day,
- scheduled CPI event day,
- scheduled NFP event day,
- scheduled Fed Chair speech day,
- no scheduled high-importance macro event day.

Volatility labels:

- prior-close VIX low,
- prior-close VIX normal,
- prior-close VIX high or stress,
- VIX/VIX3M term-structure risk label where available.

Combined labels:

- `macro_event_only`,
- `vix_risk_only`,
- `macro_plus_vix_risk`,
- `no_macro_no_vix_risk`.

All labels must be observable before the strategy decision timestamp. Scheduled macro labels may use known calendar entries. VIX/VXV labels must use prior-close or otherwise pre-entry observable values.

## Planned Tests

1. `event_vs_no_event_outcome_split`
   - Compare scheduled macro-event days against no-event days.

2. `vix_regime_outcome_split`
   - Compare prior-close VIX/VXV regimes against adverse ORB or trade outcomes.

3. `combined_macro_vix_baseline`
   - Test whether combining macro and VIX labels creates a stronger future baseline.

4. `future_news_collection_value_check`
   - Decide whether better timestamp-clean news collection is still justified after deterministic baselines.

## Split And Statistical Policy

- Use chronological split only.
- Random split is forbidden.
- OOS tuning is forbidden.
- Report sample count for every bucket.
- Report MinTRL/PSR when a trade or return series exists.
- Mark `under-sampled` when N is below MinTRL.
- Mark `underpowered` when power is insufficient.
- Keep a search log and DSR blocker or adjustment if a best trial is reported.
- Run big-day dependency checks when strategy returns exist.
- Separate mid PnL from implementable PnL when option PnL exists.

## Allowed Claims

The future run may say:

- the deterministic macro/VIX baseline is useful or weak,
- future LLM/news scores must add information beyond this baseline,
- better timestamp-clean news collection is or is not justified at E1 proxy level.

## Forbidden Claims

This preregistration does not allow:

- claiming an LLM gate was tested,
- claiming real news sentiment was tested,
- claiming timestamp-clean news cases exist,
- OpenRouter or any live LLM call,
- GDELT live retry,
- paid news provider use,
- paper trading,
- operational validation,
- real-money trading,
- E2 acceptance-grade evidence.

## Verification

```powershell
python -m json.tool experiments\h_l1_macro_event_proxy_preregistration.json
```
