# Technical DD Remediation Status

**Updated**: 2026-07-12
**Audience**: Fable 5 review and future Codex sessions

## Current Summary

Fable 5 verified Workstream 1 hermetic clean clone (`535/535`) on 2026-07-10. Workstream 1 is complete as of 2026-07-12:

- The interim Google Drive backup restored 6,785 files / 31,794,213,413 bytes into an isolated temporary directory with zero path/size differences.
- Restored-copy `verify_data_integrity.py` passed 43 dataset checks and 6,626 supplemental dual-hash checks with zero blockers.
- The historical aggregate pilot snapshot is retained and superseded by the later same-day snapshot that matches the restored directory.
- The two 2024-06-13 exit-check files are resolved as `content_verified_envelope_variance`; their historical container hashes remain immutable.
- A physical off-site copy remains planned when media arrives, but is no longer a WS1 blocker.

On 2026-07-12, the user lifted the DD purchase freeze because paid data is re-purchasable, canonical hashes are preserved, and the interim backup was restored and verified. Purchases remain bounded by `docs\FABLE5_UPGRADE_PROPOSAL.md` section 5. The user also approved retention option 1 and the first dry-run scope. The dry run found zero eligible files and performed no archival, so WS5 is complete under the tracker.

## Completed Or In Progress

| Area | Status | Evidence |
|:--|:--|:--|
| Clean-clone hermetic tier | Locally and remotely green | GitHub Actions run `29002864982` attempt 2; latest local WS5 hermetic run: 587 tests |
| Backup/restore docs | Written | `docs\BACKUP_AND_RESTORE.md` |
| Paid-data integrity checker | Implemented; blocker found | `scripts\verify_data_integrity.py`, `reports\diagnostics\data_integrity_mismatch_review_2026_07_09.md` |
| Restore rehearsal | Complete; physical copy is follow-up | `reports\diagnostics\interim_restore_rehearsal_2026_07_12.md` |
| Databento checksum mismatch diagnosis | Complete; aggregate blocker resolved by supersession | `reports\diagnostics\interim_restore_integrity_2026_07_12.json` |
| OPRA stat-type hermetic mapping | Complete | `scripts\probe_databento_opra_statistics.py`, `tests\test_probe_databento_opra_statistics.py` |
| H-A2.64 cache inventory | Complete E0 | `reports\data_cost\h_a2_targeted_geometry_cache_inventory_and_cost_plan.json` |
| Two-zone `lib/` foundation | Complete | `lib\io.py`, `timestamps.py`, `guardrails.py`, `search_log.py`, `report.py`, `regime_inputs.py`, `statistics.py` and hermetic unit tests |
| Helper drift audit | Complete; findings reported | `scripts\audit_helper_drift.py`, state-audit test, fixture-pipeline step, `reports\diagnostics\helper_drift_audit.json` |
| Locked gate manifest | Complete | `experiments\locked_gates.jsonl`, `scripts\validate_locked_gates.py`, `docs\LOCKED_GATE_POLICY.md` |
| Golden statistics anchors | Implemented | `lib\statistics.py`, `tests\test_statistics_golden.py` |
| New-script `lib/` usage audit | Complete | `config\new_code_scripts.json`, `scripts\audit_new_script_lib_usage.py`, fixture-pipeline/readiness integration, `reports\diagnostics\new_script_lib_usage_audit.json` |
| E2 adversarial-review gate | Implemented | `scripts\evaluate_research_acceptance.py`, `tests\test_evaluate_research_acceptance.py` |
| OPRA statistics boundary schema | Complete | Dataset/schema, required columns, stat-type mapping, and OPEN_INTEREST are validated before probe research use |
| Report retention policy | Approved; dry run complete | `User-approved=true`; option 1 selected; zero files qualified under cutoff 2026-06-30; no archival, move, deletion, branch, or history rewrite performed |
| Wiki citation hash audit | Complete for active preregistrations | 2 active artifacts and 9 citations pass artifact/wiki SHA-256 validation |
| Governance epoch tagging | Complete | Manifest validation plus annotated tag `technical-dd-remediation-ws5-2026-07-11` |

## Current Findings For Fable 5

- `scripts\audit_helper_drift.py` reports `pass_with_findings` with `95` divergent helper copies across the measured helper set. This is a measured DD finding, not an automatic migration request.
- `experiments\locked_gates.jsonl` currently seeds three active/locked governance gates. It is intentionally a start, not a claim that every historical preregistration has been backfilled.
- `AGENTS.md` now requires user or Fable 5 review before changing a locked preregistration artifact or locked validator.
- `tests\test_statistics_golden.py` anchors the current convention: population Sharpe/skewness, raw population kurtosis, left-tail expected shortfall, and Black-Scholes call/put price/delta/gamma.
- `scripts\audit_wiki_citation_hashes.py` reports `pass` for 2 active preregistrations and 9 wiki citations. Locked/frozen artifacts were not rewritten; companion hashes bind their current artifact SHA-256 and cited wiki SHA-256 values.
- `scripts\audit_new_script_lib_usage.py` reports `pass` with `0` new scripts bypassing shared `lib/` helpers.
- `scripts\evaluate_research_acceptance.py` now requires an adversarial/refutation review artifact before any E2 candidate can pass the acceptance gate.
- `scripts\validate_governance_epochs.py` reports `pass` for 4 governance epochs. WS1 is complete; the physical off-site copy is a non-blocking follow-up.
- WS3 is complete: future code must use `lib/`; existing H-A2 callers remain frozen, and new callers use `lib\regime_inputs.py` instead of importing `run_m5_regime_filter_sensitivity.py`.
- WS4 now also has a three-entry manifest floor and CI enforces the `Agent: model/version` trailer on every `main` push.
- WS5 is complete under the tracker. The approved dry-run manifest has zero eligible entries. Any future non-empty archival remains a separate reviewed step.
- `reports\diagnostics\databento_checksum_mismatch_diagnosis_2026_07_10.md` preserves the historical bit-level mismatch evidence. The later canonical comparison resolves the two files as content-equivalent despite metadata/container variance; the local duplicates still match the current containers, not the unavailable originals.

## Remaining Boundaries

- Do not treat the freeze lift as approval for broad calendar buying or a bypass of the section 5 decision tree.
- Databento metadata/download actions are allowed only when the section 5 decision tree, named hypothesis gap, live cost estimate, selected-key cap, and experiment-specific preregistration pass. The freeze lift does not approve live LLM research, unrestricted GDELT retries, broker orders, paper trading, or E2 claims.
- Latest broad verification: a clean clone passed standalone tracker validation with the expensive tier listed under `unverified` and passed 592 hermetic tests. Local state-audit passed 157 tests; full discovery passed 749 tests, with the recursive fixture-pipeline test skipped while the fixture pipeline was run separately and passed. Strict `--run-expensive` validation passes with all WS1-WS5 claims verified.

## Next Local Remediation Candidates

1. Review the staged H-A2 2022 H2 stress-plan approval amount before any paid action.
2. If a later retention cutoff yields eligible files, prepare a new exact dry-run manifest for review before any move.
3. When external media arrives, create the non-blocking physical off-site copy and record a second restore rehearsal.
