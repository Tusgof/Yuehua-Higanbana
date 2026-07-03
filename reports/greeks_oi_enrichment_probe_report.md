# Greeks/OI Enrichment Probe

- Status: `pass`
- Target date: `2024-01-03`
- Output JSONL: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\data\derived\spy_0dte\greeks_oi_probe\option_quote_enriched_2024-01-03.jsonl`
- Quote rows: 3488
- Underlying joined: 3488
- Open interest joined: 3488
- Computed Greeks: 1750
- Strategy use status: `blocked_until_gamma_aggregation_policy_and_validation`

## Greek Status Counts

| Status | Count |
|:--|--:|
| `blocked_mid_outside_black_scholes_bracket` | 1738 |
| `computed_with_caveats` | 1750 |

## Sample Records

```json
[
  {
    "databento_symbol": "SPY   240103C00402000",
    "delta": 0.99388,
    "gamma": 0.0005785,
    "greeks_status": "computed_with_caveats",
    "implied_volatility": 2.337013,
    "open_interest": 6,
    "quote_timestamp_et": "2024-01-03T09:31:00-05:00",
    "underlying_price": 470.44
  },
  {
    "databento_symbol": "SPY   240103C00403000",
    "delta": 0.993803,
    "gamma": 0.00059343,
    "greeks_status": "computed_with_caveats",
    "implied_volatility": 2.303826,
    "open_interest": 0,
    "quote_timestamp_et": "2024-01-03T09:31:00-05:00",
    "underlying_price": 470.44
  },
  {
    "databento_symbol": "SPY   240103C00404000",
    "delta": 0.993723,
    "gamma": 0.00060898,
    "greeks_status": "computed_with_caveats",
    "implied_volatility": 2.270715,
    "open_interest": 5,
    "quote_timestamp_et": "2024-01-03T09:31:00-05:00",
    "underlying_price": 470.44
  }
]
```

## Decision

Enrichment probe passed with caveats: target-date quotes can be enriched with prior SPY bar price, exact-symbol prior OPRA OI, and self-computed IV/Delta/Gamma. This is still not a strategy experiment and must not be used for production gamma/NOVI filtering until aggregation, validation, and report rules are defined.

This is a data enrichment probe, not a completed strategy experiment. Do not write a research log for it.
