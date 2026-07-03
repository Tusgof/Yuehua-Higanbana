# Experiment 7 Prompt Pre-Experiment

- Mode: `live_openrouter`
- Cases: 15
- Assessments: 45
- Parse valid rate: 100.00%
- Stable cases across prompts: 9 / 15
- Guarded stable cases across prompts: 15 / 15
- Expected-decision mismatches: 0
- Unknown-policy violations: 12
- Guarded unknown-policy violations: 0
- Input archive: `reports\experiments\exp07_prompt_v8_inputs.json`
- Assessment JSONL: `reports\experiments\exp07_prompt_v8_assessments.jsonl`

## Case Stability

| Case | Expected | Raw Decisions | Guarded Decisions | Raw Stable | Guarded Stable |
|:--|:--|:--|:--|:--|:--|
| `quiet_vix18_normal_term_structure` | `allow` | `allow` | `allow` | `True` | `True` |
| `very_quiet_vix13_no_news` | `allow` | `allow` | `allow` | `True` | `True` |
| `systemic_banking_panic_vix34` | `block` | `block` | `block` | `True` | `True` |
| `war_shock_futures_limit_vix42` | `block` | `block` | `block` | `True` | `True` |
| `high_vol_no_clear_news_vix27` | `unknown` | `block, unknown` | `unknown` | `False` | `True` |
| `major_fed_event_vix21` | `unknown` | `block, unknown` | `unknown` | `False` | `True` |
| `cpi_release_pending_vix22` | `unknown` | `unknown` | `unknown` | `True` | `True` |
| `jobs_report_pending_vix19` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
| `earnings_heavy_calendar_vix20` | `unknown` | `allow` | `unknown` | `True` | `True` |
| `pce_inflation_pending_vix18` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
| `high_vol_no_news_vix26` | `unknown` | `block, unknown` | `unknown` | `False` | `True` |
| `earnings_next_week_no_catalyst_vix16` | `allow` | `allow` | `allow` | `True` | `True` |
| `fed_remarks_yesterday_no_data_vix17` | `allow` | `allow` | `allow` | `True` | `True` |
| `regional_bank_halt_vix24` | `block` | `block` | `block` | `True` | `True` |
| `treasury_auction_pending_vix18` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
