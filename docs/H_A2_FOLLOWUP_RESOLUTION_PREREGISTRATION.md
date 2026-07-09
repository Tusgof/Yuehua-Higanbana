# H-A2 Follow-Up Resolution Preregistration

## Purpose

This artifact locks the next H-A2 path after the 2022-10 coarse stress review.

H-A2.10 showed that October 2022 is useful enough as a stress/regime window to keep researching. It did not show that H-A2 has edge, and it did not prove that the next step must be another exact SPY 1-minute bar chase.

## Decision

The selected next path is:

`lower_resolution_proxy_first`

This means the next H-A2 work should pre-register a lower-resolution proxy test before any IBKR historical-bar request, new paid provider, or additional 2022 option-data purchase.

## Research Question

Before seeking another exact 2022 SPY bar source, can a lower-resolution proxy test weaken, falsify, or prioritize the H-A2 macro-conditioned ORB mechanism using already-available local data?

## Rationale

The local LLM Wiki supports this choice:

- The SPY 0DTE ORB source uses a 9:30-9:35 ET opening range and is a hypothesis generator until real option-chain validation exists.
- The backtest validation protocol requires timestamp-observable inputs, chronological splits, cost handling, big-day dependency checks, MinTRL/PSR/DSR where applicable, and clear evidence labels.
- Simulation or proxy evidence must not be mixed with historical option-chain backtest evidence.

So the next safe step is not "get 1-minute bars at any cost." The next safe step is to prove what question the data resolution is supposed to answer.

## Allowed Next Artifact

A separate H-A2 lower-resolution proxy-test preregistration may be drafted.

Allowed local inputs for that future preregistration:

- existing local SPY intraday bars from 2023-2024, possibly downsampled to 5-minute or 15-minute bars,
- existing option quote summaries and implementable PnL artifacts where already available,
- macro calendar labels,
- VIX/VXV labels,
- H-A2.10 2022-10 stress/regime overlap results.

Allowed claim:

- The H-A2 mechanism is weakened, falsified at proxy level, or prioritized for exact-data work.

Forbidden claims:

- exact 2022-10 ORB entries/exits were tested,
- deployable strategy edge exists,
- paper trading or operational validation is approved,
- proxy PnL is implementable exact ORB PnL unless exact quote/fill logic is used.

## Exact Source Chase Is Not Approved

An exact SPY bar source plan is blocked until:

- lower-resolution proxy work cannot weaken or prioritize H-A2,
- a new preregistration proves exact 2022-10 ORB timing is the minimum resolution required,
- local TWS/Gateway is listening if IBKR remains the chosen no-paid source,
- the user approves any new paid provider or paid source.

This artifact does not allow:

- IBKR historical-data requests,
- paid data,
- new providers,
- LLM calls,
- strategy PnL,
- paper trading,
- operational validation,
- real-money trading.

## Requirements For The Next H-A2 Preregistration

The next H-A2 preregistration must:

- state the hypothesis first,
- state the minimum data resolution,
- explain why 1-minute bars are or are not required,
- use chronological split only,
- forbid random split,
- track all trials for DSR,
- report MinTRL/PSR or explain why not applicable,
- report big-day dependency if strategy returns exist,
- separate mid and implementable PnL if option PnL exists,
- preserve `paper_trading_allowed=false`.

## Verification

```powershell
python scripts\validate_h_a2_followup_resolution_preregistration.py
python -m unittest tests.test_validate_h_a2_followup_resolution_preregistration
```
