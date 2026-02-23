# Web-panel v2 (Jinja2 + HTMX) Pack-01: Scaffold (/admin2, /client2)

Дата: 2026-02-23

## Цель

- Начать web-панель v2 “с нуля” параллельно v1, без помех и без регрессий.
- Зафиксировать новый shell (layout + навигация 2 уровня) и базовые UI primitives.
- Подготовить основу для миграции доменов через HTMX-фрагменты (partial updates) без SPA.

## Что сделано

- Добавлен v2 модуль `backend/app/webpanel_v2/`:
  - `nav.py` — 2-уровневое меню (admin/client) + active/open состояние по URL.
  - `render.py` — Jinja2Templates + базовые render helpers + HTMX fragments (`time`, `ping`).
  - `templates/*` — layouts + index + placeholder страницы.
  - `static/*` — v2 CSS/JS и vendored `htmx.min.js` (MIT license).
- Подключены маршруты v2 (не мешают v1):
  - Admin: `/admin2`, `/admin2/*`
  - Client: `/client2`, `/client2/*`
- В шаблоны v2 встроены CSS/JS inline (чтобы не зависеть от nginx static routing на первом шаге).

## Server-first валидация

- Deploy на VPS: `rsync` изменённых файлов в `/opt/passengers-backend/app/` + `requirements.txt`.
- `docker compose ... up -d --build api` (важно: контейнер копирует код на build).
- Проверка:
  - `/admin2` = 200 (BasicAuth admin),
  - `/client2` = 200 (BasicAuth support/client),
  - `scripts/admin_panel_smoke_gate.sh` = PASS (v1 не сломан).

## Артефакты

- Скриншоты v2: `Docs/auto/web-panel/screenshots/2026-02-23-v2-alpha/`

## Следующий шаг (Pack-02)

- Выбрать первый домен для миграции: `Флот` или `Інциденти`.
- Сделать 1 real-data таблицу на HTMX:
  - сервер отдаёт HTML фрагмент таблицы,
  - клиент обновляет только `<tbody>` по таймеру,
  - состояния: loading/empty/error.

