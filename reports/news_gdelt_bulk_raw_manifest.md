# GDELT Bulk Raw Manifest Probe

- Mode: `metadata_only_no_raw_download`
- Status: `ready_for_one_file_probe`
- Candidate days: `71`
- Lookback hours: `24`
- Expected files: `6887`
- Matched files: `6883`
- Missing files: `4`
- Estimated compressed bytes: `48283138276`
- Master file list source: `http://data.gdeltproject.org/gdeltv2/masterfilelist.txt`

## Family Summary

| Family | Expected | Matched | Estimated Bytes |
|:--|--:|--:|--:|
| gkg | 6887 | 6883 | 48283138276 |

## Blockers

- None for metadata planning. Real news remains blocked until parser/import audit passes.

## Parser Blockers

- select and validate GKG columns for source/headline/url/timestamps
- distinguish exact publication time from GDELT seen/index time
- pre-register topic matching before OOS strategy use
- convert one small probe file to the existing offline news snapshot CSV shape before canonical import

## Timestamp Policy

- `decision_time_source`: reports\news_gdelt_capture_command_plan.json commands[].decision_time_et
- `window`: GDELT 15-minute file stamps from decision_time - lookback_hours through decision_time
- `publication_timestamp_status`: not_validated
- `seen_timestamp_status`: candidate_only
- `anti_leakage_requirement`: future parser must map raw timestamps into published_at/fetched_at or an honest surrogate before canonical import

## Next Step

Select one small GKG file from this manifest for a controlled parser probe. Do not download broad raw archives or run LLM research until the probe maps timestamps/source/headline/url into canonical news_item fields.

## Sample Manifest Items

- `2023-04-03` `gkg` `20230402133000.gkg.csv.zip` matched=`True` bytes=`5995836`
- `2023-04-03` `gkg` `20230402134500.gkg.csv.zip` matched=`True` bytes=`5207252`
- `2023-04-03` `gkg` `20230402140000.gkg.csv.zip` matched=`True` bytes=`5419829`
- `2023-04-03` `gkg` `20230402141500.gkg.csv.zip` matched=`True` bytes=`6542456`
- `2023-04-03` `gkg` `20230402143000.gkg.csv.zip` matched=`True` bytes=`5554767`
- `2023-04-03` `gkg` `20230402144500.gkg.csv.zip` matched=`True` bytes=`6115475`
- `2023-04-03` `gkg` `20230402150000.gkg.csv.zip` matched=`True` bytes=`5359612`
- `2023-04-03` `gkg` `20230402151500.gkg.csv.zip` matched=`True` bytes=`5767846`
- `2023-04-03` `gkg` `20230402153000.gkg.csv.zip` matched=`True` bytes=`6338907`
- `2023-04-03` `gkg` `20230402154500.gkg.csv.zip` matched=`True` bytes=`6062842`
- `2023-04-03` `gkg` `20230402160000.gkg.csv.zip` matched=`True` bytes=`5322061`
- `2023-04-03` `gkg` `20230402161500.gkg.csv.zip` matched=`True` bytes=`6054761`
- `2023-04-03` `gkg` `20230402163000.gkg.csv.zip` matched=`True` bytes=`5971978`
- `2023-04-03` `gkg` `20230402164500.gkg.csv.zip` matched=`True` bytes=`5992021`
- `2023-04-03` `gkg` `20230402170000.gkg.csv.zip` matched=`True` bytes=`5351833`
- `2023-04-03` `gkg` `20230402171500.gkg.csv.zip` matched=`True` bytes=`5395133`
- `2023-04-03` `gkg` `20230402173000.gkg.csv.zip` matched=`True` bytes=`4973167`
- `2023-04-03` `gkg` `20230402174500.gkg.csv.zip` matched=`True` bytes=`5564694`
- `2023-04-03` `gkg` `20230402180000.gkg.csv.zip` matched=`True` bytes=`5548545`
- `2023-04-03` `gkg` `20230402181500.gkg.csv.zip` matched=`True` bytes=`5429976`

## Missing Manifest Items

- `2023-04-14` `gkg` `20230414103000.gkg.csv.zip`
- `2023-05-31` `gkg` `20230530141500.gkg.csv.zip`
- `2023-07-25` `gkg` `20230724171500.gkg.csv.zip`
- `2023-11-09` `gkg` `20231109004500.gkg.csv.zip`
