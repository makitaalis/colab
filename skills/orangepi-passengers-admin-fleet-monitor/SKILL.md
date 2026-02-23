---
name: orangepi-passengers-admin-fleet-monitor
description: Fleet monitor workflow for OrangePi_passangers admin panel. Use when changing monitor snapshot composition (/api/admin/fleet/monitor, /api/admin/fleet/health, /api/admin/fleet/health/notify-auto), attention logic, monitor policy integration, or refactoring monitor helpers into modules.
---

# OrangePi Passengers Admin Fleet Monitor

## Canon

- Module architecture: `Docs/Проект/Админ-панель (модульная разработка).md`
- Server contract: `Docs/Проект/Сервер (Central→Backend).md`
- Operations checks: `Docs/Проект/Операции.md`

## Scope

- `/api/admin/fleet/monitor`
- `/api/admin/fleet/health`
- `/api/admin/fleet/health/notify-auto`
- monitor snapshot composition (`state`, `fleet`, `incidents`, `notifications`, `security`, `attention`, `alerts`)

## Workflow

1) Preserve contract:

- keep response keys and meanings stable;
- keep `window`, `limit_alerts`, `limit_attention` behavior;
- keep role restrictions for notify endpoints.

2) Refactor safely:

- isolate monitor composition in dedicated module;
- keep thin-wrapper in `main.py`;
- pass dependencies explicitly where possible.

3) Validate local:

```bash
python3 -m py_compile backend/app/main.py backend/app/admin_fleet_monitor_ops.py
python3 -m compileall -q backend/app
```

4) Rollout + smoke on server:

```bash
curl -sS -H "Authorization: Bearer <TOKEN>" "http://10.66.0.1/api/admin/fleet/monitor?window=24h"
curl -sS -H "Authorization: Bearer <TOKEN>" "http://10.66.0.1/api/admin/fleet/health?window=24h"
curl -sS -X POST -H "Authorization: Bearer <TOKEN>" "http://10.66.0.1/api/admin/fleet/health/notify-auto?dry_run=1&force=1"
```

5) Record changes:

- update `Docs/Проект/Админ-панель (модульная разработка).md`
- update `Docs/Проект/Проблемы.md` if a new failure mode appears

## References

- `references/monitor-checklist.md`
- `references/monitor-prompts.md`
