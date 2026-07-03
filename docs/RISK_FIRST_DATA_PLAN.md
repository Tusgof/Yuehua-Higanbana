# Risk-First Data Plan

## Purpose

This document closes the current planning gap before any further paid data pull. It replaces the old "keep downloading until N >= 500" framing with a risk-first data plan:

1. Define sample adequacy through MinTRL / PSR / power inputs.
2. Define market-regime coverage before buying more calendar data.
3. Decide how to handle Greeks, gamma, implied volatility, and open interest before reviving NOVI/net-gamma research.

No paid API call was made for this document.

## Current Evidence State

| Item | Current Evidence | Interpretation |
|:--|:--|:--|
| Strategy coverage | Mar-Dec 2023 in-sample plus Jan-Dec 2024 OOS |
| Candidate days | 93 |
| Closed trades | 90 |
| OOS closed trades | 49 |
| Q4 2024 incremental result | Sep remainder-Dec 2024 added 11 closed trades for about `$38.679332` |
| Current conclusion strength | Diagnostic only |
| Current sample label | `under-sampled` / `underpowered` |
| Main blocker | `requires_mintrl_psr_sample_adequacy` |

The old `N >= 500` value remains only a rough warning prior. It must not be treated as a universal acceptance gate. The current 90-trade evidence is too weak for approval, but the next question is not "how do we buy 410 more trades blindly?" The next question is "what sample length and regimes are required for this exact hypothesis?"

The data plan must therefore work backwards from the hypothesis. If Sub-System A is being tested as a post-2022 0DTE ORB edge, the next data block must improve the statistical inference or falsification power of that hypothesis. If Sub-System B is being tested as a structurally different payoff engine, the portfolio size used in research may be larger than the current starting account so the system can learn whether the structure has merit before deciding the true minimum viable account size.

## MinTRL / PSR Sample Plan

### Required Inputs

Every acceptance-grade strategy family must produce these inputs before it can claim a Sharpe-based edge:

| Input | Required By | Current Status |
|:--|:--|:--|
| Implementable trade or daily return series | PSR, MinTRL, power | Exists for current diagnostic reports, but not yet standardized into a reusable inference artifact |
| Observed Sharpe | PSR, MinTRL | Present as report-level proxy; must be recalculated consistently |
| Null Sharpe threshold | PSR, MinTRL | Not fixed; needs a project-level decision per strategy family |
| Sample length | PSR, MinTRL | 90 closed trades total, 49 OOS for current Sub-System A control |
| Skewness | Generalized Sharpe variance | Not yet reported as a reusable field |
| Kurtosis | Generalized Sharpe variance | Not yet reported as a reusable field |
| First-order autocorrelation | Generalized Sharpe variance | Not yet reported as a reusable field |
| Trial count / effective trials | DSR | Search logs exist for M5 families; effective independent trial count not yet computed |
| Filter-retained active trades | Filtered MinTRL/PSR | Reported in M5 filters; still too small |

### Minimum Rule

A strategy family is not acceptance-grade until all of the following are true:

1. The report computes PSR against at least two null thresholds: `SR0 = 0` and a minimum acceptable positive Sharpe threshold chosen before the run.
2. The report computes or explicitly blocks MinTRL using observed Sharpe, null threshold, skewness, kurtosis, autocorrelation, and desired significance/power.
3. If actual observations are below MinTRL, the result is labeled `under-sampled`.
4. If power is insufficient to reject or confirm the hypothesis, the result is labeled `underpowered`.
5. If a scenario was selected from multiple parameter/filter trials, DSR is computed or explicitly blocked with the trial count and reason.

### Current Working Null Thresholds

These are planning defaults, not final approval thresholds:

| Strategy Family | Null Threshold Set | Reason |
|:--|:--|:--|
| Sub-System A ORB debit vertical | `SR0 = 0`, then `SR0 = same-period SPY buy-and-hold Sharpe`, then a positive minimum acceptable Sharpe | A must beat not trading and beat benchmark on risk-adjusted terms |
| Sub-System B put ratio with protective wing | `SR0 = 0`, then downside-risk-adjusted threshold | B has negative-skew/tail-risk concerns, so point Sharpe is especially weak evidence |
| Regime-filtered A | Same as A, plus filter-retained active-trade MinTRL | Filtering can manufacture strong-looking averages by shrinking samples |
| Portfolio A/B | Portfolio-level null threshold after fixed allocation rule is pre-registered | Allocation must not be chosen from OOS diagnostics |
| LLM/news gate | Compare baseline vs LLM-gated return series, not only LLM classification accuracy | LLM value must show incremental strategy utility after costs and skipped trades |

## Regime Coverage Plan

Future data expansion must cover regimes, not just months. A data pull is justified only if it fills a named regime gap or a named inference gap.

This means the next paid data choice should be expressed as a coverage target, for example:

1. Add reference/pre-break coverage to test whether the post-May-2022 0DTE listing change matters.
2. Add high-VIX or stress-window coverage if current evidence lacks volatility-regime diversity.
3. Add newer OOS coverage only if it improves regime coverage or fresh validation more than it merely increases calendar length.
4. Add field coverage such as OI, IV, Greeks, or liquidity proxies only if it unlocks a blocked hypothesis such as delta selection, NOVI, or gamma/liquidity regime testing.

### Required Regime Labels

| Regime Layer | Ex-Ante Label Method | Current Status | Minimum Need Before More Broad Data |
|:--|:--|:--|:--|
| Volatility | Previous available VIX close: low `<15`, normal `15-25`, high `>25` | VIX/VIX3M data exists; current reports use previous close | Count trades and PnL by VIX bucket before selecting next years |
| Macro-event | Official scheduled same-day events known before entry | Macro calendar exists for 2022-2026 | Count filtered and retained trades by event type and importance |
| Trend / momentum | SPY rolling return or moving-average state computed before entry | Not yet standardized | Add a simple ex-ante trend label before buying more data |
| Major subperiod | Calendar subperiods: reference/pre-break, train, OOS, post-2024 extension | Reference/pre-break is missing; 2025+ is missing | Decide whether structural-break or fresh OOS is the higher-value next block |
| Economic surprise | Actual-vs-consensus surprise where available | Not currently available | Do not buy this first; use macro scheduled-event labels first |
| Gamma / liquidity | Open interest, gamma, IV, quote width, or market-maker proxy | Missing Greeks/gamma/OI; quote width exists | Run provider/proxy field test before any NOVI/net-gamma experiment |

### Current Regime Gaps

| Gap | Why It Matters | Proposed Handling |
|:--|:--|:--|
| Reference/pre-break `2019-01-01` to `2022-05-10` is absent | Cannot test the May 2022 structural-break hypothesis | Do not buy full reference data blindly; first estimate cost for a targeted pre-break probe |
| 2025+ OOS is absent | Current OOS ends at Dec 2024 and may not represent newer regimes | Consider after MinTRL/regime audit shows which VIX/macro/trend buckets are missing |
| High-volatility regime may be thin | 2023-2024 likely underrepresents crisis-style days | Use VIX bucket counts to decide whether targeted 2022 or specific stress windows are better than 2025 |
| Filtered macro sample is small | Best diagnostic macro filter retains only 64 trades total and 34 OOS | Treat macro filter result as hypothesis-generating until MinTRL/PSR passes |
| Gamma/liquidity regime absent | NOVI/net-gamma cannot be interpreted from current quotes alone | Run data-source/proxy review before spending on gamma-family experiments |

## Greeks / Gamma / Open Interest Source Review

### What The Research Needs

| Research Need | Required Field / Method | Current Local Status |
|:--|:--|:--|
| Delta-based strike selection | Delta or model inputs to compute delta | Current normalized quotes do not include Greeks |
| Gamma / NOVI proxy | Gamma, IV, open interest or position/inventory proxy, scaling convention | Missing |
| Dealer net-gamma style regime | Position reconstruction or open-close/inventory data plus Greeks | Missing; cannot infer true dealer positioning from quotes alone |
| Liquidity regime | Bid/ask spread, quote width, sizes, volume | Partly available from Databento quotes |
| IV / skew regime | IV surface or model-computed IV from option prices | Not yet computed |

