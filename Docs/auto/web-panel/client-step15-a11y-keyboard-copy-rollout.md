# Client MVP Step-15 Rollout (a11y + keyboard flow + copy audit)

- date: `2026-02-16`
- mode: `server-first`
- target server: `207.180.213.225` (`/opt/passengers-backend`)
- support actor for validation: `support-sys-0001`

## Scope

Step-15 closes accessibility and keyboard-flow baseline for client shell without API changes:

1. Accessibility baseline in shell (`skip-link`, focus-visible, aria-live status).
2. Keyboard flow for fast navigation and toolbar actions.
3. Final UA copy audit for account domain (`profile/notifications`).
4. Regression/audit marker checks updated for new shell elements.

## Code changes

- `backend/app/client_ui_kit.py`
  - Added `skipLink` to jump to main content (`#clientMainContent`).
  - Added global `:focus-visible` and `srOnly` utilities.
  - Added keyboard hints in sidebar.
  - Added `aria-label` on sidebar and `id="clientMainContent"` target on main block.
  - Upgraded `setStatus()` to `role="status"` + `aria-live="polite"`.
  - Added keyboard shortcuts:
    - `/` -> focus first toolbar search/text/select,
    - `Esc` -> blur active editable control,
    - `Alt+Shift+M` -> compact sidebar toggle,
    - `Alt+Shift+K` -> table columns toggle,
    - `Alt+Shift+S` -> focus sidebar active link,
    - `Alt+Shift+T` -> focus first toolbar action.
- `backend/app/client_profile_page.py`
  - Copy audit: support details labels localized (`Актор`, `Контур доступу`, `Попередній перегляд payload`).
  - Filter summary text localized (`контакт=готовий/відсутній`).
- `backend/app/client_notifications_page.py`
  - Copy audit: preset labels localized (`Шаблон: критично/збалансовано/реальний час`).
  - Summary/filter labels localized (`пріоритет`, `дайджест`, `канали`).
- `scripts/client_panel_regression_check.sh`
  - Added marker checks for `skipLink`, `sideCompactToggle`, `clientMainContent`.
- `scripts/client_panel_step7b_audit.py`
  - Added marker checks for new step-15 accessibility shell markers.

## Server rollout

1. Synced changed files to server:
   - `backend/app/client_ui_kit.py`
   - `backend/app/client_profile_page.py`
   - `backend/app/client_notifications_page.py`
2. Server compile gate:
   - `python3 -m py_compile app/client_ui_kit.py app/client_profile_page.py app/client_notifications_page.py`.
3. API rebuild/restart:
   - `sudo docker compose -f compose.yaml -f compose.server.yaml up -d --build api`.

## Validation

- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"` -> `PASS`
- `./scripts/client_panel_regression_check.sh --admin-user support-sys-0001 --admin-pass-file "pass client support sys-0001 panel step13-rotated"` -> `PASS`
- `python3 scripts/client_panel_step7b_audit.py --admin-user support-sys-0001 --admin-pass-file "pass client support sys-0001 panel step13-rotated" --write Docs/auto/web-panel/client-step7b-ux-audit-support-sys-0001-step15.md` -> `PASS`
- `./scripts/server_security_posture_check.sh --server-host 207.180.213.225 --server-user alis --admin-user admin --admin-pass <from pass file>` -> `PASS`

## Notes

- First smoke-gate run after restart returned transient `503` for `/api/admin/*` warmup endpoints; repeated run reached stable `200` and final `PASS`.
- No backend API/schema changes in step-15.
