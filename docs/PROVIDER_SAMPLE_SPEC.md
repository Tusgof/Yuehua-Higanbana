# PROVIDER_SAMPLE_SPEC.md

## Purpose

This document defines the first file sample needed from any historical SPY 0DTE options data provider before a provider-specific importer can be trusted.

The current adapters are sample templates only. They prove the canonical schema mapping and validation flow, but they must be checked against a real provider export before real research starts.

## Minimum Sample To Request

Ask the provider for a small SPY 0DTE option quote sample covering at least one full trading day after 2022-05-11.

Minimum rows:

- 9:35 AM ET quote snapshot for strikes around ATM.
- 10:00 AM ET quote snapshot for the option chain or moneyness grid.
- 3:45 PM ET quote snapshot for the same strikes.
- If available, 30-minute intraday quote snapshots from 9:30 AM to 3:45 PM ET.

Required columns:

| Canonical field | Why required |
|:--|:--|
| `quote_timestamp_et` | Entry/exit timing and no lookahead discipline |
| `expiration_date` | Confirms same-day 0DTE contract |
| `right` | Call/put leg construction |
| `strike` | Spread construction and payoff |
| `bid` | Implementable sell price |
| `ask` | Implementable buy price |
| `bid_size` | Liquidity sanity check |
| `ask_size` | Liquidity sanity check |
| `volume` | NOVI/liquidity proxy if available |
| `open_interest` | Liquidity context if available |
| `underlying_price` | Strike distance and moneyness checks |

## Current Template Adapters

The project currently includes two synthetic adapter templates:

```powershell
python scripts\provider_adapters.py
```

They parse:

- `tests/fixtures/provider_samples/optionsdx_option_quote_sample.csv`
- `tests/fixtures/provider_samples/thetadata_option_quote_sample.csv`

Both adapters output canonical `option_quote` records and then run `validate_m2_contracts.validate_record`.

After a sample mapping is confirmed, import the sample with:

```powershell
python scripts\import_provider_sample.py --provider optionsdx --raw-path data\raw\spy_0dte\<sample>.csv
```

This writes:

- `data/normalized/spy_0dte/option_quote.jsonl`
- `data/registry/datasets.jsonl`

The registry manifest records provider, coverage dates, schema version, raw SHA-256 hash, and license notes.

## Acceptance Rules For A Real Provider Sample

A provider sample is acceptable only if:

- Bid and ask are both present at the required timestamps.
- `ask >= bid` for every row.
- Timestamp timezone can be resolved to ET without guessing.
- Same-day SPY expiration can be identified directly.
- Rows preserve enough strikes to build vertical spreads and capped-risk ratio spreads.
- License terms allow local research use and derived reports.

## What Still Needs User Input

The user still needs to provide either:

- A real provider sample CSV/API response, or
- Approval to buy a provider subscription, or
- Confirmation of a free source that contains historical SPY 0DTE bid/ask quotes.
