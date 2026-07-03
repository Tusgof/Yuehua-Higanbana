# Databento OPRA Statistics/OI Download Probe

- **Created at UTC**: `2026-07-02T19:14:37+00:00`
- **Status**: `pass`
- **Blockers**: -
- **Dataset/schema**: `OPRA.PILLAR` / `statistics`
- **Symbol**: `SPY.OPT`
- **Window**: `2024-01-03T00:00:00+00:00` to `2024-01-04T00:00:00+00:00`
- **Estimated cost logged before download**: `$0.354911148548`
- **Download source**: `downloaded`
- **Raw path**: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\data\raw\spy_0dte\databento\opra_statistics_oi_probe_2024_01_03\2024-01-03_full_utc_day_statistics.dbn.zst`
- **Bytes**: 2834573
- **SHA-256**: `8b6a7ebc5199d3e2a17ec42247ed86ebb323b6d4dd193ee0e986717255140e5f`

## Inspection

- **Rows**: 541311
- **Index timestamp range**: `2024-01-03 11:30:00.425311070+00:00` to `2024-01-03 22:30:20.507486600+00:00`
- **Columns**: `ts_event, rtype, publisher_id, instrument_id, ts_ref, price, quantity, sequence, ts_in_delta, stat_type, channel_id, update_action, stat_flags, symbol`
- **Top stat types**: `OPEN_INTEREST`=180279, `OPENING_PRICE`=45129, `TRADING_SESSION_HIGH_PRICE`=45129, `TRADING_SESSION_LOW_PRICE`=45129, `CLOSE_PRICE`=45129, `NET_CHANGE`=45129, `HIGHEST_BID`=45129, `LOWEST_OFFER`=45129
- **Open-interest records**: 180279
- **Open-interest quantity min/mean/max**: `0.0` / `1756.0154815591388` / `227936.0`
- **Unique symbols**: 8004

## Decision

- Usable as a reference-style open-interest input for further feasibility work, with a timing caveat: full-day statistics must be mapped to a valid decision timestamp before any strategy test uses them.
- This is a data-source probe, not a strategy experiment. Do not write a research log for it.
