---
name: orangepi-passengers-admin-module-governance
description: Governance workflow for modular admin panel development in OrangePi_passangers. Use when defining module boundaries, planning extraction phases from backend/app/main.py, enforcing deploy/smoke gates, and syncing docs/prompts/skills for reproducible team rollout.
---

# OrangePi Passengers Admin Module Governance

## Canon

- Architecture and phases: `Docs/Проект/Админ-панель (модульная разработка).md`
- Prompt pack: `Docs/Проект/Промпты Codex (админка).md`
- Skills index: `Docs/Проект/Скиллы Codex.md`

## Workflow

1) Lock module scope for current phase:

- one module family per phase (`alerts-ops`, `policy-kpi`, `notify-center`, etc.);
- keep URL contracts unchanged;
- keep role behavior unchanged (`viewer/operator/admin`).

2) Implement with thin-routes policy:

- move heavy UI/API logic into `backend/app/admin_*`;
- move repeated UI shell/CSS into `backend/app/admin_ui_kit.py`;
- keep only wrapper routes in `backend/app/main.py`;
- avoid cross-module DOM coupling.

3) Run deploy gate:

```bash
python3 -m py_compile backend/app/main.py
python3 -m compileall -q backend/app
```

Then rollout to VPS and check:

- UI routes: `/admin/fleet/...` return `200`;
- API routes: `/api/admin/fleet/...` return `200` or expected `4xx`;
- unified gate `scripts/admin_panel_smoke_gate.sh` returns PASS;
- `docker logs` have no `ResponseValidationError`/`Traceback`.

4) Keep `main.py` composition-only:

- runtime/config helpers are extracted into dedicated modules (example: `admin_runtime_config.py`);
- route handlers in `main.py` only validate input, call ops/runtime functions, and return response;
- no new DB-heavy logic in handlers.

5) Sync governance artifacts:

- update module status and next phase in `Docs/Проект/Админ-панель (модульная разработка).md`;
- update reusable prompts in `Docs/Проект/Промпты Codex (админка).md`;
- update skill registry in `Docs/Проект/Скиллы Codex.md` when new skills appear.

## References

- module gate checklist: `references/module-gate-checklist.md`
- phase planning template: `references/phase-plan-template.md`
