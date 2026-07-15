# Hypothesis Registry

## Purpose

This registry is the control document for hypothesis-led research in Higanbana. Experiment IDs such as Exp01-Exp10 and M4/M5 reports are now evidence sources, not the execution order.

Every hypothesis must state why the edge should exist, what would validate it, what would falsify it, and which evidence tier currently supports it.

## Evidence Tiers

| Tier | Meaning | Allowed Claim |
|:--|:--|:--|
| E0 | Infrastructure, fixtures, parser, prompt plumbing | The machinery works |
| E1 | Real data but under-sampled, underpowered, search-contaminated, or gate-blocked | Hypothesis-generating only |
| E2 | Validation-grade research evidence | Edge exists in the tested scope |
| E3 | E2 plus operational validation and launch gates | May trade only after explicit user approval |

No current Higanbana strategy result is above E1.

## Kill And Resurrection Rule

A hypothesis can be killed only when its pre-registered statistical falsification criteria are hit and a written mechanism autopsy explains where the economic rationale broke. The mechanism matters, but numbers cannot be overridden by belief.

Resurrection is allowed only as a new registry entry with at least one new testable prediction the dead hypothesis did not make. Re-activating the same entry because the idea still feels plausible is prohibited.

## Registry Entries

### H-A1: Legacy Unconditional ORB

- **Family**: `subsystem_a`
- **Status**: `falsified-as-stated`
- **Statement**: Post-2022 SPY 0DTE ORB debit verticals beat SPY buy-and-hold risk-adjusted without conditioning on macro or regime state.
- **Economic rationale**: Opening-range breakouts may reflect early order-flow imbalance after the 0DTE listing expansion.
- **Current evidence**: 90 Sub-System A closed trades, OOS implementable PnL `-$78.44`, observed Sharpe proxy below every meaningful null, and benchmark-null validation undefined.
- **Conclusion**: `ไม่ผ่าน` for the unconditional form.
- **Mechanism autopsy**: The unconditional version likely mixes different market mechanisms: ordinary order-flow imbalance days, scheduled macro repricing days, and stress windows. If these states behave differently, a single unconditional ORB rule dilutes the intended edge and makes blind calendar expansion misleading.
- **Successor**: H-A2.

### H-A2: Macro-Conditioned ORB

- **Family**: `subsystem_a`
- **Status**: `active_blocked`
- **Statement**: The ORB edge, if it exists, is macro-conditioned: excluding high-importance scheduled macro days should improve implementable risk-adjusted OOS returns because non-macro breakout days reflect cleaner order-flow imbalance.
- **Economic rationale**: On scheduled macro days, the opening range can be dominated by anticipatory positioning and post-release repricing rather than persistent intraday imbalance. Removing those days is a mechanism claim, not merely a fitted filter.
- **Testable predictions**:
  - Macro-day trades remain weak or negative in fresh data.
  - Retained no-macro trades remain positive after cost and big-day removal.
  - The effect is not concentrated in one VIX/trend bucket unless the hypothesis is explicitly scope-restricted.
