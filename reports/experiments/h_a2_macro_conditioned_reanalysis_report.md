# H-A2 Macro-Conditioned ORB Re-Analysis

## Status
- Hypothesis: `H-A2`
- Evidence tier: `E1`
- Conclusion: ยังสรุปไม่ได้
- Reason: Existing M5.5 evidence supports H-A2 only as a diagnostic clue: excluding high-importance macro days improved current implementable PnL and OOS PnL, but the result inherits a 9-trial search, remains under-sampled/underpowered, and cannot be treated as E2 acceptance evidence.
- No new paid data: `True`

## Source Artifacts
- Source summary: `reports\experiments\m5_regime_filter_sensitivity_summary.json`
- Source search log: `reports\experiments\search_logs\m5_regime_filter_sensitivity_search_log.jsonl`

## Scenario Comparison
| Scenario | Closed trades | Total PnL | OOS PnL | Sharpe proxy | OOS Sharpe proxy | Cost drag | ES95 | Max drawdown |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| `baseline` | 90 | 545.6 | -78.44 | 0.118064 | 0.01581 | 543.9 | -59.56 | -0.370769 |
| `exclude_high_importance_macro_same_day` | 64 | 820.16 | 240.96 | 0.199493 | 0.133578 | 368.84 | -53.81 | -0.221838 |
| `exclude_major_macro_same_day` | 70 | 601.8 | 95.72 | 0.147296 | 0.06773 | 396.2 | -57.06 | -0.277636 |

## Delta Versus Baseline
| Scenario | Closed-trade delta | Total PnL delta | OOS PnL delta | Sharpe delta | OOS Sharpe delta |
|:--|--:|--:|--:|--:|--:|
| `exclude_high_importance_macro_same_day` | -26 | 274.56 | 319.4 | 0.081429 | 0.117768 |
| `exclude_major_macro_same_day` | -20 | 56.2 | 174.16 | 0.029232 | 0.05192 |

## Search Contamination And DSR
- Inherited trial count: 9
- All trials recorded: `True`
- DSR status: `blocked`
- DSR reason: The candidate macro filter was identified inside the M5.5 9-trial diagnostic grid. DSR cannot be used as acceptance evidence until a fresh/pre-registered return distribution, effective independent trial count, null Sharpe threshold, skew/kurtosis, and autocorrelation diagnostics exist.

## Tier Blockers
- `under-sampled`
- `underpowered`
- `inherited_9_trial_search_contamination`
- `dsr_blocked_until_acceptance_grade_return_distribution`
- `missing_reference_pre_break_coverage`
- `missing_high_vix_trade_coverage`

## Interpretation
- High-importance macro exclusion retained 64 closed trades and improved total implementable PnL versus the unfiltered control.
- The same scenario improved OOS implementable PnL from negative to positive on current cached data.
- The rule is ex-ante because scheduled macro event dates are known before entry.

## Why This Is Not Acceptance Evidence
- The rule was selected after inspecting a 9-trial grid.
- The retained sample has only 64 closed trades overall and 34 OOS closed trades.
- The source report labels all scenarios under-sampled and underpowered.
- Reference/pre-break coverage and high-VIX coverage remain missing.

## Next Actions
1. Run H-A2.3 to investigate whether the cached Aug 2024 high-VIX window has a labeling gap or genuine ORB silence.
2. Only after H-A2.3, decide whether estimating 2022 H2 top VIX months is justified.
3. Do not claim E2 or operational validation from this re-analysis.
