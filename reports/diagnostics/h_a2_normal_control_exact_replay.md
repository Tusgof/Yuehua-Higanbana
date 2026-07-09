# H-A2 Normal/Control Exact Replay

- Status: `complete`
- Conclusion: `ยังสรุปไม่ได้`
- Evidence tier: `E1`
- Candidate date: `2025-02-11`
- Direction: `call`
- Entry: `09:35:00 ET`
- Forced close: `15:45:00 ET`

## Candidate And Strike Mapping

- Underlying at entry: `603.52`
- Underlying at forced close: `604.93`
- Target gap: `1.48`
- Width: `2.0`
- Mapping method: `nearest_discrete_strike_rounding`
- Long strike: `605.0`
- Short strike: `607.0`
- Realized long gap: `1.48`

## Legs

| Side | Strike | Entry bid | Entry ask | Entry mid | Forced bid | Forced ask | Forced mid |
|---|---:|---:|---:|---:|---:|---:|---:|
| `buy` | `605.0` | `0.66` | `0.67` | `0.665` | `0.28` | `0.29` | `0.285` |
| `sell` | `607.0` | `0.17` | `0.18` | `0.175` | `0.01` | `0.02` | `0.015` |

## PnL

| Metric | ค่า |
|---|---:|
| Entry mid debit | `0.49` |
| Forced-close mid value | `0.27` |
| Mid PnL | `-22.0` |
| Entry implementable debit | `0.5` |
| Forced-close implementable credit | `0.26` |
| Gross implementable PnL before fees | `-24.0` |
| Total fees | `2.56` |
| Implementable PnL | `-26.56` |
| Cost drag vs mid | `4.56` |

## Guardrails

- Used only the already-downloaded normal/control candidate-date DBN file.
- Did not download data, call IBKR, call LLMs, retry GDELT, or broaden beyond `2025-02-11`.
- This is E1 single-candidate diagnostic evidence only, not E2 acceptance evidence.
- Paper trading, operational validation, and real-money trading remain forbidden.

## Next Safe Action

Treat H-A2.49 as E1 single-candidate diagnostic evidence only. Use it to decide the next pre-registered validation-data or sample-expansion step; do not claim E2 or paper-trading readiness.
