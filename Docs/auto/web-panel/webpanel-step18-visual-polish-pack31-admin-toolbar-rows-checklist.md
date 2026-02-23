# Checklist — pack-31 (admin toolbar rows)

- date: `2026-02-17`
- target: `admin toolbar`

## Manual UI checks

- На `fleet/alerts/incidents/audit/notify-center` toolbar визуально читается как 2 ряда:
  - controls сверху,
  - filterSummary/status снизу.
- Кнопки в toolbar одинаковой “высоты” (без случайных `smallbtn` у primary controls).
- Mobile (<=760px): элементы toolbar не ломают layout, становятся в колонку.

## Automated gates

- `scripts/admin_panel_smoke_gate.sh` — PASS
- `scripts/client_panel_step17_handoff_check.sh` — PASS (`Docs/auto/web-panel/client-step17-handoff-checklist-pack31b.md`)

