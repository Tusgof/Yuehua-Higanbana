# M4 Execution Rule Compliance Audit

- Status: `pass`
- Blockers: `0`
- Warnings: `1`

## Rules Checked
- Entry market orders are prohibited.
- Missing entry quote/fill evidence must skip the trade.
- No modeled close timestamp may be after 15:45:00 ET.

## Evidence Summary
- Component summary files checked: `96`
- Candidate days checked: `279`
- Closed trades checked: `273`
- Skipped trades checked: `6`
- Entry fill rows checked: `546`
- Close timestamp rows checked: `546`

## Close Time Counts
```json
{
  "09:36:00": 8,
  "09:37:00": 14,
  "09:38:00": 12,
  "09:39:00": 14,
  "09:45:00": 2,
  "09:47:00": 2,
  "09:55:00": 32,
  "09:56:00": 6,
  "09:57:00": 4,
  "09:58:00": 2,
  "09:59:00": 2,
  "10:00:00": 4,
  "10:01:00": 8,
  "10:04:00": 4,
  "10:10:00": 2,
  "10:22:00": 2,
  "10:25:00": 22,
  "10:26:00": 4,
  "10:27:00": 6,
  "10:28:00": 2,
  "10:29:00": 2,
  "10:33:00": 4,
  "10:34:00": 2,
  "10:55:00": 6,
  "11:01:00": 2,
  "11:03:00": 2,
  "11:25:00": 2,
  "11:29:00": 2,
  "11:55:00": 2,
  "12:56:00": 2,
  "14:04:00": 2,
  "15:40:00": 6,
  "15:45:00": 360
}
```

## Sub-System A Probe
```json
{
  "future_close_quote_reasons": [
    "missing quotes: close call 470.0, close call 472.0"
  ],
  "future_close_quote_status": "missing_quotes",
  "missing_entry_quote_reasons": [
    "missing quotes: entry call 472.0"
  ],
  "missing_entry_quote_status": "missing_quotes"
}
```

## Sub-System B Policy Audit
```json
{
  "blockers": [],
  "close_selector_probe": "2024-01-08T15:44:00-05:00",
  "methodology": {
    "entry_time": "10:00 ET or nearest available quote at/before 10:00",
    "exit_model": "forced_close_1545"
  },
  "status_counts": {
    "closed_forced_1545": 412,
    "missing_close_quotes": 5,
    "missing_leg_close_quotes": 6,
    "structure_unavailable": 21
  }
}
```

## Warnings
- No real M4 artifact currently contains a missing-entry-quote skipped trade; skip behavior is verified by synthetic probe.

## Blockers
- None
