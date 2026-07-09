# GDELT News Capture Command Plan

- Mode: `dry_run_no_network`
- Status: `blocked_cooldown`
- Live retry allowed now: `False`
- Candidate days: `71`
- Command count: `71`
- Max records per topic: `5`
- Lookback hours: `24`
- Latest capture status: `blocked`
- Daily status files: `6`
- Not-attempted candidate days: `65`
- Retry pressure: `cooldown_recommended`

## Blockers

- `gdelt_capture_unavailable`

## Retry Pressure

- Status: `cooldown_recommended`
- Reason: 6 per-day GDELT capture attempts are blocked; wait before the next --execute retry or switch to an offline/alternate news archive path.

## Next Unattempted Command

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-04-17T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-04-17.csv --status-output-path reports\news_gdelt_capture_status\2023-04-17.json --execute
```


## Commands

### 2023-04-03

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-04-03T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-04-03.csv --status-output-path reports\news_gdelt_capture_status\2023-04-03.json --execute
```

### 2023-04-13

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-04-13T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-04-13.csv --status-output-path reports\news_gdelt_capture_status\2023-04-13.json --execute
```

### 2023-04-14

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-04-14T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-04-14.csv --status-output-path reports\news_gdelt_capture_status\2023-04-14.json --execute
```

### 2023-04-17

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-04-17T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-04-17.csv --status-output-path reports\news_gdelt_capture_status\2023-04-17.json --execute
```

### 2023-04-20

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-04-20T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-04-20.csv --status-output-path reports\news_gdelt_capture_status\2023-04-20.json --execute
```

### 2023-04-27

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-04-27T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-04-27.csv --status-output-path reports\news_gdelt_capture_status\2023-04-27.json --execute
```

### 2023-04-28

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-04-28T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-04-28.csv --status-output-path reports\news_gdelt_capture_status\2023-04-28.json --execute
```

### 2023-05-31

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-05-31T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-05-31.csv --status-output-path reports\news_gdelt_capture_status\2023-05-31.json --execute
```

### 2023-06-01

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-06-01T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-06-01.csv --status-output-path reports\news_gdelt_capture_status\2023-06-01.json --execute
```

### 2023-06-02

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-06-02T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-06-02.csv --status-output-path reports\news_gdelt_capture_status\2023-06-02.json --execute
```

### 2023-06-13

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-06-13T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-06-13.csv --status-output-path reports\news_gdelt_capture_status\2023-06-13.json --execute
```

### 2023-06-16

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-06-16T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-06-16.csv --status-output-path reports\news_gdelt_capture_status\2023-06-16.json --execute
```

### 2023-06-23

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-06-23T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-06-23.csv --status-output-path reports\news_gdelt_capture_status\2023-06-23.json --execute
```

### 2023-06-26

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-06-26T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-06-26.csv --status-output-path reports\news_gdelt_capture_status\2023-06-26.json --execute
```

### 2023-06-27

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-06-27T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-06-27.csv --status-output-path reports\news_gdelt_capture_status\2023-06-27.json --execute
```

### 2023-07-03

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-07-03T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-07-03.csv --status-output-path reports\news_gdelt_capture_status\2023-07-03.json --execute
```

### 2023-07-13

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-07-13T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-07-13.csv --status-output-path reports\news_gdelt_capture_status\2023-07-13.json --execute
```

### 2023-07-18

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-07-18T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-07-18.csv --status-output-path reports\news_gdelt_capture_status\2023-07-18.json --execute
```

### 2023-07-25

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-07-25T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-07-25.csv --status-output-path reports\news_gdelt_capture_status\2023-07-25.json --execute
```

### 2023-07-28

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-07-28T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-07-28.csv --status-output-path reports\news_gdelt_capture_status\2023-07-28.json --execute
```

### 2023-08-01

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-08-01T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-08-01.csv --status-output-path reports\news_gdelt_capture_status\2023-08-01.json --execute
```

### 2023-08-02

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-08-02T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-08-02.csv --status-output-path reports\news_gdelt_capture_status\2023-08-02.json --execute
```

### 2023-08-10

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-08-10T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-08-10.csv --status-output-path reports\news_gdelt_capture_status\2023-08-10.json --execute
```

### 2023-08-11

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-08-11T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-08-11.csv --status-output-path reports\news_gdelt_capture_status\2023-08-11.json --execute
```

### 2023-08-21

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-08-21T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-08-21.csv --status-output-path reports\news_gdelt_capture_status\2023-08-21.json --execute
```

### 2023-08-28

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-08-28T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-08-28.csv --status-output-path reports\news_gdelt_capture_status\2023-08-28.json --execute
```

### 2023-09-01

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-09-01T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-09-01.csv --status-output-path reports\news_gdelt_capture_status\2023-09-01.json --execute
```

### 2023-09-07

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-09-07T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-09-07.csv --status-output-path reports\news_gdelt_capture_status\2023-09-07.json --execute
```

### 2023-10-02

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-10-02T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-10-02.csv --status-output-path reports\news_gdelt_capture_status\2023-10-02.json --execute
```

### 2023-10-05

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-10-05T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-10-05.csv --status-output-path reports\news_gdelt_capture_status\2023-10-05.json --execute
```

### 2023-10-23

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-10-23T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-10-23.csv --status-output-path reports\news_gdelt_capture_status\2023-10-23.json --execute
```

### 2023-10-25

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-10-25T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-10-25.csv --status-output-path reports\news_gdelt_capture_status\2023-10-25.json --execute
```

### 2023-10-27

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-10-27T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-10-27.csv --status-output-path reports\news_gdelt_capture_status\2023-10-27.json --execute
```

