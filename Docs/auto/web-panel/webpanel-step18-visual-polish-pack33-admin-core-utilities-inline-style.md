# Web-panel Step-18 Visual Polish Pack-33: Admin Core Utilities, Inline-Style Reduction

Дата: 2026-02-18

## Цель

- Снизить количество повторяющихся inline-стилей (`style="..."`) и зафиксировать единые “примитивы” в Core (чтобы домены не расходились).
- Поддержать визуальную чистоту и предсказуемый ритм: одинаковые отступы, одинаковые min-width контролов, одинаковые “статус-боксы”.

## Что сделано (Core)

- `backend/app/admin_ui_kit.py`
  - Вынесен общий паттерн “status box” в Core: `.wgBox`, `.wgTitle`, `.wgSummary`, `.wgHint`.
  - Добавлены Core utility-классы (для замены повторяющихся `style="..."`):
    - отступы: `.uMt6/.uMt8/.uMt10/.uMt12/.uMt14`, `.uMb6/.uMb14`;
    - выравнивание: `.uJcStart`;
    - inline row (лейблы с checkbox): `.uInlineRow`;
    - min-width inputs: `.uMinW150/.uMinW190/.uMinW240`;
    - max-height: `.uMaxH40vh`;
    - pre padding: `.tableWrapPre` (использовать как `class="tableWrap tableWrapPre"`).

## Что сделано (Domains)

- `backend/app/admin_overview_page.py`
  - Убраны повторяющиеся inline-отступы, приведено к Core utilities.
  - Удалены локальные определения `.wgBox/.wgTitle/.wgSummary/.wgHint` (теперь в Core).
- `backend/app/admin_commission_page.py`
  - Убраны inline `min-width`, `margin-top/margin-bottom`, `inline-flex` лейблы; заменено на Core utilities.
  - Удалены локальные `.wgBox/.wgSummary` стили (теперь в Core).
- `backend/app/admin_fleet_policy_page.py`
  - Toolbars переведены с inline стилей на `uJcStart + uMt12`.
  - `tableWrap max-height:40vh` переведён на `.uMaxH40vh`.
- `backend/app/admin_fleet_notifications_page.py`
  - Toolbars и отступы secondary-block переведены на utilities (убраны inline стили).
- `backend/app/admin_wg_page.py`
  - Убраны inline margin/max-height там, где это повторяется и уже есть в Core.
  - Pre-блоки переведены на `tableWrapPre` и `.uMaxH40vh` (padding больше не через inline).

## Server-first валидация

- Deploy на VPS: `rsync` изменённых файлов в `/opt/passengers-backend/app/`.
- `python3 -m py_compile` для изменённых модулей: OK.
- Restart: `docker compose ... restart api`: OK.
- `scripts/admin_panel_smoke_gate.sh`: PASS.

## Примечания

- Pack-33 в основном “стандартизирующий”: визуальные изменения минимальны, цель в консистентности и снижении дрейфа между доменами.

