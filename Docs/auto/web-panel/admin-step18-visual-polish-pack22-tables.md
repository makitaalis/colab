# Admin step-18 (pack-22): Tables polish (readability + scroll rhythm)

Дата: 2026-02-17

## Цель

Сделать большие таблицы читаемыми без визуальной перегрузки:

- стабильный скролл-контейнер с предсказуемой высотой,
- контрастный sticky-header,
- лёгкий zebra + hover для сканирования строк,
- единый “ритм” паддингов и чисел (tabular-nums).

## Изменения (Core)

Файл: `backend/app/admin_ui_kit.py`

1. `.tableWrap`:
- `max-height: 72vh` + `scrollbar-gutter: stable`,
- мягкий фон/рамка, скроллбар стилизован (webkit + scrollbar-color).
2. `table/th/td`:
- `min-width: 920px`, `font-variant-numeric: tabular-nums`,
- компактные паддинги, sticky `th`, `white-space: nowrap`,
- zebra (`nth-child(even)`) + hover подсветка.

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (`Docs/auto/web-panel/admin-step18-visual-polish-pack22-tables-checklist.md`).

