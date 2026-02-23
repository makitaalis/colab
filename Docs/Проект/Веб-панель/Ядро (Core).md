# Ядро (Core)

Документ описывает единые правила ядра web-панели для всех доменов (admin/client).

## 1. Ответственность ядра

- shell страницы (`header -> subnav -> body`);
- дизайн-токены, базовые CSS/JS утилиты;
- глобальная навигация `меню -> подменю`;
- общие UX-паттерны (`copyLink`, `filterSummary`, `flowStep`, `tableMeta`);
- режимы sidebar (`Simple/Extended`, `Compact/Comfort`).

## 2. Кодовые модули

- `backend/app/admin_ui_kit.py` — текущая реализация shell.
- `backend/app/admin_core/navigation.py` — ядро IA-навигации админки.
- `backend/app/admin_domains/domain_catalog.py` — доменная карта админки.
- `backend/app/client_ui_kit.py` — shell клиентской панели.
- `backend/app/client_core/navigation.py` — IA-навигация клиентской панели.
- `backend/app/client_domains/domain_catalog.py` — доменная карта клиента.
- `backend/app/client_*_page.py` — клиентские страницы домена.
- `backend/app/client_ops.py` — доменная API-логика клиентской панели.

## 2.1 v2 (Jinja2 + HTMX, параллельно v1)

v2 живёт рядом с v1 и не мешает ему (префиксы: `/admin2`, `/client2`).

Core (v2):

- `backend/app/webpanel_v2/core/render.py` — Jinja2 shell render + inline assets (CSS/JS/HTMX).
- `backend/app/webpanel_v2/core/nav.py` — IA меню (2 рівні) + active/open state.
- `backend/app/webpanel_v2/core/fragments.py` — HTMX fragments (time/ping; далее: loading/empty/error).

Domains (v2):

- `backend/app/webpanel_v2/domains/admin/*` — admin2 страницы по доменам.
- `backend/app/webpanel_v2/domains/client/*` — client2 страницы по доменам.
- `backend/app/webpanel_v2/router.py` — сборка роутеров v2 (подключается в `backend/app/main.py`).

## 3. Единый UI-контракт

Для рабочих страниц admin обязательны:

1. `appShell` — общий layout.
2. `copyLink` — shareable URL.
3. `filterSummary` — краткий контекст фильтров.
4. `flowStep` — сценарная последовательность.
5. `tableMeta` — источник/окно/сортировка данных.

Для рабочих страниц client обязательны:

1. `clientShell` — отдельный layout клиента.
2. `copyLink` — shareable URL.
3. `filterSummary` — краткий контекст страницы.
4. Отсутствие admin-терминологии и debug-блоков.
5. Данные страницы читаются через `/api/client/*`, без локальных mock-источников.
6. Для `home/vehicles` используется единый SLA/ETA контракт:
- `primary`: текущие отклонения и требуемые действия;
- `secondary`: полный список транспорта/деталей без перегруза первого экрана.
7. Для `profile/notifications` обязателен role-aware контур:
- summary в верхнем блоке + краткие CTA;
- support-детали только во secondary-контуре (`<details>`).

Для client API обязательны:

1. `whoami` + scope-контур (`central_ids`/`vehicle_ids`).
2. Bearer-валідация ключа (через nginx token injection).
3. Чёткое разделение read/write:
- read: `home/vehicles/tickets/status/profile/settings`;
- write: `profile/settings`.
4. Role contract:
- `client` — базовый режим кабинета;
- `admin-support` — расширенное представление secondary-блоков.
5. Nginx auth split:
- `/client*` и `/api/client/*` обслуживаются через `/etc/nginx/passengers-client.htpasswd`;
- `/admin*` и `/api/admin/*` обслуживаются через `/etc/nginx/passengers-admin.htpasswd`.
6. Scope isolation:
- support-логины ограничиваются через `CLIENT_SCOPE_BINDINGS` (actor -> central_id[:vehicle_id]).
7. Multi-support onboarding policy:
- naming: `support-<system_id>`;
- source of truth: onboarding matrix (`actor|password_file|scope_entries`);
- rollout script: `scripts/client_support_matrix_rollout.sh`.
8. Support actor lifecycle policy:
- operations: `rotate` / `disable` / `revoke`;
- rollout script: `scripts/client_support_lifecycle_rollout.sh`;
- `revoke` обязан удалять actor из auth и scope-контуров.
9. Lifecycle automation:
- batch rotation: `scripts/client_support_rotation_batch.sh`;
- inventory/drift report: `scripts/client_support_inventory_report.sh`;
- server timers install: `scripts/install_client_support_lifecycle_timer.sh`.

