# H-G1 Side-Aware Bucket Policy Adoption

## Status
- **Hypothesis**: H-G1
- **Artifact status**: adopted for next diagnostic rerun only
- **Created**: 2026-07-03
- **Adopted policy id**: `h_g1_required_bucket_policy_v3_side_aware`
- **Adopted candidate**: `candidate_b_side_aware_required_bucket`
- **Machine-readable artifact**: `experiments\h_g1_side_aware_bucket_policy_adoption.json`

This artifact adopts the side-aware required-bucket policy for the next H-G1 diagnostic rerun only. It does not make H-G1 pass, does not validate a trading rule, and does not allow NOVI/net-gamma strategy use.

## Source-Bounded Rationale
The local LLM Wiki describes market-maker net gamma as a reconstructed position-and-Greeks variable. It depends on option positions, Greeks, moneyness buckets, and scaling conventions; it is not directly observed trade intention. Current Higanbana data has OPRA open interest and self-computed Greeks, but no dealer/customer side and no vendor Greeks.

H-G1.15 found that all 55 blocked rows inside the five manifest-v3 failed buckets were opposite-right ITM rows created by moneyness-only bucket definitions. H-G1.17 then compared three pre-registered coverage policies on the same manifest-v3 rows, with no paid data, no new dates, and no strategy PnL. Candidate B passed coverage review across 10/10 dates and directly targets the diagnosed mechanism.

The side-aware policy is therefore adopted because it aligns pass/fail rows with the option side implied by each required bucket. It does not solve the deeper market-maker inventory limitation, so H-G1 remains a proxy-validity diagnostic until a separate diagnostic rerun passes all gates.

## Adopted Required-Bucket Rules
- `otm_put`: only put rows with `moneyness < 0.995` control pass/fail.
- `otm_call`: only call rows with `moneyness > 1.005` control pass/fail.
- `atm`: call and put rows with `0.995 <= moneyness <= 1.005` control pass/fail.
- Opposite-right ITM rows remain reported in diagnostic fields and are excluded only from required-bucket pass/fail.

## Required Gates For The Next Diagnostic
- Use manifest-v3 rows only.
- No network call, paid data, new dates, new option quotes, or new OI files.
- No strategy PnL selection.
- Required side-aware bucket must be present.
- Side-aware computed row rate must be at least `0.60`.
- Side-aware computed OI-notional share must be at least `0.80`.
- Retained absolute gamma-proxy share must be at least `0.80` when computable/reportable.
- Timestamp discipline, raw-row coverage, stability, economic-sign, and search-log gates must remain visible in the rerun.

## Allowed Next Action
Rerun the H-G1 gamma diagnostic on manifest-v3 rows under policy id `h_g1_required_bucket_policy_v3_side_aware`.

## Forbidden Claims
- H-G1 pass.
- Strategy validation from a coverage-policy adoption.
- NOVI/net-gamma strategy filter readiness.
- True market-maker net gamma from OI-only signed gamma.
- Paid data, new dates, or replacement OI justified by this artifact alone.
- Policy superiority based on strategy PnL.

## Evidence Tier
This artifact is E0/E1 control evidence. H-G1 remains `active_blocked` until the next diagnostic rerun passes under the adopted policy and still must not be treated as deployable strategy evidence without later research acceptance.

