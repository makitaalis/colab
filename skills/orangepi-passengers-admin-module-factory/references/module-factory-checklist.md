# Module Factory Checklist

## 1) Boundary

- Module scope is limited to one UI route + one API family.
- Role behavior (`viewer/operator/admin`) is explicitly defined.

## 2) Code layout

- UI page extracted to `admin_<module>_page.py`.
- API logic extracted to `admin_<module>_ops.py` (if needed).
- `main.py` only contains thin wrappers.

## 3) UI helper consistency

- Page uses `render_admin_shell(...)`.
- Page JS uses `window.AdminUiKit` primitives.
- No duplicated local helper boilerplate.

## 4) Delivery gates

- `py_compile` and `compileall` are green.
- VPS deploy completed (`api` is Up).
- `scripts/admin_panel_smoke_gate.sh` is PASS.
- Target module UI/API curl checks return expected status.
- API log scan has no `ResponseValidationError|Traceback|coroutine object`.

## 5) Docs sync

- `Docs/Проект/Админ-панель (модульная разработка).md` updated.
- `Docs/Проект/Операции.md` updated.
- `Docs/Проект/Промпты Codex (админка).md` updated.