- **Validation criteria**: E2 requires untouched validation data or DSR accounting for the inherited 9-trial M5.5 search, MinTRL/PSR against `SR0=0` and same-trade-calendar SPY, implementable PnL, big-day survival, and regime coverage or explicit scope restriction.
- **Falsification criteria**: H-A2 is killed if fresh retained no-macro trades have implementable PnL `<= 0` after reaching `MinTRL_falsify`, or if the macro-day/no-macro mechanism reverses in fresh data.
- **Formal scope restriction (2026-07-13)**: H-A2 applies only when prior-close VIX is below `25` and no high-importance macro event is scheduled for the trade date. Prior-close VIX `>= 25` is blocked/out-of-scope. Any future operational configuration must hard-block H-A2 entries outside this scope. This follows the explicit scope-restriction path in `FABLE5_UPGRADE_PROPOSAL.md` section 4.2; it does not claim that H-A2 is validated inside the retained scope.
- **Two-window stress-silence evidence**: Aug 2024 is window 1: VIX and market-data coverage were complete, but high-VIX ORB candidates were zero. Oct 2022 is window 2: all 13 target dates had complete SPY bar coverage and 3 raw 09:35 breakouts, but all 13 failed the ex-ante clean macro/VIX gate, leaving zero candidate trades and no PnL. Together these windows support the VIX guardrail and show that buying more high-VIX months is unlikely to add H-A2 trades efficiently. They are survival/identification evidence only, not edge validation.
- **Current evidence**: M5.5 `exclude_high_importance_macro_same_day`, H-A2 re-analysis, H-A2.19 proxy-first robustness, H-A2.22 residual/adverse-day analysis, H-A2.24 revised opening-followthrough diagnostic, H-A2.26 revised-condition robustness audit, H-A2.27 locked-condition signal-attribution audit, H-A2.30 delayed-entry diagnostic, and H-A2.32 original-entry revision remain E1 diagnostic evidence only. H-A2.19 is directionally consistent across 5-minute proxy, 15-minute proxy, and existing trade outcomes, but it is still under-sampled and not exact 2022-10 ORB replay. H-A2.22 finds the current clean/risk split is too coarse: 64 non-risk trade days include 40 losing days, 26 macro-only trade days include 21 losing days, and 30 of 40 non-risk losses have negative 5-minute followthrough. H-A2.24 then locked a `0.001` opening-followthrough threshold using train only and evaluated untouched OOS: OOS non-risk loss count dropped from 21 to 1, but revised OOS keeps only 13 trade days. H-A2.26 kept that threshold fixed, used no threshold search and no OOS tuning, and found the result survives basic big-day/concentration checks while still being under-sampled and underpowered. H-A2.27 then found the full locked condition is not knowable at the original 09:35 ET entry because the 15-minute conflict component is only known around 09:45 ET. H-A2.30 confirms the locked condition is timestamp-clean at `09:45:00` ET, but current source artifacts do not contain auditable 09:45 delayed-entry option quotes/fills, so delayed-entry implementable PnL is not computable. H-A2.32 then tests a timestamp-clean original-entry branch using only 09:35-known features: clean macro/VIX plus `proxy_5m_followthrough >= 0.001`. It excludes the 15-minute conflict component, keeps threshold `0.001` locked, retains 14 OOS trade days, and improves original-entry context PnL versus baseline, but remains under-sampled/underpowered E1 evidence only.
- **Conclusion**: `ยังสรุปไม่ได้`.

