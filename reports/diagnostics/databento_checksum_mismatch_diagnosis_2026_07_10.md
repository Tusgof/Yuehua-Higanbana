# Databento Checksum Mismatch Diagnosis - 2026-07-10

- **Status**: `blocked`
- **Target files**: 2
- **Decision**: No rebaseline performed. The blocker remains open until original files are restored or user/Fable accepts a documented revalidation/rebaseline decision.

## Findings

| File | Expected bytes delta | Expected SHA-256 | Actual SHA-256 | Duplicate same as current | Status |
|:--|--:|:--|:--|:--:|:--|
| `raw/spy_0dte/databento/oos_2024_06_intraday_exit_30m_chunk2/2024-06-13_exit_check_1430.dbn.zst` | 54 | `fca9775548d422cc7fc2ebb92c18fcf35fda2e9185aceb12e3a60ba208d84302` | `32618eb467825a9e828e909af3947e86d56bfd2e519f45fe307e76053ad66c57` | `True` | `sha256_mismatch` |
| `raw/spy_0dte/databento/oos_2024_06_intraday_exit_30m_chunk2/2024-06-13_exit_check_1500.dbn.zst` | 112 | `ef707e9ea1de56c14f0524d5879eab9abe5086be4228c75facfe4f3637e53ec5` | `81e0940d2bee249939071be44035d5cdf2b6df5e84ddddb2fae306ba04091465` | `True` | `sha256_mismatch` |

## Interpretation

- The committed supplemental checksum registry and the original Databento download report agree on the expected hashes.
- The current local files are larger than the recorded download artifacts and have different bit-level hashes.
- The normalized `oos_2024_06` duplicate copies have the same current hashes as the mismatched files, so they are not independent backups of the expected originals.
- Existing normalization evidence still shows both windows were parsed as 90,700 input rows and 2,380 0DTE output rows, but that does not clear the bit-level integrity blocker.
- No registry hash, download-result hash, or data file was rebaselined by this diagnosis.

## Required Closure

Workstream 1 remains open until the original expected files are restored from external backup or the user/Fable approves a documented revalidation/rebaseline decision.
