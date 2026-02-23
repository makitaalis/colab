# Сервер (Central → Backend)

Цель: Central (`central-gw`) отправляет агрегированные данные на внешний сервер, где ведётся статистика по каждому транспортному средству.

## Текущий тестовый backend (MVP)

- Сервер: `207.180.213.225` (Ubuntu 24.04)
- Доступ: `ssh alis@207.180.213.225` (только по SSH ключу)
- Endpoint (через **VPN WireGuard**, HTTP в тесте): `http://10.66.0.1/api/v1/ingest/stops`
- Auth: `Authorization: Bearer <api_key>`

Реализация backend (MVP) лежит в репозитории:

- `backend/` (FastAPI + SQLite + idempotency по `batch_id`)
- Деплой на сервер: `Docs/настройка ПО/План/4. Backend сервер (Ubuntu + Docker Compose).md`

Переход на **HTTPS** делаем отдельным шагом, когда появится домен (или когда решим вариант VPN/self-signed).

## Транспорт до интернета

У `central-gw` интернет может быть через:

- Wi‑Fi
- GSM/LTE модем EM7455

При отсутствии интернета Central обязан буферизовать и “догонять” после восстановления.

## Модель для 100–200 систем (надёжная)

На каждый транспорт — отдельный `central` и отдельный WG peer:

- отдельный `system_id` (реестр);
- отдельный `wg_ip` и ключи WireGuard;
- отдельный ingest API key;
- отдельный `central_id` в payload heartbeat/alerts.

Принятый формат: `central_id = system_id` (например `sys-0002`).

Почему это надёжно:

- изоляция отказов между транспортами;
- точечная ротация/отзыв ключей без влияния на весь fleet;
- корректные per-central алерты, инциденты и overrides;
- предсказуемый rollout и диагностика при масштабе `100–200`.

## Рекомендация по интеграции (что лучше для проекта)

### 1) Протокол

- **HTTPS + JSON** (один endpoint приёма).
- Семантика доставки: **at-least-once** (повторы допустимы), на стороне сервера — дедупликация.

### 2) Аутентификация

Для транспорта/полевых устройств чаще всего лучше **статический API key на транспортное средство** (или на устройство `central-gw`), потому что:

- не требует “логина” и обновления токенов (важно при нестабильном интернете)
- проще внедрять и сопровождать
- ключ можно ротировать и отзывать по одному ТС

Рекомендуемый вариант:

- заголовок `Authorization: Bearer <api_key>`
- `vehicle_id` задаётся **вручную** в конфиге на `central-gw` и передаётся:
  - либо заголовком `X-Vehicle-Id: <vehicle_id>`
  - либо полем `vehicle_id` в JSON (предпочтительно, чтобы пакет был самодостаточным)

Формат `vehicle_id` (включая госномер) фиксируется здесь:

- `Docs/Проект/Конфигурация.md`

Опционально (если нужно усилить защиту):

- `X-Signature` (HMAC подпись тела запроса ключом) + `X-Timestamp` для защиты от подмены/повторов

Где хранить ключ/URL на `central-gw`:

- см. `Docs/Проект/Конфигурация.md` (рекомендован `EnvironmentFile` для systemd)
- управление per-system ключами и ротацией: `scripts/fleet_api_keys.py`

### 3) Что отправлять: агрегаты или сырые события

В вашем сценарии правильнее отправлять **агрегаты пакетами “на остановку”**:

- меньше трафика и меньше нагрузки на сервер
- проще строить статистику по ТС
- стабильнее при плохой связи (меньше запросов)

При этом сырые события лучше **сохранять локально ограниченное время** (например 24–72 часа) для диагностики/перепроверки, но не обязательно отправлять наружу постоянно.

## Пакетирование “на остановку”

### Что такое “остановка”

Точка “flush” может определяться как:

- скорость по GPS < порога в течение N секунд
- или внешний сигнал (если будет доступен)
- + fallback: если “остановка” не распознана, отправлять агрегаты каждые X минут

⚠️ Решение по детекции “остановки” (GPS vs таймер vs ручное) зафиксировано как отдельный пункт плана и будет выбрано позже.

### Рекомендация по расписанию отправки

- основное: **в конце остановки** (или при старте движения после остановки)
- fallback: каждые 5–10 минут или при достижении лимита по объёму локального буфера

## Контракт с backend (минимум)

Ниже — минимальные требования, чтобы дальше не переписывать систему:

- аутентификация (API key / token)
- подтверждение доставки (ACK)
- идемпотентность (уникальный ключ пакета)
- ретраи (backoff) и локальный буфер на Central

### Предложение по endpoint

- `POST /api/v1/ingest/stops` — приём пакета агрегатов по остановке
- `POST /api/v1/ingest/central-heartbeat` — приём heartbeat от Central (мониторинг состояния)

### Предложение по payload (агрегаты)

```json
{
  "schema_ver": 1,
  "vehicle_id": "bus-017_AA1234BB",
  "batch_id": "sys-0001:2026-02-05T15:00:00Z:manual:0042",
  "ts_sent": "2026-02-05T15:12:00Z",
  "stop": {
    "stop_id": "0042",
    "ts_start": "2026-02-05T15:10:00Z",
    "ts_end": "2026-02-05T15:11:20Z",
    "gps": { "lat": 50.4501, "lon": 30.5234 }
  },
  "doors": [
    { "door_id": 1, "in": 3, "out": 1 },
    { "door_id": 2, "in": 1, "out": 2 },
    { "door_id": 3, "in": 0, "out": 1 }
  ]
}
```