- **Current control artifact**: H-A2.33 pre-registers the stricter original-entry robustness/prioritization review before any claim upgrade. It preserves the H-A2.32 09:35-only rule and threshold `0.001`, then requires leave-one/big-day dependency, regime/calendar concentration, skip-cost tradeoff, and validation-priority decision checks. This is E0 control evidence only, not a new experiment result.
- **Latest H-A2.34 result**: `reports/experiments/h_a2_original_entry_robustness_prioritization_summary.json` is E1 diagnostic evidence. The 09:35-only rule survives leave-one-out and big-day checks directionally, and skipped trades remain strongly negative, but retained OOS is still only 14 trade days and has no high-VIX retained bucket. Decision is to pre-register independent validation-data planning or no-paid validation feasibility before any paid data, IBKR request, exact replay, paper trading, or E2 claim.
- **Current control artifact**: H-A2.35 `experiments/h_a2_independent_validation_feasibility_preregistration.json` is E0 control evidence. It pre-registers a no-paid feasibility diagnostic for independent validation data, preserves the locked `09:35:00` signal and threshold `0.001`, and forbids paid data, live cost estimates, IBKR requests, exact replay, LLM calls, GDELT retries, paper trading, and E2 claims from the preregistration itself.
- **Latest H-A2.35 result**: `reports/diagnostics/h_a2_independent_validation_feasibility.json` is E1 diagnostic evidence. No-paid sources can define the validation gap and regime requirements, but they cannot add independent implementable SPY 0DTE PnL days.
- **Current control artifact**: H-A2.37 `experiments/h_a2_independent_validation_paid_cost_plan_preregistration.json` is E0 control evidence. It pre-registers a narrow paid-cost estimate plan with exact independent validation windows: one high-VIX sample day `2025-04-08`, a high-VIX pack `2025-04-04` to `2025-04-11`, and two control packs `2025-02-03` to `2025-02-14` and `2025-05-05` to `2025-05-16`. It names required OPRA `cbbo-1m`, SPY `ohlcv-1m`, VIX/VXV, and macro fields, records the `$5.010294` remaining cost guard, and forbids live estimate, paid download, IBKR request, exact replay, paper trading, and E2 claims from the preregistration itself.
- **Latest H-A2.38-H-A2.40 cost/data gate**: `reports/data_cost/h_a2_independent_validation_paid_cost_estimate.json`, `experiments/h_a2_independent_validation_paid_download_decision.json`, and `reports/data_cost/databento_download_result_h_a2_independent_validation_2025_04_08.json` are E0 cost/data-control evidence only. Databento estimated and then downloaded/cache-confirmed `sample_cost_probe_high_vix_one_day` (`2025-04-08`) at `$0.504662` for 15 requests and 54,014,593 bytes. This does not validate H-A2 edge, approve exact replay, approve paper trading, or create E2 evidence.
- **Current control artifact**: H-A2.41 `experiments/h_a2_independent_validation_import_diagnostic_preregistration.json` is E0 control evidence. It pre-registers local parsing/normalization of only the already-downloaded `2025-04-08` raw DBN files, requires raw-file inventory, SPY bar import, OPRA quote import, timestamp alignment, locked-signal reconstruction, and entry/exit quote availability checks, and forbids additional downloads, exact replay, threshold changes, paper trading, and E2 claims.
- **Latest H-A2.42 result**: `reports/diagnostics/h_a2_independent_validation_import_diagnostic.json` is E1 import/availability evidence. All 15 raw DBN files parse locally, SPY bars cover `09:30` to `15:59` ET, OPRA windows contain `1,686,591` quote rows and `43,965` 0DTE valid-mid rows, and the locked `09:35` 5-minute put followthrough passes threshold `0.001`. However, clean macro/VIX is false because prior VIX was `46.98`, so no candidate trade signal exists. This gives high-VIX availability/regime evidence only; it does not create independent validation PnL, exact replay, paper trading approval, or E2 evidence.
- **User decision 2026-07-06**: The next H-A2 independent-validation sample should prioritize normal/control samples, not more high-VIX samples, so we can test whether the edge is specific to normal regimes. The locked `09:35` rule and threshold `0.001` must remain unchanged until a new preregistration says otherwise.
- **Latest H-A2.43 decision**: `experiments/h_a2_normal_control_sample_decision.json` is E0 control evidence. It pauses the old high-VIX-first sequence and selects `low_normal_vix_control_pack` (`2025-02-03` to `2025-02-14`) as the next metadata-only estimate target, using selected key env `DATABENTO_API_MO` without storing the key value. This does not approve download, exact replay, paper trading, or E2.
- **Latest H-A2.44 cost gate**: `reports/data_cost/h_a2_normal_control_low_normal_vix_control_pack_cost_estimate.json` is E0 cost-control evidence. It estimates the normal/control pack at `$5.398913` using selected key env `DATABENTO_API_MO`, with 150 planned required windows grouped into 20 conservative metadata calls. No data was downloaded, projected selected-key usage is `$5.398913` against the `$100` per-key cap and `$200` MO/AI pool cap, and a separate download decision artifact is still required.
- **Fresh OOS 2025-2026 plan**: `reports/data_cost/h_a2_fresh_oos_2025_2026_decision_tree_cost_plan.json` and `.md` propose 20 untouched dates: 10 with prior VIX below 15 in 2025 and 10 with prior VIX 15-25 in 2026. The historical-analogue base estimate is `$10.957555`; the proposed user-approval ceiling with 15% contingency is `$12.601188`. This is plan-only E0 control evidence. No metadata call or purchase occurred, and explicit user approval is required before any purchase.
- **Methodology correction (2026-07-15)**: Code inspection before parsing the fresh OOS block found that `proxy_5m.directional_followthrough_to_close_pct` uses the underlying close at `15:45` even though prior H-A2 artifacts described the feature as known at `09:35`. Every threshold-`0.001` result that selected trades with this feature is now `lookahead-contaminated` diagnostic evidence and cannot support an edge, timestamp-clean, E2, paper-trading, or deployment claim. The frozen artifacts remain unchanged as evidence of the error.
- **Fresh OOS methodology result**: `reports/experiments/h_a2_fresh_oos_timestamp_clean_checkpoint.json` found 6 retrospective candidates across 20 dates, but it also exposed a second timestamp problem. Databento `ohlcv-1m` timestamps the minute interval start, so the close of the bar stamped `09:35` is available around `09:36`; the replay used option quotes stamped `09:35`. The resulting `$249.64` mechanical PnL and its PSR/MinTRL calculations are retained for audit but are invalid for inference because the entry quote precedes signal availability. The exact 09:35 question remains unanswered.
- **Current H-A2 status**: Active but blocked on a valid decision-time definition. Stop additional data expansion. The next design must either use a price observable at 09:35 or explicitly move the decision and entry to 09:36, and it must be tested on outcomes not viewed during this run. Neither the invalidated threshold-`0.001` branch nor the entry-before-signal PnL may be reused as edge evidence.

