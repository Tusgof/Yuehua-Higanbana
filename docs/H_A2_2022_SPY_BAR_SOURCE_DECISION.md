# H-A2 2022 SPY Bar Source Decision

## Status
- **Date**: 2026-07-04
- **Track**: H-A2 Macro-Conditioned ORB Edge
- **Decision**: Use a no-paid source probe first. Prefer an IBKR data-only historical-bars probe if the local IBKR setup and market-data permissions are already available. Do not buy more 2022 option data until 2022 SPY bars are resolved.
- **Conclusion**: H-A2 2022-10 stress rerun remains blocked, but the next source action is now explicit and cost-controlled.

## Problem
The 2022-10 H-A2 stress option quotes are already downloaded and normalized:

- `reports\data_cost\databento_download_result_h_a2_2022_10_stress.json`
- `reports\data_cost\databento_normalization_summary_h_a2_2022_10_stress.json`

The rerun is blocked because Databento `EQUS.MINI` cannot supply 2022 SPY underlying 1-minute bars. The blocker is recorded in:

- `reports\data_cost\databento_spy_bars_plan_h_a2_2022_10_unavailable.json`

That means buying 2022-09 option quotes now would be wrong. It would increase cost while leaving the same underlying-bar blocker unresolved.

## Source Findings

| Source | Finding | Decision |
|:--|:--|:--|
| Local cache | No 2022-10 SPY 1-minute bars found. Current local Databento SPY bars start in 2023 and extend through 2024. | Cannot unblock H-A2. |
| Databento `EQUS.MINI` | Live metadata returned `data_start_before_available_start`; available start is `2023-03-28`. | Do not retry 2022-10 unless availability changes. |
| IBKR TWS API | Official limitations page says historical requests must be paced and 1-minute requests should use step sizes such as 1 day per request; it also notes that hard limits for bar sizes of 1 minute and greater have been lifted, with soft throttling still possible. | Preferred no-paid probe if local TWS/Gateway and data permissions are available. Data-only only; no order transmission. |
| Alpaca Market Data | Official page advertises a free plan with 7+ years of historical data, aggregate bars, and IEX exchange coverage for the free tier. | Fallback probe only if the user approves using/creating Alpaca credentials. Must validate whether IEX-only is acceptable or only diagnostic. |
| FirstRate Data | SPY product page advertises SPY intraday bars from 2000-01-03 through 2026-07-02, including 1-minute OHLCV CSV. | Plausible paid CSV fallback, but new paid provider approval and exact price confirmation are required. |
| Alpha Vantage | Official docs/premium page indicate historical intraday data is premium and the entry listed plan is `$49.99/month`. | Paid fallback only after explicit approval and confirmation that 2022-10 1-minute bars are accessible. |
| Massive/Polygon-style stock aggregates | Official stocks API docs support historical aggregate OHLCV over custom ranges. Pricing/search result indicates paid historical intraday access. | Paid fallback only after explicit approval. |
| Tiingo IEX | Official docs expose historical intraday IEX endpoint. | Diagnostic fallback only; IEX-only bars are not preferred for acceptance-grade ORB against OPRA quotes. |

## Required Probe Output
Any source that claims to solve this blocker must produce a small audited artifact before H-A2 rerun:

1. Raw or API-derived 2022-10 SPY 1-minute bars for at least one trading day.
2. Provenance: provider, endpoint/file, retrieval time, raw hash where file-based, and license notes.
3. Coverage audit for regular trading hours and required ORB timestamps.
4. Timestamp conversion check to ET.
5. Import path into canonical `spy_bar` shape without lookahead.

## Locked Rules
- Do not buy 2022-09 option data while 2022 SPY bars are unresolved.
- Do not buy a new paid provider without explicit user approval.
- IBKR can be used only as a data-only source. Order transmission remains blocked.
- IEX-only bars cannot become acceptance-grade consolidated bars without a separate proxy decision.
- H-A2 stays E1 or below until 2022-10 stress diagnostics can run with valid SPY bars and already-downloaded option quotes.

## Sources Checked
- IBKR historical data limitations: https://interactivebrokers.github.io/tws-api/historical_limitations.html
- IBKR historical data article: https://www.interactivebrokers.com/campus/ibkr-quant-news/retrieving-historical-data-from-ibkr/
- Alpaca market data: https://alpaca.markets/data
- FirstRate Data SPY: https://firstratedata.com/i/etf/SPY
- Alpha Vantage documentation: https://www.alphavantage.co/documentation/
- Alpha Vantage premium: https://www.alphavantage.co/premium/
- Massive stocks API docs: https://massive.com/docs/rest/stocks/overview
- Tiingo IEX docs: https://www.tiingo.com/documentation/iex

## Verification
```powershell
python scripts\validate_h_a2_2022_spy_bar_source_decision.py
python -m unittest tests.test_validate_h_a2_2022_spy_bar_source_decision
python scripts\audit_research_readiness.py
```
