# รายงานการทดลอง exp03_risk_parity

## สมมติฐาน
Tail-risk-aware allocation between Sub-System A and Sub-System B reduces max drawdown and improves Sortino.

## หลักฐานที่ใช้
- Evidence type: fixture / synthetic smoke test
- Train window: 2022-05-11 to 2023-12-31
- OOS window: 2024-01-01 to 2026-06-29
- Chart: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\experiments\charts\exp03_risk_parity_equity.svg`

![equity curve](D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\experiments\charts\exp03_risk_parity_equity.svg)

## Metrics
```json
{
  "benchmark_return": 0.0005,
  "cost_drag": 3.0,
  "es95": -5.0,
  "es99": -5.0,
  "max_drawdown": -0.00495,
  "payoff_ratio": 2.0,
  "sharpe": 5.3616,
  "sortino": 0.0,
  "total_net_pnl": 5.0,
  "trade_count": 2,
  "win_rate": 0.5,
  "worst_day_loss": -5.0
}
```

## ข้อสรุป
ยังสรุปไม่ได้

## เหตุผล
ผลนี้ยังเป็น fixture ถ้า trade_count ต่ำกว่าเกณฑ์ N >= 500 ต้องถือว่ายังสรุปไม่ได้ ไม่ใช่หลักฐานว่า edge ใช้งานได้จริง

## เงื่อนไขที่จะทำให้ข้อสรุปล้ม
- ข้อมูลจริงไม่มี bid/ask ที่ timestamp เข้าและออก
- OOS ถูกใช้ปรับ parameter
- ผลลัพธ์พึ่งพา extreme trades ไม่กี่ครั้ง

## ถ้าล้มเหลวต้องทำอะไรต่อ
ตรวจ data source, execution cost, split policy, และสร้าง hypothesis ใหม่ที่วัดผลได้

## Local Wiki References
- `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki\concepts\backtest-validation-protocol.md`
- `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki\concepts\implementable-option-pnl.md`
