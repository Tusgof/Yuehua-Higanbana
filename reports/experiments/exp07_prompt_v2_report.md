# Experiment 7 Prompt Pre-Experiment

- Mode: `live_openrouter`
- Cases: 6
- Assessments: 18
- Parse valid rate: 100.00%
- Stable cases across prompts: 5 / 6
- Expected-decision mismatches: 0
- Input archive: `reports\experiments\exp07_prompt_v2_inputs.json`
- Assessment JSONL: `reports\experiments\exp07_prompt_v2_assessments.jsonl`

## Case Stability

| Case | Expected | Decisions | Stable |
|:--|:--|:--|:--|
| `quiet_vix18_normal_term_structure` | `allow` | `allow` | `True` |
| `very_quiet_vix13_no_news` | `allow` | `allow` | `True` |
| `systemic_banking_panic_vix34` | `block` | `block` | `True` |
| `war_shock_futures_limit_vix42` | `block` | `block` | `True` |
| `high_vol_no_clear_news_vix27` | `unknown` | `unknown` | `True` |
| `major_fed_event_vix21` | `unknown` | `block, unknown` | `False` |
