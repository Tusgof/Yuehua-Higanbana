# Interim Data Restore Rehearsal - 2026-07-12

## Result

- **Status**: `pass`
- **Disposition**: `interim_rehearsal_completed`
- **Machine**: `DESKTOP-1C8CPTE`
- **Repository commit tested**: `792eba52acef72804192e002782d6b4cf3eac717`
- **Paid download or broker action during rehearsal**: none

## Backup And Restore Path

- Source data tree: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\data`
- Interim backup: Google Drive Computers backup, exposed through the user-created shortcut under `My Drive\Investment\Higanbana`
- Cloud restore source: `G:\.shortcut-targets-by-id\188BxJiLNXCtLUogu4uEQXRwfDYGi0GtX\data`
- Isolated restore target: `D:\Fogust\Workspace\Investment\.higanbana_restore_rehearsal_20260712\data`

The restore read from the Google Drive cloud mount into a separate temporary directory. It did not validate the original source directory in place.

## Inventory Evidence

| Check | Source | Restored | Result |
|:--|--:|--:|:--|
| Files | 6,785 | 6,785 | pass |
| Bytes | 31,794,213,413 | 31,794,213,413 | pass |
| Path or size differences | - | 0 | pass |

`robocopy` reported transient Google Drive placeholder/resource errors during transfer, retried them, and completed with `FAILED=0`, `Bytes copied=29.610 GiB`, and exit code `1` (files copied successfully).

## Integrity Evidence

`HIGANBANA_DATA_ROOT` was set to the isolated restore target before running:

```text
python scripts/verify_data_integrity.py --output reports/diagnostics/interim_restore_integrity_2026_07_12.json
```

Result:

- Overall status: `pass`
- Blockers: `0`
- Dataset registry checks: `43`
- Supplemental paid-artifact checks: `6,626`
- Exact container and canonical-content passes: `6,624`
- Accepted `content_verified_envelope_variance`: `2`
- Missing/uncovered paid artifacts: `0`

The old aggregate directory snapshot `databento-one-month-pilot-ef3f49c75c55` is retained as historical evidence and marked `superseded` by the later same-day snapshot `databento-one-month-pilot-bc0f2b1dac6a`. The later snapshot hash matches the restored directory. No historical hash was overwritten.

## Decision

The interim cloud backup and isolated restore are verified. This satisfies the user-approved WS1 interim rehearsal exit condition. A physical off-site copy remains planned when external media arrives, but it is a non-blocking resilience improvement rather than a WS1 blocker.
