# Technical DD Remediation Status

**Updated**: 2026-07-09  
**Audience**: Fable 5 review and future Codex sessions

## Current Summary

Technical DD Workstream 1 is locally implemented but not fully closed. The remaining closure item depends on external restore media:

- The user will order a flash drive.
- After the drive is available, run the physical restore rehearsal described in `docs\BACKUP_AND_RESTORE.md`.
- The two Databento checksum mismatches remain unresolved until restore/revalidation/rebaseline is explicitly completed.
- Do not silently overwrite historical hashes or claim Workstream 1 complete before that external step.

While this external blocker is parked, Codex may continue `$0` local remediation that does not require paid data, provider metadata calls, live LLM calls, broker access, or new hypothesis expansion.

## Completed Or In Progress

| Area | Status | Evidence |
|:--|:--|:--|
| Clean-clone hermetic tier | Locally and remotely green | GitHub Actions run `29002864982` attempt 2; latest local hermetic run: 538 tests |
| Backup/restore docs | Written | `docs\BACKUP_AND_RESTORE.md` |
| Paid-data integrity checker | Implemented; blocker found | `scripts\verify_data_integrity.py`, `reports\diagnostics\data_integrity_mismatch_review_2026_07_09.md` |
| Restore rehearsal | External blocker | Waiting for user flash drive |
| H-A2.64 cache inventory | Complete E0 | `reports\data_cost\h_a2_targeted_geometry_cache_inventory_and_cost_plan.json` |
| Two-zone `lib/` foundation | Started | `lib\environment.py`, `lib\integrity.py`, `lib\io.py` |
| Helper drift audit | Implemented; findings reported | `scripts\audit_helper_drift.py`, `reports\diagnostics\helper_drift_audit.json` |
| Locked gate manifest | Seeded | `experiments\locked_gates.jsonl`, `scripts\validate_locked_gates.py` |
| Golden statistics anchors | Implemented | `lib\statistics.py`, `tests\test_statistics_golden.py` |
| Report retention policy | Proposed only | `docs\REPORT_RETENTION_POLICY_PROPOSAL.md` |
| Wiki citation hash audit | Implemented; missing hashes measured | `scripts\audit_wiki_citation_hashes.py`, `reports\diagnostics\wiki_citation_hash_audit.json` |

## Current Findings For Fable 5

- `scripts\audit_helper_drift.py` reports `pass_with_findings` with `92` divergent helper copies across the measured helper set. This is a measured DD finding, not an automatic migration request.
- `experiments\locked_gates.jsonl` currently seeds three active/locked governance gates. It is intentionally a start, not a claim that every historical preregistration has been backfilled.
- `AGENTS.md` now requires user or Fable 5 review before changing a locked preregistration artifact or locked validator.
- `tests\test_statistics_golden.py` anchors the current convention: population Sharpe/skewness, raw population kurtosis, left-tail expected shortfall, and Black-Scholes call/put price/delta/gamma.
- `scripts\audit_wiki_citation_hashes.py` reports `5` existing wiki citations with missing embedded hashes and no missing source file under the current local wiki root.

## Do Not Claim Yet

- Do not claim Technical DD Workstream 1 complete.
- Do not lift the paid-data and hypothesis-expansion freeze.
- Do not call Databento metadata, download paid data, call live LLM research APIs, run GDELT retries, request broker data/orders, approve paper trading, or claim E2 evidence from the current remediation work.

## Next Local Remediation Candidates

1. Expand `locked_gates.jsonl` to additional active locked gates after Fable/user review confirms the seed format.
2. Backfill `wiki_citation_hashes` for active preregistrations where Fable/user agrees the audit format is correct.
3. Add ingest-time OPRA statistics schema validation at the Databento boundary.
4. Decide whether to implement the report-retention proposal; first implementation must be dry-run only.
