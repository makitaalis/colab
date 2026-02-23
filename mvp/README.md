# Passengers MVP (Edge → Central → Backend)

Этот каталог содержит минимальные “скелетные” сервисы, которые позволяют собрать рабочий контур без GPS/RTC:

- Edge (`door-1`, `door-2`) буферизует события в локальный SQLite и досылает на Central по HTTP.
- Central (`central-gw`) принимает события по HTTP, складывает в SQLite и отправляет агрегаты на backend через `central_flush.py` (режим `STOP_MODE=manual|timer`).

Для всех сервисов используется `preflight.py` (ExecStartPre), чтобы не стартовать pipeline до готовности:

- время синхронизировано
- для edge доступен Central health endpoint
- для central uplink доступен backend health endpoint по VPN

Деплой/юниты: `scripts/deploy_passengers_mvp.sh`.

Режим остановки на Central задаётся через `/etc/passengers/passengers.env`:

- `STOP_MODE=manual` — только ручной flush (`central_flush.py --send-now`), `passengers-central-flush.timer` отключён.
- `STOP_MODE=timer` — авто flush по таймеру `passengers-central-flush.timer`.
- `scripts/deploy_passengers_mvp.sh` по умолчанию разворачивает `STOP_MODE=manual`.

Дополнительно на `central-gw` включён heartbeat в backend:

- `central_heartbeat.py` формирует состояние (`systemd`, очередь, двери) и отправляет на backend
- `passengers-central-heartbeat.timer` запускает heartbeat каждые ~45 секунд
- данные отображаются в админке backend на странице `/admin/fleet`

GPS (опционально):

- если на Central установлен модуль GPS snapshot (`/var/lib/passengers/gps/latest.json` с `fix=true`), то `central_flush.py` добавит `stop.gps={lat,lon}` в батч.

## Ретеншн/лимиты очередей

На всех узлах запускается `queue_maintainer.py` по timer:

- `passengers-queue-maintenance.service`
- `passengers-queue-maintenance.timer` (каждые ~15 минут)

Границы задаются через `/etc/passengers/passengers.env`:

- Edge: `EDGE_OUTBOX_MAX_ROWS`, `EDGE_OUTBOX_MAX_AGE_SEC`
- Central:
  - `CENTRAL_EVENTS_MAX_ROWS`, `CENTRAL_EVENTS_MAX_AGE_SEC`
  - `CENTRAL_SENT_BATCHES_MAX_ROWS`, `CENTRAL_SENT_BATCHES_MAX_AGE_SEC`
  - `CENTRAL_PENDING_BATCHES_MAX_ROWS`, `CENTRAL_PENDING_BATCHES_MAX_AGE_SEC`, `CENTRAL_PENDING_BATCHES_DROP_AGE`

## Watchdog (внедрено)

На всех OPi используется двухуровневый watchdog:

- hardware/system watchdog через `systemd` (`RuntimeWatchdogSec`, `ShutdownWatchdogSec` в `/etc/systemd/system.conf`);
- сервисный watchdog `passengers-service-watchdog.timer`, который запускает `service_watchdog.py` и восстанавливает критичные `passengers-*` юниты.

Скрипты:

- `mvp/service_watchdog.py` — проверка/восстановление сервисов по роли узла (`edge|central`) и `STOP_MODE`;
- `scripts/install_opi_watchdog.sh` — установка watchdog baseline на текущие узлы;
- `scripts/deploy_passengers_mvp.sh` — теперь включает установку watchdog по умолчанию при деплое.
