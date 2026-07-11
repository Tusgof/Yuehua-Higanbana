# Locked Gate Policy

## Scope

`experiments/locked_gates.jsonl` is the append-only manifest for the explicitly designated preregistration and policy-adoption gates listed in that file. It is a seed inventory of active governance locks, not a backfill claim for every historical experiment artifact.

Each active entry records immutable SHA-256 values for its decision artifact and validator. `python scripts/validate_locked_gates.py` verifies those values in the hermetic tier and fixture pipeline.

## Revising A Locked Gate

Do not edit a locked decision artifact or validator in place. A permitted revision requires all of the following:

1. Append a new JSONL entry with a new `gate_id`.
2. Set `supersedes_gate_id` to the earlier gate id.
3. Keep the same `artifact_path` and `validator_path`.
4. Record the new SHA-256 values, a non-empty `human_approval`, and `reviewed_by` as the user or Fable 5.
5. State the reason and review evidence in `notes`.

The predecessor remains in the manifest as historical evidence. The validator marks it `superseded` and verifies the hashes of only the active successor. A missing approval, reviewer, predecessor, or path match blocks the manifest.

## Engineering Rule

The commit that performs a permitted revision must follow `AGENTS.md`: review by the user or Fable 5 before merge and an `Agent: model/version` trailer. A green test suite alone is never authorization to weaken a locked gate.
