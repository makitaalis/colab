# Phase Plan Template

Use this template when planning the next extraction phase.

## Phase header

- Phase: `phase-<N>`
- Module family: `<module>`
- Scope: `<ui/api/ops>`
- Risk level: `<low|medium|high>`

## In scope

- Route(s): `<list>`
- Files to add: `<list>`
- Files to update: `<list>`
- `main.py` wrappers to keep composition-only: `<yes/no>`

## Out of scope

- `<list>`

## Gate

- compile: `python3 -m py_compile ...`
- rollout: `docker compose ... up -d --build api`
- unified smoke: `scripts/admin_panel_smoke_gate.sh ...`
- smoke endpoints: `<list>`
- log check: no traceback/validation errors

## Docs update

- `Docs/Проект/Админ-панель (модульная разработка).md`
- `Docs/Проект/Промпты Codex (админка).md`
- `Docs/Проект/Скиллы Codex.md` (if needed)
