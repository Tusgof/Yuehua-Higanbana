# H-A2 Mechanism Revision Audit

- Status: `complete`
- Evidence tier: `E1`
- Conclusion: `ยังสรุปไม่ได้`
- Decision: `preregister_train_only_revised_rule`

## Mechanism Autopsy

| Date | Direction | Entry | Close | Long strike | Mid PnL | Implementable PnL | Cost drag | Finding |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 2025-02-11 | call | 603.52 | 604.93 | 605.00 | -22.00 | -26.56 | 4.56 | direction_correct_but_option_spread_lost_value_before_forced_close |
| 2025-05-05 | call | 563.12 | 564.38 | 565.00 | -28.00 | -32.56 | 4.56 | direction_correct_but_option_spread_lost_value_before_forced_close |

## Interpretation

- Both candidates were directionally correct at the underlying level.
- Both candidates still had negative implementable PnL.
- In both cases, the forced-close underlying price remained below the long call strike.
- Total mid PnL: `-50.0`.
- Total implementable PnL: `-59.12`.
- Total cost drag versus mid: `9.12`.

## Next Safe Action

Pre-register H-A2.61 as a train-only revised rule focused on cost-adjusted post-entry magnitude, strike reachability, and implementable friction before any more paid data, exact replay expansion, threshold/filter change, E2 claim, paper trading, operational validation, or real-money work.

## Guardrails

- No paid data was used.
- No exact replay expansion was used.
- No threshold search or OOS filter selection was used.
- No paper trading, operational validation, real-money, or E2 claim is allowed.
