# Experiment 7 Prompt Pre-Experiment

- Mode: `live_openrouter`
- Cases: 9
- Assessments: 27
- Parse valid rate: 100.00%
- Stable cases across prompts: 5 / 9
- Expected-decision mismatches: 0
- Unknown-policy violations: 5
- Input archive: `reports\experiments\exp07_prompt_v6_inputs.json`
- Assessment JSONL: `reports\experiments\exp07_prompt_v6_assessments.jsonl`

## Case Stability

| Case | Expected | Decisions | Stable |
|:--|:--|:--|:--|
| `quiet_vix18_normal_term_structure` | `allow` | `allow` | `True` |
| `very_quiet_vix13_no_news` | `allow` | `allow` | `True` |
| `systemic_banking_panic_vix34` | `block` | `block` | `True` |
| `war_shock_futures_limit_vix42` | `block` | `block` | `True` |
| `high_vol_no_clear_news_vix27` | `unknown` | `unknown` | `True` |
| `major_fed_event_vix21` | `unknown` | `allow, unknown` | `False` |
| `cpi_release_pending_vix22` | `unknown` | `block, unknown` | `False` |
| `jobs_report_pending_vix19` | `unknown` | `allow, unknown` | `False` |
| `earnings_heavy_calendar_vix20` | `unknown` | `allow, unknown` | `False` |