### H-B1: Put Ratio At Current Small-Account Sizing

- **Family**: `subsystem_b`
- **Status**: `falsified`
- **Statement**: The tested current-account, always-eligible capped-risk put ratio spread template is feasible and profitable under `$300` allocation and `$20` risk budget on a `$1,000` account.
- **Economic rationale**: Selling short-dated downside skew may have premium edge if tail risk is capped by a protective wing, but H-B1 did not test whether the structure needs a specific volatility/skew/regime context before entry.
- **Current evidence**: M4.2 produced 412 closed trades, implementable PnL `-$5,973.44`, OOS implementable PnL `-$3,866.76`, and 0 trades fit the `$300` allocation or `$20` risk budget.
- **Conclusion**: `ไม่ผ่าน`.
- **Mechanism autopsy**: The structure may be too large and fee-heavy for the current account constraints; strike granularity and defined-risk width dominate the intended skew-premium mechanism. More importantly, the failed H-B1 framing implicitly treated the structure as broadly eligible rather than asking when a capped put ratio spread is actually suitable.
- **Successor**: H-B2.

### H-B2: Put Ratio Structure At Realistic Scale

- **Family**: `subsystem_b`
- **Status**: `parked`
- **Statement**: The put-ratio-with-wing structure may have positive expectancy at simulated `$10k` to `$25k` scale only under appropriate market regimes or entry filters where strike granularity, premium-to-account ratios, volatility/skew state, and tail-risk context are favorable.
- **Economic rationale**: If short-dated downside skew is overpriced, a capped-risk structure may monetize it at sufficient account size while preserving survival through the protective wing. The current grid may have failed because it treated structure eligibility too broadly, not necessarily because the structure has no conditional use.
- **Testable predictions**:
  - Cost drag is not the dominant share of gross edge at all wing widths.
  - Implementable PnL and ES95-adjusted return are not negative at both simulated scales.
  - Results are not dependent on fractional contracts or hidden undefined risk.
  - A pre-registered regime/suitability filter can identify conditions where the structure's tail-risk and skew-premium tradeoff is economically coherent.
- **Validation criteria**: Pre-registered account sizes, wing grid, sizing rule, regime/suitability filter, search log, DSR or DSR blocker, implementable PnL, ES95, drawdown, and sample labels.
- **Falsification criteria**: H-B2 is killed if implementable PnL and ES95-adjusted return are negative at both simulated scales with adequate falsification sample under the pre-registered suitability scope, if cost drag exceeds 60% of gross at all wing widths, or if no logically justified volatility/skew/regime filter can be specified without OOS fitting.
- **Current evidence**: `reports/experiments/h_b2_subsystem_b_scale_summary.json` is E1 diagnostic evidence. The 8 pre-registered trials found zero scenarios with both positive total implementable PnL and positive OOS implementable PnL. H-B2 is parked pending MinTRL_falsify review, with no deployment or paper-trading edge claim allowed.
- **Conclusion**: `ยังสรุปไม่ได้`.

- **User decision 2026-07-06**: Do not treat the current H-B2 grid as proof that capped put ratio spreads are useless. Before reopening Sub-System B, write a new mechanism note that asks the real question: under which volatility/skew/regime/suitability conditions should this structure be used, and what evidence would falsify that conditional claim?

### H-G1: Signed-OI Gamma Proxy Validity

