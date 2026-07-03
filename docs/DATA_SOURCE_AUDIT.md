# DATA_SOURCE_AUDIT.md

## Purpose
This document completes the first pass of Milestone 2.1-2.2: audit realistic data sources for the SPY 0DTE research system before writing strategy or backtest logic.

The project needs data that can support implementable 0DTE option PnL, not only theoretical mid-price results. The controlling local references are:

- `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki\concepts\backtest-validation-protocol.md`
- `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki\concepts\implementable-option-pnl.md`
- `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki\concepts\zero-dte-conditional-trading-rules.md`
- `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki\questions\python-finance-backtesting-knowledge-base.md`

## Minimum Data Requirements

| Data | Required For | Minimum Requirement | Status |
|:--|:--|:--|:--|
| SPY underlying intraday bars | ORB, benchmark, option moneyness | 1-minute OHLCV, ET timestamps | Available from multiple sources |
| SPY 0DTE option chain/quotes | Entry, exits, implementable PnL | bid, ask, strike, expiry, right, timestamp, volume/size if available | Paid or limited-free source likely required |
| 9:35 AM ET option snapshot | Sub-System A entry | all near-ATM strikes or full chain | Required |
| 10:00 AM ET option snapshot | Sub-System B entry and implied-state features | full same-day chain | Required |
| 3:45 PM ET option snapshot | forced close valuation | held strikes at minimum; full chain preferred | Required |
| 30-minute option quotes/volume | stop checks, NOVI proxy | bid/ask/volume by interval | Strongly preferred |
| VIX/VXV | regime filters | daily close is acceptable for research; intraday is optional | Official Cboe CSV source selected/imported |
| Macro calendar | no-trade/event filters | FOMC, CPI, NFP, PCE with release time in ET | Official sources exist but need normalization |
| News/LLM input | DeepSeek gate research | fetched_at, source, prompt input/output, decision | Deferred until LLM milestone |

## Provider Audit

| Provider | Covers | Strength | Weakness | Cost/Access | Recommendation |
|:--|:--|:--|:--|:--|:--|
| OptionsDX | SPY option chains, bid/ask/last, greeks, IV, underlying price, multiple quote frequencies | Good fit for snapshot-style research; SPY product lists EOD, 30-minute, 15-minute, 5-minute, and minutely CSVs | Public product page currently lists years through 2023, so OOS 2024-current may be unavailable unless store has newer data not visible in audit | SPY product page shows $0-$50 range depending year/frequency | Good first paid candidate for historical 2022-2023 in-sample and possible reference data; blocked for full OOS unless newer years are available |
| ThetaData | Options quotes/trades, Greeks, historical access, API workflow | Strong fit if we need API-driven 1-minute or 30-minute option quote research | Requires subscription and account; exact downloadable historical coverage should be checked before purchase | Pricing page shows Options Value at $40/month with 4 years of data and 1-minute intervals | Recommended first subscription candidate if OptionsDX lacks 2024-current OOS or if API workflow matters |
| Cboe DataShop | Official OPRA option quote interval and EOD summary datasets | High-quality source; option quote intervals cover U.S. listed options and include bid/ask/size/underlying bid/ask for ETFs; EOD summary includes 15:45 snapshot | Likely more expensive and heavier than project needs; full-market files can be very large | Commercial Cboe purchase/subscription | Best institutional fallback; not first choice for a $1,000-account research project |
| Massive/Polygon options API | Historical options quotes with bid/ask and precise timestamps | API-friendly; useful if per-contract quote retrieval is enough | Could be costly for historical quotes; chain-wide intraday reconstruction may be slow or expensive | Options Advanced page shows $199/month in search result | Secondary candidate; use only if ThetaData/OptionsDX fail |
| Databento OPRA | Usage-based historical OPRA options data with API cost estimation before download | Good fit for pay-as-you-go testing if we keep requests narrow and estimate cost first | Parent-symbol requests may overestimate because they can include more than 0DTE only; careless full-day/tick requests can become expensive | Usage-based; use `metadata.get_cost` before downloading | Recommended low-commitment candidate before any monthly subscription; run one-day then one-month cost checks first |
| Alpha Vantage | SPY intraday OHLCV | Official docs provide intraday adjusted/raw OHLCV and long history | Does not solve option bid/ask problem | API key; free/premium tiers | Acceptable for SPY bars if provider licensing and rate limits fit |
| Stooq | Daily/hourly/5-minute historical market data | Free/simple fallback for broad SPY bars | Not enough for 1-minute ORB precision and no option quotes | Free downloads | Useful only as fallback/sanity data, not primary ORB source |
| FRED | VIX and VXV/VIX3M daily close | Free, stable, easy to cite and download | Daily close only; not intraday pre-entry | Free | Recommended for first VIX/VXV research filters |
| Cboe volatility index CSVs | VIX/VIX3M official history | Official volatility-index source | Requires file handling and symbol mapping | Free public files for some indexes | Use if FRED coverage is insufficient |
| Federal Reserve FOMC calendar | FOMC meetings | Official source | Needs parser/normalizer; release time and minutes/SEP logic must be handled carefully | Free | Recommended source for FOMC event filter |
| BLS schedule | CPI, Employment Situation/NFP, PPI and other labor/inflation releases | Official release dates and times | Government shutdown/revisions can alter schedule; must preserve source timestamp | Free | Recommended source for CPI/NFP/PPI filters |
| BEA pages/schedule | PCE/GDP releases | Official source | Schedule pages may need custom parsing | Free | Recommended source for PCE/GDP filters |
| Trading Economics Calendar API | Consolidated macro calendar | Convenient API and broad coverage | Paid/commercial dependency; user approval required | API subscription | Defer unless official-source scraping becomes too brittle |

