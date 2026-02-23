---
name: orangepi-passengers-admin-modules
description: Modular admin panel development workflow for OrangePi_passangers. Use when splitting admin UI/API into modules, adding a new admin module route, defining module boundaries, writing rollout checks, and keeping module docs/prompts in sync.
---

# OrangePi Passengers Admin Modules

## Canon

- Module rules: `Docs/Проект/Админ-панель (модульная разработка).md`
- Prompt templates: `Docs/Проект/Промпты Codex (админка).md`
- Project index: `Docs/Проект/INDEX.md`

## Workflow

1) Choose module scope and boundary:

- UI route (`/admin/fleet/...`)
- API route (`/api/admin/fleet/...`)
- role matrix (`viewer/operator/admin`)

2) Implement module atomically:

- add/adjust API first;
- add/adjust UI for same module;
- avoid coupling to foreign module DOM ids.

3) Validate:

```bash
python3 -m py_compile backend/app/main.py
python3 -m compileall -q backend/app
```

4) Deploy and smoke-check on server:

```bash
scp backend/app/main.py alis@207.180.213.225:/tmp/passengers-main.py
ssh alis@207.180.213.225 'sudo install -m 644 -o alis -g alis /tmp/passengers-main.py /opt/passengers-backend/app/main.py && cd /opt/passengers-backend && sudo docker compose -f compose.yaml -f compose.server.yaml up -d --build api'
```

5) Keep docs aligned:

- update `Docs/Проект/Операции.md` (how to use/check);
- update `Docs/Проект/Проблемы.md` (new failure mode if introduced);
- update `Docs/Проект/INDEX.md` for new module page/doc.

## References

- module template: `references/module-template.md`
- rollout smoke template: `references/rollout-smoke.md`
