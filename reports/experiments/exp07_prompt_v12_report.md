# Experiment 7 Prompt Pre-Experiment

- Mode: `live_openrouter`
- Cases: 43
- Assessments: 129
- Parse valid rate: 100.00%
- Stable cases across prompts: 35 / 43
- Guarded stable cases across prompts: 43 / 43
- Expected-decision mismatches: 0
- Unknown-policy violations: 13
- Guarded unknown-policy violations: 0
- Input archive: `reports\experiments\exp07_prompt_v12_inputs.json`
- Assessment JSONL: `reports\experiments\exp07_prompt_v12_assessments.jsonl`

## Case Stability

| Case | Expected | Raw Decisions | Guarded Decisions | Raw Stable | Guarded Stable |
|:--|:--|:--|:--|:--|:--|
| `quiet_vix18_normal_term_structure` | `allow` | `allow` | `allow` | `True` | `True` |
| `very_quiet_vix13_no_news` | `allow` | `allow` | `allow` | `True` | `True` |
| `systemic_banking_panic_vix34` | `block` | `block` | `block` | `True` | `True` |
| `war_shock_futures_limit_vix42` | `block` | `block` | `block` | `True` | `True` |
| `high_vol_no_clear_news_vix27` | `unknown` | `unknown` | `unknown` | `True` | `True` |
| `major_fed_event_vix21` | `unknown` | `unknown` | `unknown` | `True` | `True` |
| `cpi_release_pending_vix22` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
| `jobs_report_pending_vix19` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
| `earnings_heavy_calendar_vix20` | `unknown` | `allow` | `unknown` | `True` | `True` |
| `pce_inflation_pending_vix18` | `unknown` | `allow, block, unknown` | `unknown` | `False` | `True` |
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
| `fomc_minutes_next_week_vix16` | `allow` | `allow` | `allow` | `True` | `True` |
| `treasury_auction_yesterday_vix17` | `allow` | `allow` | `allow` | `True` | `True` |
| `emergency_drill_vix14` | `allow` | `allow` | `allow` | `True` | `True` |
| `single_stock_halt_after_close_vix16` | `allow` | `allow` | `allow` | `True` | `True` |
| `bank_stress_contained_fed_today_vix21` | `unknown` | `unknown` | `unknown` | `True` | `True` |
| `banking_stress_spreads_systemic_vix24` | `block` | `block` | `block` | `True` | `True` |
| `futures_halt_rumor_vix29` | `block` | `block` | `block` | `True` | `True` |
| `cpi_today_earnings_next_month_vix18` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
| `powell_tomorrow_no_major_data_vix17` | `allow` | `allow` | `allow` | `True` | `True` |
| `cpi_yesterday_digested_vix18` | `allow` | `allow` | `allow` | `True` | `True` |
| `treasury_auction_tomorrow_vix16` | `allow` | `allow` | `allow` | `True` | `True` |
| `vix_vxv_inversion_vix24` | `unknown` | `block, unknown` | `unknown` | `False` | `True` |
| `normal_vix24_vxv25_no_news` | `allow` | `allow` | `allow` | `True` | `True` |
| `spy_etf_halt_risk_vix23` | `block` | `block` | `block` | `True` | `True` |
| `ism_services_today_vix18` | `unknown` | `allow, unknown` | `unknown` | `False` | `True` |
| `jolts_today_vix18` | `unknown` | `unknown` | `unknown` | `True` | `True` |
| `retail_sales_today_vix18` | `unknown` | `unknown` | `unknown` | `True` | `True` |
| `no_war_risk_eased_vix17` | `allow` | `allow` | `allow` | `True` | `True` |
| `limit_down_drill_vix15` | `allow` | `allow` | `allow` | `True` | `True` |
| `near_inversion_below_threshold_vix20` | `allow` | `allow` | `allow` | `True` | `True` |
| `war_risk_escalates_vix22` | `block` | `block` | `block` | `True` | `True` |
| `circuit_breaker_risk_vix24` | `block` | `block` | `block` | `True` | `True` |