- **Family**: `gamma`
- **Status**: `parked`
- **Statement**: A signed-OI gamma proxy aggregated from OPRA open interest and self-computed Greeks carries economic signal: high positive proxy days should exhibit attenuated realized intraday volatility.
- **Economic rationale**: Positive aggregate dealer-style gamma exposure can damp realized volatility through hedging flows, while negative gamma can amplify moves. Higanbana cannot claim true dealer inventory yet, so this is a proxy-validity hypothesis.
- **Testable predictions**:
  - Proxy terciles show monotonic or sign-consistent realized variance differences.
  - The relationship survives across at least 10 dates and at least 3 regimes.
  - Coverage passes the pre-registered v2 policy without retroactively passing v1.
- **Validation criteria**: `GAMMA_AGGREGATION_VALIDATION_POLICY.md` v2, dual raw-row and bucket-weighted coverage reporting, a validated 12-date regime-set manifest, timestamp discipline, stability, economic-sign validation, and no strategy use before data-validity pass.
- **Falsification criteria**: H-G1 is killed if there is no monotonic or sign-consistent relation between proxy tercile and realized 10:00-15:45 SPY variance across the pre-registered multi-regime date set.
- **Current evidence**: One-day 2024-01-03 gamma diagnostic is E1 diagnostic and blocked. The 12-date H-G1.4 diagnostic is also E1 and `ยังสรุปไม่ได้`: stability, timestamp discipline, economic sign, and search-log gates pass, but coverage remains blocked. Raw computed-Greeks rate is `0.622771` versus the `0.70` gate, underlying join rate is `0.842449` versus the `0.95` gate because two March 2023 dates lack local SPY bars, and required-bucket coverage fails on 7 of 12 dates. Manifest v3 replaces the weak `2023-07-12` bucket with `2023-09-13`; H-G1.12 metadata cost gate and H-G1.13 one-day OI download are complete as E0 control evidence. H-G1.14 manifest-v3 diagnostic is E1 and still `ยังสรุปไม่ได้`: raw-row coverage passes (`computed_greeks_rate=0.740255`, `underlying_join_rate=1.0`, `open_interest_join_rate=0.989369`), timestamp/stability/economic-sign/search-log gates pass, but bucket-weighted coverage fails on five date/bucket cells. H-G1.15 then diagnosed those five failed buckets as a policy-definition problem: all `55` blocked rows are opposite-right ITM rows created by moneyness-only buckets, while minimum computed OI-notional share remains `0.880098`. H-G1.17 no-paid policy comparison is E1 and still `ยังสรุปไม่ได้`: candidate B `side_aware_required_bucket` passes coverage review across 10/10 dates and is recommended for separate adoption review. H-G1.18 adopts candidate B as `h_g1_required_bucket_policy_v3_side_aware` for the next diagnostic rerun only. H-G1.19 then passes the side-aware data-validity diagnostic with status `pass_diagnostic_only`: 10 dates, 2,822 quote rows, 2,089 computed Greeks rows, raw-row coverage, side-aware required-bucket coverage, timestamp discipline, stability, economic-sign, and search-log gates pass, with no network, no paid data, no strategy PnL, and `strategy_use_allowed=false`. H-G1.20 acceptance blocker review records six hard blockers and one soft blocker before any strategy use. H-G1.21 pre-registers the strategy-ablation design as E0 control evidence before PnL review. H-G1.22 then runs that preregistered ablation as E1 `complete_underpowered`: only 2 of 90 baseline closed trades intersect the gamma-proxy date set (`2023-10-27`, `2024-12-18`), all three gamma-filtered variants collapse to 0 active trades, MinTRL/PSR and big-day dependency are blocked by insufficient observations, and no strategy/paper-trading approval is allowed. H-G1.23 parks H-G1 pending a separate sample-expansion plan and returns active implementation to News-Unblock N.7. H-G1.24a no-paid local-cache overlap scan found 0 additional baseline trade dates with local quote, local SPY bar, and local OI files beyond the current 2-date gamma intersection, so MinTRL/PSR remains blocked and H-G1 stays parked. H-G1 remains E1 proxy-validity/underpowered strategy-ablation evidence only.
- **Conclusion**: `ยังสรุปไม่ได้`.

