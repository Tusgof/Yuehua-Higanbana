# Experiment 7 Prompt Pre-Experiment

- Mode: `live_openrouter`
- Cases: 21
- Assessments: 63
- Parse valid rate: 100.00%
- Stable cases across prompts: 13 / 21
- Guarded stable cases across prompts: 21 / 21
- Expected-decision mismatches: 0
- Unknown-policy violations: 10
- Guarded unknown-policy violations: 0
- Input archive: `reports\experiments\exp07_prompt_v9_inputs.json`
- Assessment JSONL: `reports\experiments\exp07_prompt_v9_assessments.jsonl`

## Case Stability

| Case | Expected | Raw Decisions | Guarded Decisions | Raw Stable | Guarded Stable |
|:--|:--|:--|:--|:--|:--|
| `quiet_vix18_normal_term_structure` | `allow` | `allow` | `allow` | `True` | `True` |
| `very_quiet_vix13_no_news` | `allow` | `allow` | `allow` | `True` | `True` |
| `systemic_banking_panic_vix34` | `block` | `block` | `block` | `True` | `True` |
| `war_shock_futures_limit_vix42` | `block` | `block` | `block` | `True` | `True` |
| `high_vol_no_clear_news_vix27` | `unknown` | `allow, block, unknown` | `unknown` | `False` | `True` |
| `major_fed_event_vix21` | `unknown` | `block, unknown` | `unknown` | `False` | `True` |
| `cpi_release_pending_vix22` | `unknown` | `block, unknown` | `unknown` | `False` | `True` |
| `jobs_report_pending_vix19` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
| `earnings_heavy_calendar_vix20` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
| `pce_inflation_pending_vix18` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
| `high_vol_no_news_vix26` | `unknown` | `block, unknown` | `unknown` | `False` | `True` |
| `earnings_next_week_no_catalyst_vix16` | `allow` | `allow` | `allow` | `True` | `True` |
| `fed_remarks_yesterday_no_data_vix17` | `allow` | `allow` | `allow` | `True` | `True` |
| `regional_bank_halt_vix24` | `block` | `block` | `block` | `True` | `True` |
| `treasury_auction_pending_vix18` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
| `earnings_after_close_vix16` | `allow` | `allow` | `allow` | `True` | `True` |
| `cpi_tomorrow_vix16` | `allow` | `allow` | `allow` | `True` | `True` |
| `cpi_next_week_fed_today_vix19` | `unknown` | `unknown` | `unknown` | `True` | `True` |
| `stress_contained_vix18` | `allow` | `allow` | `allow` | `True` | `True` |
| `panic_bid_defensives_vix17` | `allow` | `allow` | `allow` | `True` | `True` |
| `market_panic_vix28` | `block` | `block` | `block` | `True` | `True` |
