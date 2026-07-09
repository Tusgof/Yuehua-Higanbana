# H-G1 Bucket Policy Review

## Status
- **Hypothesis**: H-G1
- **Artifact status**: pre-registered review, not adopted policy
- **Created**: 2026-07-03
- **Controlling policy remains**: `docs\GAMMA_AGGREGATION_VALIDATION_POLICY.md` v2
- **Machine-readable pre-registration**: `experiments\h_g1_bucket_policy_review_preregistration.json`

This document locks the next H-G1 policy-review step before any rerun, paid data pull, replacement date, or NOVI/net-gamma strategy-use claim. It does not make H-G1 pass.

## Source-Bounded Rationale
The local LLM Wiki describes market-maker net gamma as a position-and-Greeks reconstruction problem, not a directly observed trade intention. Current Higanbana data has OPRA open interest and self-computed Greeks, but no dealer/customer side and no vendor-calculated Greeks.

H-G1.15 found a narrower implementation issue: all 55 blocked rows inside the five manifest-v3 failed buckets are opposite-right ITM rows created by moneyness-only bucket definitions. This means the remaining v3 blocker is policy definition, not OI join, timestamp discipline, or paid-data availability.

## Source Evidence
- `docs\GAMMA_AGGREGATION_VALIDATION_POLICY.md`
- `docs\H_G1_POLICY_V2_1_REVIEW.md`
- `reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v3.json`
- `reports\diagnostics\h_g1_manifest_v3_bucket_failure_diagnostic.json`
- `data\derived\spy_0dte\h_g1_gamma_regime\option_quote_enriched_manifest_v3_snapshot.jsonl`

Key H-G1.15 facts:

| Metric | Value |
|---|---:|
| Failed manifest-v3 buckets | 5 |
| Blocked rows in failed buckets | 55 |
| Opposite-right blocked row share | 1.0 |
| Minimum failed-bucket computed OI-notional share | 0.880098 |
| Minimum failed-bucket retained gamma-proxy share | 1.0 |
| Weak-notional failure count | 0 |

## Review Question
Should H-G1 required-bucket coverage continue using moneyness-only buckets, or should the diagnostic rerun evaluate a pre-registered bucket policy that separates expected option side from opposite-right ITM rows?

This review is allowed to answer only a coverage-policy question. It is not allowed to answer whether H-G1 is a profitable strategy.

## Candidate Policies To Compare
### Candidate A: Current v2 Moneyness-Only Gate
- Keep `otm_put`, `atm`, and `otm_call` buckets defined only by `strike / underlying_price`.
- Keep required-bucket computed row-rate floor at `0.60`.
- Keep combined computed OI-notional floor at `0.80`.
- Treat this as the baseline policy.

### Candidate B: Side-Aware Required-Bucket Gate
- `otm_put` pass/fail rows include only put rows with `moneyness < 0.995`.
- `otm_call` pass/fail rows include only call rows with `moneyness > 1.005`.
- `atm` pass/fail rows include both calls and puts with `0.995 <= moneyness <= 1.005`.
- Opposite-right ITM rows remain reportable in separate diagnostic fields, but they do not control required-bucket pass/fail.
- Minimum gates remain:
  - required side-aware bucket present,
  - side-aware computed rate >= `0.60`,
  - side-aware computed OI-notional share >= `0.80`,
  - no timestamp-discipline failure.

### Candidate C: OI/Gamma-Notional Coverage Gate
- Keep the moneyness bucket labels for reporting.
- Required-bucket pass/fail emphasizes economic exposure represented by computed rows:
  - computed OI-notional share >= `0.80`,
  - retained absolute gamma-proxy share >= `0.80`,
  - row-rate below `0.60` becomes a warning only when both notional gates pass.
- Opposite-right ITM rows remain reportable and must be counted separately.

## Acceptance And Rejection Criteria
### Policy Review Can Pass Only If
- The rerun uses manifest v3 and existing local data only.
- No new paid data, replacement date, or strategy-PnL selection enters the policy choice.
- All candidate policies report the same source rows and same failed-bucket lineage.
- Candidate B and Candidate C both preserve timestamp discipline and raw-row coverage reporting.
- The chosen candidate has a clear mechanism reason, not only a better pass rate.
- The final output labels the result as `policy_review_only`.

### Policy Review Must Fail Or Stay Blocked If
- The rerun changes source dates, OI inputs, quote inputs, or SPY bar inputs.
- Any candidate hides opposite-right ITM rows instead of reporting them.
- Any candidate claims true dealer net gamma from OI-only data.
- Any candidate selects thresholds after seeing strategy PnL.
- Any candidate upgrades H-G1 above E1 without a later strategy-independent validation report.

## Rerun Plan
1. Validate `experiments\h_g1_bucket_policy_review_preregistration.json`.
2. Run a no-paid policy-review script against:
   - `reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v3.json`
   - `reports\diagnostics\h_g1_manifest_v3_bucket_failure_diagnostic.json`
   - `data\derived\spy_0dte\h_g1_gamma_regime\option_quote_enriched_manifest_v3_snapshot.jsonl`
3. Compare Candidate A, B, and C on the same manifest-v3 rows.
4. Write a JSON/Markdown policy-review report under `reports\diagnostics\`.
5. Keep H-G1 blocked unless the review only authorizes a separate diagnostic rerun under an explicitly adopted policy version.

## Forbidden Claims
- Do not say H-G1 has passed.
- Do not say policy v2.1 or any new policy has been adopted by this document alone.
- Do not use NOVI/net-gamma as a strategy filter.
- Do not say OI-only signed gamma is true market-maker net gamma.
- Do not buy more OI or option quote data for H-G1 from this artifact alone.
- Do not treat side-aware or notional-weighted coverage as strategy validation.

## Next Safe Action
Implement and run the no-paid H-G1 bucket-policy comparison script using the locked pre-registration. If that script produces a real diagnostic result, write the next research log as `017-higanbana-...` unless it is only a minor correction to an existing log.
