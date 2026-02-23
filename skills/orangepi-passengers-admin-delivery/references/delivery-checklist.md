# Delivery Checklist

Use this checklist at the end of every admin module phase.

## 1) Boundaries

- Module code extracted into dedicated `backend/app/admin_*` files.
- `backend/app/main.py` remains thin-wrapper/composition-only.
- No route/API contract changes unless phase explicitly requires it.

## 2) Local validation

- `python3 -m py_compile ...` passed for changed files.
- `python3 -m compileall -q backend/app` passed.

## 3) VPS rollout

- Updated files copied to `/opt/passengers-backend/app`.
- `sudo docker compose -f compose.yaml -f compose.server.yaml up -d --build api`.
- `docker compose ps` shows `api` in `Up` state.

## 4) Smoke gate

- `./scripts/admin_panel_smoke_gate.sh` passed.
- Changed API endpoints return expected statuses (`200` / controlled `4xx`).
- API logs have no `ResponseValidationError|Traceback|coroutine object`.

## 5) Documentation and reuse

- Phase entry updated in `Docs/Проект/Админ-панель (модульная разработка).md`.
- New commands updated in `Docs/Проект/Операции.md`.
- Reusable prompt updated in `Docs/Проект/Промпты Codex (админка).md`.
- Skill catalog updated in `Docs/Проект/Скиллы Codex.md` if skill set changed.
