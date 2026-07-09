# H-A2 Revised Opening-Followthrough Condition Preregistration

## Purpose

This artifact pre-registers the revised H-A2 condition before any exact replay, paid data, IBKR request, GDELT live retry, LLM call, or paper-trading work.

H-A2.22 showed that the current clean/risk split is too coarse. Non-risk losing days are still common, and 30 of 40 non-risk losses have negative 5-minute followthrough. The next question is therefore not "buy more data immediately." The next question is whether H-A2 can be restated as a narrower, falsifiable opening-followthrough condition without tuning on OOS.

## Revised Hypothesis

If H-A2 is a real macro-conditioned ORB mechanism, a clean macro/VIX regime is necessary but not sufficient. The system should also require opening-followthrough confirmation after the first 5-minute opening range.

Opening-followthrough confirmation is only a mechanism candidate at this stage. It is not validated edge evidence.

## Source Artifacts

- `reports/diagnostics/h_a2_residual_adverse_day_analysis.json`
- `reports/diagnostics/h_a2_residual_adverse_day_analysis.md`
- `reports/diagnostics/search_logs/h_a2_residual_adverse_day_analysis_search_log.jsonl`
- `reports/experiments/h_a2_proxy_first_robustness_summary.json`
- `reports/experiments/h_l1_macro_event_proxy_baseline_summary.json`
- `D:/Fogust/Workspace/LLM Wiki/LLM Wiki/wiki/concepts/spy-zero-dte-opening-range-breakout.md`
- `D:/Fogust/Workspace/LLM Wiki/LLM Wiki/wiki/concepts/regime-filtering-for-zero-dte.md`
- `D:/Fogust/Workspace/LLM Wiki/LLM Wiki/wiki/concepts/backtest-validation-protocol.md`

## Candidate Condition Family

The future runner may test only pre-registered opening-followthrough checks:

| Candidate | Meaning |
|:--|:--|
| 5-minute agreement | 5-minute followthrough sign agrees with the ORB direction |
| 15-minute non-adverse confirmation | 15-minute followthrough is not adverse when 5-minute followthrough is weak |
| Train-only magnitude threshold | Followthrough magnitude exceeds a threshold selected only from in-sample data |
| Ambiguity skip | Skip days where 5-minute and 15-minute proxies conflict |

The final threshold must not be selected from OOS PnL.

## Planned Future Tests

| Test | Question | Required Output |
|:--|:--|:--|
| `train_only_threshold_lock` | Which threshold can be locked using in-sample data only? | Grid, train-only rule, trial count, search log, DSR policy |
| `chronological_oos_holdout_check` | Does the locked condition improve OOS without OOS tuning? | IS/OOS counts, OOS implementable PnL, loss rate, cost drag, sample labels |
| `residual_loss_reduction_check` | Does it reduce H-A2.22 residual non-risk losses? | Baseline vs revised loss count, skipped trades, remaining largest losses |
| `mechanism_consistency_check` | Is this ORB momentum logic rather than a fitted blacklist? | Rationale, failure modes, falsification rule, remaining blockers |

## Guardrails

- No network.
- No paid data.
- No new provider.
- No IBKR historical-data request.
- No GDELT live retry.
- No live LLM call.
- No paper trading approval.
- No operational validation approval.
- No real-money approval.

## Statistical Rules

- Use chronological split only.
- Fit thresholds only on in-sample data.
- Do not tune on OOS.
- Report trade count and split count after every condition.
- Report skipped-trade count.
- Report implementable PnL and cost drag if option PnL exists.
- Report MinTRL/PSR blockers where trade or return series exist.
- Mark under-sampled and underpowered buckets honestly.
- Preserve a search log and DSR policy for the threshold grid.
- Include big-day dependency context.

## Decision Rules

### Run Local Revised-Condition Test If

- This preregistration validates.
- The future runner can use existing local artifacts only.
- Train-only threshold selection can be separated from OOS evaluation.

### Park Revised Condition If

- No train-only threshold rule can be stated without OOS tuning.
- The condition mostly removes trades without preserving enough sample for inference.

### Prioritize Exact Replay If

- The revised condition improves residual-loss behavior in OOS without OOS tuning.
- The main remaining blocker becomes exact 2022-10 entry/exit replay rather than hypothesis wording.

## Forbidden Claims

- Do not claim H-A2 edge is validated.
- Do not claim E2 evidence.
- Do not claim exact 2022-10 ORB entries or exits were tested.
- Do not approve paper trading, operational validation, or real-money trading.

## Future Outputs

- `reports/experiments/h_a2_revised_opening_followthrough_condition_summary.json`
- `reports/experiments/h_a2_revised_opening_followthrough_condition_report.md`
- `reports/experiments/search_logs/h_a2_revised_opening_followthrough_condition_search_log.jsonl`
- `research_log/027-higanbana-h-a2-revised-opening-followthrough-condition.md` if the actual revised-condition experiment completes as a real experiment result.
