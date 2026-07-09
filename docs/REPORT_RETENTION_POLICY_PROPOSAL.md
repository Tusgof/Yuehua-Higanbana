# Report Retention Policy Proposal

**Status**: Proposal only. Do not archive, delete, rewrite, or move existing reports until the user approves this policy.

## Goal

Keep decision-grade evidence durable in git while preventing bulk diagnostics from making future review and agent context management harder.

## Proposed Retention Classes

| Class | Examples | Default Storage | Retention |
|:--|:--|:--|:--|
| Decision record | preregistrations, paid download decisions, falsification decisions, policy adoptions | main repo | permanent |
| Acceptance-grade evidence | E2+ strategy reports, launch gates, paper/dry-run approval artifacts | main repo | permanent |
| Current-state audit | latest readiness, cost, integrity, launch, helper-drift, locked-gate reports | main repo | keep latest plus material milestones |
| Bulk diagnostics | repeated exploratory summaries, search-log-heavy local probes, stale generated markdown mirrors | archive branch/LFS/external archive after approval | retain by audit index, not necessarily main branch |
| Raw paid data | gitignored `data/` with registry checksums | external backup + local data tree | permanent while hypothesis may be reproduced |

## Approval Gate

Before implementation, the user must approve:

1. Archive destination: git branch, Git LFS, external drive, or another repository.
2. First archive scope: exact file list or report class.
3. Restore test: confirm archived files can be found from the audit index.

## Rules

- Do not delete decision records.
- Do not rewrite existing reports to make history cleaner.
- Do not archive artifacts that are cited by active validators unless the validator points to a durable index.
- Keep a machine-readable audit index as the source of truth for archived diagnostics.
- The first implementation must be dry-run only and list planned moves without changing files.

## Current Recommendation

Do not implement retention movement yet. First finish Technical DD Workstream 1 closure, complete the golden statistics anchors, and let Fable 5 review the proposed classes.
