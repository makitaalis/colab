# Client Step-13 Lifecycle Automation Pack

- generated_at_utc: `2026-02-16T16:00:27Z`
- server: `207.180.213.225`

## Implemented Tooling

- `scripts/client_support_rotation_batch.sh`
  - batch rotation по plan-файлу `actor|new_password_file|old_password_file`
  - использует `scripts/client_support_lifecycle_rollout.sh --action rotate`
- `scripts/client_support_inventory_report.sh`
  - локальный inventory/drift отчёт из реального server state
- `scripts/install_client_support_lifecycle_timer.sh`
  - устанавливает server timers:
    - `passengers-client-support-inventory.timer` (daily)
    - `passengers-client-support-rotation-reminder.timer` (monthly)

## Real Server Execution

1. Batch rotation выполнен для активного actor:
- plan: `Docs/auto/web-panel/client-step13-rotation-plan.txt`
- actor: `support-sys-0001`
- old password после rotate -> `401`
- new password после rotate -> `200`

2. Timers installed on server:
- `passengers-client-support-inventory.timer` => `active`
- `passengers-client-support-rotation-reminder.timer` => `active`

3. Server-generated reports:
- `/opt/passengers-backend/ops-reports/client-support-inventory-latest.md`
- `/opt/passengers-backend/ops-reports/client-support-rotation-reminder.txt`

## Current State

- `CLIENT_SUPPORT_USERS=support-sys-0001`
- `CLIENT_SCOPE_BINDINGS=support-sys-0001:sys-0001`
- `CLIENT_AUTH_USERS=admin,support-sys-0001`

## Validation

- `./scripts/client_support_rotation_batch.sh --plan-file Docs/auto/web-panel/client-step13-rotation-plan.txt --admin-pass-file "pass admin panel"` => `PASS`
- `./scripts/client_support_inventory_report.sh --write Docs/auto/web-panel/client-support-inventory-latest.md` => `PASS` (`status=PASS`)
- `./scripts/admin_panel_smoke_gate.sh` => `PASS`
- `./scripts/client_panel_regression_check.sh --admin-user support-sys-0001 ...` => `PASS`
- `python3 scripts/client_panel_step7b_audit.py --admin-user support-sys-0001 --write Docs/auto/web-panel/client-step7b-ux-audit-support-sys-0001-step13.md` => `PASS`
- `./scripts/server_security_posture_check.sh ...` => `PASS`
