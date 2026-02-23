# Toolkit Migration Checklist

Use this checklist before closing a toolkit migration phase.

## 1) Shared layer

- `backend/app/admin_ui_kit.py` exists and is used by target pages.
- Shared CSS/tokens live in toolkit, not duplicated in each page file.
- Shared JS helper (`window.AdminUiKit`) is present and used by target pages.

## 2) Page migration

- Target page uses `render_admin_shell(...)`.
- Existing route and API endpoint usage unchanged.
- JS action payloads unchanged.

## 3) UX baseline

- `Скинути фільтри` available for filter-heavy page.
- Text filters use debounce.
- Enter key triggers immediate refresh.
- local page scripts do not duplicate helper boilerplate (`setStatus`/`apiGet`/`scheduleRefresh` copy-paste).

## 4) Delivery checks

- `py_compile` and `compileall` passed.
- VPS deploy completed and `api` container is `Up`.
- `scripts/admin_panel_smoke_gate.sh` passed.
- HTML checks confirm `window.AdminUiKit` on migrated pages.
- Logs have no `ResponseValidationError|Traceback|coroutine object`.

## 5) Docs sync

- `Docs/Проект/Админ-панель (модульная разработка).md` phase updated.
- `Docs/Проект/Операции.md` rollout commands updated.
- `Docs/Проект/Промпты Codex (админка).md` prompt templates updated.
