# H-G1 Policy v2.1 Review Artifact

## Status
- **Hypothesis**: H-G1
- **Artifact status**: review-only, not adopted
- **Created**: 2026-07-03
- **Controlling policy remains**: `docs\GAMMA_AGGREGATION_VALIDATION_POLICY.md` v2

This artifact records the narrow policy question raised by H-G1.8/H-G1.9. It does not make the current 10-date diagnostic pass and must not be used to claim NOVI/net-gamma readiness.

## Source Evidence
- `reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v2_10date.json`
- `reports\diagnostics\h_g1_bucket_failure_diagnostic.json`
- `reports\diagnostics\h_g1_policy_manifest_decision.json`

H-G1.9 rejects policy revision alone because `2023-07-12 otm_put` has only `0.662545` computed OI-notional coverage, below the `0.80` review floor. Four other failing buckets have high computed OI-notional coverage (`0.906923` to `0.984773`) and look more like row-rate strictness than economically material missing notional coverage.

## Candidate v2.1 Rule
The candidate v2.1 coverage rule would keep raw-row reporting, but move required-bucket pass/fail emphasis to exposure-weighted coverage:

1. Required buckets remain `otm_put`, `atm`, and `otm_call`.
2. Every required bucket must be present on every candidate day.
3. Every required bucket must have computed OI-notional coverage `>= 0.80`.
4. Required-bucket row-rate below `0.60` becomes a warning, not a primary pass gate, only when computed OI-notional coverage is `>= 0.80`.
5. Combined required-bucket computed OI-notional coverage must remain `>= 0.80`.
6. Raw-row coverage gates remain reportable and cannot be hidden: underlying join rate, prior OI join rate, and computed-Greeks raw-row rate must still be shown.
7. Deep buckets remain reportable; if a deep bucket exceeds the v2 materiality rule, it must be reviewed before any pass claim.

## Why This Is Not Adopted Yet
The current 10-date diagnostic fails the candidate v2.1 rule because `2023-07-12 otm_put` is below the `0.80` computed OI-notional floor. Adopting v2.1 now would still leave H-G1 blocked, and adopting it to pass only the four high-notional row-rate failures would be a silent post-hoc policy change.

## Required Before Adoption
- Create and validate a manifest v3 replacement plan before any new paid OI pull.
- Replace or repair the weak `2023-07-12 otm_put` bucket through pre-registered date selection, not after viewing gamma results.
- Rerun H-G1 enrichment/diagnostic under the explicit v2.1 review rule.
- Preserve the v1 and v2 failures permanently in reports and decision logs.

## Forbidden Claims
- Do not say H-G1 coverage passed under v2 or v2.1.
- Do not use NOVI/net-gamma as a strategy filter.
- Do not say OI-only signed gamma is true market-maker net gamma.
- Do not buy replacement OI before a manifest v3 candidate validates and cost guard passes.