## 4. Правила навигации

1. 2 уровня меню: `раздел -> подменю`.
2. Неактивные разделы стартуют в свернутом виде.
3. Под header показывается page subnav текущего раздела.
4. В `Simple`-режиме sidebar минимальный:
- в доменах показываются только `hub`-пункты (подпункты скрыты, кроме активного);
- поиск в sidebar временно раскрывает подпункты (для keyboard-first навигации);
- группы меню при поиске и в `Simple` разворачиваются (иначе результат может быть скрыт в collapsed-секции);
- скрываются все mini-блоки sidebar (включая `favorites/recent/session`) для визуальной чистоты.
5. В `Розширено`-режиме:
- домены показывают все подпункты;
- mini-блоки sidebar должны быть сворачиваемыми и persistent (без длинной прокрутки).
key: `passengers_admin_sidebar_collapsed_mini_v1`.
6. В `Фокус`-режиме sidebar nav-only:
- показывается только навигация `раздел -> подменю` без вспомогательных блоков.
7. Для client shell обязателен sidebar-search:
- поиск по пунктам меню в sidebar (без прокрутки длинного списка),
- горячая клавиша фокуса на поиск: `Alt+Shift+N`.
8. Для client shell обязателен compact toggle sidebar с сохранением состояния в `localStorage`.
9. Для client shell обязателен keyboard-first минимум:
- `/` -> фокус поиска в toolbar;
- `Esc` -> blur активного editable поля;
- shortcut toggles compact/progressive режимов.
10. Каноничная карта IA хранится в `Docs/Проект/Веб-панель/Архитектура меню (admin+client).md` и обновляется перед изменением route map.

## 8. Visual-Density правила (admin/client)

1. Header chips = только контекст (роль/время/режим/статус), но не навигация.
2. Навигация живёт в:
- sidebar (`меню -> подменю`);
- `page subnav` текущего раздела;
- workflow card (если это операторский маршрут).
3. `domainSplitDetails` (primary/secondary content split) использует общий стиль ядра (`admin_ui_kit`).
4. Переключение `Просто/Розширено` не должно автоматически “раздувать” страницы (длинные `<details>` не открываются сами при выходе из Simple).
5. Keyboard-first минимум:
- все интерактивные элементы должны иметь видимую `:focus-visible` обводку;
- `<details>` в toolbar/advanced должны иметь chevron и понятный open-state.
6. Единый размер контролов:
- базовый `min-height` для кнопок/инпутов/селектов фиксируется в Core (admin/client) и не “пляшет” между страницами.
7. Таблицы (admin/client):
- таблицы оборачиваются в `.tableWrap` (скролл + max-height + визуальный “контейнер”);
- `th` sticky с контрастным фоном и `white-space: nowrap` (предсказуемая шапка при скролле);
- zebra + hover подсветка строк (быстрое сканирование больших списков);
- числа читаются в `tabular-nums` (колонки выравниваются визуально).
8. Subnav (admin/client):
- page subnav не должен раздувать высоту header: при большом количестве пунктов используется горизонтальный scroll (nowrap + overflow-x).
8.1. Header chips (admin/client):
- chips в header не должны раздувать высоту страницы: при большом количестве chips используется горизонтальный scroll.
8.2. Client toolbar:
- `clientToolbar` = controls-only (filters/actions/toggles/copyLink) + meta/status.
- `toolbar_html` оформляется 2 рядами: `toolbarMain` (controls) и `toolbarMeta` (meta/status).
- `updatedAt` относится к контексту и отображается в chips, а не в toolbar.
8.3. Admin toolbar:
- `toolbar_html` оформляется 2 рядами: `toolbarMain` (controls) и `toolbarMeta` (filterSummary/status).
- `copyLink` и ключевые дії в toolbar должны иметь единый размер контролов (не `smallbtn`).
- Для навигационных ссылок в header toolbar использовать `toolbarBtn` (ссылка выглядит как кнопка).
8.4. Core utilities (без inline styles):
- Повторяющиеся паттерны обязаны жить в Core, а не как `style="..."` на страницах доменов.
- Каноничный “status box” (WG/commission/overview): `.wgBox`, `.wgTitle`, `.wgSummary`, `.wgHint`.
- Каноничные utility-классы (использовать вместо inline):
  - отступы: `.uMt6/.uMt8/.uMt10/.uMt12/.uMt14`, `.uMb6/.uMb14`;
  - выравнивание: `.uJcStart`;
  - inline row: `.uInlineRow` (лейблы с checkbox);
  - min-width inputs: `.uMinW150/.uMinW190/.uMinW240`;
  - max-height: `.uMaxH40vh`;
  - pre padding: `.tableWrapPre` (как `class="tableWrap tableWrapPre"`).
