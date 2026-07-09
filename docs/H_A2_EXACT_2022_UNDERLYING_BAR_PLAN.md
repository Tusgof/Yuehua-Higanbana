# H-A2 Exact 2022 Underlying-Bar Plan

## Status

- **Date**: 2026-07-05
- **Track**: H-A2 Macro-Conditioned ORB Edge
- **Evidence tier**: E0 plan/control artifact
- **Decision**: build a bounded acquisition/import tool before any source execution.
- **Conclusion**: H-A2 still needs exact 2022-10 SPY 1-minute bars, but this plan does not request IBKR data, buy data, run strategy PnL, approve paper trading, or claim edge.

## Hypothesis First

H-A2 asks whether the SPY 0DTE ORB edge is conditional on macro/VIX risk state.

SPY 1-minute bars are not the hypothesis. They are required only for exact ORB timing, breakout ordering, stop/target path reconstruction, and timestamp-aligned option fills.

## Exact Inference Gap

The project already has 2022-10 0DTE option quotes and regime labels, but it cannot run the exact 2022-10 ORB stress rerun until SPY 1-minute underlying bars for the same window pass:

- provenance validation,
- regular-session coverage validation,
- timestamp conversion to ET,
- canonical import validation,
- join validation against the already-downloaded 2022-10 option quotes.

## Scope

| Field | Requirement |
|:--|:--|
| Symbol | `SPY` |
| Data type | underlying bars |
| Bar size | 1 minute |
| Window | `2022-10-03` through `2022-10-31` |
| Session | regular trading hours |
| Timezone | `America/New_York` after conversion |
| Required fields | timestamp, open, high, low, close, volume |
| Trading days | 21 |
| Quote-available exact-rerun days | 13 |

The 13 quote-available dates are the minimum exact-rerun target:

`2022-10-03`, `2022-10-05`, `2022-10-07`, `2022-10-10`, `2022-10-12`, `2022-10-14`, `2022-10-17`, `2022-10-19`, `2022-10-21`, `2022-10-24`, `2022-10-26`, `2022-10-28`, `2022-10-31`.

The full 21-day October window remains required for auditing no-trade days, quote-missing days, regime labels, and accidental survivorship/filtering effects.

## Execution Order

1. Rescan local normalized/raw roots for 2022-10 SPY 1-minute bars.
   - No network.
   - No paid data.
   - No broker interaction.

2. Build a bounded acquisition/import tool.
   - Must support dry-run and fixture mode.
   - Must write source manifests.
   - Must validate timestamp conversion and canonical `spy_bar` output.
   - Must not transmit orders.

3. Run IBKR data-only probe only if readiness passes.
   - Required gate: `reports/diagnostics/ibkr_spy_bars_readiness_probe_h_a2_2022_10.json` has `status == ready_for_manual_data_probe`.
   - Data-only historical-bars request only.
   - No order transmission.

4. If IBKR cannot be made available, stop and create a new source decision before any new provider or paid source.

## Validation Gates Before Exact Rerun

The exact H-A2 stress rerun is forbidden until all gates pass:

- provider/request provenance exists,
- raw hash or API request manifest exists,
- license notes exist,
- regular-session coverage audit passes,
- ORB timestamp coverage passes,
- timestamp conversion to ET passes,
- canonical import passes,
- join to existing 2022-10 option quotes passes,
- no-lookahead timestamp rule is checked.

## Forbidden

This plan does not allow:

- IBKR historical-bar requests before the bounded tool and readiness gate pass,
- 2022-09 option-data purchase,
- a new provider without explicit user approval,
- broker order transmission,
- exact H-A2 strategy rerun before validation gates pass,
- paper trading,
- operational validation,
- real-money trading,
- an H-A2 edge claim.

## Verification

```powershell
python scripts\validate_h_a2_exact_2022_underlying_bar_plan.py
python -m unittest tests.test_validate_h_a2_exact_2022_underlying_bar_plan
python scripts\audit_research_readiness.py
```