- **H-G1.16 update**: `docs\H_G1_BUCKET_POLICY_REVIEW.md` and `experiments\h_g1_bucket_policy_review_preregistration.json` are now E0 control evidence. They lock current v2 moneyness-only, side-aware required-bucket, and OI/gamma-notional coverage candidates before any rerun. H-G1 remains blocked for NOVI/net-gamma strategy use pending a no-paid policy-comparison diagnostic.
- **H-G1.17 update**: `reports\diagnostics\h_g1_bucket_policy_comparison.json` is E1 policy-review evidence. Candidate A current v2 remains blocked with 5 failures, candidate B side-aware required-bucket passes coverage review with 0 failures, and candidate C notional-weighted remains blocked with 1 failure plus 5 warnings. Next safe action is an explicit side-aware policy-adoption artifact and diagnostic rerun under that policy; do not treat the comparison as strategy validation.
- **H-G1.18 update**: `docs\H_G1_SIDE_AWARE_BUCKET_POLICY_ADOPTION.md` and `experiments\h_g1_side_aware_bucket_policy_adoption.json` adopt candidate B only for the next diagnostic rerun. The adoption forbids strategy use, paid data, new dates, new OI files, new option quotes, and strategy-PnL selection.
- **H-G1.19 update**: `reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v3_side_aware.json` is E1 data-validity evidence. It passes with status `pass_diagnostic_only` under policy id `h_g1_required_bucket_policy_v3_side_aware`, but this does not validate strategy edge. Next safe action is a strategy-independent acceptance blocker review before any NOVI/net-gamma strategy filter.
- **H-G1.20 update**: `reports\diagnostics\h_g1_acceptance_blocker_review.json` is E1 acceptance-blocker evidence. It keeps H-G1 at `ยังสรุปไม่ได้` and forbids strategy use, paper trading, and NOVI/net-gamma filter claims until a pre-registered strategy ablation provides search log/DSR, MinTRL/PSR, implementable PnL, big-day dependency, and proxy-caveat handling.
- **H-G1.21 update**: `experiments\h_g1_gamma_strategy_ablation_preregistration.json` and `docs\H_G1_GAMMA_STRATEGY_ABLATION_PREREGISTRATION.md` are E0 control evidence. They lock the no-paid strategy-ablation design before any strategy PnL review. Next safe action is implementing the ablation runner against this artifact; do not add variants, tune OOS, buy data, approve paper trading, or claim true market-maker net gamma.
- **H-G1.22 update**: `reports\experiments\h_g1_gamma_strategy_ablation_summary.json` is E1 underpowered strategy-ablation evidence. The test used no paid data and no network, but only 2 baseline trades intersected gamma-proxy dates, and every gamma-filtered variant had 0 active trades. Next safe action is a decision to park H-G1, write a separate sample-expansion decision, or return to News-Unblock N.7; do not reuse H-G1.22 as a trading gate.
- **H-G1.23 update**: `experiments\h_g1_post_ablation_decision.json` and `docs\H_G1_POST_ABLATION_DECISION.md` park H-G1 pending a separate sample-expansion plan. H-G1 is not falsified, but it is not strategy-ready; no gamma filter, paid data from H-G1.22 alone, paper trading approval, or true market-maker net-gamma claim is allowed. Active implementation returns to News-Unblock N.7.
- **H-G1.24 update**: `experiments\h_g1_sample_expansion_plan.json` and `docs\H_G1_SAMPLE_EXPANSION_PLAN.md` pre-register the sample-expansion requirements before H-G1 can reopen. The only allowed H-G1 next step from this artifact is a no-paid local-cache overlap scan; paid data, strategy use, paper trading, and true net-gamma claims remain forbidden.
- **H-G1.24a update**: `reports\diagnostics\h_g1_local_cache_overlap_scan.json` is E0 no-paid scan evidence. It found no additional no-paid gamma-ready baseline trade dates beyond `2023-10-27` and `2024-12-18`, so the projected no-paid gamma-ready intersection remains 2. H-G1 remains parked; do not run a metadata cost check, paid download, new gamma ablation, strategy use, paper trading, or true net-gamma claim from this scan.

### H-L1: LLM News Measurement

- **Family**: `llm_news`
- **Status**: `active_blocked`
- **Statement**: LLM sentiment, market-impact, and volatility-relevance scores over timestamp-clean pre-entry news are stable across repeated calls/prompt families and add information beyond VIX plus macro calendar.
- **Economic rationale**: Language models may compress qualitative news context into continuous sentiment/impact/volatility scores that deterministic calendars cannot capture, but only if stability and contamination controls pass first.
- **Testable predictions**:
  - Repeated calls have acceptable dispersion for the selected prompt family.
  - Masking/anonymization reduces event memorization without destroying signal.
  - Scores correlate with same-day realized volatility or adverse tails after controlling for VIX and macro calendar.
