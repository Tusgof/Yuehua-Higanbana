# Hypothesis Data Resolution Audit

## Purpose

This audit corrects the project decision frame: a data source or bar interval is not the hypothesis. Data resolution is a method for answering a specific hypothesis at a specific evidence tier.

The project must not treat missing SPY 1-minute bars or missing timestamp-clean news as a total research blocker unless the next question truly requires that exact data resolution.

## Rule

Before asking for a new data source, paid download, broker data session, or live news/LLM capture, identify:

1. The hypothesis being tested.
2. The evidence tier being targeted.
3. The minimum data resolution needed for that tier.
4. Whether a coarser proxy can falsify, weaken, or prioritize the hypothesis first.
5. What claim is forbidden if only proxy data is used.

## Evidence Tiers By Data Resolution

| Level | Purpose | Possible Data | Allowed Claim | Forbidden Claim |
|:--|:--|:--|:--|:--|
| Mechanism plausibility | Check whether the economic story is coherent enough to continue | Daily SPY/VIX, macro calendar, existing trade summaries, regime labels | The hypothesis is worth/ not worth deeper work | Exact ORB execution edge exists |
| Coarse proxy test | Falsify weak forms and rank which branch deserves detailed data | Daily bars, 5-minute/15-minute bars, event-day labels, existing option snapshots | A lower-resolution version supports or weakens the mechanism | Deployable performance or precise entry/exit validity |
| Exact backtest | Reproduce the strategy rule and fill/exit timing | SPY intraday bars at the rule's required interval, option bid/ask quotes, decision-time features | Strategy evidence inside the tested scope, still subject to MinTRL/PSR/DSR | Live readiness without acceptance and operational gates |
| Deployable evidence | Decide whether paper/operational validation is justified | Exact backtest data plus implementable fills, costs, regime coverage, acceptance gates | E2 candidate if all gates pass | Real-money readiness without launch gate |

## H-A2: Macro-Conditioned ORB

### Hypothesis

H-A2 claims the ORB edge, if it exists, is macro-conditioned: excluding high-importance scheduled macro days should improve implementable risk-adjusted returns because non-macro breakout days reflect cleaner order-flow imbalance.

### Data Resolution Assessment

| Question | Minimum Resolution | Current Status | Next Use |
|:--|:--|:--|:--|
| Does the macro/no-macro mechanism make sense across regimes? | Daily SPY/VIX, macro calendar, current closed-trade summaries | Available enough for proxy review | Can proceed without 2022 SPY 1-minute bars |
| Did 2022-10 stress month contain regimes that should challenge H-A2? | Daily SPY/VIX, macro calendar, option quote availability summary | Mostly available; option quotes downloaded | Can classify stress/regime coverage before exact ORB rerun |
| Can current exact ORB implementation be rerun for 2022-10? | SPY bars at the rule's required opening-range/trigger interval plus option quotes | Blocked on 2022 SPY 1-minute bars from current source path | Only this exact rerun is blocked |
| Can a lower-resolution ORB-like proxy be tested? | 5-minute/15-minute SPY bars or daily range proxies plus clear downgraded claim | Not yet designed | Allowed as a new proxy pre-registration if it cannot be confused with exact execution evidence |

### Decision

Do not treat H-A2 as fully blocked by missing 2022 SPY 1-minute bars. Treat only the exact 2022-10 ORB rerun as blocked.

The next H-A2 step should be a proxy-resolution decision: either run a no-paid coarse stress/regime review on 2022-10 using available daily/regime/event information, or pre-register a lower-resolution ORB proxy before seeking another 1-minute bar source.

Claims from proxy work must remain E1 unless later confirmed by exact backtest data.

## H-L1: LLM News Measurement

### Hypothesis

H-L1 claims LLM sentiment, market-impact, and volatility-relevance scores over pre-entry news can be stable and add information beyond VIX plus macro calendar.

### Data Resolution Assessment

| Question | Minimum Resolution | Current Status | Next Use |
|:--|:--|:--|:--|
| Do deterministic event labels explain part of the target outcome? | Macro calendar, event-day/no-event-day labels, VIX/regime labels | Macro calendar available | Can proceed as event-risk proxy, not LLM/news evidence |
| Can LLM score real historical news without lookahead contamination? | Real timestamp-clean news with publication/fetch/decision timestamps and provenance | Blocked by GDELT response quality | Exact H-L1 historical prompt execution remains blocked |
| Can prospective news capture start going forward? | Timestamp-clean capture policy and user-approved source/method | Plausible but not yet approved/implemented | Allowed as a future capture design, not a backtest shortcut |
| Can synthetic or reconstructed news be used? | Only for parser/prompt plumbing | Existing old Exp07 work is E0 only | Must not be used as research evidence |

### Decision

Do not treat all news-related thinking as blocked by GDELT. Event-risk proxy work can proceed using macro calendar and regime labels, but it must not be called LLM/news evidence.

Live LLM prompt research remains blocked until real timestamp-clean cases exist. The project may still test whether event labels or coarse risk proxies are worth collecting better news for.

## H-G1: Gamma/OI Proxy

H-G1 is parked because the current gamma-ready overlap with baseline trades is too small. This is a sample-overlap and power problem, not a reason to buy broad data blindly.

Before reopening H-G1, define whether the next question is:

- proxy validity across dates and regimes,
- strategy ablation overlap,
- or deployable gamma filter evidence.

Each question has different data requirements. A broad download is forbidden unless it targets the exact missing tier.

## Next Safe Action

Replace the current "wait for exact data blockers" posture with this sequence:

1. Run no-paid data-resolution planning for H-A2 and H-L1.
2. Identify which proxy tests can proceed with current data.
3. Pre-register any proxy test with explicit forbidden claims.
4. Only then decide whether 1-minute bars, another news source, or paid data is still justified.

## Verification

This audit is a planning/control artifact. It is verified when:

- `IMPLEMENT_PLAN.md` points to it as the immediate planning layer.
- `PROJECT_BRAIN.md` records that missing exact-resolution data blocks only exact-resolution claims, not all hypothesis work.
- No paid data, broker request, or live LLM call is approved by this document alone.
