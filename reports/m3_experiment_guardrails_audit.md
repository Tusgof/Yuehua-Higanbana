# M3 Experiment Guardrails Audit

- Status: `pass`
- Blocker count: 0
- Warning count: 1
- Experiment count: 10
- Manifest: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\experiments\experiment_manifests.json`
- Guardrails: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\experiments\m3_experiment_guardrails.json`

## Experiments

| Experiment | Search log policy | Strike mapping | Split method | Blockers |
|:--|:--:|:--:|:--|:--|
| `exp01_net_gamma_filter` | True | True | `chronological` | None |
| `exp02_llm_gate` | True | True | `chronological` | None |
| `exp03_risk_parity` | True | True | `chronological` | None |
| `exp04_account_feasibility` | False | True | `chronological` | None |
| `exp05_structural_break_2022` | False | True | `chronological` | None |
| `exp06_vix_range` | True | True | `chronological` | None |
| `exp07_cost_latency` | True | True | `chronological` | None |
| `exp08_entry_timing` | True | True | `chronological` | None |
| `exp09_exit_thresholds` | True | True | `chronological` | None |
| `exp10_macro_filter` | True | True | `chronological` | None |

## Blockers

- None

## Warnings

- `exp05_structural_break_2022:search_like_metrics_without_required_search_policy`
