---
name: orangepi-passengers-admin-module-factory
description: Module factory workflow for OrangePi_passangers admin panel. Use when creating a new admin module block (UI route + API route + docs/prompts/skills sync) with consistent boundaries and rollout gates.
---

# OrangePi Passengers Admin Module Factory

## Canon

- Module architecture: `Docs/Проект/Админ-панель (модульная разработка).md`
- Ops rollout checks: `Docs/Проект/Операции.md`
- Prompt pack: `Docs/Проект/Промпты Codex (админка).md`
- Skill catalog: `Docs/Проект/Скиллы Codex.md`

## Workflow

1) Freeze module boundary:

- module name and ownership;
- one UI route (`/admin/fleet/<module_slug>`);
- one API family (`/api/admin/fleet/<module_slug>*`);
- role matrix (`viewer/operator/admin`).

2) Implement by layers:

- create page file `backend/app/admin_<module_slug>_page.py` using `render_admin_shell(...)`;
- create ops file `backend/app/admin_<module_slug>_ops.py` if API logic is non-trivial;
- keep `backend/app/main.py` as thin route wrappers only.

3) Reuse toolkit helpers:

- use `window.AdminUiKit` methods for status/api/debounce/enter/clear filters;
- avoid local helper duplication in page scripts.

4) Validate locally:

```bash
python3 -m py_compile backend/app/main.py backend/app/admin_<module_slug>_page.py backend/app/admin_<module_slug>_ops.py
python3 -m compileall -q backend/app
```

5) Rollout and verify:

- deploy updated files to `/opt/passengers-backend/app`;
- rebuild API container with compose;
- run `scripts/admin_panel_smoke_gate.sh`;
- run targeted curl checks for module UI/API and log scan.

6) Sync documentation artifacts:

- update phase status in `Docs/Проект/Админ-панель (модульная разработка).md`;
- add/refresh operational commands in `Docs/Проект/Операции.md`;
- add reusable prompt in `Docs/Проект/Промпты Codex (админка).md`.

## References

- module factory checklist: `references/module-factory-checklist.md`
