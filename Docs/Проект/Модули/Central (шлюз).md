# Central (шлюз)

## Назначение

- Принимать события от edge-узлов.
- Агрегировать и отправлять на backend.
- Вести heartbeat/health контур.
- Работать как источник времени для edge.

## MVP baseline (без GPS/RTC)

- `passengers-collector`
- `central_flush.py` + `passengers-central-flush.timer`
- `central_heartbeat.py` + `passengers-central-heartbeat.timer`
- `service_watchdog.py` + `passengers-service-watchdog.timer`
- `preflight.py` (проверка времени и backend health)

## Камера OAK-D Lite (этап 12.3)

- Runtime ставится **на узел с камерой** (Central или Door): `python3-venv`, `libusb`, `udev`, `depthai` (в venv).
- Для доступа к устройству обязательно `udev` правило `03e7` (`/etc/udev/rules.d/80-movidius.rules`).
- Headless проверка: `scripts/oakd_v3_smoke.py`.
- Боевой сервис: `passengers-camera-counter.service` (`mvp/camera_counter.py`).
- Диагностический сервис: `passengers-camera-debug-stream.service` (`mvp/camera_debug_stream.py`).
- Переключение режимов: `scripts/camera_mode_switch.sh` (`prod` / `debug-stream` / `depth-counting` / `oak-viewer`) через `--camera-ip`.
- Важно: `debug-stream` и `oak-viewer` взаимоисключающие на одной камере.

Принятая схема подсчёта v1:

- `DetectionNetwork(person)` + `ObjectTracker` + line-crossing (hysteresis).
- Запись событий:
  - `store=central` — напрямую в `central.sqlite3` (на Central с камерой);
  - `store=edge` — в `edge.sqlite3:outbox` (на Door с камерой), дальше `edge_sender` пересылает на Central.
- Агрегатор/heartbeat работают без изменений (единый контур данных).

## Контракт

- Приём от edge: `POST /api/v1/edge/events`.
- Отправка агрегатов: `POST /api/v1/ingest/stops`.
- Heartbeat: `POST /api/v1/ingest/central-heartbeat`.

## Связанные документы

- Серверный контракт: `Docs/Проект/Сервер (Central→Backend).md`
- Операции: `Docs/Проект/Операции.md`
- Практика камеры: `Docs/Проект/Операции/Камера OAK-D Lite (Luxonis).md`
- Подробно: `Docs/Проект/Модули (подробно).md`

## Depth фильтрация (голова/плечи)

Для подсчёта включён depth-gate:

- диапазон: `0.40–1.50 м`;
- зона измерения: верхняя часть bbox (голова/плечи);
- трек с depth вне диапазона или `n/a` не участвует в line-crossing event.

Режимы камеры на узле с камерой:

- `prod` — `passengers-camera-counter.service`
- `debug-stream` — `passengers-camera-debug-stream.service`
- `depth-counting` — `passengers-camera-depth-counting.service` (transport strict: person+track_id+2 линии)
- `oak-viewer` — все сервисы остановлены, камера освобождена

## Калибровка depth-counting (операционный слой)

Для режима `passengers-camera-depth-counting.service` добавлен helper:

- `scripts/camera_depth_calibrate.sh`

Что он делает:

- применяет профиль/ручные `CAM_DEPTH_COUNT_*` в `/etc/passengers/passengers.env`;
- перезапускает depth-counting сервис;
- снимает `health` после старта.

Рекомендуемая последовательность полевой настройки:

1. `--show --health`
2. `--preset wide-scan --health`
3. `--preset transport-strict --health` (общественный транспорт, приоритет: меньше ложных; стартово `FPS=10` на `usb_speed=HIGH`)
4. точечные `--set KEY=VALUE --health`
5. возврат в `prod` режим, когда тюнинг завершён.

## IMU поток в режиме depth-counting

В `passengers-camera-depth-counting.service` добавлена диагностика IMU:

- данные акселерометра/гироскопа публикуются в `GET /health`;
- `imu_type` на OAK-D Lite ожидаемо `BMI270`;
- параметры управления: `CAM_IMU_ENABLE`, `CAM_IMU_RATE_HZ`.
