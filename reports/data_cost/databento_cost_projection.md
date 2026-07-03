# Databento Cost Projection

- **Source report**: `reports\data_cost\databento_cost_plan.json`
- **Source scenario**: `one_month_pilot`
- **Source mode**: `live`
- **Source successful request count**: 63
- **Source error count**: 0
- **Average cost per research window**: `$0.02355251`

## Projection

| Scenario | Requests | Projected Cost USD |
|:--|--:|--:|
| `one_day_sample` | 3 | `$0.070658` |
| `one_month_pilot` | 63 | `$1.483808` |
| `oos_2024_2025` | 1122 | `$26.425911` |
| `full_research` | 3111 | `$73.271845` |

## Use Rule

- This is a projection from live one-month cost estimates, not a Databento quote.
- Run live `get_cost` for the next wider scenario only after reviewing this projection.
- Do not download data until the live cost report for that exact scope is accepted.