Дедупликация на сервере:

- ключ `batch_id` должен быть уникальным (если пакет отправится повторно — сервер отвечает `200` и не удваивает статистику).

## Heartbeat Central (MVP мониторинг)

Heartbeat нужен для простой диагностики состояния Centrals в админке.

### Endpoint

- `POST /api/v1/ingest/central-heartbeat`
- `GET /api/admin/fleet/centrals` (для админки, возвращает `health` + `alerts` по каждому Central, требует `ADMIN_API_KEYS`)
- `GET /api/admin/fleet/overview` (для dashboard: totals + top alerts, опция `include_centrals=1`)
- `GET /api/admin/fleet/alerts` (лента алертов с фильтрами `severity`, `include_silenced`, `central_id`, `code`, `q`)
- `GET /api/admin/fleet/monitor` (единый dashboard snapshot: fleet/incidents/notifications/security/attention)
- `GET /api/admin/fleet/health` (облегчённый health snapshot для внешнего мониторинга)
- `POST /api/admin/fleet/health/notify-test` (ручной health-alert test для каналов уведомлений)
- `POST /api/admin/fleet/health/notify-auto` (авто-логика health-alert: state-change + rate-limit + recovery-policy)
- `GET /api/admin/fleet/monitor-policy` (текущие monitor policy thresholds)
- `POST /api/admin/fleet/monitor-policy` (обновление monitor policy thresholds)
- `GET /api/admin/fleet/monitor-policy/overrides` (список per-central overrides)
- `POST /api/admin/fleet/monitor-policy/overrides` (upsert override по `central_id`)
- `DELETE /api/admin/fleet/monitor-policy/overrides/{central_id}` (удаление override)
- `GET /api/admin/fleet/incidents` (слой incidents: `open/acked/silenced/resolved` + SLA поля)
- `GET /api/admin/fleet/incidents/{central_id}/{code}` (incident detail + timeline)
- `POST /api/admin/fleet/incidents/sync` (ручной пересчёт incidents)
- `GET /api/admin/fleet/incidents/notifications` (лог доставки `telegram/email`)
- `GET /api/admin/fleet/metrics/history` (bucketed тренды fleet health/notifications/actions)
- `GET /api/admin/whoami` (текущая роль/actor для admin token)
- `GET /api/admin/audit` (журнал admin API действий, только роль `admin`)
- `GET /api/admin/fleet/notification-settings` (текущие policy-правила уведомлений)
- `POST /api/admin/fleet/notification-settings` (обновление policy-правил уведомлений)
- `POST /api/admin/fleet/notification-settings/test` (ручной тест отправки, включая `channel` и `dry_run`)
- `POST /api/admin/fleet/notifications/retry` (manual retry по `notification_id` для каналов `telegram/email`)
- `GET /api/admin/fleet/central/{central_id}` (drill-down: текущий срез + history)
- `GET /api/admin/fleet/alerts/actions` (журнал admin-действий с фильтрами `central_id`, `code`, `action`, `q`)
- `POST /api/admin/fleet/alerts/ack|silence|unsilence` (операционные действия по алертам)

RBAC для admin API:

- роли: `viewer`, `operator`, `admin`
- маппинг token→role задаётся в `/opt/passengers-backend/.env` через `ADMIN_API_KEY_ROLES`
- формат: `ADMIN_API_KEY_ROLES=<token1>:admin,<token2>:operator,<token3>:viewer`

### Payload (пример)

```json
{
  "schema_ver": 1,
  "central_id": "sys-0001",
  "vehicle_id": "bus-017_AA1234BB",
  "ts_sent": "2026-02-06T17:57:06.334247Z",
  "time_sync": "synced",
  "services": {
    "passengers-collector": "active",
    "passengers-central-uplink": "active",
    "passengers-central-flush.timer": "inactive",
    "wg-quick@wg0": "active"
  },
  "queue": {
    "events_total": 15,
    "pending_batches": 0,
    "sent_batches": 5,
    "last_event_ts_received": "2026-02-06T17:30:07.264825Z",
    "pending_oldest_age_sec": null,
    "wg_latest_handshake_age_sec": 55,
    "stop_mode": "manual"
  },
  "doors": [
    {
      "node_id": "door-1",
      "door_id": 2,
      "ip": "192.168.10.11",
      "reachable": true,
      "last_event_ts_received": "2026-02-06T17:30:07.264825Z",
      "last_event_age_sec": 1619
    },
    {
      "node_id": "door-2",
      "door_id": 3,
      "ip": "192.168.10.12",
      "reachable": true,
      "last_event_ts_received": "2026-02-06T17:30:07.238877Z",
      "last_event_age_sec": 1619
    }
  ]
}
```

Примечание:

- при `stop_mode=manual` отсутствие `active` у `passengers-central-flush.timer` не считается ошибкой.
- ответ `POST /api/v1/ingest/central-heartbeat` также содержит служебные блоки `incidents` и `notifications`.

## Что нужно уточнить

1) URL(ы) backend API  
2) формат (события сырые или агрегаты)  
3) схема авторизации  
4) политика ретеншна/пакетирования  
