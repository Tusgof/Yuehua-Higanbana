# H-A2 ORB 09:36 Cost Plan

## สถานะ

- `awaiting_user_approval`
- Mode: `plan_only_no_network_no_purchase`
- ยังไม่อนุญาตให้ซื้อข้อมูล

## ขอบเขต

- วันที่เป้าหมาย: `20`
- หลัง cutoff: `2026-04-24`
- Regime: `{"vix": {"low": 0, "normal": 20}, "macro": {"control": 20, "high_importance": 0}, "trend": {"pending_prior_only_spy_daily_history": 20}}`

## วันที่เป้าหมาย

- `2026-04-27`: prior VIX `18.71`, `normal`, `control_no_high_importance_event`
- `2026-04-28`: prior VIX `18.02`, `normal`, `control_no_high_importance_event`
- `2026-05-01`: prior VIX `16.89`, `normal`, `control_no_high_importance_event`
- `2026-05-04`: prior VIX `16.99`, `normal`, `control_no_high_importance_event`
- `2026-05-06`: prior VIX `17.38`, `normal`, `control_no_high_importance_event`
- `2026-05-07`: prior VIX `17.39`, `normal`, `control_no_high_importance_event`
- `2026-05-11`: prior VIX `17.19`, `normal`, `control_no_high_importance_event`
- `2026-05-13`: prior VIX `17.99`, `normal`, `control_no_high_importance_event`
- `2026-05-14`: prior VIX `17.87`, `normal`, `control_no_high_importance_event`
- `2026-05-15`: prior VIX `17.26`, `normal`, `control_no_high_importance_event`
- `2026-05-18`: prior VIX `18.43`, `normal`, `control_no_high_importance_event`
- `2026-05-19`: prior VIX `17.82`, `normal`, `control_no_high_importance_event`
- `2026-05-21`: prior VIX `17.44`, `normal`, `control_no_high_importance_event`
- `2026-05-22`: prior VIX `16.76`, `normal`, `control_no_high_importance_event`
- `2026-05-26`: prior VIX `16.7`, `normal`, `control_no_high_importance_event`
- `2026-05-27`: prior VIX `17.01`, `normal`, `control_no_high_importance_event`
- `2026-05-29`: prior VIX `15.74`, `normal`, `control_no_high_importance_event`
- `2026-06-01`: prior VIX `15.32`, `normal`, `control_no_high_importance_event`
- `2026-06-03`: prior VIX `15.77`, `normal`, `control_no_high_importance_event`
- `2026-06-04`: prior VIX `16.06`, `normal`, `control_no_high_importance_event`

## ประมาณการต้นทุน

```json
{
  "base_projected_cost_usd": 12.361983,
  "contingency_rate": 0.15,
  "daily_history_cost_status": "must_be_included_in_live_metadata_refresh_and_fit_inside_ceiling",
  "method": "latest completed 20-date H-A2 actual estimate basis plus 15 percent contingency",
  "source": "reports/data_cost/databento_download_result_h_a2_fresh_oos_2025_2026.json",
  "source_date_count": 20,
  "source_estimated_cost_usd": 12.361983,
  "user_approval_ceiling_usd": 14.21628
}
```

## MinTRL

ค่า MinTRL ที่แม่นยำยังไม่ทราบเพราะยังไม่มี valid timestamp-correct returns ตารางใน JSON เป็นเพียง idealized scenarios สำหรับวางแผน ห้ามใช้อนุมัติ E2

## ขั้นต่อไป

User reviews this plan. A separate approved session must refresh live metadata cost and stop if total exceeds the ceiling.
