# H-A2 Post-Stress Normalization/Control Exact Replay

- Status: `complete`
- Conclusion: `ยังสรุปไม่ได้`
- Evidence tier: `E1`
- Candidate date: `2025-05-05`
- Direction: `call`
- Entry: `09:35:00 ET`
- Forced close: `15:45:00 ET`

## Candidate And Strike Mapping

- Underlying at entry: `563.12`
- Underlying at forced close: `564.38`
- Target gap: `1.48`
- Width: `2.0`
- Mapping method: `nearest_discrete_strike_rounding`
- Long strike: `565.0`
- Short strike: `567.0`
- Realized long gap: `1.88`

## Legs

| Side | Strike | Entry bid | Entry ask | Entry mid | Forced bid | Forced ask | Forced mid |
|---|---:|---:|---:|---:|---:|---:|---:|
| `buy` | `565.0` | `1.03` | `1.04` | `1.035` | `0.29` | `0.3` | `0.295` |
| `sell` | `567.0` | `0.48` | `0.49` | `0.485` | `0.02` | `0.03` | `0.025` |

## PnL

| Metric | Value |
|---|---:|
| Entry mid debit | `0.55` |
| Forced-close mid value | `0.27` |
| Mid PnL | `-28.0` |
| Entry implementable debit | `0.56` |
| Forced-close implementable credit | `0.26` |
| Gross implementable PnL before fees | `-30.0` |
| Total fees | `2.56` |
| Implementable PnL | `-32.56` |
| Cost drag vs mid | `4.56` |

## Guardrails

- Used only the already-downloaded post-stress normalization/control candidate-date DBN file.
- Did not download data, call IBKR, call LLMs, retry GDELT, or broaden beyond `2025-05-05`.
- This is E1 single-candidate diagnostic evidence only, not E2 acceptance evidence.
- Paper trading, operational validation, and real-money trading remain forbidden.

## Next Safe Action

Treat H-A2.57 as E1 single-candidate diagnostic evidence only. Use it with the previous normal/control exact replay to decide the next pre-registered sample-expansion or hypothesis-revision step; do not claim E2 or paper-trading readiness.
