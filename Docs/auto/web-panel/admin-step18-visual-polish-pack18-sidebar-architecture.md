# Admin step-18 (pack-18): Sidebar architecture (Simple = hub-only)

Дата: 2026-02-17

## Цель

Сократить визуальную перегрузку левого меню, закрепить паттерн `меню (домен) -> подменю (page subnav)` и сохранить быстрый доступ к ключевым разделам без “простыни” пунктов.

## Изменения (Core / admin shell)

Файл: `backend/app/admin_ui_kit.py`

1. `Simple` режим sidebar стал “hub-only”:
- подпункты домена скрыты, кроме активного (чтобы было видно текущую страницу);
- при вводе в поиск sidebar временно раскрывает подпункты (класс `body.sidebar-searching`).
2. `Simple` режим больше не прячет целиком полезные мини-блоки:
- скрываются только heavy-блоки: `quick`, `hub`, `mission`, `cheat`;
- `favorites`, `recent`, `session` остаются доступными.
3. `Фокус` режим:
- кнопка перенесена в верхнюю панель инструментов sidebar (не зависит от видимости “командного центра”).

## UX-эффект

- Левый sidebar в `Simple` режиме читабельный: 5 доменов + обране/останні, без перегруза.
- Переходы по подменю происходят через `page subnav` на странице (2 уровень).
- Поиск по меню работает “как палитра”: в момент поиска доступны все пункты, включая скрытые подпункты.

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (report: `Docs/auto/web-panel/admin-step18-visual-polish-pack18-sidebar-architecture-checklist.md`).

