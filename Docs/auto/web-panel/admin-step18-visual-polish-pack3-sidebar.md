# Admin step-18 visual polish: pack-3 (sidebar без перегруза)

Дата: 2026-02-17

Цель: убрать визуальную перегрузку левого sidebar в admin panel, сохранив доступ к “операционным” мини-блокам (hub/mission/shortcuts) без длинной прокрутки.

## Изменения (Core)

Файл: `backend/app/admin_ui_kit.py`.

1) Сворачиваемые мини-блоки sidebar
- Блоки `quick/hub/mission/cheat/favorites/recent/session` получили toggle (chevron) и тело `sideMiniBody-*`.
- Состояние сохраняется в `localStorage`:
  - key: `passengers_admin_sidebar_collapsed_mini_v1`
  - default: свернуты тяжелые блоки (`quick/hub/mission/cheat/recent/session`), `favorites` открыт.

2) Исправлена семантика кнопки режима sidebar `Просто/Розширено`
- `aria-pressed` теперь отражает состояние Simple-mode (Simple=true).
- Текст кнопки соответствует текущему режиму (`Просто` или `Розширено`).

## Проверки (server-first)

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 handoff checklist (регрессия): `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack3-sidebar-collapsible.md`

Примечание: server `docker compose --build` может временно падать из-за DNS/доступа к `auth.docker.io`; для UI-правок достаточно `docker compose restart api` после `rsync`.

## Результат для UX

- Sidebar остаётся коротким даже в режиме `Розширено`.
- Оператор может включать “хаб” и “центр інцидентів” по необходимости, без постоянного вертикального шума.
- Поведение совместимо с `Simple`-режимом (мини-блоки скрываются целиком).

