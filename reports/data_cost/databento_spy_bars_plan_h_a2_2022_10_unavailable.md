# H-A2 2022-10 SPY Bars Availability Blocker

## Result
Databento `EQUS.MINI` cannot supply the requested 2022-10 SPY 1-minute bars.

The live metadata cost check failed with:

- Error: `data_start_before_available_start`
- Requested start: `2022-10-03T13:30:00+00:00`
- Dataset available start: `2023-03-28T00:00:00+00:00`

No SPY bar download was attempted.

## Impact
- H-A2 2022-10 option quotes are downloaded and normalized.
- H-A2 2022-10 ORB/backtest rerun is still blocked because the strategy needs SPY underlying 1-minute bars.
- Buying more 2022 option data does not solve this blocker.

## Next Safe Action
- Decide a no/low-cost source for 2022 SPY 1-minute bars before any new provider purchase.
- Do not download 2022-09 option data while the missing 2022 underlying bars are the active H-A2 blocker.
- Keep H-A2 at E1 diagnostic evidence or below until the stress month can be rerun with timestamp-clean underlying bars.
