# Technical DD Remediation Status

**Updated**: 2026-07-11
**Audience**: Fable 5 review and future Codex sessions

## Current Summary

Fable 5 verified Workstream 1 hermetic clean clone (`535/535`) on 2026-07-10. Workstream 1 is still not fully closed. The remaining closure items are external restore media and the unrelated aggregate pilot checksum mismatch:

- The user will order a flash drive.
- After the drive is available, run the physical restore rehearsal described in `docs\BACKUP_AND_RESTORE.md`.
- The two 2024-06-13 exit-check files are resolved as `content_verified_envelope_variance`; their historical container hashes remain immutable.
- Do not silently overwrite historical hashes or claim Workstream 1 complete before that external step.

On 2026-07-11, the user explicitly directed WS4 gate-integrity and WS3 two-zone completion as no-paid remediation work. WS5 remains not started; the WS1 freeze remains active.

## Completed Or In Progress

| Area | Status | Evidence |
|:--|:--|:--|
| Clean-clone hermetic tier | Locally and remotely green | GitHub Actions run `29002864982` attempt 2; latest local WS3 hermetic run: 583 tests |
| Backup/restore docs | Written | `docs\BACKUP_AND_RESTORE.md` |
| Paid-data integrity checker | Implemented; blocker found | `scripts\verify_data_integrity.py`, `reports\diagnostics\data_integrity_mismatch_review_2026_07_09.md` |
| Restore rehearsal | External blocker | Waiting for user flash drive |
| Databento checksum mismatch diagnosis | Complete; blocker remains | `reports\diagnostics\databento_checksum_mismatch_diagnosis_2026_07_10.md` |
| OPRA stat-type hermetic mapping | Complete | `scripts\probe_databento_opra_statistics.py`, `tests\test_probe_databento_opra_statistics.py` |
| H-A2.64 cache inventory | Complete E0 | `reports\data_cost\h_a2_targeted_geometry_cache_inventory_and_cost_plan.json` |
| Two-zone `lib/` foundation | Complete | `lib\io.py`, `timestamps.py`, `guardrails.py`, `search_log.py`, `report.py`, `regime_inputs.py`, `statistics.py` and hermetic unit tests |
| Helper drift audit | Complete; findings reported | `scripts\audit_helper_drift.py`, state-audit test, fixture-pipeline step, `reports\diagnostics\helper_drift_audit.json` |
| Locked gate manifest | Complete | `experiments\locked_gates.jsonl`, `scripts\validate_locked_gates.py`, `docs\LOCKED_GATE_POLICY.md` |
| Golden statistics anchors | Implemented | `lib\statistics.py`, `tests\test_statistics_golden.py` |
| New-script `lib/` usage audit | Complete | `config\new_code_scripts.json`, `scripts\audit_new_script_lib_usage.py`, fixture-pipeline/readiness integration, `reports\diagnostics\new_script_lib_usage_audit.json` |
| E2 adversarial-review gate | Implemented | `scripts\evaluate_research_acceptance.py`, `tests\test_evaluate_research_acceptance.py` |
| OPRA statistics boundary schema | Implemented | `schemas\opra_statistics_boundary.schema.json`, `lib\opra_statistics_schema.py`, `tests\test_opra_statistics_schema.py` |
| Report retention policy | Proposed only | `docs\REPORT_RETENTION_POLICY_PROPOSAL.md` |
| Wiki citation hash audit | Implemented; missing hashes measured | `scripts\audit_wiki_citation_hashes.py`, `reports\diagnostics\wiki_citation_hash_audit.json` |
| Governance epoch tagging | Implemented | `config\governance_epochs.json`, `docs\GOVERNANCE_EPOCH_TAGGING.md`, `scripts\validate_governance_epochs.py` |

## Current Findings For Fable 5

- `scripts\audit_helper_drift.py` reports `pass_with_findings` with `95` divergent helper copies across the measured helper set. This is a measured DD finding, not an automatic migration request.
- `experiments\locked_gates.jsonl` currently seeds three active/locked governance gates. It is intentionally a start, not a claim that every historical preregistration has been backfilled.
- `AGENTS.md` now requires user or Fable 5 review before changing a locked preregistration artifact or locked validator.
- `tests\test_statistics_golden.py` anchors the current convention: population Sharpe/skewness, raw population kurtosis, left-tail expected shortfall, and Black-Scholes call/put price/delta/gamma.
- `scripts\audit_wiki_citation_hashes.py` reports `5` existing wiki citations with missing embedded hashes and no missing source file under the current local wiki root.
- `scripts\audit_new_script_lib_usage.py` reports `pass` with `0` new scripts bypassing shared `lib/` helpers.
- `scripts\evaluate_research_acceptance.py` now requires an adversarial/refutation review artifact before any E2 candidate can pass the acceptance gate.
- `scripts\validate_governance_epochs.py` reports `pass` for 4 governance epochs. The Technical DD epoch remains `active_with_external_blocker` until the flash-drive restore/checksum closure is done.
- WS3 is complete: future code must use `lib/`; existing H-A2 callers remain frozen, and new callers use `lib\regime_inputs.py` instead of importing `run_m5_regime_filter_sensitivity.py`.
- WS4 now also has a three-entry manifest floor and CI enforces the `Agent: model/version` trailer on every `main` push.
- `reports\diagnostics\databento_checksum_mismatch_diagnosis_2026_07_10.md` preserves the historical bit-level mismatch evidence. The later canonical comparison resolves the two files as content-equivalent despite metadata/container variance; the local duplicates still match the current containers, not the unavailable originals.

## Do Not Claim Yet

- Do not claim Technical DD Workstream 1 complete.
- Do not lift the paid-data and hypothesis-expansion freeze.
- Do not call Databento metadata, download paid data, call live LLM research APIs, run GDELT retries, request broker data/orders, approve paper trading, or claim E2 evidence from the current remediation work.
- Latest broad verification: hermetic 583 tests passed, state-audit 155 tests passed, full discovery 738 tests passed, fixture pipeline passed, and the DD tracker validator passed with WS3 marked `done`.

## Next Local Remediation Candidates

1. Start WS5 only under a separate user-directed session.
2. Expand `locked_gates.jsonl` to additional active locked gates after Fable/user review confirms the seed format.
3. Backfill `wiki_citation_hashes` for active preregistrations where Fable/user agrees the audit format is correct.
