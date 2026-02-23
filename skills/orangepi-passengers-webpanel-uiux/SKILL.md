---
name: orangepi-passengers-webpanel-uiux
description: UI/UX стандарты и этапный workflow для web-панели (admin+client): единый Core, IA меню, визуальная чистота, server-first deploy и синхронизация документации.
---

# orangepi-passengers-webpanel-uiux

Эта skill применяется для любых изменений UI/UX web-панели (admin/client), особенно если нужно:

- сократить визуальную перегрузку (sidebar, header, таблицы, “простыни” на страницах);
- перестроить IA меню (`раздел -> подменю`) и разнести контент по страницам;
- зафиксировать единый “канон” компонентов в Core и привести домены к стандарту;
- делать правки “пакетами” с server-first проверкой и обновлением docs.

## Карта модулей (Core vs Domains)

Core (общее ядро):

- `backend/app/admin_ui_kit.py` (admin shell + CSS/JS primitives)
- `backend/app/client_ui_kit.py` (client shell + CSS/JS primitives)
- `backend/app/admin_core/navigation.py` (admin: page-subnav)
- `backend/app/client_core/navigation.py` (client: nav-groups)
- `backend/app/admin_domains/domain_catalog.py` (admin: домены/роуты)
- `backend/app/client_domains/domain_catalog.py` (client: домены/роуты)

Domains (страницы):

- `backend/app/admin_*_page.py`
- `backend/app/client_*_page.py`

Docs (канон IA и стандартов):

- `Docs/Проект/Веб-панель/Ядро (Core).md`
- `Docs/Проект/Веб-панель/Архитектура меню (admin+client).md`
- `Docs/Проект/Веб-панель/Домен *.md`
- `Docs/Проект/Паспорт релиза документации.md`

## Стандарты UI/UX (обязательные правила)

1) IA навигации

- 2 уровня: `раздел -> подменю` (sidebar + page subnav).
- В sidebar раскрыт только активный раздел.
- В `Simple` sidebar: минимальная навигация, без вспомогательных mini-блоков.
- В `Фокус` sidebar: nav-only (только меню).
- Любое изменение меню делается через `*_domains/domain_catalog.py` и `*_core/navigation.py`, а не “ручными ссылками” в шаблоне.

2) Header/Chips/Subnav

- Chips в header = только контекст (роль/режим/время/статус), не навигация.
- В chips запрещены ссылки (`<a class="chip" ...>`): любые переходы должны жить в `page subnav` или в `toolbar/sectionTools`.
- Subnav и chips не должны раздувать header: используем горизонтальный scroll (nowrap + overflow-x).

3) Структура страницы (визуальная чистота)

- Один экран = один primary-сценарий.
- Secondary-контент: в `<details>` или на отдельную подстраницу.
- Заголовки секций: использовать Core классы (`sectionTitle/sectionKicker/sectionHead/sectionTools`).

3.1) Client toolbar rhythm

- `clientToolbar` = controls-only (filters/actions/toggles/copyLink/meta/status).
- Время обновления (`updatedAt`) относится к контексту и должно жить в `chips_html`, а не в toolbar.
- `clientToolbar` должен быть визуальным контейнером (padding/border/background) уровня Core, чтобы страницы выглядели одинаково.
- `toolbar_html` на client страницах оформляется 2 рядами:
  - `<div class="toolbarMain">...</div>` (controls),
  - `<div class="toolbarMeta">...</div>` (metaChip/status).
- Внутри `clientToolbar` не использовать `class="smallbtn"` для кнопок (стиль уже задаётся Core через `.clientToolbar button`).

3.2) Admin toolbar rhythm

- Admin `toolbar` на страницах оформляется 2 рядами:
  - `<div class="toolbarMain">...</div>` (controls + advanced `<details>`),
  - `<div class="toolbarMeta">...</div>` (filterSummary/status).