## Current Recommendation

Use a staged provider strategy:

1. **No paid purchase yet.** Finish contracts and importer stubs using fixtures.
2. **SPY bars**: start with Alpha Vantage or another low-cost/free intraday source, but keep the schema provider-neutral.
3. **VIX/VXV**: use official Cboe CSVs: `VIX_History.csv` and `VIX3M_History.csv`, with VIX3M close mapped to project `vxv_close`.
4. **Macro calendar**: start with official sources: Federal Reserve for FOMC, BLS for CPI/NFP/PPI, BEA for PCE/GDP.
5. **SPY 0DTE options**:
   - First inspect OptionsDX availability for 2022-2025/2026 SPY 5-minute or 30-minute/minutely chains.
   - If OptionsDX cannot cover OOS 2024-current, run Databento cost estimates before choosing a monthly subscription.
   - Prefer ThetaData only if Databento cost/coverage is worse than a simple monthly plan.
   - Use Cboe DataShop only if the cheaper routes cannot provide reliable bid/ask snapshots.

## Blocked Items

- `[BLOCKED: user approval required]` Buying OptionsDX, ThetaData, Cboe DataShop, Massive/Polygon, or Trading Economics data.
- `[BLOCKED: provider inspection required]` OptionsDX visible SPY page lists through 2023; we need 2024-current for untouched OOS.
- `[BLOCKED: API key required later]` Alpha Vantage, DeepSeek, and any paid data API key.
- `[BLOCKED: Databento account/key required]` Live Databento cost estimate and download require local API key, but dry-run request plans work without a key.
- `[SAFETY]` Databento `full_research` dry-run currently expands into thousands of small cost windows; live mode is guarded by `--max-live-requests` and should start with `one_day_sample`.
- `[SAFETY]` Databento cost reports use default decision thresholds: below $5 pass, $5-$25 review, $25+ block. Wider budgets require explicit user approval.
- `[SAFETY]` Wider Databento scopes should be projected from the latest accepted live report before running thousands of live `get_cost` calls.
- `[SAFETY]` Databento download requires a `pass` cost report, no request errors, a bounded request count, and explicit `--execute`.

## Required Follow-Up Before Milestone 3

- Choose the first actual options data source after user approval or after confirming a free usable source.
- Save at least one small raw sample file under `data/raw/spy_0dte/`.
- Record provider, source URL, download timestamp, raw hash, coverage start/end, and license notes in the registry manifest.

## Source Notes

- OptionsDX SPY product page: https://www.optionsdx.com/product/spy-option-chains/
- OptionsDX field definitions: https://www.optionsdx.com/option-chain-field-definitions/
- ThetaData options data: https://www.thetadata.net/options-data
- ThetaData pricing: https://www.thetadata.net/pricing
- Cboe DataShop option quote intervals: https://datashop.cboe.com/option-quote-intervals
- Cboe DataShop option EOD summary: https://datashop.cboe.com/option-eod-summary
- Cboe DataShop FAQ on SPY/SPX expirations: https://datashop.cboe.com/faqs
- Cboe VIX history CSV: https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv
- Cboe VIX3M history CSV: https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv
- Databento options data: https://databento.com/options
- Databento historical metadata get_cost: https://databento.com/docs/api-reference-historical/metadata/metadata-get-cost
- Alpha Vantage documentation: https://www.alphavantage.co/documentation/
- FRED VIX: https://fred.stlouisfed.org/series/VIXCLS
- FRED VXV/VIX3M: https://fred.stlouisfed.org/series/VXVCLS
- Federal Reserve FOMC calendar: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
- BLS schedule: https://www.bls.gov/schedule/
- BEA PCE page: https://www.bea.gov/data/personal-consumption-expenditures-price-index
- Trading Economics calendar API: https://tradingeconomics.com/api/calendar.aspx
