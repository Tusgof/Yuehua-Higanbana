# Databento Cache Audit

- **Created at UTC**: `2026-06-29T10:15:38+00:00`
- **Source plan**: `reports\data_cost\databento_download_result_insample_2023_12_intraday_exit_30m.json`
- **Scenario**: `insample_2023_12`
- **Planned windows**: 280
- **Present files**: 280
- **Missing files**: 0
- **Invalid files**: 0
- **Total present bytes**: 485177337
- **All present**: `True`

## Missing Windows

- none

## Use Rule

- This audit is offline-only and does not call Databento.
- Missing windows need explicit user-approved download before real experiments.
- Present files can be reused by repeated experiments without another Databento request.
