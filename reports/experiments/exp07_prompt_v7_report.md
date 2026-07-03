# Experiment 7 Prompt Pre-Experiment

- Mode: `live_openrouter`
- Cases: 9
- Assessments: 27
- Parse valid rate: 100.00%
- Stable cases across prompts: 5 / 9
- Guarded stable cases across prompts: 9 / 9
- Expected-decision mismatches: 0
- Unknown-policy violations: 5
- Guarded unknown-policy violations: 0
- Input archive: `reports\experiments\exp07_prompt_v7_inputs.json`
- Assessment JSONL: `reports\experiments\exp07_prompt_v7_assessments.jsonl`

## Case Stability

| Case | Expected | Raw Decisions | Guarded Decisions | Raw Stable | Guarded Stable |
|:--|:--|:--|:--|:--|:--|
| `quiet_vix18_normal_term_structure` | `allow` | `allow` | `allow` | `True` | `True` |
| `very_quiet_vix13_no_news` | `allow` | `allow` | `allow` | `True` | `True` |
| `systemic_banking_panic_vix34` | `block` | `block` | `block` | `True` | `True` |
| `war_shock_futures_limit_vix42` | `block` | `block` | `block` | `True` | `True` |
| `high_vol_no_clear_news_vix27` | `unknown` | `unknown` | `unknown` | `True` | `True` |
| `major_fed_event_vix21` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
| `cpi_release_pending_vix22` | `unknown` | `block, unknown` | `unknown` | `False` | `True` |
| `jobs_report_pending_vix19` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
| `earnings_heavy_calendar_vix20` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
