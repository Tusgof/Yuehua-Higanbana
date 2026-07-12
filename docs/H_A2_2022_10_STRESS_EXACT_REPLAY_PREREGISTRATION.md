# H-A2 October 2022 Stress Exact Replay Preregistration

This replay uses the 13 dates locked by the approved cost plan. The decision timestamp is 09:35 ET. A date can become a strategy candidate only when the prior-close VIX is below 25, no high-importance macro event is scheduled, and the 09:35 close breaks the 09:30-09:34 range.

The replay explicitly forbids using the 15:45 close or any same-day realized followthrough as a 09:35 decision feature. If every date fails the ex-ante regime gate, the correct result is zero candidate trades, no PnL fabrication, and failure of the trade-density checkpoint.

September data remains blocked unless at least two candidate trades survive this replay.
