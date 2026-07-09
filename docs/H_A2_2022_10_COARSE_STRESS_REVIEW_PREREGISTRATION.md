# H-A2 2022-10 Coarse Stress Review Preregistration

## Purpose

This artifact pre-registers the next H-A2 step after the data-resolution correction.

The project previously treated missing 2022 SPY 1-minute bars as if H-A2 itself were blocked. That was too narrow. The exact ORB rerun is blocked, but a lower-resolution stress/regime review can still answer whether October 2022 is worth preserving as a priority validation window.

## Research Question

Does the already-downloaded 2022-10 stress month contain enough macro, volatility, and 0DTE option-quote context to justify continuing H-A2 exact rerun work, even though exact ORB execution remains blocked by missing 2022 SPY 1-minute bars?

## Inputs

| Input | Path | Use |
|:--|:--|:--|
| Data-resolution rule | `docs\HYPOTHESIS_DATA_RESOLUTION_AUDIT.md` | Controls allowed and forbidden claims |
| 2022-10 option availability | `reports\data_cost\databento_normalization_summary_h_a2_2022_10_stress.json` | Counts 0DTE quote-available days |
| VIX/VXV | `data\normalized\spy_0dte\vix_vxv\vix_vxv.jsonl` | Labels high/stress volatility days |
| Macro calendar | `data\normalized\spy_0dte\macro_calendar\macro_event.jsonl` | Labels high-importance scheduled macro days |
| SPY bar blocker | `reports\data_cost\databento_spy_bars_plan_h_a2_2022_10_unavailable.json` | Preserves exact-backtest blocker |

## Method

The diagnostic will work at trading-day resolution only. It will not simulate ORB entries, exits, fills, or PnL.

Metrics to compute:

- trading-day count,
- 0DTE quote-available day count,
- 0DTE quote-missing day count,
- same-day high/stress VIX counts,
- prior-close high/stress VIX counts,
- high-importance macro-day counts,
- overlap between quote availability and VIX/macro regimes.

VIX thresholds:

- `high_vix`: VIX close >= 25.0
- `stress_vix`: VIX close >= 30.0

Same-day VIX close is diagnostic only. Prior-close VIX is the ex-ante proxy.

## Decision Rules

Continue exact-rerun research if:

- at least one 0DTE quote-available day overlaps with prior-close or same-day high/stress VIX, and
- at least one 0DTE quote-available day overlaps with high-importance macro events, or the month has enough non-macro stress days to challenge the H-A2 mechanism.

Deprioritize exact-rerun research if:

- 0DTE quote availability is too sparse to cover the stress/macro regimes, or
- the month contains no useful volatility or macro-regime contrast.

## Guardrails

This preregistration does not allow:

- paid data,
- network calls,
- IBKR historical-data requests,
- LLM calls,
- strategy PnL,
- paper trading,
- operational validation,
- real-money trading.

Allowed claim: October 2022 is or is not a useful coarse stress/regime window for prioritizing H-A2 follow-up.

Forbidden claim: H-A2 edge is validated.

## Verification

This preregistration is verified by:

```powershell
python scripts\validate_h_a2_2022_10_coarse_stress_preregistration.py
python -m unittest tests.test_validate_h_a2_2022_10_coarse_stress_preregistration
```
