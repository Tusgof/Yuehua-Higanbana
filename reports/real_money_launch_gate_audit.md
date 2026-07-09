# Real-Money Launch Gate Audit

- Status: `blocked`
- Real money allowed: `False`
- Blocker count: 14

## Blockers

- `checklist_missing:backup_close_order_plan_tested`
- `checklist_missing:cash_account_constraints_documented`
- `checklist_missing:defined_risk_only_confirmed`
- `checklist_missing:forced_close_tested`
- `checklist_missing:kill_switch_tested`
- `checklist_missing:options_permission_approved`
- `checklist_missing:research_acceptance_passed`
- `checklist_missing:user_real_money_approval_recorded`
- `ibkr_config_not_live:paper`
- `ibkr_options_permission_not_confirmed`
- `ibkr_transmit_disabled`
- `kill_switch_enabled`
- `research_acceptance_not_approved:blocked`
- `research_acceptance_real_money_not_allowed`

## Source Paths

- `acceptance`: `reports\research_acceptance_evaluation.json`
- `checklist`: `config\real_money_launch_checklist.example.json`
- `ibkr_config`: `config\ibkr.example.json`
- `kill_switch`: `config\kill_switch.json`
