# Governance Epoch Tagging

## Purpose

Governance epochs mark project-level rule changes that affect how later evidence should be interpreted. They are not strategy results and must not be used as proof of edge.

The controlling machine-readable record is `config\governance_epochs.json`. Selected governance epochs also receive immutable annotated Git tags, but the manifest remains the audit source because it can be validated in the hermetic tier.

## Current Rules

- Add an epoch when a policy, plan, evidence gate, or hypothesis lifecycle decision changes the meaning of future work.
- Do not rewrite old reports to fit a new epoch. New reports should cite the active epoch when relevant.
- Each epoch must include an ID, date, kind, status, description, and evidence paths.
- Evidence paths must exist in the repository unless the path is an allowed directory placeholder such as `Backup_IMPLEMENT_PLAN`.
- A tagged epoch records `git_tag` in the manifest. Tags are created only after the evidence commit exists and are pushed explicitly.
- Never move or retarget an existing governance tag. A correction requires a new epoch and a new tag.
- The Technical DD epoch remains `active_with_external_blocker` until restore rehearsal and paid-data checksum closure are complete.

## Active Epochs

- `implement-plan-v2`: hypothesis-led planning replaced legacy experiment-number sequencing.
- `gamma-policy-v2`: gamma proxy work is diagnostic-only until policy gates and strategy-ablation gates pass.
- `technical-dd-remediation-2026-07-09`: paid data and hypothesis expansion are frozen while Technical DD Workstream 1 remains open.
- `h-a2-targeted-data-plan-v1`: H-A2 targeted geometry expansion exists but is blocked from paid/metadata follow-up by the DD freeze.

## First Tag

`technical-dd-remediation-ws5-2026-07-11` marks the commit that establishes WS5 evolution-hygiene controls. It does not declare WS1 complete or lift the paid-data freeze.
