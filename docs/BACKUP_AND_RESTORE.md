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

## Required Physical Rehearsal

The user must schedule one restore rehearsal on a second machine or isolated VM after Workstream 1 code verification. Completion requires recording:

- date and machine/VM identifier,
- restored Git commit hashes,
- data and Wiki source used,
- hermetic/state-audit/integrity results,
- missing files or manual corrections,
- final pass/fail decision.

Until that rehearsal is scheduled, backups are prepared but disaster recovery is not empirically proven.
