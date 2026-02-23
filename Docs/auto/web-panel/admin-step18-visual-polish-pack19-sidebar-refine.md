# Admin step-18 (pack-19): Sidebar refine (Simple: usable hubs + search раскрывает)

Дата: 2026-02-17

## Цель

Добить левое меню до состояния “минималистично, но удобно”:

- `Simple` режим должен показывать все домены как быстрые входы (hub links), а не только заголовки групп.
- Поиск по меню должен раскрывать нужные пункты, даже если группы были свернуты.
- Верхние переключатели sidebar должны выглядеть аккуратно и не быть визуально “сжатыми”.

## Изменения

Файл: `backend/app/admin_ui_kit.py`

1. Sidebar tools layout:
- `sideNavTools` переключён на сетку `2x2` для кнопок (вместо узкой строки `4x1`).
2. Simple-mode nav behavior:
- в `Simple` принудительно разворачиваются группы меню (показываются хотя бы hub-пункты всех доменов);
- подпункты скрыты, кроме активного (чтобы был контекст текущей страницы).
3. Search-mode behavior:
- при вводе в поиск (`sidebar-searching`) группы меню принудительно разворачиваются, чтобы результаты были видимы.
4. Focus-mode compatibility:
- `Фокус`-режим сохраняет “hub/mission” даже если включён `Simple` (через CSS override).

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (`Docs/auto/web-panel/admin-step18-visual-polish-pack19-sidebar-refine-checklist.md`).