9. Empty-state (admin/client):
- пустые таблицы должны явно показывать “нет данных” и короткую подсказку (обычно: “Спробуйте змінити фільтри або період.”);
- правило по умолчанию реализуется на уровне Core (без ручных правок каждой страницы).
- поддерживаются атрибуты:
  - `data-empty-title` (например `OK`),
  - `data-empty-tone` (`good|warn|bad|neutral`),
  - `data-empty-text` (короткая подсказка).

## 5. Правила изменений

1. Добавление route:
- сначала регистрация в `*_domains/domain_catalog.py`;
- затем подключение в `*_core/navigation.py`;
- затем page модуль.
2. Запрещено:
- добавлять route напрямую в shell без доменной регистрации;
- переносить доменные действия в `Core`.

## 6. Server-first quality gate

Перед закрытием этапа обязательно:

0. Immediate VPS deploy (правило для web-панели):
- Любые изменения UI/UX (Core или Domains) должны выкатываться на VPS сразу после завершения логического набора правок, а не копиться локально.
- Минимальный цикл: `py_compile` -> `rsync` -> `docker compose ... up -d --build api` -> smoke gate.

1. `py_compile` изменённых модулей.
2. deploy: `docker compose -f compose.yaml -f compose.server.yaml up -d --build api`.
3. `scripts/admin_panel_smoke_gate.sh` = PASS (`/admin*`, `/api/admin/*`, `/client*`).
4. `/api/client/*` возвращают `200` под BasicAuth и `401` без auth.
5. Для client финального этапа:
- `scripts/client_panel_step7b_audit.py` формирует real-data отчёт `Docs/auto/web-panel/client-step7b-ux-audit.md`.
6. Для client accessibility-этапа:
- `scripts/client_panel_step16_accessibility_check.sh` формирует acceptance-отчёт `Docs/auto/web-panel/client-step16-accessibility-acceptance.md`.
7. Для client RC/handoff этапа:
- `scripts/client_panel_step17_handoff_check.sh` формирует checklist-отчёт `Docs/auto/web-panel/client-step17-handoff-checklist.md`.
8. обновление docs:
- этот файл;
- профильный доменный файл;
- `Паспорт релиза документации`.

## 7. Единый паттерн декомпозиции страниц

Для перегруженных страниц применяется общий шаблон:

1. `Primary`-контур (KPI + главный операторский сценарий) всегда видим сверху.
2. `Secondary`-контур (детальные журналы/расширенная аналитика) выносится в `<details>`.
3. Состояние раскрытия secondary-блока сохраняется в `localStorage`.
4. Нейминг key:
- `passengers_admin_<domain>_secondary_details_v1`.
- `passengers_client_<domain>_secondary_v1`.
5. Для mobile-first:
- таблицы доменов используют `mobileFriendly`;
- вторичные колонки маркируются `mobileHide`.
6. Для client-домена:
- страницы `Огляд` и `Мої транспорти` обязаны держать SLA/ETA сводку в верхнем блоке;
- полноразмерный список транспорта размещается во secondary-контуре.
7. Для account-поддомена (`Профіль/Сповіщення`):
- сохраняется единый паттерн `summary -> form -> secondary details`;
- destructive-действия (очистка профиля) не допускаются без явного подтверждения.
8. Для table-heavy client страниц:
- вторичные колонки маркируются `progressiveCol`;
- переключение `базово/детально` реализуется через единый `tableToggle` и сохраняется в `localStorage`.
9. Для a11y baseline:
- shell содержит `skip-link` к main-контенту;
- status-элементы используют `aria-live=polite`;
- interactive controls имеют видимый `focus-visible` контур.
