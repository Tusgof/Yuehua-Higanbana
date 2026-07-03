# Databento OPRA Statistics/OI Metadata Probe

- **Status**: `pass_with_timing_caveat`
- **Mode**: `metadata_only_no_download`
- **Dataset**: `OPRA.PILLAR`
- **Schema**: `statistics`
- **Symbol**: `SPY.OPT`
- **Download performed**: `False`
- **Has stat_type field**: `True`
- **Has quantity/price field**: `True`

## Record Count Checks

| Window | Start | End | Record count |
|:--|:--|:--|--:|
| `intraday_research_window` | `2024-01-03T14:30:00+00:00` | `2024-01-03T20:50:00+00:00` | 0 |
| `full_utc_day` | `2024-01-03T00:00:00+00:00` | `2024-01-04T00:00:00+00:00` | 541311 |
| `three_utc_days` | `2024-01-02T00:00:00+00:00` | `2024-01-05T00:00:00+00:00` | 1628952 |

## Full-Day Cost Estimates

| Window | Estimated cost |
|:--|--:|
| `2024-01-03 full UTC day` | `$0.354911148548` |
| `2024-01-02 to 2024-01-05 full UTC days` | `$1.068024158478` |

## Field Names

`length`, `rtype`, `publisher_id`, `instrument_id`, `ts_event`, `ts_recv`, `ts_ref`, `price`, `quantity`, `sequence`, `ts_in_delta`, `stat_type`, `channel_id`, `update_action`, `stat_flags`, `_reserved`

## Interpretation

The metadata probe confirms that the OPRA `statistics` schema is queryable for `SPY.OPT` and has the fields needed to identify statistics records: `stat_type`, `quantity`, and `price`.

The normal intraday research window has zero statistics records, while the full UTC day has records. This means OI/statistics should be treated as a full-day/reference-style input first, not as an entry/exit-window quote input.

Next probe: If proceeding, estimate and then download only one full UTC day of OPRA statistics under the existing cost guard; inspect stat_type values and timestamp semantics before using OI in a strategy report.
