---
name: orangepi-passengers-admin-fleet-overview
description: Fleet overview module workflow for OrangePi_passangers admin panel. Use when developing or refactoring /admin/fleet UI, ops feed integration, focus filters, table density/mobile behavior, and related overview APIs.
---

# OrangePi Passengers Admin Fleet Overview

## Canon

- Module architecture: `Docs/Проект/Админ-панель (модульная разработка).md`
- Prompt templates: `Docs/Проект/Промпты Codex (админка).md`
- Operations checks: `Docs/Проект/Операции.md`

## Scope

- UI route: `/admin/fleet`
- Related APIs:
  - `/api/admin/fleet/overview`
  - `/api/admin/fleet/alerts`
  - `/api/admin/fleet/incidents`
  - `/api/admin/fleet/ops-feed`

## Workflow

1) Keep UX controls stable:

- filters (`q`, `central`, `code`, `severity`);
- focus presets;
- auto refresh toggle;
- density mode and reset filters.

2) Keep status semantics stable:

- summary badges;
- priority cards;
- state line with selected filters.

3) Validate safely:

```bash
python3 -m py_compile backend/app/main.py backend/app/admin_fleet_page.py
python3 -m compileall -q backend/app
```

4) Rollout + smoke:

```bash
curl -k -u "admin:<BASIC_AUTH_PASS>" https://127.0.0.1:8443/admin/fleet
```

5) Update docs if behavior changes:

- `Docs/Проект/Операции.md`
- `Docs/Проект/Проблемы.md` (if new failure mode)

## References

- `references/fleet-ui-checklist.md`
- `references/fleet-prompts.md`
