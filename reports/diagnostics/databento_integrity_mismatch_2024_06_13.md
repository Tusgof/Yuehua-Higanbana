# Databento Integrity Mismatch Diagnosis - 2024-06-13 Exit Checks

- **Status**: `blocked`
- **Target files**: 2
- **Most likely classification**: `b` / `post_download_modification_or_replacement`
- **Confidence**: `medium_low`
- **Decision**: No rebaseline performed. The blocker remains open until original files are restored, or the user/Fable accepts a documented revalidation/rebaseline decision after the freeze is lifted.

## Findings

| File | Byte delta | Expected SHA-256 | Actual SHA-256 | Parse status | Duplicate same as current | Status |
|:--|--:|:--|:--|:--|:--:|:--|
| `raw/spy_0dte/databento/oos_2024_06_intraday_exit_30m_chunk2/2024-06-13_exit_check_1430.dbn.zst` | 54 | `fca9775548d422cc7fc2ebb92c18fcf35fda2e9185aceb12e3a60ba208d84302` | `32618eb467825a9e828e909af3947e86d56bfd2e519f45fe307e76053ad66c57` | `valid_dbn` | `True` | `sha256_mismatch` |
| `raw/spy_0dte/databento/oos_2024_06_intraday_exit_30m_chunk2/2024-06-13_exit_check_1500.dbn.zst` | 112 | `ef707e9ea1de56c14f0524d5879eab9abe5086be4228c75facfe4f3637e53ec5` | `81e0940d2bee249939071be44035d5cdf2b6df5e84ddddb2fae306ba04091465` | `valid_dbn` | `True` | `sha256_mismatch` |

## Current File Evidence

### `2024-06-13_exit_check_1430.dbn.zst`
- Current size/mtime/SHA-256: `1985057` bytes, `2026-06-30T20:49:12+00:00`, `32618eb467825a9e828e909af3947e86d56bfd2e519f45fe307e76053ad66c57`
- Expected SHA-256: `fca9775548d422cc7fc2ebb92c18fcf35fda2e9185aceb12e3a60ba208d84302`
- Parse probe: `valid_dbn`; rows `90700`; dataset/schema `OPRA.PILLAR` / `cbbo-1m`
- Referenced by 7 repo text artifacts after excluding this report.

### `2024-06-13_exit_check_1500.dbn.zst`
- Current size/mtime/SHA-256: `2002219` bytes, `2026-06-30T20:49:30+00:00`, `81e0940d2bee249939071be44035d5cdf2b6df5e84ddddb2fae306ba04091465`
- Expected SHA-256: `ef707e9ea1de56c14f0524d5879eab9abe5086be4228c75facfe4f3637e53ec5`
- Parse probe: `valid_dbn`; rows `90700`; dataset/schema `OPRA.PILLAR` / `cbbo-1m`
- Referenced by 7 repo text artifacts after excluding this report.


## Interpretation

- The committed supplemental checksum registry and the original Databento download report agree on the expected hashes.
- The current local files are larger than the recorded download artifacts and have different bit-level hashes.
- The normalized `oos_2024_06` duplicate copies have the same current hashes as the mismatched files, so they are not independent backups of the expected originals.
- Existing normalization evidence still shows both windows were parsed as 90,700 input rows and 2,380 0DTE output rows, but that does not clear the bit-level integrity blocker.
- Both current files parse as valid DBN locally, so truncation/corruption is not the best explanation from available evidence.
- No later Databento download log was found for these exact files. By elimination, the most likely class is post-download replacement/modification, although local mtimes are not enough to prove the exact mechanism.
- No registry hash, download-result hash, or data file was rebaselined by this diagnosis.

## Affected Experiment Scan

- Completed experiment reports directly referencing either raw filename: `0`
- No completed experiment report directly references these two raw filenames by scan.
- Affected data-pipeline artifacts: `2`
  - `reports/data_cost/databento_download_result_oos_2024_06_intraday_exit_30m_chunk2.json`
  - `reports/data_cost/databento_normalization_summary_2024_06.json`

## Required Closure

Workstream 1 remains open until the original expected files are restored from external backup or the user/Fable approves a documented revalidation/rebaseline decision.
If restore is impossible, a small re-download comparison may be the cleanest next evidence step, but it is a user decision because the purchase freeze is active.
## Addendum: User-Approved Re-download Comparison

- Status: `blocked`
- Cost: `$0.054061412812`

### `2024-06-13_exit_check_1430`
- Case/disposition: `case_3` / `escalated_unexplained`
- Historical hash: `fca9775548d422cc7fc2ebb92c18fcf35fda2e9185aceb12e3a60ba208d84302` (raw original unavailable).
- Current-before hash: `32618eb467825a9e828e909af3947e86d56bfd2e519f45fe307e76053ad66c57`; fresh hash: `0b704de04c863efedc0289d836ba1fc0e3e366014f08a3af6497644f80d80764`.
- Parse rows current/fresh: `90700` / `90700`.

### `2024-06-13_exit_check_1500`
- Case/disposition: `case_3` / `escalated_unexplained`
- Historical hash: `ef707e9ea1de56c14f0524d5879eab9abe5086be4228c75facfe4f3637e53ec5` (raw original unavailable).
- Current-before hash: `81e0940d2bee249939071be44035d5cdf2b6df5e84ddddb2fae306ba04091465`; fresh hash: `8984bd5a7293d73bd5912c0697aefac1a6c0e220b7149b8c2613bd4d8912e1bf`.
- Parse rows current/fresh: `90700` / `90700`.

## Addendum: Canonical Content Resolution

- **Status**: `content_verified_envelope_variance`
- **Method**: SHA-256 over the zstd-decompressed DBN record body after its metadata header, plus SHA-256 over a sorted canonical export of all decoded records.
- **Policy**: `docs/DATABENTO_INTEGRITY_POLICY.md`

| Window | Record-body hash equal | Canonical record-export hash equal | Records | Disposition |
|:--|:--:|:--:|--:|:--|
| `2024-06-13_exit_check_1430` | `True` | `True` | 90,700 | `content_verified_envelope_variance` |
| `2024-06-13_exit_check_1500` | `True` | `True` | 90,700 | `content_verified_envelope_variance` |

- The compressed containers and DBN metadata-header hashes still differ between the current and fresh provider copies. The identical record bodies show that this is an envelope/metadata difference for the copies that can be inspected now.
- The original historical containers are unavailable. Therefore this explains the present mismatch mechanism but cannot prove which header/container bytes were in the original download. Historical SHA-256 values were retained unchanged.
- `python scripts/verify_data_integrity.py --backfill-canonical-hashes` recorded canonical record-body hashes for all 6,626 local raw Databento artifacts. The target files now verify as `content_verified_envelope_variance`; no canonical mismatch or missing supplemental artifact remains.
- The full integrity run remains blocked only by the unrelated pre-existing aggregate registry mismatch `databento-one-month-pilot-ef3f49c75c55`. The physical restore rehearsal also remains pending.
