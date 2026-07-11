# Report Retention Policy Proposal

- **Policy status**: `proposed`
- **User-approved**: `false`
- **Approval date**: `null`
- **Archival implementation allowed**: `false`

No report may be moved, deleted, rewritten, or archived under this proposal until the user changes `User-approved` to `true` in a reviewed commit and selects the first archive destination and scope.

## Goal

Keep decision-grade evidence durable and easy to audit while reducing main-branch clutter from repeated generated diagnostics. This policy addresses repository navigation and agent context load; it does not rewrite Git history or claim to reduce historical repository size.

## Proposed Retention Classes

| Class | Examples | Main-branch policy | Retention |
|:--|:--|:--|:--|
| Decision record | preregistrations, policy adoptions, paid-download decisions, hypothesis kill/resurrection decisions | keep | permanent |
| Acceptance evidence | E2+ reports, paper/dry-run approvals, launch gates, adversarial reviews | keep | permanent |
| Reproduction index | dataset registry, checksums, search logs selected by a decision report, archive index | keep | permanent |
| Current-state audit | readiness, cost, integrity, launch, helper-drift, locked-gate reports | keep latest and governance-epoch snapshots | permanent for retained snapshots |
| Bulk diagnostic | superseded exploratory summaries, repeated generated mirrors, non-decision debug output | eligible only after approval and dry run | preserve through archive index and restore test |
| Paid/raw data | gitignored `data/` artifacts and canonical hashes | never place in normal Git history | preserve in local/external backup while reproducibility is required |

## Proposed Destination

Recommended first destination: a dated `archive/reports-YYYY` branch plus an immutable JSON index retained on `main`. This removes eligible files from the current tree without rewriting history. Git LFS or an external repository may be considered later, but neither is required for the first controlled archive.

The user must choose one destination before implementation:

1. Dated archive branch (recommended).
2. External drive with checksum manifest.
3. Separate archive repository.
4. Git LFS for future large artifacts only.

## Approval Gate

Approval must record all of the following:

1. `User-approved: true` and approval date.
2. Selected destination.
3. Exact first-scope file list or retention class and cutoff date.
4. Restore-test location and success criterion.

Approval of this document does not authorize automatic deletion. The first implementation after approval must be a dry-run manifest containing source path, destination path, SHA-256, retention class, reason, and inbound references. A separate reviewed step performs any move.

## Permanent Exclusions

- Never archive or delete decision records, E2+ evidence, paid-cost records, integrity records, dataset registry entries, locked-gate records, or active-validator dependencies.
- Never rewrite an existing report to make history appear cleaner.
- Never remove an artifact with an unresolved inbound reference from an active preregistration, validator, tracker, governance epoch, research log, or project-control document.
- Never use retention work to rewrite Git history.
- Never treat an archive as valid until a restore rehearsal verifies the indexed SHA-256 values.

## Proposed Review Cadence

- Review eligibility quarterly or when tracked report count grows by 500 files, whichever happens later.
- Do not archive merely because a file is old; it must be superseded, non-decision-grade, indexed, and restorable.
- Keep the archive audit index on `main` as the source of truth.

## Current Decision

Await user approval. No archival script, dry-run manifest, branch, move, deletion, or history rewrite is authorized by this proposal.
