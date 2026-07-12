# Higanbana Backup And Restore

Higanbana is complete only when all four stores below can be restored together.

| Store | Current role | Backup requirement | Verification |
|:--|:--|:--|:--|
| Higanbana repository | Code, governance, preregistrations, reports | GitHub remote plus a second clone | `git fsck --full`; hermetic tier |
| `research_log` repository | Published Thai research notes | Its own GitHub remote plus a second clone | clean worktree, matching local/remote HEAD |
| `HIGANBANA_DATA_ROOT` | Raw, normalized, derived, and paid market data | Encrypted external disk or versioned object storage | `python scripts/verify_data_integrity.py` (container plus canonical DBN record-body hashes) |
| `HIGANBANA_WIKI_ROOT` | Methodology and cited research basis | Separate Git remote or versioned archive | repository/hash audit; cited hashes are added under Workstream 5 |

## Backup Checklist

1. Push both Git repositories and record their commit hashes.
2. Copy `HIGANBANA_DATA_ROOT` to a second physical device or versioned object store.
3. Run `python scripts/verify_data_integrity.py` before and after the copy. The command verifies immutable container hashes plus canonical DBN record-body hashes. If legacy paid downloads are not yet represented in `datasets.jsonl`, generate/refresh the local per-file registry with `python scripts/verify_data_integrity.py --write-supplemental-registry`.
4. Back up the LLM Wiki with history or a dated archive.
5. Store `config/machine.json` separately if used. It may contain paths only and must never contain credentials.
6. Keep API keys in the operating-system secret store; do not include them in backups of this repository.

## Restore Checklist

1. Clone Higanbana and the `research_log` repository into separate directories.
2. Restore the data tree and Wiki.
3. Set `HIGANBANA_DATA_ROOT`, `HIGANBANA_WIKI_ROOT`, and optionally `HIGANBANA_IBKR_PYTHON`, or create untracked `config/machine.json`.
4. Run `python scripts/run_test_tier.py hermetic`.
5. Run `python scripts/verify_data_integrity.py`.
6. Run `python scripts/run_test_tier.py state-audit`.
7. Run `python scripts/run_fixture_pipeline.py`.
8. Confirm no broker order transmission or paid download occurred during restoration.

See `docs/DATABENTO_INTEGRITY_POLICY.md` for the dual-hash rule and the restricted `content_verified_envelope_variance` disposition.

## Interim Rehearsal Record

The user-approved interim Google Drive rehearsal passed on 2026-07-12. The full `data/` tree was restored from the cloud mount into an isolated temporary directory: 6,785 files and 31,794,213,413 bytes matched with zero path/size differences, and `verify_data_integrity.py` passed 6,626 supplemental dual-hash checks with zero blockers. See `reports/diagnostics/interim_restore_rehearsal_2026_07_12.md` and `reports/diagnostics/interim_restore_integrity_2026_07_12.json`.

This closes the WS1 restore exit condition as `interim_rehearsal_completed`.

## Physical Off-Site Follow-Up

The user still plans a physical off-site copy when external media arrives. That follow-up should record:

- date and machine/VM identifier,
- restored Git commit hashes,
- data and Wiki source used,
- hermetic/state-audit/integrity results,
- missing files or manual corrections,
- final pass/fail decision.

The physical copy is a non-blocking resilience improvement after the verified cloud restore. It does not reopen WS1 unless a later integrity check fails.
