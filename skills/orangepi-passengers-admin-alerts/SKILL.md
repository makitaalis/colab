---
name: orangepi-passengers-admin-alerts
description: Operational alerts workflow for OrangePi_passangers. Use when implementing or tuning /admin/fleet/alerts and /admin/fleet/incidents, grouped alert triage, bulk ack/silence actions, and alert monitoring APIs.
---

# OrangePi Passengers Admin Alerts

## Canon

- Module architecture: `Docs/Проект/Админ-панель (модульная разработка).md`
- Server contract: `Docs/Проект/Сервер (Central→Backend).md`
- Ops procedures: `Docs/Проект/Операции.md`

## Workflow

1) Verify alert sources:

- `/api/admin/fleet/alerts`
- `/api/admin/fleet/alerts/groups`
- `/api/admin/fleet/incidents`
- `/api/admin/fleet/alerts/actions`

2) Build triage UX:

- grouped by `code`;
- exact filters by `central_id` and `code`;
- severity and silenced toggles;
- mass actions for selected alerts and for whole group.

3) Enforce operator safety:

- no action when role is `viewer`;
- visible success/error counters per bulk operation;
- no implicit filter resets after action.

4) Validate:

```bash
python3 -m py_compile backend/app/main.py
```

5) Rollout and verify on VPS with curl + container logs.

## References

- API checklist: `references/alerts-api-checklist.md`
- Prompt templates: `references/alerts-prompts.md`