- **Validation criteria**: Real timestamp-clean news cases, prompt-family comparison, 5-call stability where cost allows, contamination probe, model/cutoff/fetch metadata, and incremental information tests before any strategy ablation.
- **Falsification criteria**: H-L1 is killed or parked if real cases remain unavailable, parse validity is unreliable, repeated-call dispersion is too high, or scores add no information beyond VIX/macro baselines.
- **Current evidence**: `docs\LLM_MEASUREMENT_EXPERIMENT_DESIGN.md` is E0 design evidence and L.7 `reports\experiments\h_l1_macro_event_proxy_baseline_summary.json` is E1 deterministic macro/VIX baseline evidence. L.7 is not LLM/news evidence; it sets the incremental-information baseline that future real-news or LLM scores must beat. Live execution remains blocked until real timestamp-clean news exists.
- **Conclusion**: `ยังสรุปไม่ได้`.

- **User decision 2026-07-06**: News-Unblock should actively evaluate other timestamp-clean real-news source paths instead of waiting only on GDELT. No live LLM prompt research may run until real headlines, publication/fetch timestamps, decision-time discipline, parser output, and canonical import audit pass.

### H-L2: LLM Price-Input Exit Assistance

- **Family**: `llm_price`
- **Status**: `proposed`
- **Statement**: LLM prompts fed only chronological price/quote context may improve exit timing versus fixed TP/SL rules.
- **Economic rationale**: A model might summarize intraday price/quote context into a dynamic exit assessment, but this must be separated from H-L1 and tested against strict chronological controls.
- **Testable predictions**:
  - Parse validity stays above the pre-registered threshold.
  - Any improvement survives ablation against fixed TP/SL grids.
  - No future same-day aggregate or post-decision data enters the prompt.
- **Validation criteria**: Separate pre-registration, strict timestamp controls, search log, cost guard, and no mixing with news/sentiment prompts.
- **Falsification criteria**: H-L2 is killed or parked if parse validity is below threshold, chronological controls cannot be proven, or cost/latency makes the branch impractical.
- **Current evidence**: `docs\H_L2_PRICE_INPUT_DESIGN.md` is E0 design evidence. The branch remains dormant; no live research run exists.
- **Conclusion**: `ยังสรุปไม่ได้`.

### H-L3: Market-Outcome Text Filter vs Semantic Filter

- **Family**: `llm_news`
- **Status**: `active_blocked`
- **Statement**: A text filter trained on timestamp-clean SPY market outcomes after the decision time reduces strategy tail loss and adds information beyond semantic sentiment plus VIX and macro-calendar controls.
- **Economic rationale**: A market-outcome label may teach the model which language precedes actual SPY downside rather than merely whether the language sounds positive or negative. The SMARTyBERT paper motivates this construct, but its stock-level next-day residual-return labels and validation-tuned aggregation thresholds cannot be copied directly into a same-day SPY 0DTE test.
- **Testable predictions**:
  - Market-based scores predict post-decision SPY downside or adverse excursion better than semantic sentiment on untouched chronological data.
  - The market-based gate improves ES99 and worst-day loss without reducing active trades below a credible sample.
  - Any benefit survives implementable costs, DSR, big-day dependency, and separate Sub-System A/B ablations.
- **Validation criteria**: Use real timestamp-clean news; create SPY-specific labels after the applicable decision time; use chronological train/validation/test splits; compare quantitative-only, semantic-only, market-based-only, and both combined controls; freeze thresholds on validation data; separate the 09:35 ORB test from a 10:00 delayed-entry branch; report ES99 uncertainty and MinTRL/PSR/DSR where applicable.
- **Falsification criteria**: Park or kill H-L3 if it adds no information beyond semantic/VIX/macro controls, fails untouched chronological data or implementable-cost tests, leaves too few tail observations, or cannot prove timestamp and label chronology.
- **Current evidence**: Hypothesis registration only. No model training, live LLM call, strategy ablation, or research result exists.
- **Conclusion**: `ยังสรุปไม่ได้`.
