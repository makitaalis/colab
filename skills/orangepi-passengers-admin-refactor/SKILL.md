---
name: orangepi-passengers-admin-refactor
description: Stage-by-stage refactor workflow for splitting backend/app/main.py admin routes into module files (without behavior changes). Use when extracting alerts/fleet/policy pages and APIs into separate modules with safe rollout and rollback checks.
---

# OrangePi Passengers Admin Refactor

## Canon

- Architecture target: `Docs/Проект/Админ-панель (модульная разработка).md`
- Prompt set: `Docs/Проект/Промпты Codex (админка).md`
- Ops checks: `Docs/Проект/Операции.md`

## Rules

1) Refactor by module, not by file chunks.
2) Keep URL contracts unchanged for UI and API.
3) Keep role behavior unchanged (`viewer/operator/admin`).
4) Move logic first, then routes, then shared helpers.
5) Every step must compile and pass curl smoke before next move.
6) `main.py` stays composition-only (no new heavy runtime/DB logic).

## Workflow

1) Identify extraction boundaries in `backend/app/main.py`:

- module routes (`/admin/...`, `/api/admin/...`);
- helper functions used only by this module;
- dependency list needed from db/env/auth.

2) Extract to `backend/app/<module>_ops.py`:

- pure business logic;
- no direct side effects outside return payload.

3) Replace in `main.py` with thin routes:

- parse request/filters;
- call extracted functions;
- keep same response schema.

4) Validate local:

```bash
python3 -m py_compile backend/app/main.py backend/app/<module>_ops.py
python3 -m compileall -q backend/app
```

5) Rollout on VPS:

```bash
scp backend/app/main.py backend/app/<module>_ops.py alis@207.180.213.225:/tmp/
ssh alis@207.180.213.225 'sudo install -m 644 -o alis -g alis /tmp/main.py /opt/passengers-backend/app/main.py && sudo install -m 644 -o alis -g alis /tmp/<module>_ops.py /opt/passengers-backend/app/<module>_ops.py && cd /opt/passengers-backend && sudo docker compose -f compose.yaml -f compose.server.yaml up -d --build api'
```

6) Smoke:

- API status codes (200/4xx expected only);
- HTML route loads without JS crash;
- logs show no startup/runtime exceptions.

## References

- `references/extract-checklist.md`
- `references/rollback-checklist.md`
