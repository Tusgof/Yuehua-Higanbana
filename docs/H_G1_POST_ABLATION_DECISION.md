# H-G1 Post-Ablation Decision

## Decision
- **Hypothesis**: `H-G1`
- **Decision date**: 2026-07-04
- **Decision**: Park H-G1 pending a separate sample-expansion plan.
- **Next safe action**: Return to News-Unblock N.7.
- **Conclusion**: ยังสรุปไม่ได้
- **Evidence tier**: E1

## Why
H-G1.22 completed the pre-registered no-paid gamma strategy-ablation run, but the usable intersection was too small to support a strategy conclusion. Only 2 of 90 baseline closed trades intersected the available gamma-proxy date set, and all three gamma-filtered variants collapsed to 0 active trades.

This means H-G1 is not falsified as an economic idea, but it is not useful enough for strategy work from the current sample. More gamma work would first need a separate sample-expansion plan that estimates expected trade overlap, regime coverage, MinTRL/PSR requirements, and cost before buying or generating more evidence.

## Locked Restrictions
- Do not use H-G1 as a trading filter from H-G1.22.
- Do not approve paper trading from H-G1.22.
- Do not buy paid data from H-G1.22 alone.
- Do not claim true market-maker net gamma or dealer net gamma from signed-OI gamma proxy evidence.
- Do not add new gamma variants, change H-G1 dates, or tune OOS without a new pre-registration.

## Reopen Conditions
H-G1 may be reopened only if one of these conditions is met:

- A separate pre-registered sample-expansion plan estimates expected gamma-date/trade overlap before any paid data pull.
- The plan states which inference gap the new sample will answer and how MinTRL/PSR, regime coverage, and cost guard will be evaluated.
- The user explicitly approves any paid gamma-specific expansion if the projected cost exceeds the current guard or introduces a new provider.
- Future non-gamma work discovers additional timestamp-clean cached decision days that materially improve gamma overlap without new paid data.

## Resulting Path
Active implementation should move back to News-Unblock N.7. The priority is to create real timestamp-clean news cases before any live LLM research or further LLM strategy integration.