### Provider Findings

| Provider | Current Finding | Fit For Higanbana | Decision |
|:--|:--|:--|:--|
| Databento OPRA | Provides historical OPRA options quotes/trades, covers SPY, and provides reference/statistics schemas. It does not currently provide pre-calculated IV or Greeks; open interest is available through statistics schemas. | Best near-term continuation because tooling and cost guard already exist. Good for quotes, spreads, trades, OI field probes, and self-computed IV/Greeks. | Use first for low-cost OI/statistics probe and self-computed Greeks feasibility. Do not expect vendor Greeks. |
| ThetaData | Official site advertises 1st/2nd/3rd order Greeks, IV calculations, historical access, and daily open interest updates. Retail options plans are monthly subscriptions. | Strong candidate if we need ready-made Greeks/OI across SPY chains without building the model layer first. | New paid provider: requires user approval before purchase. Research trial/sample endpoint first if possible. |
| ORATS | Official pages advertise EOD data back to 2007 and one-minute intraday data back to Aug 2020, with Greeks, IV/SMV, and many indicators. | Strong for clean derived options indicators, especially if we need vendor-smoothed values. Intraday starts Aug 2020, enough for post-2022 and some pre-break, but likely a new paid-provider decision. | Defer unless Databento self-computation or ThetaData is insufficient. |
| Cboe DataShop / Open-Close style data | Needed for stronger dealer-position reconstruction in academic-style gamma inventory work. | Potentially best for true dealer/investor flow inference, but likely expensive and heavier than current stage. | Defer. Use only if gamma-family research becomes central and cheaper proxies fail. |

### Provider Sources Checked

- Databento options page: `https://databento.com/options`
- Databento OPRA dataset/spec docs: `https://databento.com/docs/venues-and-datasets/opra-pillar`
- Databento statistics schema docs: `https://databento.com/docs/schemas-and-data-formats/statistics`
- ThetaData options page: `https://www.thetadata.net/options-data`
- ThetaData pricing page: `https://www.thetadata.net/pricing`
- ORATS Data API page: `https://orats.com/data-api`
- ORATS Intraday Data API page: `https://orats.com/intraday-data-api`
- ORATS API docs page: `https://orats.com/docs`

## Near-Term Data Decision

Do not buy broad calendar data yet.

The next data work should be:

1. Use the existing Risk-first audit as the current blocker ledger: sample inference, regime coverage, and missing field coverage.
2. Run a Databento no-download or low-cost field probe for OPRA statistics/open interest availability on a very small SPY sample.
3. If Databento OI/statistics is usable, test whether self-computed IV/Greeks are feasible from existing quote fields plus underlying price, expiry, and rate assumptions.
4. If Databento cannot support the blocked gamma/Greeks/OI hypotheses, present a purchase decision between ThetaData, ORATS, or a cheaper alternative before using a new provider.
5. Only after the field decision, choose the next paid coverage target: reference/pre-break, high-VIX/stress windows, newer OOS, or a revised higher-density hypothesis.

## Next Safe Action

Use the first automated Risk-first audit before buying broad data:

1. Read `reports\risk_first_data_audit.md` as the current pre-purchase checkpoint.
2. Run the tiny Databento OPRA statistics/OI cost/schema probe.
3. Decide whether Databento plus self-computed Greeks is enough for gamma-family research.
4. Then choose the next targeted data block or revise the strategy hypothesis.

Only after those field and regime questions are answered should the project estimate any new broad paid data block.

## Local Knowledge Sources

- `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki\concepts\minimum-track-record-length.md`
- `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki\concepts\probabilistic-sharpe-ratio.md`
- `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki\concepts\backtest-validation-protocol.md`
- `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki\concepts\regime-filtering-for-zero-dte.md`
- `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki\concepts\dealer-gamma-inventory.md`
- `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki\concepts\volatility-attenuation.md`
- `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki\sources\how-to-use-the-sharpe-ratio.md`
