# Real-Money IBKR Guardrails

## Policy
The original preference was to skip paper trading, but IBKR options permission is currently pending. The updated launch path is:

1. Research acceptance.
2. Order-ticket construction and validation without transmit.
3. Paper trading bridge if real options permission or small-account feasibility is not ready.
4. Explicit user approval for real-money IBKR.
5. Bounded first-live-trade mode.
6. Daily monitoring and journal review.

Paper trading is an operational validation bridge, not proof of edge. Edge must come from historical backtests and research reports.

## Non-Negotiable Rules
- No IBKR order transmission before research acceptance.
- No live order transmission while options permission is missing.
- No undefined-risk option positions.
- No SPY option position may remain open past 3:45 PM ET.
- No overnight option exposure.
- No order if max possible loss exceeds configured risk limit.
- No order if the protective wing is missing from Sub-System B.
- No order if daily loss limit is hit.
- No order if kill switch is active.
- No credentials in repository files.

## $1,000 Account Constraints
- Baseline risk fraction: 2% of equity per trade.
- Baseline max risk on $1,000: $20 per trade.
- Real order sizing must round down to feasible contracts.
- If no valid defined-risk trade fits the account, the system must skip.
- SPY assignment risk is unacceptable for this account; forced close is mandatory.

## Required Pre-Transmit Checks
Before any real-money order can be transmitted:
- Research gate status is `PASS`.
- User approval file exists for the current launch date.
- Account equity and buying power are read from IBKR.
- Strategy ticket is defined-risk.
- Max loss is known before transmit.
- Entry price limit is within configured slippage cap.
- 3:45 PM ET close watchdog is running.
- Kill switch is off.
- No conflicting open position exists.

## First-Live-Trade Mode
The first real-money launch must be constrained:
- One opening trade maximum.
- One subsystem active at a time unless user explicitly approves both.
- No scaling after entry.
- Forced close watchdog active before order transmit.
- Post-trade report required the same day.

## Paper Trading Bridge
Paper trading becomes required if:
- IBKR options permission is not approved.
- Account size cannot support the researched defined-risk structure.
- Real-money order transmission has not yet passed ticket simulation and close-watchdog tests.

Paper trading must test:
- order ticket shape,
- limit-entry skip behavior,
- backup closing order workflow,
- 3:45 PM ET forced close,
- email alerts,
- journal and incident report generation.

## Approval Record
The approval record must include:
- Date.
- IBKR account alias, not account secret.
- Max risk per trade.
- Max daily loss.
- Enabled subsystem(s).
- Confirmation that paper trading is intentionally skipped.
- Or, if paper trading was used, confirmation that it only validated operations and did not override research evidence.
- Confirmation that the user accepts real-money execution risk.

## Stop Conditions
- IBKR connection unstable.
- Market data delayed or missing.
- Option chain stale.
- Spread width too wide.
- Macro/news gate says no-go.
- LLM risk score >= configured no-go threshold.
- Forced close scheduler/watchdog not active.