- Внутри `toolbar` избегать `class="smallbtn"` для основных действий (особенно `copyLink`): toolbar должен держать единый размер контролов.
- Для навигационных ссылок внутри header toolbar использовать `<a class="toolbarBtn" ...>` (визуально как кнопка, но остаётся ссылкой).

4) Таблицы

- Таблицы обязательно в `.tableWrap` (скролл, sticky header, zebra/hover).
- Для пустых таблиц: Core empty-state (через `applyEmptyTables()` + `data-empty-*`).
- Числа: `tabular-nums`.

4.1) Inline styles (запрещены как дефолт)

- Повторяющиеся паттерны обязаны жить в Core, а не как `style="..."` на доменных страницах.
- Допускается оставить inline только для реально уникальных вещей (например, редкая `min-width` конкретной таблицы), но:
  - отступы, min-width контролов, inline-flex лейблы, выравнивание toolbars должны быть через Core utilities.

Каноничные admin utilities (Core):

- `.wgBox/.wgTitle/.wgSummary/.wgHint` (status box паттерн).
- Отступы: `.uMt6/.uMt8/.uMt10/.uMt12/.uMt14`, `.uMb6/.uMb14`.
- Выравнивание: `.uJcStart`.
- Inline row: `.uInlineRow` (лейблы с checkbox).
- Min-width inputs: `.uMinW150/.uMinW190/.uMinW240`.
- Max-height: `.uMaxH40vh`.
- Pre padding: `.tableWrapPre` (использовать как `class="tableWrap tableWrapPre"`).

5) A11y и keyboard-first

- Везде видимый `:focus-visible`.
- Для sidebar поиска: hotkeys и `Enter` на единственный результат.
- Уважать `prefers-reduced-motion`.

## Этапный workflow (пакеты правок)

Каждый “пакет” (Pack-N) делается так:

1. Сформулировать цель пакета (1-2 строки): что убираем из перегруза и как измеряем успех.
2. Выбрать слой изменений:
- Core (если паттерн повторяется на 2+ страницах),
- Domain (если правка уникальна для страницы).
3. Реализация:
- сначала Core primitive,
- затем миграция 1-3 страниц на primitive,
- без изменения backend API контрактов (если явно не оговорено).
4. Обязательное правило: immediate VPS deploy (всегда)
- Любые правки web-панели (Core или Domains) считаются “незавершёнными”, пока они не выкатаны на VPS.
- После каждого логически законченного набора правок (минимум: один изменённый модуль/страница) сразу делаем:
  - `py_compile` изменённых модулей,
  - `rsync` на VPS,
  - `docker compose ... up -d --build api`,
  - прогон smoke gates.
  Это нужно, чтобы UI/UX валидировался на реальном окружении и не было “локально ок, на сервере иначе”.
5. Server-first проверка:
- deploy на VPS,
- `py_compile` изменённых модулей,
- restart контейнера API,
- прогон smoke gates.
5. Документация:
- обновить `Core` и `Архитектура меню`,
- обновить доменный документ затронутого раздела,
- добавить pack-отчёт в `Docs/auto/web-panel/`,
- записать кратко в `Docs/Проект/Паспорт релиза документации.md`.

## Server-first: каноничные команды

VPS:

- SSH: `ssh -4 alis@207.180.213.225`
- Path: `/opt/passengers-backend/app`

Deploy изменённых файлов:

- `rsync -av <files> alis@207.180.213.225:/opt/passengers-backend/app/`

Перезапуск:

- `ssh -4 alis@207.180.213.225 'cd /opt/passengers-backend; python3 -m py_compile app/<changed>.py; sudo docker compose -f compose.yaml -f compose.server.yaml up -d --build api'`

Quality gates:

- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/<report>.md`

## Definition of Done (DoD) для пакета UI/UX

- Pack цель достигнута без визуальной регрессии (sidebar/header/tables).
- `py_compile` = OK для изменённых модулей.
- VPS build+restart (`up -d --build api`) = OK.
- Smoke gate = PASS.
- Обновлены docs (Core + IA + domain + паспорт).
