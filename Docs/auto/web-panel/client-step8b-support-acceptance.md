# Client Step-8b Support Acceptance

- date: `2026-02-16`
- target: `https://207.180.213.225:8443`

## Scope

Проведен операторский acceptance-run режима `admin-support` с контролируемым rollback:

1. Временное включение:
- `CLIENT_SUPPORT_USERS=admin` в `/opt/passengers-backend/.env`
- `docker compose -f compose.yaml -f compose.server.yaml up -d --build api`

2. Проверка support-режима:
- `/api/client/whoami` -> `role=admin-support`, `support_console=true`
- `scripts/admin_panel_smoke_gate.sh` -> `PASS`
- `scripts/client_panel_regression_check.sh` -> `PASS`
- `scripts/client_panel_step7b_audit.py` -> `PASS`

3. Rollback:
- восстановлен backup `.env.step8b.20260216162039.bak`
- `docker compose -f compose.yaml -f compose.server.yaml up -d --build api`
- `/api/client/whoami` -> `role=client`, `support_console=false`
- повторный `scripts/admin_panel_smoke_gate.sh` -> `PASS`

## Verdict

- status: `PASS`
- server state after rollback: `client` baseline restored.
