---
name: orangepi-passengers-admin-delivery
description: End-to-end phased delivery workflow for OrangePi_passangers admin panel modules. Use when implementing a module phase (code changes, VPS deploy, smoke gate, docs/prompts/skills sync) without regressions.
---

# OrangePi Passengers Admin Delivery

## Canon

- Architecture and phase status: `Docs/Проект/Админ-панель (модульная разработка).md`
- Ops runbook: `Docs/Проект/Операции.md`
- Prompt pack: `Docs/Проект/Промпты Codex (админка).md`
- Skill catalog: `Docs/Проект/Скиллы Codex.md`

## Workflow

1) Lock phase scope:

- one module family per phase;
- no API/URL contract changes;
- no role matrix regressions (`viewer/operator/admin`).

2) Implement with thin-route policy:

- business logic in `backend/app/admin_*`;
- `backend/app/main.py` only as route composition layer.

3) Validate local:

```bash
python3 -m py_compile backend/app/main.py
python3 -m compileall -q backend/app
```

4) Rollout to VPS (`/opt/passengers-backend/app`) and rebuild `api`.

5) Run smoke gate:

- `./scripts/admin_panel_smoke_gate.sh ...`;
- targeted API checks for changed endpoints;
- log scan without `ResponseValidationError|Traceback|coroutine object`.

6) Sync artifacts:

- phase status in `Docs/Проект/Админ-панель (модульная разработка).md`;
- operational commands in `Docs/Проект/Операции.md`;
- reusable prompt in `Docs/Проект/Промпты Codex (админка).md`;
- skill registry in `Docs/Проект/Скиллы Codex.md` when adding/updating skill.

## References

- delivery checklist: `references/delivery-checklist.md`
- phase prompt template: `references/phase-prompt-template.md`
