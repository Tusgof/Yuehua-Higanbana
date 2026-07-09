# H-A2 Residual Adverse-Day Analysis Preregistration

## Purpose

This artifact pre-registers the next local-only H-A2 analysis before any new data purchase, IBKR data request, GDELT live retry, or LLM call.

The question is not whether exact 2022-10 ORB replay is already solved. It is not. The question is whether the current H-A2 proxy evidence has a coherent failure pattern that tells us whether to revise H-A2, park it, or keep exact replay as the next justified blocker.

## Hypothesis

If H-A2 is a real macro-conditioned ORB mechanism, residual losing days should cluster around explainable local features such as macro-event subtype, VIX/VXV state, weak opening followthrough, OOS regime, or adverse existing trade-outcome structure.

If losses remain broad and unexplained after these checks, H-A2 should be revised or parked before more exact-data work.

## Source Artifacts

- `experiments/h_a2_h_l1_post_proxy_decision.json`
- `reports/experiments/h_a2_proxy_first_robustness_summary.json`
- `reports/experiments/h_l1_macro_event_proxy_baseline_summary.json`
- `reports/baselines/subsystem_a_orb_baseline_summary.json`
- `data/normalized/spy_0dte/macro_event.jsonl`
- `data/normalized/spy_0dte/vix_vxv.jsonl`
- `data/normalized/spy_0dte/spy_bar.jsonl`

## Planned Tests

| Test | Question | Required Output |
|:--|:--|:--|
| `residual_loss_bucket_profile` | Are non-risk losing trade days concentrated in a smaller bucket? | Count, average PnL, win rate, cost drag, largest loss labels |
| `macro_only_loss_profile` | Are macro-only losing days explained by event type, weak proxy, or OOS regime? | Macro-only counts, loss counts, event/proxy/split context |
| `non_risk_failure_mode_check` | Does the clean/no-risk bucket still contain a repeated failure mode? | Shared loss features, missing local fields, revision candidate |
| `decision_rule_application` | Should H-A2 be revised, parked, or prioritized for exact replay? | Rule results, evidence tier, blockers, next safe action |

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

- Report sample count for every bucket.
- Use chronological split only.
- Do not tune on OOS.
- Report MinTRL/PSR blockers where trade or return series exist.
- Mark under-sampled and underpowered buckets honestly.
- Preserve a search log or DSR blocker if any best bucket is selected.
- Include big-day dependency context.
- Separate mid PnL from implementable PnL where option PnL exists.

## Decision Rules

### Revise H-A2 If

- Residual adverse days cluster around a clear local feature that can become a narrower falsifiable condition.
- The current macro/VIX risk label is too coarse and needs a more precise pre-registered condition.

### Park H-A2 If

- Residual adverse days are broad, unstable across chronological split, or dominated by unexplained OOS losses.
- No local feature improves the mechanism without OOS tuning.

### Prioritize Exact Replay If

- Residual losses are explainable enough that exact 2022-10 entry/exit replay remains the main remaining blocker.
- The analysis preserves the existing directionally coherent H-A2 evidence without adding fitted filters.

## Forbidden Claims

- Do not claim H-A2 edge is validated.
- Do not claim exact 2022-10 ORB entries or exits were tested.
- Do not claim E2 evidence.
- Do not treat deterministic macro/VIX evidence as LLM or real-news evidence.
- Do not approve paper trading, operational validation, or real-money trading.

## Future Outputs

- `reports/diagnostics/h_a2_residual_adverse_day_analysis.json`
- `reports/diagnostics/h_a2_residual_adverse_day_analysis.md`
- `reports/diagnostics/search_logs/h_a2_residual_adverse_day_analysis_search_log.jsonl`
- `research_log/026-higanbana-h-a2-residual-adverse-day-analysis.md` if the actual analysis completes as a real experiment result.
