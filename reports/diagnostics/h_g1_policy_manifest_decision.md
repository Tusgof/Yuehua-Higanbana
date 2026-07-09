# H-G1 Policy / Manifest Decision

- Status: `policy_revision_alone_rejected_manifest_v3_required`
- Conclusion: `ยังสรุปไม่ได้`
- Evidence tier: `E1`
- Paid data used: `False`
- Network used: `False`

## Decision

Four failures look like row-rate policy strictness, but 2023-07-12 otm_put keeps only 0.662545 computed OI-notional coverage; relaxing the policy alone would hide a material uncovered bucket.

Recommended next step: Draft policy v2.1 as a review artifact and create a manifest v3 replacement plan for the below-floor bucket before any new paid OI pull.

## Findings

- Failed bucket count: `5`
- All failures are Black-Scholes bracket blocks: `True`
- High-notional row-rate failures: `4`
- Below-notional-floor buckets: `1`
- Below-notional-floor list: `2023-07-12 otm_put`

## Candidate Policy Review

- Candidate name: `v2.1_review_candidate_not_adopted`
- Notional floor: `0.8`
- Row-rate treatment: `warning_not_primary_pass_gate`
- Rationale: H-G1 signal is exposure-weighted; row-rate alone can overweight low-notional rows, but notional coverage cannot excuse a material uncovered bucket.

## Forbidden Actions

- Do not claim H-G1 coverage pass.
- Do not use NOVI/net-gamma as a strategy filter.
- Do not buy replacement OI before a v3 manifest validates.
- Do not edit policy v2 to make the current 10-date set pass silently.

## Tier Blockers

- E1 diagnostic decision only
- H-G1 remains coverage-blocked
- No strategy-return MinTRL/PSR evidence
- No true dealer-side gamma inventory data
