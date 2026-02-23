# Module Gate Checklist

Use this checklist before marking an admin module phase complete.

## 1) Code boundaries

- New module code lives in `backend/app/admin_*` file(s).
- `backend/app/main.py` contains thin route wrappers only.
- Runtime/config helpers are extracted from `main.py` into dedicated modules.
- No route contract changes (UI/API path and response shape preserved).

## 2) Validation

- `python3 -m py_compile backend/app/main.py` passed.
- `python3 -m compileall -q backend/app` passed.
- Target module pages load without white screen.
- For filter-heavy pages: text inputs use debounce and support Enter-to-refresh.
- UI copy is UA-consistent for visible controls/messages.

## 3) VPS rollout and smoke

- Deploy updated files to `/opt/passengers-backend/app`.
- `docker compose -f compose.yaml -f compose.server.yaml up -d --build api`.
- Unified smoke-gate `scripts/admin_panel_smoke_gate.sh` passed.
- Smoke matrix recorded: endpoint -> HTTP status.
- `docker logs passengers-backend-api-1` has no new traceback.

## 4) Documentation sync

- Phase status updated in `Docs/Проект/Админ-панель (модульная разработка).md`.
- Prompt templates updated in `Docs/Проект/Промпты Codex (админка).md` if workflow changed.
- Skill catalog updated in `Docs/Проект/Скиллы Codex.md` if new skill added.
