# Data Integrity Mismatch Review - 2026-07-09

## Scope
Technical DD Workstream 1 follow-up for the paid-data checksum blocker found by `scripts\verify_data_integrity.py`.

## Files Reviewed
| File | Expected bytes | Actual bytes | Expected SHA-256 | Actual SHA-256 | Decode status |
|:--|--:|--:|:--|:--|:--|
| `data\raw\spy_0dte\databento\oos_2024_06_intraday_exit_30m_chunk2\2024-06-13_exit_check_1430.dbn.zst` | 1985003 | 1985057 | `fca9775548d422cc7fc2ebb92c18fcf35fda2e9185aceb12e3a60ba208d84302` | `32618eb467825a9e828e909af3947e86d56bfd2e519f45fe307e76053ad66c57` | decoded |
| `data\raw\spy_0dte\databento\oos_2024_06_intraday_exit_30m_chunk2\2024-06-13_exit_check_1500.dbn.zst` | 2002107 | 2002219 | `ef707e9ea1de56c14f0524d5879eab9abe5086be4228c75facfe4f3637e53ec5` | `81e0940d2bee249939071be44035d5cdf2b6df5e84ddddb2fae306ba04091465` | decoded |

## Review Result
- Both current files decode as Databento DBN `OPRA.PILLAR` / `cbbo-1m`.
- Both current files contain `90700` records.
- The decoded receive-time windows match the intended request windows:
  - `1430`: `2024-06-13T18:25:00Z` to `2024-06-13T18:34:00Z`.
  - `1500`: `2024-06-13T18:55:00Z` to `2024-06-13T19:04:00Z`.
- The normalized June 2024 summary previously read each file as `90700` input rows and `2380` 0DTE output rows.
- A recursive filename search across `D:\Fogust` found duplicate copies under `data\raw\spy_0dte\databento\oos_2024_06\`, but those copies have the same current hashes as the mismatched files. No local copy with the expected original hashes was found.

## Decision
The files are not obviously corrupt, but the integrity blocker remains open because the current bit-level hashes do not match the committed download-result evidence.

Do not silently rebaseline these hashes. Workstream 1 should remain open until one of these happens:
1. the original expected files are restored from an external backup, or
2. the user/Fable explicitly accepts a documented revalidation/rebaseline decision.