### 2023-10-31

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-10-31T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-10-31.csv --status-output-path reports\news_gdelt_capture_status\2023-10-31.json --execute
```

### 2023-11-09

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-11-09T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-11-09.csv --status-output-path reports\news_gdelt_capture_status\2023-11-09.json --execute
```

### 2023-11-10

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-11-10T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-11-10.csv --status-output-path reports\news_gdelt_capture_status\2023-11-10.json --execute
```

### 2023-11-13

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-11-13T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-11-13.csv --status-output-path reports\news_gdelt_capture_status\2023-11-13.json --execute
```

### 2023-11-20

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-11-20T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-11-20.csv --status-output-path reports\news_gdelt_capture_status\2023-11-20.json --execute
```

### 2023-11-27

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-11-27T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-11-27.csv --status-output-path reports\news_gdelt_capture_status\2023-11-27.json --execute
```

### 2023-11-30

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-11-30T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-11-30.csv --status-output-path reports\news_gdelt_capture_status\2023-11-30.json --execute
```

### 2023-12-06

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-12-06T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-12-06.csv --status-output-path reports\news_gdelt_capture_status\2023-12-06.json --execute
```

### 2023-12-12

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2023-12-12T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2023-12-12.csv --status-output-path reports\news_gdelt_capture_status\2023-12-12.json --execute
```

### 2024-01-05

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-01-05T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-01-05.csv --status-output-path reports\news_gdelt_capture_status\2024-01-05.json --execute
```

### 2024-01-08

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-01-08T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-01-08.csv --status-output-path reports\news_gdelt_capture_status\2024-01-08.json --execute
```

### 2024-01-10

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-01-10T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-01-10.csv --status-output-path reports\news_gdelt_capture_status\2024-01-10.json --execute
```

### 2024-01-11

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-01-11T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-01-11.csv --status-output-path reports\news_gdelt_capture_status\2024-01-11.json --execute
```

### 2024-01-29

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-01-29T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-01-29.csv --status-output-path reports\news_gdelt_capture_status\2024-01-29.json --execute
```

### 2024-01-30

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-01-30T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-01-30.csv --status-output-path reports\news_gdelt_capture_status\2024-01-30.json --execute
```

### 2024-02-13

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-02-13T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-02-13.csv --status-output-path reports\news_gdelt_capture_status\2024-02-13.json --execute
```

### 2024-02-14

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-02-14T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-02-14.csv --status-output-path reports\news_gdelt_capture_status\2024-02-14.json --execute
```

### 2024-02-27

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-02-27T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-02-27.csv --status-output-path reports\news_gdelt_capture_status\2024-02-27.json --execute
```

### 2024-03-06

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-03-06T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-03-06.csv --status-output-path reports\news_gdelt_capture_status\2024-03-06.json --execute
```

### 2024-03-07

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-03-07T09:30:00-05:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-03-07.csv --status-output-path reports\news_gdelt_capture_status\2024-03-07.json --execute
```

### 2024-03-12

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-03-12T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-03-12.csv --status-output-path reports\news_gdelt_capture_status\2024-03-12.json --execute
```

### 2024-03-20

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-03-20T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-03-20.csv --status-output-path reports\news_gdelt_capture_status\2024-03-20.json --execute
```

### 2024-04-02

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-04-02T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-04-02.csv --status-output-path reports\news_gdelt_capture_status\2024-04-02.json --execute
```

### 2024-04-08

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-04-08T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-04-08.csv --status-output-path reports\news_gdelt_capture_status\2024-04-08.json --execute
```

### 2024-04-10

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-04-10T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-04-10.csv --status-output-path reports\news_gdelt_capture_status\2024-04-10.json --execute
```

### 2024-04-16

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-04-16T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-04-16.csv --status-output-path reports\news_gdelt_capture_status\2024-04-16.json --execute
```

### 2024-04-18

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-04-18T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-04-18.csv --status-output-path reports\news_gdelt_capture_status\2024-04-18.json --execute
```

### 2024-05-02

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-05-02T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-05-02.csv --status-output-path reports\news_gdelt_capture_status\2024-05-02.json --execute
```

### 2024-05-03

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-05-03T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-05-03.csv --status-output-path reports\news_gdelt_capture_status\2024-05-03.json --execute
```

### 2024-05-15

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-05-15T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-05-15.csv --status-output-path reports\news_gdelt_capture_status\2024-05-15.json --execute
```

### 2024-05-20

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-05-20T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-05-20.csv --status-output-path reports\news_gdelt_capture_status\2024-05-20.json --execute
```

### 2024-05-30

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-05-30T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-05-30.csv --status-output-path reports\news_gdelt_capture_status\2024-05-30.json --execute
```

### 2024-05-31

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-05-31T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-05-31.csv --status-output-path reports\news_gdelt_capture_status\2024-05-31.json --execute
```

### 2024-06-13

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-06-13T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-06-13.csv --status-output-path reports\news_gdelt_capture_status\2024-06-13.json --execute
```

### 2024-06-18

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-06-18T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-06-18.csv --status-output-path reports\news_gdelt_capture_status\2024-06-18.json --execute
```

### 2024-06-21

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-06-21T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-06-21.csv --status-output-path reports\news_gdelt_capture_status\2024-06-21.json --execute
```

### 2024-06-27

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-06-27T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-06-27.csv --status-output-path reports\news_gdelt_capture_status\2024-06-27.json --execute
```

### 2024-06-28

```powershell
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-06-28T09:30:00-04:00 --lookback-hours 24 --max-records 5 --output-path data\raw\spy_0dte\news\gdelt\2024-06-28.csv --status-output-path reports\news_gdelt_capture_status\2024-06-28.json --execute
```

## Next Step

GDELT 429 pressure is persistent. Pause live GDELT --execute retries before trying the next candidate day, then import and audit only after a real CSV capture succeeds.
