# Experiment 7 Prompt Pre-Experiment

- Mode: `live_openrouter`
- Cases: 3
- Assessments: 9
- Parse valid rate: 100.00%
- Stable cases across prompts: 1 / 3
- Expected-decision mismatches: 1
- Input archive: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\experiments\exp07_prompt_inputs.json`
- Assessment JSONL: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\experiments\exp07_prompt_assessments.jsonl`

## Case Stability

| Case | Expected | Decisions | Stable |
|:--|:--|:--|:--|
| `quiet_vix18_normal_term_structure` | `allow` | `allow, block` | `False` |
| `systemic_banking_panic_vix34` | `block` | `block` | `True` |
| `high_vol_no_clear_news_vix27` | `unknown` | `allow, block` | `False` |
