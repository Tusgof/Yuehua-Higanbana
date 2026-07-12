# Report Retention Policy Proposal

- **Policy status**: `approved_dry_run_only`
- **User-approved**: `true`
- **Approval date**: `2026-07-12`
- **Selected destination**: `option_1_dated_archive_branch`
- **Archive branch pattern**: `archive/reports-YYYY`
- **Immutable index location**: `main`
- **First retention class**: `Bulk diagnostic`
- **First cutoff**: reports superseded on or before `2026-06-30`
- **Restore-test criterion**: every archived file must be restorable from the archive branch with SHA-256 matching the immutable JSON index on `main`
- **Archival implementation allowed**: `false`

The user approved the policy and first dry-run scope on 2026-07-12. This approval authorizes only the dry-run manifest. No report may be moved, deleted, rewritten, or archived until a separate reviewed step approves the exact manifest.

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

The selected destination is option 1. The other options remain alternatives for future policy revisions:

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

Approved for dry-run only on 2026-07-12. The first scan covers only `Bulk diagnostic` reports superseded on or before 2026-06-30. The dry-run manifest is `reports/diagnostics/report_retention_dry_run_2026_07_12.json`. Creating an archive branch, moving files, deleting files, or rewriting history still requires a separate reviewed step after the user sees that manifest.
