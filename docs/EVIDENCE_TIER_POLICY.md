# Evidence Tier Policy

## Purpose
This policy prevents Higanbana reports from claiming strategy acceptance before the evidence is strong enough and linked to a registered hypothesis.

## Required Metadata For Top-Level Research Summaries
Every new top-level research summary under `reports\baselines\`, `reports\experiments\`, or `reports\diagnostics\` should include:

- `hypothesis_id`: hypothesis id from `experiments\hypothesis_registry.json`.
- `evidence_tier`: one of `E0`, `E1`, `E2`, or `E3`.
- `tier_blockers`: list of missing evidence gates that prevent the report from moving to the next tier.

Legacy summaries that were written before this policy may be reported as migration warnings, but they must not claim acceptance-grade evidence.

## Tier Definitions
| Tier | Meaning | Allowed Claim |
|:--|:--|:--|
| `E0` | Design, scaffold, smoke test, synthetic prompt run, or operational dry run | No edge claim |
| `E1` | Diagnostic backtest or feasibility evidence with known blockers | `ยังสรุปไม่ได้`, `ไม่ผ่าน`, or diagnostic-only |
| `E2` | Research acceptance candidate with registered hypothesis, chronological discipline, MinTRL/PSR/DSR handling, implementable PnL, big-day check, and regime coverage | May claim `ผ่าน` for scoped operational validation |
| `E3` | Live/paper forward evidence after E2, with monitored operational behavior | May support broader deployment review |

## Hard Blocks
The validator must block:

- Any summary with `hypothesis_id` that is not present in the registry.
- Any summary with invalid `evidence_tier`.
- Any summary that claims `ผ่าน`, `accepted`, `approved_for_operational_validation`, or equivalent strategy acceptance while `evidence_tier` is missing, `E0`, or `E1`.
- Any `E0` or `E1` summary with empty `tier_blockers`.

## Transitional Rule
Old summaries without the three metadata fields are warnings unless they make an acceptance claim. New experiment runners should write the fields at creation time. After migration, the project can switch the validator to strict mode and fail missing metadata on all top-level summaries.
