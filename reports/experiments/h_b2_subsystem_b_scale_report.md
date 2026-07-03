# H-B2 Sub-System B Simulated-Scale Diagnostic

## Status
- Hypothesis: `H-B2`
- Evidence tier: `E1`
- Conclusion: ยังสรุปไม่ได้
- Recommendation: `consider_falsification_after_mintrl_falsify_review`
- No new paid data was used.
- This report does not allow deployment or paper-trading edge claims.

## Pre-Registration
```json
{
  "manifest_path": "experiments\\h_b2_subsystem_b_scale_preregistration.json",
  "registered_at": "2026-07-03",
  "trial_count": 8,
  "validation_status": "pass"
}
```

## Scenario Results

| Scenario | Account | Wing | Eligible | Total PnL | OOS PnL | Mid PnL | Cost Drag | Drag Ratio | ES95 | MDD | Labels |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|:--|
| `account_10000_wing_5` | 10000 | 5 | 413 | -5604.56 | -3332.88 | -441.0 | 5163.56 | 11.708753 | -141.6914 | -0.588764 | under-sampled, underpowered |
| `account_25000_wing_5` | 25000 | 5 | 413 | -5604.56 | -3332.88 | -441.0 | 5163.56 | 11.708753 | -141.6914 | -0.235506 | under-sampled, underpowered |
| `account_10000_wing_10` | 10000 | 10 | 90 | -784.8 | -686.68 | 354.5 | 1139.3 | 3.213822 | -196.12 | -0.151096 | under-sampled, underpowered |
| `account_25000_wing_10` | 25000 | 10 | 412 | -5973.44 | -3866.76 | -857.5 | 5115.94 | 5.966111 | -161.4533 | -0.25023 | under-sampled, underpowered |
| `account_10000_wing_15` | 10000 | 15 | 0 | 0 | 0 | 0 | 0 | None | None | 0.0 | under-sampled, underpowered |
| `account_25000_wing_15` | 25000 | 15 | 406 | -5729.72 | -3641.04 | -702.0 | 5027.72 | 7.161994 | -168.739 | -0.240695 | under-sampled, underpowered |
| `account_10000_wing_20` | 10000 | 20 | 0 | 0 | 0 | 0 | 0 | None | None | 0.0 | under-sampled, underpowered |
| `account_25000_wing_20` | 25000 | 20 | 0 | 0 | 0 | 0 | 0 | None | None | 0.0 | under-sampled, underpowered |

## Tier Blockers

- `sample_adequacy_pending_mintrl_falsify`
- `grid_search_requires_dsr_or_fresh_validation_before_acceptance`
- `no_deployment_claim_allowed_from_simulated_scale_diagnostic`

## Diagnostics
```json
{
  "all_cost_drag_high_when_mid_positive": true,
  "positive_total_and_oos_scenarios": [],
  "wing_status_counts": {
    "10.0": {
      "closed_forced_1545": 412,
      "missing_close_quotes": 5,
      "missing_leg_close_quotes": 6,
      "structure_unavailable": 21
    },
    "15.0": {
      "closed_forced_1545": 412,
      "missing_close_quotes": 5,
      "missing_leg_close_quotes": 1,
      "structure_unavailable": 26
    },
    "20.0": {
      "closed_forced_1545": 412,
      "missing_close_quotes": 5,
      "structure_unavailable": 27
    },
    "5.0": {
      "closed_forced_1545": 413,
      "missing_close_quotes": 5,
      "missing_leg_close_quotes": 10,
      "structure_unavailable": 16
    }
  }
}
```
