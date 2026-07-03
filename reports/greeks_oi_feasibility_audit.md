# Greeks/OI Feasibility Audit

- Status: `pass`
- Strategy use status: `blocked_until_normalized_quote_enrichment_and_gamma_aggregation_policy`
- Target date: `2024-01-03`
- Research decision: Feasible with caveats: Databento OPRA statistics can provide exact-symbol reference OI before the target decision timestamp, and current bid/ask quotes plus SPY bars can support a self-computed IV/Delta/Gamma probe. This is not strategy-ready until normalized quote enrichment, rate/dividend policy, American-option caveat handling, and gamma aggregation rules are implemented.

## Blockers

- `None`

## Quote Fields

- Quote count: 3488
- Missing required fields: none

## Underlying Join

- Status: `pass`
- Sample matched: 100 / 100
- Rule: Use the latest SPY 1-minute bar with timestamp_et <= option quote timestamp_et.

## OPRA OI Mapping

- Status: `pass`
- Loaded OI records: 180279
- First quote timestamp UTC: `2024-01-03T14:31:00+00:00`
- Sample symbol matches: 50 / 50
- OI records before first quote for matched sample: 850
- Mapping rule: For a decision timestamp, use only OPEN_INTEREST records for the exact Databento option symbol with ts_recv <= decision timestamp UTC. If no such record exists, treat OI as missing for that decision.

## IV/Delta/Gamma Probe

- Status: `pass_with_caveats`
- Implied volatility: `0.215206`
- Delta: `0.499072`
- Gamma: `0.14988577`
- Caveat: `SPY options are American-style and can be affected by dividends/early exercise; this probe is only to prove field feasibility, not production-grade Greeks.`

## Note

This is a data-source and model-input feasibility audit, not a completed strategy experiment. Do not write a research log for it.
