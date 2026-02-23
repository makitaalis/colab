# Checklist — pack-30 (client toolbar rows)

- date: `2026-02-17`
- target: `client toolbar`

## Manual UI checks

- Toolbar выглядит как 2 ряда: controls сверху, meta/status снизу.
- На desktop status визуально уходит вправо (не мешает controls).
- На mobile controls и meta элементы становятся в одну колонку (100% ширины).
- Нет дублирования стилей `smallbtn` внутри toolbar (кнопки ровные по высоте/ширине).

## Automated gates

- `scripts/admin_panel_smoke_gate.sh` — PASS
- `scripts/client_panel_step17_handoff_check.sh` — PASS (`Docs/auto/web-panel/client-step17-handoff-checklist-pack30b.md`)

