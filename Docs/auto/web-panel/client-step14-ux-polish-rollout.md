# Client MVP Step-14 Rollout (UX polish navigation + progressive disclosure)

- date: `2026-02-16`
- mode: `server-first`
- target server: `207.180.213.225` (`/opt/passengers-backend`)
- support actor used for client verification: `support-sys-0001`

## Scope

Step-14 closes final client-shell UX polish:

1. Compact sidebar mode for client panel (`clientShell.sideCompact`) with persistent state.
2. Two-level navigation groups rendered as collapsible submenu sections (`<details>`).
3. Progressive disclosure for table-heavy pages via `Колонки: базово/детально` toggle.
4. Preservation of previous role-aware account pattern (`summary -> form -> support details`).

## Code changes

- `backend/app/client_ui_kit.py`
  - Added compact sidebar toggle and persistence (`passengers_client_sidebar_compact_v1`).
  - Added persistent side-group open state (`passengers_client_sidebar_group_<group>_v1`).
  - Added progressive columns mode with persistence (`passengers_client_tables_progressive_v1`).
  - Switched sidebar rendering to grouped `<details>` navigation with short markers.
  - Added shell bootstrap `window.ClientUiKit.initShell()`.
- `backend/app/client_home_page.py`
  - Added table progressive toggle button.
  - Marked route column as `progressiveCol`.
- `backend/app/client_vehicles_page.py`
  - Added table progressive toggle button.
  - Marked secondary columns (`route`, `queue/incidents`, `updated`, `hint`) as `progressiveCol`.
- `backend/app/client_tickets_page.py`
  - Added table progressive toggle button.
  - Marked comment column as `progressiveCol`.
- `backend/app/client_status_page.py`
  - Added table progressive toggle button.
  - Marked category column as `progressiveCol`.

## Server rollout

1. Synced changed files to server:
   - `rsync ... backend/app/client_*.py -> /opt/passengers-backend/app/`
2. Server compile gate:
   - `python3 -m py_compile app/client_ui_kit.py app/client_home_page.py app/client_vehicles_page.py app/client_tickets_page.py app/client_status_page.py`.
3. API rebuild/restart:
   - `sudo docker compose -f compose.yaml -f compose.server.yaml up -d --build api`.

## Validation

- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"` -> `PASS`
- `./scripts/client_panel_regression_check.sh --admin-user support-sys-0001 --admin-pass-file "pass client support sys-0001 panel step13-rotated"` -> `PASS`
- `python3 scripts/client_panel_step7b_audit.py --admin-user support-sys-0001 --admin-pass-file "pass client support sys-0001 panel step13-rotated" --write Docs/auto/web-panel/client-step7b-ux-audit-support-sys-0001-step14.md` -> `PASS`
- `./scripts/server_security_posture_check.sh --server-host 207.180.213.225 --server-user alis --admin-user admin --admin-pass <from pass file>` -> `PASS`

## Notes

- During first warmup run, `/api/admin/wg/conf` returned transient `503`; repeated smoke-gate after API warmup returned stable `200` and final `PASS`.
- No backend API schema changes; step is UI/UX-only for client shell and table readability.
