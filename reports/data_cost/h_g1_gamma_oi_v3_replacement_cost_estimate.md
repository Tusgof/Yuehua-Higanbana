# H-G1 Gamma/OI Cost Gate

- **Hypothesis**: `H-G1`
- **Scenario**: `h_g1_gamma_oi_v3_replacement`
- **Mode**: `live_metadata_cost_no_download`
- **Download performed**: `False`
- **Missing OI dates estimated**: 1
- **Existing probe dates**: 2024-01-03
- **Total estimated cost**: `0.384999`
- **Cost guard used**: `$109.082227` / `$125.0`
- **Remaining before stop**: `$15.917773`
- **Projected usage if downloaded**: `$109.467226`
- **Decision**: `pass`
- **Download allowed under current guard**: `True`
- **Reason**: Estimated H-G1 OI cost $0.384999 fits within remaining headroom $15.917773.

## Planned Full-Day Requests

| Date | Window | Start | End | Cost |
|:--|:--|:--|:--|--:|
| `2023-09-13` | `2023-09-13_full_utc_day_statistics` | `2023-09-13T00:00:00+00:00` | `2023-09-14T00:00:00+00:00` | `0.384999` |

## Guardrail

This report is a metadata cost gate only. It must not be treated as a Databento download, an OI coverage pass, or a gamma strategy result.
