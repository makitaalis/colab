# Камера OAK-D Lite (Luxonis)

## Официальные источники (канон)

Правило: все решения/параметры по камере сверяем с официальной документацией Luxonis. Если есть сомнения — сначала ищем в `https://docs.luxonis.com/`, и только потом меняем код/пресеты.

- DepthAI v3 docs index: `https://docs.luxonis.com/software-v3/depthai/`
- Dynamic Calibration (host node): `https://docs.luxonis.com/software-v3/depthai/depthai-components/host_nodes/dynamic_calibration`
- Object Tracker node: `https://docs.luxonis.com/software-v3/depthai/depthai-components/nodes/object_tracker/`
- Detection Network node: `https://docs.luxonis.com/software-v3/depthai/depthai-components/nodes/detection_network/`
- Tracklets message: `https://docs.luxonis.com/software-v3/depthai/depthai-components/messages/tracklets/`
- Example object tracker remap: `https://docs.luxonis.com/software-v3/depthai/examples/object_tracker/object_tracker_remap/`
- OAK-D Lite hardware page: `https://docs.luxonis.com/hardware/products/OAK-D%20Lite`
- RVC2 platform: `https://docs.luxonis.com/hardware/platform/rvc/rvc2`
- Depth people counting example (ограничения): `https://github.com/luxonis/oak-examples/blob/main/neural-networks/counting/depth-people-counting/README.md`
- Сравнение алгоритмов (под вашу задачу IN/OUT): `Docs/Проект/Операции/Сравнение Luxonis depth-people-counting vs transport-strict.md`

## Принятое решение для проекта (надежный baseline)

Основной контур подсчёта:

1. `DetectionNetwork` (person) на RGB кадре.
2. `ObjectTracker` с постоянными track-id.
3. Пересечение виртуальной линии с гистерезисом.
4. Запись событий `in/out` в `central.sqlite3` (контракт `schema_ver=1`).

Почему не depth-only как основной режим:

- в `oak-examples/depth-people-counting` есть предупреждение про hardcoded параметры под конкретную запись/сцену;
- для транспорта это высокий риск нестабильности без долгого тюнинга на каждой двери.

Роль depth на старте:

- как дополнительный фильтр/валидация на следующем подэтапе;
- не как единственный источник детекции в baseline v1.

## Где сейчас камера (факт стенда)

На текущем стенде камера физически подключена к edge‑узлу:

- `door-1` (`192.168.10.11`, `door_id=2`) — OAK‑D Lite по USB.

Важно:

- скрипты переключения режимов работают **для любого узла с камерой** (Central или Door) через `--camera-ip`;
- Central (`192.168.10.1`) в этой схеме может работать как **коллектор/шлюз**, даже без камеры.

## Шаги настройки (камера-узел: Central или Door)

### Шаг 1. Runtime зависимости

Рекомендуемый путь (устойчивый к PEP 668): **venv + system-site-packages**.

Edge‑узел с камерой (`door-1`, `192.168.10.11`):

```bash
./scripts/install_edge_camera_counter.sh --edge-ip 192.168.10.11 --user orangepi --door-id 2
```

Примечание (про интернет на edge):

- edge‑узлы обычно без интернета; для установки пакетов можно временно включить NAT через Central:
  - `./scripts/central_edge_inet_bridge.sh enable`
  - на edge: `sudo ip route replace default via 192.168.10.1 dev end0 metric 900`
  - после установки: `./scripts/central_edge_inet_bridge.sh disable` и удалить default route на edge.

Central‑узел с камерой (если камера будет подключена на Central позже):

```bash
./scripts/install_central_camera_counter.sh --central-ip 192.168.10.1 --user orangepi
```

### Шаг 2. USB-права (udev)

```bash
ssh orangepi@192.168.10.11 '
  echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"03e7\", MODE=\"0666\"" | sudo tee /etc/udev/rules.d/80-movidius.rules >/dev/null &&
  sudo udevadm control --reload-rules &&
  sudo udevadm trigger
'
```

Проверка `lsusb`:

- допустимые USB ID камеры на стенде: `03e7:2485` или `03e7:f63b`;
- если на целевом узле нет этих ID, сервисы `debug-stream/depth-counting/counter` не стартуют.

### Шаг 3. Smoke OAK-D Lite

```bash
scp scripts/oakd_v3_smoke.py orangepi@192.168.10.11:/tmp/oakd_v3_smoke.py
ssh orangepi@192.168.10.11 'python3 /tmp/oakd_v3_smoke.py --duration-sec 5 --min-frames 5'
```

Ожидаемый результат: `SMOKE_OK`, `device=OAK-D-LITE`.

### Шаг 4. Деплой camera-counter сервиса

```bash
./scripts/install_edge_camera_counter.sh --edge-ip 192.168.10.11 --user orangepi --door-id 2
```

Central‑узел с камерой (если камера на Central):

```bash
./scripts/install_central_camera_counter.sh --central-ip 192.168.10.1 --user orangepi
```

### Шаг 5. Проверка сервиса

```bash
ssh orangepi@192.168.10.11 'systemctl --no-pager --full status passengers-camera-counter.service | sed -n "1,30p"'
ssh orangepi@192.168.10.11 'journalctl -u passengers-camera-counter.service -n 80 --no-pager'
```

Ожидаем в логах:

- `camera-counter device: name=OAK-D-LITE`;
- heartbeat и события `camera-counter event: ...` при проходах.

### Шаг 6. Режимы диагностики камеры (debug-stream / oak-viewer)

Для одной физической OAK-D Lite режимы `debug-stream` и `oak-viewer` одновременно не работают:

- `debug-stream` держит устройство занятым через `passengers-camera-debug-stream.service`;
- `oak-viewer` требует свободное устройство.

Переключение режимов:

```bash
# 1) Диагностический MJPEG поток на узле с камерой (пример: door-1)
./scripts/camera_mode_switch.sh --mode debug-stream --camera-ip 192.168.10.11 --user orangepi

# 2) Открыть поток на ПК через SSH-туннель
ssh -N -L 8091:127.0.0.1:8091 orangepi@192.168.10.11
# Browser: http://127.0.0.1:8091/

# 3) Освободить камеру под oak-viewer
./scripts/camera_mode_switch.sh --mode oak-viewer --camera-ip 192.168.10.11 --user orangepi

# 4) Вернуть боевой режим подсчёта
./scripts/camera_mode_switch.sh --mode prod --camera-ip 192.168.10.11 --user orangepi
```

Проверка статуса после любого переключения:

```bash
./scripts/camera_mode_switch.sh --status --camera-ip 192.168.10.11 --user orangepi
```

## Параметры тюнинга (через `/etc/passengers/passengers.env`)

- `CAM_COUNTER_AXIS=y|x`
- `CAM_COUNTER_AXIS_POS=0.0..1.0`
- `CAM_COUNTER_HYSTERESIS=0.00..0.25`
- `CAM_COUNTER_CONFIDENCE=0.0..1.0`
- `CAM_COUNTER_FPS=<число>`
- `CAM_COUNTER_TRACKER_TYPE=short_term_imageless|short_term_kcf|zero_term_imageless|zero_term_color_histogram`
- `CAM_COUNTER_TRACKER_BIRTH=<число>`
- `CAM_COUNTER_TRACKER_LIFESPAN=<число>`
- `CAM_COUNTER_TRACKER_OCCLUSION=<число>`

## Следующий этап и зачем

- Включить такой же контур на `door-1` и `door-2`, чтобы все 3 двери работали по единому алгоритму.
- Добавить depth-gate (ROI/дистанция) поверх baseline, чтобы снизить ложные пересечения в сложных сценах.

## Интерактивное меню переключения режимов

Для быстрого ежедневного переключения режимов используйте:

```bash
./scripts/camera_mode_menu.sh --camera-ip 192.168.10.11 --user orangepi --debug-port 8091
```

Чтобы не вводить IP/пользователя после перезагрузки ПК, в меню есть пункт **Edit connection settings** — он сохраняет локальные дефолты в:

- `~/.config/passengers/camera_menu.env` (на вашем ПК)

Что есть в меню:

- `PROD` (боевой подсчёт);
- `DEBUG local` (включает debug-stream, поднимает SSH-туннель, открывает видео на `http://127.0.0.1:8091/`);
- `DEBUG LAN` (включает debug-stream на `0.0.0.0`, открывает видео по IP central);
- `OAK-VIEWER` (освобождает камеру для `oak-viewer`);
- `start/stop tunnel`, быстрый переход на `video/health`, просмотр логов сервисов.

Примечание:

- `DEBUG local` безопаснее (камера не открыта в LAN), предпочтительный режим для теста.
- `DEBUG LAN` использовать только в доверенной локальной сети.

## Depth-gate для головы/плеч (внедрено)

Depth-gate используется как фильтр поверх детекции/tracking (fail-safe).

Есть 2 рабочих профиля:

1) **Commissioning (широкий диапазон)** — для быстрого пуско‑наладочного прогона и первичной проверки depth:

- `CAM_DEPTH_MIN_M=0.20`
- `CAM_DEPTH_MAX_M=2.50`

2) **Production (узкий диапазон “голова/плечи”)** — чтобы снижать ложные события на реальной двери:

- область измерения: верхняя часть bbox человека (голова/плечи);
- рабочий диапазон: `0.40–1.50 м`;
- источник: стерео-глубина OAK-D Lite (mono B/C -> StereoDepth, align на CAM_A).

Узкий production‑диапазон включаем после финального монтажа камеры/геометрии и проверки на реальном транспорте.

Параметры в `/etc/passengers/passengers.env`:

- `CAM_DEPTH_ENABLE=1`
- `CAM_DEPTH_MIN_M=<0.20..0.40>`
- `CAM_DEPTH_MAX_M=<1.50..2.50>`
- `CAM_DEPTH_HEAD_FRACTION=0.45`
- `CAM_DEPTH_MIN_VALID_PX=25`

Поведение:

- если глубина головы/плеч вне диапазона, трек не участвует в подсчёте пересечений;
- если глубина недоступна (`n/a`), трек также исключается из подсчёта (fail-safe);
- в debug-stream поверх bbox выводится `z=<метры>` и статус `ok/reject`.

## Live панель под видео (внедрено)

На странице `http://127.0.0.1:8091/` теперь встроена живая панель статистики под/рядом с видео.

- обновление: раз в 1 секунду через `GET /health`;
- отображаются `status`, `messages`, `tracklets`, `active`, `depth_pass/reject/missing`, диапазон depth и timestamp;
- для диагностики доступен блок `raw_json` (полный payload `health`).

## Режим `depth-people-counting` (по мотивам Luxonis примера)

Базируется на идее официального примера:

- `DetectionNetwork (person)` + `ObjectTracker (track_id)`;
- depth-gate по зоне головы/плеч (commissioning: широкий диапазон, prod: `0.40–1.50 м`);
- подсчёт только полного пересечения двух линий `A↔B` (in/out), anti-duplicate и cooldown.

Источник:

- `https://docs.luxonis.com/software-v3/depthai/depthai-components/nodes/object_tracker/`
- `https://docs.luxonis.com/software-v3/depthai/depthai-components/messages/tracklets/`
- `https://docs.luxonis.com/software-v3/depthai/depthai-components/nodes/detection_network/`
- `https://github.com/luxonis/oak-examples/blob/main/neural-networks/counting/depth-people-counting/README.md` (как референс по depth-идее)

В проекте этот режим доступен как отдельный сервис:

- `passengers-camera-depth-counting.service`
- скрипт: `mvp/camera_transport_strict_counting.py`

Переключение через mode switch:

```bash
./scripts/camera_mode_switch.sh --mode depth-counting --camera-ip 192.168.10.11 --user orangepi
```

Или через интерактивное меню:

```bash
./scripts/camera_mode_menu.sh --camera-ip 192.168.10.11 --user orangepi --debug-port 8091
```

- пункт `5` — `DEPTH-COUNT local` (через SSH tunnel)
- пункт `6` — `DEPTH-COUNT LAN` (по IP central)
- пункт `7` — `DEPTH-HEIGHT-MULTI local` (stereo-only, мультитрекинг, depth-видео)
- пункт `8` — `DEPTH-HEIGHT-MULTI LAN` (stereo-only по IP)

URL в браузере (как и debug-stream):

- `http://127.0.0.1:8091/` — видео + live статистика
- `http://127.0.0.1:8091/health` — JSON
- `http://127.0.0.1:8091/?view=stats` — **только большой счётчик** (без видео), live обновление 1s. При открытии этого режима preview авто‑отключается (меньше нагрузка).

В UI:

- кнопка `Video: ON/OFF` — включает/выключает preview на стороне сервиса (уменьшает нагрузку, когда видео не нужно).

Параметры тюнинга (`/etc/passengers/passengers.env`):

- `CAM_DEPTH_COUNT_FPS`
- `CAM_DEPTH_COUNT_CONFIDENCE`
- `CAM_DEPTH_COUNT_TRACKER_TYPE`
- `CAM_DEPTH_COUNT_AXIS`
- `CAM_DEPTH_COUNT_AXIS_POS`
- `CAM_DEPTH_COUNT_AXIS_HYST`
- `CAM_DEPTH_COUNT_LINE_GAP_NORM`
- `CAM_DEPTH_COUNT_ANCHOR_MODE` (`center|leading_edge`)
- `CAM_DEPTH_COUNT_MIN_TRACK_AGE`
- `CAM_DEPTH_COUNT_MAX_LOST_FRAMES`
- `CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC`
- `CAM_DEPTH_COUNT_MIN_MOVE_NORM`
- `CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC`
- `CAM_DEPTH_COUNT_INVERT`
- `CAM_DEPTH_MIN_M` / `CAM_DEPTH_MAX_M`
- `CAM_JPEG_QUALITY` (качество MJPEG на странице видео; снижать при USB2/X_LINK проблемах)
- `CAM_PREVIEW_SIZE` (размер preview для MJPEG, пример: `480x300`)
- `CAM_PREVIEW_FPS` (частота обновления MJPEG в UI, например `5`; не меняет `CAM_DEPTH_COUNT_FPS`)

Важно:

- это строгий транспортный режим (`person + track_id + 2 линии`), приоритет — меньше ложных;
- режим требует полевой калибровки линии/гапа/возраста трека под конкретную дверь;
- при `usb_speed=HIGH` стартовать с `FPS=10` для стабильности, затем повышать по факту.

### Направление IN/OUT (как интерпретируется)

В `passengers-camera-depth-counting.service` направление считается по переходу зоны:

- `start_side=-1` → `end_side=+1` = `a_to_b` = **IN**
- `start_side=+1` → `end_side=-1` = `b_to_a` = **OUT**

Для текущей геометрии `axis=x` (горизонтальные линии):

- движение **сверху → вниз** в кадре = `a_to_b` = **IN** (как вам нужно).

Если в конкретной установке IN/OUT окажутся перепутаны — включаем инверсию:

- `CAM_DEPTH_COUNT_INVERT=1`

### Где ставить линии (практика для транспорта)

Цель линий: считать только факт **прохода через дверной проём**, а не “движение рядом с дверью”.

Правила размещения:

1. Линии ставим **внутри проёма**, а не по внешнему краю кадра — детекция/трек там стабильнее.
2. Центр `AXIS_POS` должен попадать в реальную траекторию людей (проверка: растёт `zone_mid_hits` и `middle_entries`).
3. Gap (`LINE_GAP_NORM`) задаёт “коридор” между линиями:
   - слишком маленький → трек может “перепрыгивать” middle за кадр (пропуски);
   - слишком большой → выше риск считать тех, кто стоит/двигается в дверях.
4. Для вашего кейса (сверху→вниз = IN) обычно удобно:
   - верхняя зона (`-1`) — “до двери” (наружная сторона в кадре),
   - нижняя зона (`+1`) — “после двери” (внутри салона),
   - событие только при полном пересечении `-1 → middle → +1`.

Метод подстройки (быстро, без “угадываний”):

1) Откройте видео+статы: `http://127.0.0.1:8091/`.
2) Сделайте 10–15 секунд быстрых проходов и смотрите:
   - если `zone_mid_hits=0` → `AXIS_POS` мимо траектории;
   - если растёт `zone_flip_no_middle` → увеличьте `LINE_GAP_NORM` или `AXIS_HYST`, и держите `ANCHOR_MODE=center`;
   - если события есть, но много ложных → поднимайте `CONFIDENCE` и/или `MIN_TRACK_AGE`, затем переходите на `transport-strict`.

## Шаг 7. Быстрая калибровка depth-counting (новый helper)

Добавлен скрипт:

- `scripts/camera_depth_calibrate.sh`

Назначение:

- быстро применить профиль калибровки без ручного редактирования `/etc/passengers/passengers.env`;
- перезапустить `passengers-camera-depth-counting.service`;
- сразу снять `health` и проверить рост `messages/tracklets_total`.

Быстрые команды:

```bash
# Показать текущие параметры + health
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --show --health

# Рекомендуемый первый прогон (широкий охват)
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --preset wide-scan --health

# Рекомендуемый профиль для транспорта (приоритет: меньше ложных)
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --preset transport-strict --health

# Быстрый commissioning‑профиль для транспорта (быстрее детект/счёт, выше риск ложных)
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --preset transport-fast-pass --health

# Возврат к базовым параметрам
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --preset baseline --health

# Ручной тюнинг
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi \
  --set CAM_DEPTH_COUNT_ROI=0.10,0.12,0.90,0.95 \
  --set CAM_DEPTH_COUNT_AREA_MIN=2600 \
  --health
```

Профили:

- `baseline` — исходные дефолты (узкий порог, консервативно).
- `wide-scan` — стартовый мягкий профиль (ниже `confidence`, мягче фильтры).
- `door-tight` — когда геометрия двери уже известна и нужен более строгий фильтр.
- `transport-strict` — профиль для общественного транспорта (меньше ложных): `confidence=0.65`, 2 линии (`gap=0.25`), `min_track_age=8`, `max_lost=5`, `cooldown=1.8s`, `FPS=10`.
- `transport-fast-pass` — commissioning‑профиль для транспорта (быстрые проходы): `confidence=0.30`, `min_track_age=1`, `max_lost=10`, `cooldown=0.60s`, `rearm=1.20s`, `FPS=10`, `CAM_JPEG_QUALITY=70`.

Рекомендуемая стратегия для вашей текущей цели (меньше ложных):

1. `--preset wide-scan` (проверить, что `messages/tracklets_total` стабильно растут на реальном проходе).
2. `--preset transport-fast-pass` (commissioning: добиться стабильных `events` и быстрой реакции на проходы).
3. `--preset transport-strict` (боевой профиль: меньше ложных на транспорте).
4. При необходимости точечный тюнинг `LINE_GAP_NORM / MIN_TRACK_AGE / MIN_MOVE_NORM / AXIS_HYST`.

Если `tracklets_total` растёт, но `count_in/out` не меняются:

- проверить ось пересечения по реальному движению в кадре:
  - движение слева↔направо => `CAM_DEPTH_COUNT_AXIS=y` (вертикальные линии);
  - движение сверху↕вниз => `CAM_DEPTH_COUNT_AXIS=x` (горизонтальные линии).
- для быстрого пуско-наладочного прогона можно временно применить:
  - `AXIS=y`, `LINE_GAP_NORM=0.10`, `CONFIDENCE=0.45`, `MIN_TRACK_AGE=3`, `MIN_MOVE_NORM=0.04`, `HANG_TIMEOUT=8.0`, `COOLDOWN=0.80`.

Факт прогона (door-1, `192.168.10.11`, `2026-02-16`):

- применён профиль: `transport-strict`;
- сервис: `passengers-camera-depth-counting.service` = `active (running)`;
- `/health`: `status=running`, `device=OAK-D-LITE`, `messages/tracklets_total` растут, `active_tracks` > 0, `imu_type=BMI270`.

Через интерактивное меню:

```bash
./scripts/camera_mode_menu.sh --camera-ip 192.168.10.11 --user orangepi --debug-port 8091
```

- пункт `19` — запустить helper калибровки;
- пункт `20` — снять 5 подряд `health`-сэмплов для быстрой оценки стабильности.

## Режим `depth-height-multi` (stereo-only, мультитрекинг) — 2026-02-19

Что сделано и зачем:

- добавлен отдельный режим `depth-height-multi` в `camera_mode_switch.sh` и интерактивное меню;
- добавлен отдельный сервис `passengers-camera-depth-height-multi.service` (не ломает `depth-counting`);
- добавлен новый рантайм `mvp/camera_depth_height_multi.py`:
  - только `StereoDepth` (без RGB-детекции),
  - выделение depth-компонент в ROI,
  - мультитрекинг по нескольким `track_id` с защитами (`min_track_age`, `max_lost`, `cooldown`, `rearm`, `hang timeout`),
  - подсчёт IN/OUT по пересечению 2 линий,
  - depth-видео в браузере (`/`) + `/?view=stats` без видео для снижения нагрузки.

Быстрый запуск:

```bash
# Переключить на stereo-only multi-tracking
./scripts/camera_mode_switch.sh --mode depth-height-multi --camera-ip 192.168.10.11 --user orangepi

# Туннель на ПК
ssh -N -L 8091:127.0.0.1:8091 orangepi@192.168.10.11

# Браузер
http://127.0.0.1:8091/
```

Безопасные дефолты для USB2 (`usb_speed=HIGH`):

- `CAM_DEPTH_MULTI_FPS=10`
- `CAM_DEPTH_MULTI_PREVIEW_SIZE=416x256`
- `CAM_DEPTH_MULTI_PREVIEW_FPS=5`
- `CAM_DEPTH_MULTI_OUTPUT_SIZE=320x200`
- `CAM_JPEG_QUALITY=58`
- depth-гейт от камеры для head-only старта: `CAM_DEPTH_MULTI_MIN_M=0.35`, `CAM_DEPTH_MULTI_MAX_M=0.95`

Live IN/OUT watcher для этого режима:

```bash
./scripts/depth_counter_io_watch.sh --camera-ip 192.168.10.11 --user orangepi --unit passengers-camera-depth-height-multi.service --bootstrap-since "today"
```

Следующий этап и зачем:

- провести 3 цикла теста (`1 человек`, `2 рядом`, `паровозиком`) в `depth-height-multi`, зафиксировать `events`, `zone_flip_no_middle`, `age/dup/rearm rejects`;
- после этого зафиксировать дверной пресет `stereo-only transport` (чтобы быстро тиражировать на остальные системы без ручной импровизации).

Факт прогона и калибровки (door-2 `192.168.10.11`, 2026-02-19):

- первый прогон `depth-height-multi`: сервис стабилен, `usb_speed=HIGH`, получено `events_total=3` (`IN=1`, `OUT=2`) при активном depth-video;
- в логах были события с глубиной около `0.36–0.41 м` (`depth-height-multi event ... depth_m=...`);
- после `stop` применён быстрый тюнинг под более быстрые проходы:
  - `CAM_DEPTH_MULTI_MIN_M=0.30`
  - `CAM_DEPTH_MULTI_MAX_M=1.20`
  - `CAM_DEPTH_MULTI_MIN_TRACK_AGE=2`
  - `CAM_DEPTH_MULTI_MAX_LOST_FRAMES=8`
  - `CAM_DEPTH_MULTI_MATCH_DIST_PX=60`
  - `CAM_DEPTH_MULTI_AREA_MIN=120`
  - `CAM_DEPTH_MULTI_COUNT_COOLDOWN_SEC=0.60`
  - `CAM_DEPTH_MULTI_PER_TRACK_REARM_SEC=0.80`
- безопасный preview-профиль сохранён: `416x256 @ 5fps`, `output=320x200`, `JPEG=58`.

Следующий этап и зачем:

- повторить цикл теста после тюнинга (минимум 60–90 сек, быстрые проходы + 2 рядом), чтобы подтвердить рост `events_total` без всплеска ложных срабатываний;
- после подтверждения зафиксировать `stereo-only transport` как пресет commissioning для эталонной двери.

## Эксперимент high FPS + higher depth resolution (2026-02-19)

Что сделано:

- включён профиль повышенной нагрузки для `depth-height-multi` на `192.168.10.11`:
  - `CAM_DEPTH_MULTI_FPS=15`
  - `CAM_DEPTH_MULTI_OUTPUT_SIZE=384x240`
  - `CAM_DEPTH_MULTI_PREVIEW_SIZE=480x300`
  - `CAM_DEPTH_MULTI_PREVIEW_FPS=5`
  - `CAM_JPEG_QUALITY=58`

Результат быстрой проверки:

- сервис `passengers-camera-depth-height-multi.service` остаётся `active`;
- в течение прогона `messages` стабильно растут;
- в логах идут `event` и `heartbeat` без `X_LINK_ERROR`;
- текущий стартовый лог: `usb_speed=HIGH`, `fps=15.0`, `output=384x240`.

Rollback (если на длинном прогоне появится нестабильность):

- вернуть безопасный профиль:
  - `CAM_DEPTH_MULTI_FPS=12`
  - `CAM_DEPTH_MULTI_OUTPUT_SIZE=320x200`
  - `CAM_DEPTH_MULTI_PREVIEW_SIZE=416x256`
  - `CAM_DEPTH_MULTI_PREVIEW_FPS=5`

Следующий этап и зачем:

- прогнать длинный цикл (10–15 минут) на этом профиле с реальными проходами и зафиксировать стабильность для решения “оставить 15/384x240 или откатить”.

Факт обновления профиля (2026-02-19, следующий шаг):

- профиль поднят до:
  - `CAM_DEPTH_MULTI_FPS=20`
  - `CAM_DEPTH_MULTI_OUTPUT_SIZE=640x400`
  - `CAM_DEPTH_MULTI_PREVIEW_SIZE=416x256`
  - `CAM_DEPTH_MULTI_PREVIEW_FPS=4`
  - `CAM_JPEG_QUALITY=55`
- после повышения применён балансирующий тюнинг для снижения ложных при “топтании” и сохранения мультитрекинга:
  - `CAM_DEPTH_MULTI_MIN_M=0.35`
  - `CAM_DEPTH_MULTI_MAX_M=1.00`
  - `CAM_DEPTH_MULTI_MIN_TRACK_AGE=3`
  - `CAM_DEPTH_MULTI_MAX_LOST_FRAMES=8`
  - `CAM_DEPTH_MULTI_MATCH_DIST_PX=55`
  - `CAM_DEPTH_MULTI_AREA_MIN=220`
  - `CAM_DEPTH_MULTI_AXIS_HYST=0.02`
  - `CAM_DEPTH_MULTI_COUNT_COOLDOWN_SEC=1.00`
  - `CAM_DEPTH_MULTI_PER_TRACK_REARM_SEC=1.60`
  - `CAM_DEPTH_MULTI_WATERSHED_DIST_RATIO=0.42`

Короткий smoke после изменений:

- сервис `active`;
- `messages` растут (без пауз);
- в коротком окне проверки `X_LINK_ERROR` не зафиксирован.

Что обязательно донастроить на этом профиле (по официальным рекомендациям DepthAI/Luxonis):

1) Проверка глубины на реальной сцене (дверь/высота/угол) и коррекция `MIN_M/MAX_M`.
2) Подстройка `AREA_MIN` и `MATCH_DIST_PX` под “1 человек / 2 рядом / паровозиком”.
3) Подстройка анти‑дубликатов (`cooldown/rearm`) под “топтание в зоне”.
4) При финальном монтаже — пройти Dynamic Calibration и зафиксировать эталонные параметры.

Следующий этап и зачем:

- провести полноценный 10–15 минутный прогон (одиночные и массовые проходы), чтобы подтвердить профиль `20 FPS + 640x400` как рабочий либо откатить до `15/384x240`.

Операционный факт (2026-02-19, live test):

- выполнен повторный `restart` сервиса `passengers-camera-depth-height-multi.service` с повторным применением профиля `20 FPS + 640x400`;
- после рестарта сервис `active`, `/health` доступен, поток depth-видео поднимается;
- стартовые счётчики после рестарта обнулены (новая сессия), дальше требуется новый прогон проходов для сравнения дельт `IN/OUT`.

Комплексный разбор повторного теста `10 + 10` (2026-02-19, после тюнинга):

- профиль: `20 FPS`, `640x400`, `depth=0.35..1.20`, `area_min=190`, `cooldown=0.4`, `rearm=1.1`;
- результат: `events_total=14` (`IN=6`, `OUT=8`) при целевых `20` проходах;
- полнота счёта: ~`70%` (недосчёт `6` событий);
- стабильность: сервис `active`, `X_LINK` нет; в логе только `BrokenPipeError` (закрытие браузерного клиента, не падение счётчика);
- качество crossing-логики: `zone_flip_no_middle=0`, `age_reject=0`, `hang_reject=0`, `dup_reject=0`, `rearm_reject=0`.

Вывод по причине недосчёта:

- проблема не в антидубликатах и не в частоте кадров;
- узкое место — continuity треков/геометрия полного crossing в плотном потоке (часть траекторий не завершается как валидный `A→B/B→A`).

Нужно ли повышать FPS выше 20:

- для этого стенда (`usb_speed=HIGH`, USB2) **повышение FPS выше 20 не является приоритетным улучшением точности**;
- ожидаемый эффект от роста FPS сейчас низкий, а риск нестабильности (USB/поток/рестарты) выше;
- следующий прирост точности даёт не FPS, а тюнинг трекинга и геометрии.

Рекомендованный следующий тюнинг (при том же `20/640x400`):

- `CAM_DEPTH_MULTI_MAX_LOST_FRAMES=10..12`
- `CAM_DEPTH_MULTI_MATCH_DIST_PX=65..75`
- `CAM_DEPTH_MULTI_AREA_MIN=160..180`
- `CAM_DEPTH_COUNT_LINE_GAP_NORM=0.18..0.20` (чуть облегчить полный crossing)

Следующий этап и зачем:

- применить указанный tracking/geometric тюнинг и повторить `10+10`, чтобы поднять полноту счёта к целевому диапазону `18..20` без роста ложных.

## Результат прогона “10 в одну сторону + 10 в другую” (2026-02-19, профиль 20/640x400)

Факт сессии (с момента `ActiveEnterTimestamp` сервиса):

- `events_total=15` (`IN=7`, `OUT=8`) при целевых `20` проходах;
- детекции: `979`, `messages: 4811`, `heartbeats: 34`;
- глубина событий: `0.386..0.955 м` (среднее `0.517 м`);
- `zone_flip_no_middle=0` (геометрия линий корректная, “flip без middle” не доминирует);
- ошибки канала `X_LINK` не зафиксированы; был `BrokenPipeError` от закрытия браузерного MJPEG‑клиента (не критично для счётчика).

Ключевые причины недосчёта (по метрикам):

1. Глобальный антидубль слишком строгий для плотного потока:
   - `dup_reject=6`, при `count_cooldown_sec=1.0` часть быстрых последовательных проходов подавляется.
2. Верхняя граница depth‑gate близко к наблюдаемому максимуму:
   - события доходят до `0.955 м`, при `max=1.00 м` часть реальных проходов на дальнем крае может отбрасываться.
3. Фильтр площади (`area_min=220`) может резать небольшие валидные объекты в краях ROI при массовом потоке.

Рекомендованный следующий тюнинг для массовых проходов (без увеличения ложных скачком):

- `CAM_DEPTH_MULTI_COUNT_COOLDOWN_SEC=0.30..0.45`
- `CAM_DEPTH_MULTI_PER_TRACK_REARM_SEC=1.00..1.20`
- `CAM_DEPTH_MULTI_MAX_M=1.10..1.20`
- `CAM_DEPTH_MULTI_AREA_MIN=180..200`

Следующий этап и зачем:

- применить указанный тюнинг и повторить тот же тест `10+10`, чтобы довести счёт к целевому диапазону `18..20` при сохранении стабильности и контроля ложных.

Критерий успешной калибровки (без модуля камеры в финальной схеме):

- сервис `passengers-camera-depth-counting.service` в статусе `active`;
- в `/health` поле `messages` растёт;
- в сцене с человеком растут `tracklets_total` и `depth_pass`;
- `count_in/count_out` меняются только при полном пересечении `A↔B`.

Диагностика “почему не считает” через `/health`:

- `zone_neg_hits / zone_mid_hits / zone_pos_hits` — в какие зоны реально попадает tracked-point;
- `middle_entries` — сколько раз трек входил в middle-зону между линиями;
- `middle_inferred` — middle inferred по span bbox (для быстрых проходов, когда tracked-point может “перепрыгнуть” middle за кадр);
- `zone_flip_no_middle` — трек менял сторону без корректного middle-прохода.

Если растёт только `zone_pos_hits` (или только `zone_neg_hits`), а `zone_mid_hits=0`:

- трек физически не проходит через middle по логике счётчика (визуально bbox может касаться линий, но tracked-point не пересекает контур).
- сначала можно проверить альтернативный anchor без смены геометрии:
  - `--set CAM_DEPTH_COUNT_ANCHOR_MODE=leading_edge --health`.

Минимальная правка геометрии (1 параметр) без изменения остальных порогов:

- сдвиг центра линий: `--set CAM_DEPTH_COUNT_AXIS_POS=0.78 --health`
- критерий успеха: `zone_mid_hits` начинает расти (контур попал в реальную траекторию).

Текущий рабочий шаг диагностики на стенде `door-1` (`192.168.10.11`):

- после прогона с `leading_edge` возвращаем `CAM_DEPTH_COUNT_ANCHOR_MODE=center` для стабильной зоны (меньше прыжков side↔side без middle);
- затем делаем реальный проход и смотрим дельты в `/health`.

Быстрый live-анализ (рекомендуется):

```bash
./scripts/camera_depth_live_probe.sh --camera-ip 192.168.10.11 --user orangepi --seconds 60 --out /tmp/door1-live.jsonl
```

## Журналирование калибровок (обязательно)

Правило: **каждое** изменение параметров (preset/`--set`) фиксируем отдельным “прогоном” в `Docs/auto/camera-tuning/`.

Зачем:

- можно сравнивать итерации и откатываться на рабочие значения;
- видны причины отказов (ROI/bbox/conf/depth) без гаданий.

Шаблон:

```bash
# 1) применили изменение
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --preset head-yolov8-host-loose --health

# 2) сделали 10+10 проходов

# 3) сохранили прогон (env + health.jsonl + journal + summary)
./scripts/camera_tuning_run.sh --camera-ip 192.168.10.11 --label office_10x10_loose --seconds 180
```

Результат:

- создаётся папка `Docs/auto/camera-tuning/<ip>/<timestamp>_<label>/` с `summary.md`.

Альтернатива (ручной one-liner, 60 секунд, во время прогона):

```bash
start=$(ssh orangepi@192.168.10.11 'curl -sS http://127.0.0.1:8091/health')
for i in $(seq 1 60); do
  ssh orangepi@192.168.10.11 'curl -sS http://127.0.0.1:8091/health' | jq -c '{events_total,count_in,count_out,zone_neg_hits,zone_mid_hits,zone_pos_hits,middle_entries,zone_flip_no_middle,age_reject,move_reject,hang_reject,conf_reject,depth_reject,depth_missing}'
  sleep 1
done
end=$(ssh orangepi@192.168.10.11 'curl -sS http://127.0.0.1:8091/health')
jq -n --argjson s "$start" --argjson e "$end" '{
  d_events: ($e.events_total-$s.events_total),
  d_in: ($e.count_in-$s.count_in),
  d_out: ($e.count_out-$s.count_out),
  d_zone_neg: ($e.zone_neg_hits-$s.zone_neg_hits),
  d_zone_mid: ($e.zone_mid_hits-$s.zone_mid_hits),
  d_zone_pos: ($e.zone_pos_hits-$s.zone_pos_hits),
  d_middle_entries: ($e.middle_entries-$s.middle_entries),
  d_flip_no_middle: ($e.zone_flip_no_middle-$s.zone_flip_no_middle),
  d_age_reject: ($e.age_reject-$s.age_reject),
  d_move_reject: ($e.move_reject-$s.move_reject),
  d_hang_reject: ($e.hang_reject-$s.hang_reject),
  d_conf_reject: ($e.conf_reject-$s.conf_reject),
  d_depth_reject: ($e.depth_reject-$s.depth_reject),
  d_depth_missing: ($e.depth_missing-$s.depth_missing)
}'
```

Интерпретация:

- `d_events=0` и `d_zone_mid=0` -> линии не попали в траекторию (подстройка `AXIS_POS/LINE_GAP/AXIS`);
- `d_events=0` и `d_flip_no_middle` большой -> трек перескакивает сторону без middle (проверить `anchor_mode=center`, затем `AXIS_HYST`/`LINE_GAP`);
- `d_events=0` и растут `d_age_reject`/`d_move_reject` -> слишком строгие `MIN_TRACK_AGE`/`MIN_MOVE_NORM`;
- `d_events=0` и растут `d_depth_reject`/`d_depth_missing` -> поправить depth-диапазон/монтаж/угол.

Факт live-прогона (2026-02-16, door-2 физически на узле `192.168.10.11`):

- при `axis=y` и `line_a/b=0.73/0.83` получены дельты:
  - `d_events=0`, `d_zone_mid=1353`, `d_middle_entries=27`;
  - `d_conf_reject=176`, `d_depth_reject=73`, `d_age_reject=10`, `d_hang_reject=13`.
- вывод: пересечения есть по геометрии, но событие режется качественными фильтрами в момент прохода;
- следующий тестовый шаг: переключение оси на `axis=x` (`line_a/b=0.46/0.64`) для проверки соответствия реальному направлению движения в кадре.

Факт контрольного прогона `axis=x` (2026-02-16):

- `d_events=0`, при этом почти весь поток в `zone_pos` (`d_zone_pos=1212`, `d_zone_neg=17`);
- вывод: на этом монтаже рабочая ось — `axis=y` (ось `x` не соответствует траектории прохода).

Факт контрольного прогона `axis=y` + мягкие фильтры + `CAM_DEPTH_ENABLE=0` (2026-02-16):

- `d_events=10`, `d_in=5`, `d_out=5` за 75 секунд;
- это доказало, что логика пересечения и трекинг работают, а блокером были фильтры качества (`confidence/depth`).

Комиссионный режим (только для первичной пуско-наладки):

```bash
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --preset commissioning-no-depth --health
```

- назначение: быстро подтвердить рабочую геометрию и направление счёта;
- ограничение: для прод-эксплуатации в транспорте вернуть depth-gate (`CAM_DEPTH_ENABLE=1`) и ужесточить пороги.

Комиссионный режим с depth-gate (мягкий):

```bash
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --preset commissioning-depth-soft --health
```

Факт прогона `commissioning-depth-soft` (2026-02-16):

- за 75 секунд: `d_events=8`, `d_in=4`, `d_out=4`;
- `depth` включён, счёт сохраняется;
- это текущий рабочий профиль для стенда до финальной геометрии/освещения транспорта.

Факт прогона `near-prod` (2026-02-16, промежуточное ужесточение):

- при `confidence=0.35`, `min_track_age=2`, `min_move=0.04`, `depth=0.30..2.20` получено `d_events=0`;
- растут `conf_reject/depth_reject/age_reject`, что снова обнуляет счёт на текущем стенде.

Рекомендуемая лестница перехода к прод-порогам:

1. `commissioning-depth-soft` (подтверждение стабильного счёта).
2. Поднимать только `CAM_DEPTH_COUNT_CONFIDENCE` (+0.05 за шаг), оставляя остальное без изменений.
3. Затем поднимать `CAM_DEPTH_COUNT_MIN_TRACK_AGE` и `CAM_DEPTH_COUNT_MIN_MOVE_NORM` по одному параметру за итерацию.
4. В каждом шаге прогон `camera_depth_live_probe` 60–90s и фиксация `d_events`/reject-дельт.

Факт шага `CONFIDENCE=0.25` (2026-02-16, depth включён):

- за 75 секунд получено `d_events=9`, `d_in=4`, `d_out=5`;
- `depth_missing=0`, `age_reject=0`, `move_reject=0`;
- профиль остаётся рабочим, можно поднимать `CONFIDENCE` дальше на следующий шаг.

Факт шага `CONFIDENCE=0.30` (2026-02-16, depth включён):

- за 75 секунд: `d_events=25`, `d_in=12`, `d_out=13`;
- счёт остаётся стабильным (`OK: events are increasing`);
- следующий риск: потенциальный overcount на колебаниях трека, поэтому следующим шагом повышаем анти-дубль (`COUNT_COOLDOWN_SEC`).

Факт шага `COUNT_COOLDOWN_SEC=1.20` при `CONFIDENCE=0.30` (2026-02-16):

- за 75 секунд: `d_events=7`, `d_in=4`, `d_out=3`;
- счёт остаётся рабочим, частота событий заметно ниже (консервативнее, меньше риска дублей);
- для следующего шага ужесточения целесообразно поднимать `MIN_TRACK_AGE` (с `1` до `2`) при сохранении `COUNT_COOLDOWN_SEC=1.20`.

Факт шага `MIN_TRACK_AGE=2` (2026-02-16):

## CrowdHuman model (blob) — статус интеграции (2026-02-19)

Что сделано:

- в проект добавлен blob-файл: `mvp/models/yolov8n_crowdhuman_person.blob`;
- проверен запуск на `door-2` (`192.168.10.11`) через `CAM_DEPTH_COUNT_MODEL=/opt/passengers-mvp/models/yolov8n_crowdhuman_person.blob`.

Факт:

- runtime `camera_transport_strict_counting.py` поддерживает локальную загрузку `.blob` через `DetectionNetwork.setBlobPath(...)`
  (то есть без обращения к `easyml.cloud.luxonis.com`).

Вывод:

- для YOLO-моделей `.blob` **сам по себе** не содержит head/parser-метаданных, которые использует `DetectionNetwork` в DepthAI v3.
  На практике это часто означает `detections=[]` (нулевой поток детекций), даже если инференс реально выполняется.
- надёжный путь для on-device YOLO в DepthAI v3: использовать **NNArchive** (`*.rvc2.tar.xz`) с заполненным `config.json:model.heads`
  (parser=`YOLO`, `subtype`, `classes`, `yolo_outputs`).

Откат после проверки:

- `CAM_DEPTH_COUNT_MODEL` возвращён на `yolov6-nano`;
- `passengers-camera-depth-counting.service` снова `active`.

Что делать дальше (по шагам):

1. Подтвердить, что внедряем custom-модель через локальный blob (доработка runtime).
2. Добавить в runtime отдельный путь `local-blob` (без обращения в облако Luxonis).
3. Зафиксировать входной размер сети (`640x640` или `416x416`) и пороги.
4. Прогнать `10+10` и сравнить полноту/ложные с baseline.

### Официальный путь Luxonis для custom-модели (использовать как первичный источник)

Ссылки (официально):

- Model conversion (DepthAI v3): `https://docs.luxonis.com/software-v3/ai-inference/conversion/`
- RVC conversion online: `https://docs.luxonis.com/software-v3/ai-inference/conversion/rvc-conversion/online/`
- RVC conversion offline: `https://docs.luxonis.com/software-v3/ai-inference/conversion/rvc-conversion/offline`
- DetectionNetwork node: `https://docs.luxonis.com/software-v3/depthai/depthai-components/nodes/detection_network/`

Практический вывод для текущего проекта:

- `.blob` можно загрузить локально (в runtime добавлена поддержка local blob), но для корректной детекции нужен совместимый parser/архив модели;
- в runtime `DetectionNetwork.build(..., NNModelDescription(...))` custom `.blob` без корректного упаковочного формата/метаданных не даёт рабочий поток детекций;
- поэтому для прод-внедрения custom CrowdHuman-модели идём через официальный conversion-поток Luxonis и валидируем формат модели, который ожидает `DetectionNetwork` в вашем пайплайне.

### Что делаю я / что делаете вы (чёткое разделение)

Что делаю я:

1. Поддержка local blob в `camera_transport_strict_counting.py` уже добавлена (путь + размер входа `CAM_DEPTH_COUNT_MODEL_INPUT_SIZE`).
2. Добавлен default в mode-switch: `CAM_DEPTH_COUNT_MODEL_INPUT_SIZE=640x640`.
3. Дальше: после получения валидного артефакта модели от official converter — подключаю в сервис, запускаю `10+10`, фиксирую метрики и обновляю пресет.

Что делаете вы руками:

1. Готовите финальный артефакт модели через официальный Luxonis conversion workflow.
2. Передаёте путь артефакта в проект (например, `mvp/models/...`).
3. Делаете физический прогон проходов (`10+10`, `2 рядом`, быстрые проходы) для валидации на двери.

## Анализ чата по схеме HEAD+DEPTH (2026-02-19)

Основание (официальные источники Luxonis):

- `https://docs.luxonis.com/software-v3/ai-inference/integrations/yolo`
- `https://docs.luxonis.com/software-v3/ai-inference/conversion`
- `https://docs.luxonis.com/software-v3/depthai/depthai-components/nodes/detection_network/`
- `https://docs.luxonis.com/software-v3/depthai/depthai-components/nodes/object_tracker/`

Вывод по текущему состоянию:

1. Настроить **целевой вариант из чата (HEAD + depth + track_id + line-crossing)** на текущей модели `yolov8n_best...` в полном объёме нельзя, так как в metadata OpenVINO модель имеет класс `person`, а не `head`.
2. Базовая инфраструктура под эту схему уже есть:
   - depth-gate,
   - ObjectTracker + line crossing,
   - debug UI/health/logs,
   - загрузка local `.blob` в runtime.
3. Чего не хватает для полного HEAD-режима:
   - корректной head-модели (`head`/`head_shoulders`),
   - валидного для пайплайна Luxonis артефакта conversion (модель + parser/config),
   - отдельных фильтров `bbox size/aspect/w*Z` как конфигурируемых правил,
   - финальной калибровки на двери транспорта (10+10, 2 рядом, быстрые проходы).

Рабочий промежуточный статус:

- `person`-модель можно использовать только как промежуточный этап для проверки канала и трекинга.
- Для целевого качества (меньше склеек при 5–6 людях) нужно перейти именно на head-модель.

### Что можно сделать прямо сейчас на `yolov6-nano` (без head-модели)

Важно: `yolov6-nano` в нашем стенде — это **person**-детектор (не head). Поэтому “head-схема” здесь реализуется только частично:

- детекция = person,
- depth-gate = по верхней части bbox (head/shoulders region),
- трекинг = `ObjectTracker(track_id)`,
- событие = `2 линии + middle-cross + anti-duplicate`.

Тем не менее это полезно, чтобы:

- стабилизировать геометрию линий/ROI,
- подобрать пороги трекера и антидублей,
- подготовить commissioning-процесс до прихода head-модели.

#### Рекомендуемый “комиссионный” профиль на стенде (старт)

В `/etc/passengers/passengers.env` на узле с камерой:

- `CAM_DEPTH_COUNT_MODEL=yolov6-nano`
- `CAM_DEPTH_COUNT_FPS=10..15` (USB2 → начинать с 10)
- `CAM_DEPTH_MIN_M=0.40`
- `CAM_DEPTH_MAX_M=1.80` (после реальных измерений можно ужать)
- `CAM_DEPTH_HEAD_REGION=top`
- `CAM_DEPTH_HEAD_FRACTION=0.45`
- `CAM_DEPTH_COUNT_MIN_TRACK_AGE=5`
- `CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC=0.50`
- `CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC=1.00`

#### ROI (зона прохода) — уже поддерживается в `depth-counting`

В runtime добавлена поддержка ROI через переменную:

- `CAM_DEPTH_COUNT_ROI=x1,y1,x2,y2` (нормализованные координаты `0..1`)

Эффект:

- счёт/логика crossing работает **только внутри ROI**;
- вне ROI треки игнорируются и не влияют на side/middle.

Проверка:

- `GET /health` содержит поля `roi` и `roi_reject`.

#### BBox фильтры (size / aspect / w*Z) — добавлено (под head-модель)

Это реализация практики из чата: фильтровать “мусор” по форме bbox и по физике `w*Z` (ширина bbox в пикселях * глубина в метрах).

Переменные (в `/etc/passengers/passengers.env`, применяются в `passengers-camera-depth-counting.service`):

- `CAM_DEPTH_COUNT_BBOX_MIN_W_PX`
- `CAM_DEPTH_COUNT_BBOX_MIN_H_PX`
- `CAM_DEPTH_COUNT_BBOX_MAX_W_PX`
- `CAM_DEPTH_COUNT_BBOX_MAX_H_PX`
- `CAM_DEPTH_COUNT_BBOX_MIN_AREA_PX2`
- `CAM_DEPTH_COUNT_BBOX_MAX_AREA_PX2`
- `CAM_DEPTH_COUNT_BBOX_MIN_AR`
- `CAM_DEPTH_COUNT_BBOX_MAX_AR`
- `CAM_DEPTH_COUNT_BBOX_MIN_WZ`
- `CAM_DEPTH_COUNT_BBOX_MAX_WZ`

Как интерпретируются значения:

- `*_W_PX/*_H_PX/*_AREA_PX2` считаются в пространстве `CAM_DEPTH_COUNT_MODEL_INPUT_SIZE` (по умолчанию для `yolov6-nano` это `512x288`).
- `AR` = `w/h`.
- `WZ` = `w_px * depth_m` (например `45..110` для head‑bbox в `416x416` — как стартовая гипотеза, потом тюнится по логам).

Метрики:

- `/health`: `bbox_reject_size`, `bbox_reject_ar`, `bbox_reject_wz`
- на preview над bbox теперь показываются `w/h/ar/wz` (для калибровки).

Важно:

- на `yolov6-nano` (person) эти фильтры полезны как анти‑мусор, но их “идеальные пороги” будут другими, чем у head‑bbox.
- целевая польза — когда детектор действительно head (1 класс).

#### Поддержка local `NNArchive` (offline head-модель)

Под head‑модель на OAK‑D Lite предпочтительно использовать артефакт конвертации вида:

- `*.rvc2.tar.xz` (RVC2 archive)

Runtime `depth-counting` умеет грузить такой файл локально (без интернета) через `dai.NNArchive(...)`, если:

- `CAM_DEPTH_COUNT_MODEL=/opt/passengers-mvp/models/<model>.rvc2.tar.xz`.

Это соответствует тому же подходу, что использует model‑zoo `yolov6-nano` (файл хранится в `~/.depthai_cached_models/.../*.rvc2.tar.xz`).

#### Кандидат head-модели (проверить/прототипировать)

Репозиторий: `https://github.com/Abcfsa/YOLOv8_head_detector`

Что даёт:

- готовые веса YOLOv8 для head detection (`nano.pt`, `medium.pt`).

Ограничения:

- репозиторий не DepthAI/OAK‑ready “из коробки” (нужна конвертация по official Luxonis workflow);
- обязательно проверить лицензию весов и датасета под прод.

#### Конвертация Abcfsa YOLOv8 head → NNArchive (факт стенда, 2026-02-19)

Цель:

- получить офлайн‑артефакт `*.rvc2.tar.xz`, который понимает `DetectionNetwork.build(camera, dai.NNArchive(...))`,
  и тем самым запускать head‑детектор on-device (без интернета).  
  ⚠ На практике (DepthAI `3.3.0`) конкретный YOLOv8 DFL‑архив **не декодируется** `DetectionNetwork` (в `detections=0`),
  поэтому добавлен fallback **host‑декодер** (инференс остаётся на OAK).

Что сделано в проекте (артефакты):

- исходные веса (локально, игнорируются git): `mvp/models/src/yolov8_head_detector/yolov8_head_scut_nano.pt`
- подготовленный NNArchive (кандидат): `mvp/models/HEAD_YOLOv8n_SCUT_Nano_416_YOLO_RAW_head.rvc2.tar.xz`

Официальная база Luxonis (первичные источники):

- conversion: `https://docs.luxonis.com/software-v3/ai-inference/conversion/`
- NNArchive: `https://docs.luxonis.com/software-v3/ai-inference/nn-archive/`
- DetectionNetwork: `https://docs.luxonis.com/software-v3/depthai/depthai-components/nodes/detection_network/`

Как делали (воспроизводимо в репозитории):

1. Экспорт `.pt -> .onnx` (Ultralytics) с фиксированным input `416x416`.
2. Переключение выходов ONNX на “сырые” 3‑скейла YOLOv8 DFL (в нашем случае это тензоры `cat_13/cat_14/cat_15`).
3. Конвертация ONNX → RVC2 NNArchive через официальный `ghcr.io/luxonis/modelconverter-rvc2`.
4. Патч `config.json` внутри NNArchive: добавление head‑секции `parser=YOLO` с `subtype=yolov8`, `classes=[head]`,
   `yolo_outputs=[cat_13,cat_14,cat_15]`.

Автоматизация (скрипты проекта):

- поиск raw‑выходов: `scripts/onnx_find_yolov8_raw_outputs.py`
- переписать outputs в ONNX: `scripts/onnx_set_outputs.py`
- добавить YOLO head в NNArchive: `scripts/nnarchive_add_yolo_head.py`
- end-to-end обёртка: `scripts/model_convert_yolov8_to_rvc2_nnarchive.sh`

Факт валидации на устройстве (door‑2 / `192.168.10.11`):

- NNArchive загружается, сервис стартует;
- при этом при backend=`device` `detections/tracklets=0` (YOLO parser не отдаёт детекции).

Решение (факт стенда, 2026‑02‑19):

- добавлен backend `host-yolov8-raw` для `mvp/camera_transport_strict_counting.py`:
  - на устройстве запускается `NeuralNetwork` с тем же `NNArchive` (инференс на OAK),
  - на OPi делается лёгкий host‑декод YOLOv8 DFL (`cat_13/cat_14/cat_15`) + NMS,
  - далее используется та же строгая логика подсчёта (ID + 2 линии) через “tracklets-like” объекты.
- включается параметром:
  - `CAM_DEPTH_COUNT_BACKEND=host-yolov8-raw`

Доп. параметры host‑декодера:

- `CAM_DEPTH_COUNT_NMS_IOU` (например `0.5`)
- `CAM_DEPTH_COUNT_MAX_DET` (например `120`)
- `CAM_DEPTH_COUNT_MATCH_DIST_PX` (например `90`) — match дистанция центров bbox между кадрами.

Наблюдение/гипотеза (важно для отладки, 2026‑02‑19):

- в ранней версии `camera_transport_strict_counting.py` порог `DetectionNetwork.setConfidenceThreshold(...)` был “зажат”
  снизу до `>=0.10`;
- при офлайн‑прогоне `nano.pt` на реальном `snapshot.jpg` со стенда максимальный `conf` был ~`0.099` (т.е. чуть ниже 0.10),
  что **могло полностью обнулять** поток детекций на устройстве.

Исправление в коде (факт, 2026‑02‑19):

- добавлен отдельный порог для DNN: `CAM_DEPTH_COUNT_DNN_CONFIDENCE` (может быть < 0.10),
- пороги теперь разделены:
  - `CAM_DEPTH_COUNT_DNN_CONFIDENCE` — что попадает в трекер (что вообще “видит” пайплайн),
  - `CAM_DEPTH_COUNT_CONFIDENCE` — что допускается до логики подсчёта/событий.

Практический вывод:

- путь конвертации/упаковки **готов** и воспроизводим;
- качество/совместимость конкретной head‑модели Abcfsa под вашу геометрию **не подтверждено** — для “2–3 рядом” вероятно потребуется:
  - другая head‑модель (с нормальной лицензией), и/или
  - дообучение под top‑down двери (ваши кадры + head-аннотации), затем тот же conversion-поток.

#### Запуск head‑модели на стенде (door‑2 / `192.168.10.11`) — тестовый режим (2026-02-19)

Цель:

- быстро проверить, даёт ли head‑детектор хоть какие‑то bbox в вашей геометрии (top‑down, ~20°), прежде чем тратить время на глубину/линии.

Факт стенда:

- модель включена в `passengers-camera-depth-counting.service` как `NNArchive`:
  - `CAM_DEPTH_COUNT_MODEL=/opt/passengers-mvp/models/HEAD_YOLOv8n_SCUT_Nano_416_YOLO_RAW_head.rvc2.tar.xz`
  - `CAM_DEPTH_COUNT_MODEL_INPUT_SIZE=416x416`
- включён host‑декодер (инференс на OAK, декод на OPi):
  - `CAM_DEPTH_COUNT_BACKEND=host-yolov8-raw`
- на первом этапе depth выключаем (чтобы не ловить OOM/X_LINK_ERROR до подтверждения детекций):
  - `CAM_DEPTH_ENABLE=0`

Быстро применить commissioning‑preset (с ПК):

- `./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --preset head-yolov8-host --health`

Стартовые фильтры bbox под head (в пикселях пространства `416x416`):

- size:
  - `CAM_DEPTH_COUNT_BBOX_MIN_W_PX=28`
  - `CAM_DEPTH_COUNT_BBOX_MIN_H_PX=28`
  - `CAM_DEPTH_COUNT_BBOX_MIN_AREA_PX2=900`
  - `CAM_DEPTH_COUNT_BBOX_MAX_W_PX=150`
  - `CAM_DEPTH_COUNT_BBOX_MAX_H_PX=170`
  - `CAM_DEPTH_COUNT_BBOX_MAX_AREA_PX2=22000`
- aspect ratio:
  - `CAM_DEPTH_COUNT_BBOX_MIN_AR=0.70`
  - `CAM_DEPTH_COUNT_BBOX_MAX_AR=1.40`
- commissioning порог:
  - `CAM_DEPTH_COUNT_CONFIDENCE=0.20`
  - (при необходимости для head‑моделей можно временно опускать, но тогда обязательно включать bbox‑фильтры и depth‑гейт).

Доп. порог для DNN (новое):

- `CAM_DEPTH_COUNT_DNN_CONFIDENCE=0.01` (тестовый/commissioning уровень — чтобы увидеть bbox вообще),
- затем поднимать вверх после подтверждения, что детекции адекватные.

Как открыть видео на ПК (безопасно, камера не открыта в LAN):

1. Включить SSH‑туннель (если не используете меню):

   - `ssh -N -L 8091:127.0.0.1:8091 orangepi@192.168.10.11`

2. Открыть:

   - `http://127.0.0.1:8091/`
   - `http://127.0.0.1:8091/health`

Что ожидаем увидеть:

- в `/health`: `status=running`, `messages` растёт;
- в `/health`: `tracklets_total > 0`, `active_tracks > 0` при проходе человека;
- в видео: bbox вокруг головы (класс `head`);
- если bbox нет даже при проходе под камерой → эта head‑модель, вероятно, не подходит под top‑down, и нужно:
  - менять head‑модель, или
  - дообучать под вашу геометрию.

#### Примечание по размеру входа модели `yolov6-nano`

Мы наблюдаем, что модель zoo загружается как:

- `/home/orangepi/.depthai_cached_models/.../YOLOv6_Nano-R2_COCO_512x288.rvc2.tar.xz`

Т.е. фактический input модели отличается от “416×416” из чата. Это критично только для bbox-фильтров “в пикселях”; для ROI/линий это не важно.

- счёт перестал проходить (`d_events=0`, фиксировался рост `d_age_reject`);
- вывод: для текущего стенда `MIN_TRACK_AGE=2` слишком жёстко (потеря проходов).

Откат на рабочий профиль и валидация (2026-02-16):

- выполнен откат на `MIN_TRACK_AGE=1` при сохранении `CONFIDENCE=0.30`, `COUNT_COOLDOWN_SEC=1.20`;
- контрольный live-probe `/tmp/door2_depth_conf030_cd120_age1_20260216_161603.jsonl`:
  - `d_events=19`, `d_in=9`, `d_out=10`;
  - `d_zone_mid=257` (реальные пересечения есть), `d_dup_reject=1`, `d_flip_no_middle=3`;
- сервис `passengers-camera-depth-counting.service` после отката: `active`;
- итог: счётчик снова считает, профиль принят как текущий рабочий для стенда.

Анти-дубль по `track_id` (новый guard, 2026-02-16):

- добавлен параметр `CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC` (0 = выключено, >0 = минимальная пауза перед повторным событием того же `track_id`);
- в `/health` добавлены поля:
  - `per_track_rearm_sec`;
  - `rearm_reject` (сколько событий отвергнуто rearm-guard);
- для стенда door-2 установлен `CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC=2.40`;
- цель: снизить overcount при колебании одного и того же трека в зоне линий.

Факт контрольного прогона после включения rearm-guard (2026-02-16):

- live-probe 45s: `/tmp/door2_rearm240_20260216_163022.jsonl`;
- дельта: `d_events=3`, `d_in=1`, `d_out=2`;
- guard активен, сервис стабилен (`per_track_rearm_sec=2.4`), на этом прогоне `d_rearm_reject=0` (колебаний трека в окне guard не было).

Центровка линий для следующего этапа (2026-02-16):

- линии перенесены в центр проёма:
  - `CAM_DEPTH_COUNT_AXIS=y`
  - `CAM_DEPTH_COUNT_AXIS_POS=0.50`
- фактически в `/health`: `line_a=0.45`, `line_b=0.55` (при `line_gap_norm=0.10`);
- сервис после изменения: `active`, видео-стрим доступен через `http://127.0.0.1:8091/`.

Смена ориентации на **вертикальные** линии (2026-02-16):

- установлено:
  - `CAM_DEPTH_COUNT_AXIS=x`
  - `CAM_DEPTH_COUNT_AXIS_POS=0.50`
- фактически в `/health`: `axis=x`, `line_a=0.45`, `line_b=0.55`;
- результат: в кадре используется **вертикальная** пара линий (вместо горизонтальной), сервис `active`.

⚠️ Важное (исправление путаницы по оси, 2026-02-20):

- `CAM_DEPTH_COUNT_AXIS=y` → **горизонтальные** линии (пересечение сверху↕вниз по кадру).
- `CAM_DEPTH_COUNT_AXIS=x` → **вертикальные** линии (пересечение слева↔направо по кадру).

## Официальная документация Luxonis — выводы для 15 FPS

Что подтверждено по официальным источникам:

- OAK-D Lite построена на платформе `RVC2`; инференс и трекинг выполняются на камере, а OPi обрабатывает бизнес-логику/агрегацию.
- `DetectionNetwork` и `ObjectTracker` относятся к on-device контуру DepthAI; это позволяет повышать FPS без прямого переноса инференса на CPU OPi.
- пример Luxonis `depth-people-counting` использует `tracklets` + глубину, но **детекция в нём не NN**: он делает сегментацию по disparity на host (HostNode),
  и в текущей реализации выбирает **один max‑контур** (т.е. из коробки “1 человек/1 blob”).
  Поэтому его можно использовать как *идею* “counting по depth”, но не как готовый алгоритм для сценария “2–3 человека рядом”.
- `Standalone mode` в актуальной документации ориентирован на `RVC4`; для `OAK-D Lite (RVC2)` это не является обязательным путём.

Практический вывод для нашего стенда:

- `10 -> 15 FPS` возможно, но на текущем стенде с `usb_speed=HIGH (USB2)` это может усилить `X_LINK_ERROR`;
- до стабилизации USB/питания считаем `FPS=10` “боевым” для commissioning/debug;
- при переходе на `FPS=15` обязательно сохранить временное окно “жизни” трека в секундах (поднять `MAX_LOST_FRAMES`).

## Версии рабочего профиля (door-2 / 192.168.10.11)

`v1 (рабочая базовая, зафиксирована перед переходом на 15 FPS)`:

- `CAM_DEPTH_COUNT_FPS=10`
- `CAM_DEPTH_COUNT_AXIS=y`, `CAM_DEPTH_COUNT_AXIS_POS=0.50`, `line_a=0.39`, `line_b=0.61`
- `CAM_DEPTH_COUNT_CONFIDENCE=0.30`
- `CAM_DEPTH_COUNT_MIN_TRACK_AGE=1`
- `CAM_DEPTH_COUNT_MAX_LOST_FRAMES=5`
- `CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC=1.20`
- `CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC=2.40`

`v2 (эксперимент, 15 FPS + донастройка)`:

- `CAM_DEPTH_COUNT_FPS=15`
- `CAM_DEPTH_COUNT_MAX_LOST_FRAMES=8` (донастройка под новый FPS)
- остальные параметры сохранены как в `v1`.

Факт запуска `v2` (2026-02-16 / 2026-02-18):

- `/health` показывает `fps=15`, `status=running`;
- на USB2 (`usb_speed=HIGH`) наблюдались частые `X_LINK_ERROR` → для стенда зафиксирован откат к `FPS=10` как более стабильный режим.

## Аудит offload (что на камере, что на OPi) — 2026-02-16

Текущее состояние (факт по коду и runtime):

- на OAK-D Lite (RVC2) выполняются:
  - `DetectionNetwork` (детекция person);
  - `ObjectTracker` (track_id);
  - `StereoDepth` (глубина);
  - IMU node (сырые IMU пакеты);
- на OPi выполняются:
  - логика crossing (линии/направление in/out);
  - depth-фильтры по ROI и anti-duplicate (`cooldown`, `per_track_rearm`);
  - HTTP `/health` + визуализация и `MJPEG` (в режиме depth-counting);
  - запись/передача событий.

Важно по ограничениям платформы:

- для `OAK USB` на `RVC2` standalone mode не поддерживается (камера в peripheral-режиме требует host);
- значит полностью убрать OPi из контура на текущем железе нельзя.

Вывод:

- на камеру уже вынесен основной тяжёлый AI-контур (детекция/трекер/depth);
- OPi сейчас дополнительно нагружается в основном из-за host-логики и постоянного `MJPEG` рендера.

Следующие шаги для снижения нагрузки OPi (если потребуется):

1. Использовать боевой `camera-counter` сервис (без веб-видео) в прод-режиме.
2. Оставить `depth-counting`+видео только для калибровки/диагностики.
3. При необходимости вынести кодирование видео в `VideoEncoder` на устройстве и/или отключать overlay/JPEG при отсутствии клиентов.

## Downscale depth output (host-side stability tweak) — 2026-02-18

Добавлен параметр, чтобы снизить нагрузку на USB/host при включённой глубине:

- `CAM_DEPTH_OUTPUT_SIZE` (по умолчанию `320x200`)

Это не влияет на детекцию/трекер, но уменьшает размер depth‑фрейма, который приходит на host для depth‑gate (head/shoulders).
Цель: меньше риск `X_LINK_ERROR` на USB2 (`usb_speed=HIGH`) и меньше нагрузка на OPi при debug‑режимах.

## Multi-person / crowd tuning (2 рядом) — 2026-02-18

Проблема: когда 2 человека идут рядом/впритык, один трек может “склеиваться” или теряться на пересечениях.

Быстрый тюнинг без смены модели:

- переключить трекер на KCF (лучше держит ID при близких объектах):
  - `CAM_DEPTH_COUNT_TRACKER_TYPE=short_term_kcf`
- ослабить порог окклюзии трекера:
  - `CAM_DEPTH_COUNT_TRACKER_OCCLUSION_RATIO=0.60`
- поднять лимит объектов:
  - `CAM_DEPTH_COUNT_TRACKER_MAX_OBJECTS=15`

Важно: если на видео всё равно рисуется один bbox на двух людей — это ограничение детектора (нужна смена модели/входного разрешения или
кастомное обучение под top-down двери).

## План: детекция голов (head detector) для 2–3 рядом — подход под транспорт

Зачем:

- в двери транспорта люди часто идут “плечом к плечу”; person‑bbox может **слипаться** или перекрывать 2 людей одной рамкой;
- головы сверху обычно разделяются лучше → меньше “склеек” и стабильнее `track_id`.

Где будет выполняться “тяжёлое”:

- **на OAK‑D Lite (RVC2)**: нейросеть детекции + `ObjectTracker` + `StereoDepth` (как и сейчас);
- **на OPi**: только счёт “пересечение 2 линий” + анти‑дубли + буферизация/передача + (опционально) debug‑UI видео.

Можно ли “настроить текущую модель” (`yolov6-nano person`) под головы:

- нет, это другая задача/класс. Можно лишь брать head‑ROI внутри person‑bbox (эвристика), но это не решает “2 рядом”.
- для реального улучшения нужен **отдельный head / head+shoulders detector** (готовая модель или кастом под top‑down двери).

Как это будет работать (целевой контур):

1) `DetectionNetwork` выдаёт bbox **голов** (а не “person”).
2) `ObjectTracker` даёт стабильный `track_id` на каждую голову.
3) `StereoDepth` даёт depth‑кадр; depth‑gate берём по ROI головы (либо на устройстве через spatial‑детекции, либо как сейчас на host через sampling).
4) Событие IN/OUT = один `track_id`, который пересёк обе линии (2‑линейный crossing + cooldown/rearm/hang‑guard).

Что нужно, чтобы внедрить:

- выбрать модель головы (совместимую с OAK / DepthAI) и определить:
  - входное разрешение (важно при высоте 2.3м: голова маленькая → часто нужен ≥640 по ширине);
  - единственный класс `head` (желательно label=0), чтобы трекер отслеживал правильную метку.
- добавить/зафиксировать commissioning‑профиль `head-counting` (геометрия линий + пороги + depth‑gate).
- зафиксировать отдельный depth‑gate “head-only” (дистанция **от камеры**, не от пола):
  - стартовая гипотеза под “2 рядом” и минимизацию ложных: `0.35–0.95 м`;
  - финальные границы подтверждаем на эталонном монтаже по overlay `z=...m` и логам `depth_pass/depth_reject`.
- сделать A/B тест на стенде:
  - “2 рядом” и “паровозиком” → сравнить bbox‑разделение и стабильность `track_id`.

Критерий успеха:

- при сценарии “2 рядом” в кадре стабильно **2 bbox головы** (а не 1);
- `events_total` растёт и не даёт двойных срабатываний от “стояния в дверях”.

Выбор нейросети (план, v0):

- целевой baseline: **YOLOv8n (или YOLOv8s, если FPS позволит) с 1 классом `head`**, обученная/дообученная под top‑down двери транспорта;
- обязательное требование к датасету: присутствуют **капюшоны/шапки/кепки**, частичные перекрытия (2–3 рядом), разные источники света (день/ночь/подсветка);
- инференс выполняется **на OAK‑D Lite** (детекция+трекер+depth), OPi остаётся “лёгким” хостом (счёт/буфер/диагностика).

Почему не “face detector”:

- в транспорте сверху/под углом лицо часто не видно (капюшон/маска/взгляд вниз) → модель лица даёт пропуски;
- нам нужен “head silhouette”, не лицо.

План внедрения head‑детектора:

1) Быстрый POC: поднять head‑детектор на OAK‑D Lite и проверить, что “2 рядом” даёт 2 bbox стабильно.
2) Если bbox “слипаются” → повысить входное разрешение (≥640), проверить предобработку (letterbox) и пороги.
3) Если bbox всё равно 1 (часто) → собрать 1–2 часа видео/снапшотов с эталонной двери и дообучить модель под top‑down.
4) Зафиксировать `head-counting` пресет (линии + трекер + depth‑gate head-only) как боевой стандарт под транспорт.

Факт переключения на прод-режим без MJPEG (2026-02-16):

- выполнено на `door-2` (`192.168.10.11`): `./scripts/camera_mode_switch.sh --mode prod --camera-ip 192.168.10.11 --user orangepi`;
- активный сервис: `passengers-camera-counter.service` (`NRestarts=0`);
- метрика процесса после стабилизации: ~`14.5% CPU`, ~`29.9% MEM` (значительно ниже, чем в `depth-counting` с веб-видео);
- единичный `X_LINK` reconnect после старта был восстановлен автоматически; далее стабильные heartbeat.

Важно:

- в `prod` используется `camera_counter.py` и параметры `CAM_COUNTER_*` (они независимы от `CAM_DEPTH_COUNT_*`);
- поэтому геометрия/пороги, настроенные в `depth-counting`, автоматически не переносятся в `camera-counter` без отдельной синхронизации env-переменных.

Факт синхронизации `CAM_COUNTER_*` с текущим профилем двери (2026-02-16):

- применено на `192.168.10.11`:
  - `CAM_COUNTER_AXIS=x`
  - `CAM_COUNTER_AXIS_POS=0.50`
  - `CAM_COUNTER_FPS=15`
  - `CAM_COUNTER_CONFIDENCE=0.30`
  - `CAM_COUNTER_MIN_TRACK_AGE=1`
  - `CAM_COUNTER_HYSTERESIS=0.00`
  - `CAM_COUNTER_INVERT=0`
- `passengers-camera-counter.service` после рестарта: `active`.

Факт возврата на strict-алгоритм (2026-02-16):

- на `192.168.10.11` выполнен переход в режим:
  - `passengers-camera-depth-counting.service` = `active`
  - `passengers-camera-counter.service` = `inactive`
- активный контур снова: `2 линии + middle-cross + anti-duplicate (cooldown + per-track rearm)`.

Факт смены ориентации линий (2026-02-17):

- на `192.168.10.11` линии развернуты в горизонтальные:
  - `CAM_DEPTH_COUNT_AXIS=x`
  - `/health`: `axis=x`, `line_a=0.375`, `line_b=0.625`
  - сервис: `passengers-camera-depth-counting.service` = `active`.

Факт “commissioning-relaxed” тюнинга (2026-02-17, чтобы пошёл счёт):

- причина: при `confidence_min=0.65` crossing часто не фиксировался (детекции проходили с `conf~0.4–0.6`), из‑за чего рос `zone_flip_no_middle`, а `events_total` оставался `0`;
- применено на `192.168.10.11` (оставляя горизонтальные линии `axis=x`):
  - `confidence_min=0.45`, `min_track_age=3`
  - `line_gap_norm=0.10` (линии `0.45..0.55`)
  - `anchor_mode=center`, `axis_hyst=0.00`
  - `min_move_norm=0.04`, `hang_timeout=8s`
  - `cooldown=0.8s`, `max_lost_frames=8`
- цель: восстановить стабильный подсчёт, затем по одному параметру ужесточать до `transport-strict`.

Факт “fast-pass” тюнинга (2026-02-18, цель: быстрее считать быстрые проходы):

- ограничение стенда: OAK-D Lite на OPi Zero 3 работает по USB `HIGH` (USB2). При попытке поднять `FPS=15` в `depth-counting` появлялись `X_LINK_ERROR`, после чего `/health` мог зависать на `messages=0`.
- поэтому маршрут тюнинга “быстрее без роста FPS”:
  - держим `FPS=10` (стабильность);
  - снижаем `min_track_age` (быстрее засчитываем проход);
  - расширяем “mid” зону (чтобы crossing успевал пройти `A -> mid -> B` даже при быстром движении).
- применён “fast-pass v1” (door-2 `192.168.10.11`):
  - `FPS=10`, `axis=x` (горизонтальные линии)
  - `line_gap_norm=0.14` (линии `0.43..0.57`), `axis_hyst=0.01`
  - `confidence_min=0.35`, `min_track_age=2`
  - `cooldown=0.8s`, `per_track_rearm=2.4s`, `track_gap_sec=0.20`, `max_lost_frames=10`
- evidence (пробы 60s):
  - индекс: `Docs/auto/camera-probes/INDEX.md`
  - `door-2-probe-fast-20260218-0902Z.jsonl`: `d_events=1 d_in=1` и `zone_flip_no_middle=0` (mid зона стабильнее).

Команда “только IN/OUT” в консоли:

```bash
./scripts/camera_counter_io_watch.sh --camera-ip 192.168.10.11 --user orangepi
```

- скрипт выводит только события с накопительными суммами:
  - `IN_TOTAL=<n> OUT_TOTAL=<n> (+in/+out)`.
- при старте показывает базу сумм:
  - `Initial totals since '<window>': IN=<n> OUT=<n>`;
- по умолчанию окно инициализации: `today`; можно задать явно:

```bash
./scripts/camera_counter_io_watch.sh --camera-ip 192.168.10.11 --user orangepi --bootstrap-since "2 hours ago"
```

Команда “только IN/OUT” для strict depth-counting:

```bash
./scripts/depth_counter_io_watch.sh --camera-ip 192.168.10.11 --user orangepi
```

- источник baseline: `passengers-camera-depth-counting.service` (`transport-strict event`) по окну `--bootstrap-since`;
- источник realtime: `http://127.0.0.1:8091/health` (`count_in/count_out/events_total`);
- формат: `IN_TOTAL=<n> OUT_TOTAL=<n> (+in/+out)`;
- realtime-обновление идёт через polling `http://127.0.0.1:8091/health` (по умолчанию каждые `1.0s`, опция `--poll-sec`);
- стартовые totals берутся из event-логов (`--bootstrap-since`), затем наращиваются в live-режиме;
- окно инициализации (по умолчанию `today`) можно изменить:

```bash
./scripts/depth_counter_io_watch.sh --camera-ip 192.168.10.11 --user orangepi --bootstrap-since "2 hours ago"
```

## Политика профилей калибровки (обязательная)

Правило проекта (фиксируем постоянно):

- вести отдельные калибровки по профилям и не смешивать их:
  - `profile_debug_depth` — отладка/визуализация (`CAM_DEPTH_COUNT_*`);
  - `profile_prod_counter` — боевой счётчик (`CAM_COUNTER_*`);
  - дополнительные профили (например, под другую геометрию двери) оформлять как отдельные версии.
- после каждого изменения фиксировать:
  - что изменено;
  - зачем;
  - результат и метрики;
  - rollback-точку.
- перед вводом в прод обязательно выполнять синхронизацию `CAM_COUNTER_*` под актуальную калибровку двери.

## IMU диагностика в depth-counting (гироскоп + акселерометр)

Реализация добавлена в `mvp/camera_transport_strict_counting.py`:

- IMU читается в том же процессе/пайплайне, что и depth-counting;
- в `/health` теперь доступны поля:
  - `imu_enabled`, `imu_type`, `imu_present`, `imu_updates`;
  - `imu_accel_x/y/z`, `imu_accel_norm`;
  - `imu_gyro_x/y/z`, `imu_gyro_norm`.

Важно для OAK-D Lite:

- IMU тип: `BMI270` (акселерометр + гироскоп, 6-axis);
- магнитометр для OAK-D Lite не используется (9-axis нет).

Параметры (`/etc/passengers/passengers.env`):

- `CAM_IMU_ENABLE=1|0`
- `CAM_IMU_RATE_HZ=100` (стартовое значение)

Быстрая проверка:

```bash
./scripts/camera_mode_switch.sh --mode depth-counting --camera-ip 192.168.10.11 --user orangepi
ssh orangepi@192.168.10.11 'curl -sS http://127.0.0.1:8091/health | jq .'
```

Критерий корректной работы IMU:

- `imu_present=true`
- `imu_updates` растёт
- `imu_accel_norm` и `imu_gyro_norm` обновляются

## После перезагрузки: зависание на preflight time_sync

Симптом:

- `passengers-camera-depth-counting.service` или `passengers-camera-debug-stream.service` зависает на `preflight waiting ... time_sync=unknown`.

Причина:

- после ребута `timedatectl` ещё не показывает синхронизацию времени.

Решение (внедрено):

- для `depth-counting` и `debug-stream` preflight теперь запускается с `--skip-time-sync`, чтобы сервис стартовал сразу.
- если сервис уже завис: выполнить `sudo systemctl restart passengers-camera-depth-counting.service`.

Примечание:

- для боевого `camera-counter` time sync остаётся обязательным.

## Статус на остановке (crowd + центр линий) — 2026-02-18

Где:

- камера: OAK-D Lite
- узел камеры (edge/door): `192.168.10.11` (в systemd/логах hostname может быть `door-1` — не путать с физической дверью)
- активный сервис: `passengers-camera-depth-counting.service`
- UI (через SSH tunnel): `http://127.0.0.1:8091/`
- монтаж (стенд): высота ~`2.30m` от пола, наклон ~`20°`, линии ориентируем по центру дверного проёма

Что зафиксировано как рабочее на стенде:

- линии по центру: `CAM_DEPTH_COUNT_AXIS=y`, `CAM_DEPTH_COUNT_AXIS_POS=0.50` → `/health`: `line_a=0.39`, `line_b=0.61`
- `CAM_DEPTH_COUNT_FPS=10` (попытка `15 FPS` на `usb_speed=HIGH (USB2)` даёт частые `X_LINK_ERROR`)
- downscale глубины для host depth-gate: `CAM_DEPTH_OUTPUT_SIZE=320x200`
- crowd-tuning трекера (для 2 рядом/впритык):
  - `CAM_DEPTH_COUNT_TRACKER_TYPE=short_term_kcf`
  - `CAM_DEPTH_COUNT_TRACKER_OCCLUSION_RATIO=0.60`
  - `CAM_DEPTH_COUNT_TRACKER_MAX_OBJECTS=15`
- эксперимент для top-down depth-gate (ожидаемо снижает `depth_reject` под камерой):
  - `CAM_DEPTH_HEAD_REGION=bottom`
  - `CAM_DEPTH_COUNT_LINE_GAP_NORM=0.22` (шире mid‑зона, меньше `zone_flip_no_middle`)

Что не закрыто (следующий шаг):

- на стенде “офис” (слабый свет/шум) счёт шёл редко: при 20 проходах фиксировался `d_events=1` за 180s,
  при этом росли `roi_reject`, `bbox_reject_*`, `conf_reject` (много детектов/треков сбрасывалось до пересечения).
- следующий шаг (выполнено, 2026-02-20): применить commissioning‑профиль с максимальной “recall”:
  - отключить ROI (чтобы треки не сбрасывались при выходе bbox за ROI в тестовой сцене);
  - ослабить bbox size/AR фильтры и `CONFIDENCE/DNN_CONFIDENCE`;
  - увеличить `MATCH_DIST_PX` для стабильнее ID при быстрых проходах.

Команда (door-2 / `192.168.10.11`):

- `./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --preset head-yolov8-host-loose --health`

Дальше (зачем): повторить 10+10 проходов, собрать `camera_depth_live_probe` 180s и по дельтам
`events_total / zone_* / *_reject` вернуть ROI и пороги к “strict” для транспорта.

### Факт прогонов “офис” (2026-02-20)

Все прогоны сохранены в `Docs/auto/camera-tuning/192.168.10.11/` (каждый — отдельная папка с `passengers.env`, `health.jsonl`, `journal.txt`, `summary.md`).

- `office_10x10_loose_r1`: `d_events=0`, доминируют `bbox_reject_size/bbox_reject_ar` → bbox‑фильтры всё ещё режут много.
- `office_10x10_strict_r1`: `d_events=0`, `bbox_reject_ar` резко растёт → AR‑порог `<=1.40` для этой head‑модели в офисной сцене слишком жёсткий.
- `office_10x10_nofilter_r1` (debug): `d_events=6 (in=4/out=2)` при отключённых bbox‑фильтрах и `ANCHOR_MODE=leading_edge` → геометрия/логика пересечения **работает**, дальше затягиваем “гайки” по одному параметру.
- `office_10x10_depthwz_comm_r1`: `d_events=0`, `depth_missing/bbox_reject_wz` растут → в офисной сцене depth‑ROI даёт мало валидных пикселей; перед включением `w*Z` нужно стабилизировать глубину (`HEAD_FRACTION/MIN_VALID_PX/DEPTH_OUTPUT_SIZE`).
- `office_live_matchdist220_iou0.1_r5`: `d_events=11 (in=6/out=5)` за 180s при `ROI=` (отключен), `ANCHOR_MODE=center`, `INFER_MIDDLE_FROM_SPAN=0` → счёт **вернулся**, но доминируют `bbox_reject_size` и `conf_reject` (порог/модель/свет).
- `office_2p_stand_bbox28_move0.18_r6`: `d_events=1` за 180s при `BBOX_MIN=28/28 area=900` и `min_move_norm=0.18` → для офисной сцены такой bbox‑минимум слишком жёсткий (сильно режет реальные головы). В транспорте может быть ок, но для стенда пока возвращаемся к `BBOX_MIN=20/20 area=400` + ROI.

### Два человека рядом / встречное движение (важно)

Если “2 рядом” или встречный проход часто превращается в 1 событие, причины обычно две:

1) **Детектор даёт один bbox** на двоих (в браузере видно 1 рамку) → это ограничение модели/света/ракурса.
   Решение: улучшать head‑модель (дообучение под top‑down двери, свет, вход 416), а не трекер.
2) **bbox два, но ID “меняются местами”** при пересечении → это проблема data association (трек‑матчинг).
   Решение: улучшать matching (IoU‑first) + затем уже “затягивать” `rearm/cooldown/min_move`.

В проекте внедрено (2026-02-20):

- для backend `host-yolov8-raw` добавлен IoU‑first matching (уменьшает swap ID при пересечениях).
- новый параметр: `CAM_DEPTH_COUNT_MATCH_IOU_MIN` (по умолчанию `0.10`).
- новый параметр (анти‑ложные при “топтании”): `CAM_DEPTH_COUNT_INFER_MIDDLE_FROM_SPAN`:
  - `1` (по умолчанию): разрешает “middle seen” по span bbox через обе линии (полезно при `ANCHOR_MODE=leading_edge`, но может давать ложные при стоянии).
  - `0`: запрещает span‑инференс (строже, меньше ложных при стоянии между линиями).
- новые параметры (2026-02-20, host backend):
  - `CAM_DEPTH_COUNT_MIN_SIDE_FRAMES_BEFORE_MIDDLE` (по умолчанию `2`): сколько кадров трек должен стабильно быть на одной стороне, прежде чем “армить” middle (убирает ложные при дрожании bbox в mid‑зоне).
  - `CAM_DEPTH_COUNT_MAX_JUMP_PX` (по умолчанию `0` = выключено): дополнительный лимит на “прыжок” ассоциации det→track в пикселях (страхует от ID‑leap при шумных детектах).

- если при проходе “2 рядом” детектор даёт 1 bbox на двоих — это ограничение модели (требуется смена модели/разрешения входа или кастомная модель
  под top-down дверь); трекер это не вылечит.

Как воспроизводить тест:

1. На ПК: `ssh -N -L 8091:127.0.0.1:8091 orangepi@192.168.10.11`
2. Открыть `http://127.0.0.1:8091/`
3. Прогнать сценарии:
   - 2 человека рядом через линии
   - 2 человека “паровозиком” с маленьким интервалом
4. Зафиксировать: в кадре 2 bbox или 1 bbox (это определяет дальнейшую стратегию).

### Примечание по логам прогонов

`scripts/camera_tuning_run.sh` (2026-02-20) фиксирует `journal.txt` по remote epoch (`journalctl --since @<epoch> --until @<epoch>`),
чтобы журнал корректно сохранялся даже при неидеальной синхронизации времени на узле.

---

## Схема настройки подсчёта (Transport strict, head + tracking + 2 lines)

Ниже — “полная карта” того, что настраивается и за что отвечает (для OAK‑D Lite + OPi).

### 1) Режимы (что запускаем)

- `passengers-camera-depth-counting.service` — основной стендовый/боевой режим **строгого подсчёта** (ID + 2 линии + антидубли).
- `passengers-camera-debug-stream.service` — только MJPEG‑картинка (без подсчёта), для проверки камеры/USB/света.
- `oak-viewer` — ручная диагностика (камера “освобождена”, сервисы остановлены).

Запуск/переключение:

- интерактивно: `./scripts/camera_mode_menu.sh --camera-ip <IP>`
- напрямую: `./scripts/camera_mode_switch.sh --mode depth-counting --camera-ip <IP> --user orangepi`

UI в браузере (через SSH tunnel на ПК):

1. `ssh -N -L 8091:127.0.0.1:8091 orangepi@<IP>`
2. открыть `http://127.0.0.1:8091/`
3. облегчённый режим без видео: `http://127.0.0.1:8091/?view=stats`

### 2) Пайплайн (что “тяжёлое” делаем где)

`Transport strict counting` состоит из:

- (A) **Детекция head** (YOLO) — выполняется **на OAK‑D** (Myriad X / RVC2).
- (B) **Декодирование YOLOv8 DFL + NMS + трекинг + логика пересечения** — выполняется **на OPi** (host backend `host-yolov8-raw`).
- (C) (опционально) **Depth gate** — отдельно включается (`CAM_DEPTH_ENABLE=1`) и отсекает нецелевые дистанции.
- (D) (опционально) **Preview/MJPEG** — только для тестов, в проде желательно отключать.

### 3) Геометрия 2 линий (самое важное для in/out)

Параметры:

- `CAM_DEPTH_COUNT_AXIS` — какая ось используется для пересечения.
  - ⚠️ В проекте есть “инверсия маппинга”: `axis=x` на практике означает пересечение по **вертикали кадра** (top↔bottom), а `axis=y` — по **горизонтали** (left↔right). Проверяйте по `zone_*` в `/health`.
- `CAM_DEPTH_COUNT_AXIS_POS` — позиция центра (0..1).
- `CAM_DEPTH_COUNT_LINE_GAP_NORM` — расстояние между линиями (ширина mid‑зоны).
- `CAM_DEPTH_COUNT_AXIS_HYST` — гистерезис границ mid‑зоны (снижает дрожание).
- `CAM_DEPTH_COUNT_ANCHOR_MODE`:
  - `center` — устойчивее против дрожания bbox (рекомендуется).
  - `leading_edge` — быстрее “срабатывает”, но чаще даёт ложные при шуме/стоянии.
- `CAM_DEPTH_COUNT_INVERT` — поменять местами IN/OUT (если направление перепутано).

### 4) Детектор (какие пороги и почему)

- `CAM_DEPTH_COUNT_CONFIDENCE` — порог уверенности для учёта детекта в подсчёте.
- `CAM_DEPTH_COUNT_DNN_CONFIDENCE` — порог уверенности на уровне DNN (для host backend влияет на decode‑вход).
- `CAM_DEPTH_COUNT_NMS_IOU` — IoU порог NMS:
  - выше → чаще “слипает” 2 головы в 1 bbox;
  - ниже → больше дублей/ложных.
- `CAM_DEPTH_COUNT_MAX_DET` — ограничение количества детектов на кадр (защита от перегруза и “шума”).

### 5) BBox‑фильтры (отсечь “мусор”)

Все пороги в пикселях **NN‑входа** (`CAM_DEPTH_COUNT_MODEL_INPUT_SIZE`, обычно `416x416`):

- `CAM_DEPTH_COUNT_BBOX_MIN_W_PX`, `..._MIN_H_PX`, `..._MIN_AREA_PX2` — отсечь слишком мелкие боксы.
- `CAM_DEPTH_COUNT_BBOX_MAX_W_PX`, `..._MAX_H_PX`, `..._MAX_AREA_PX2` — отсечь слишком крупные/кривые.
- `CAM_DEPTH_COUNT_BBOX_MIN_AR`, `..._MAX_AR` — фильтр по aspect ratio.
- `CAM_DEPTH_COUNT_BBOX_MIN_WZ`, `..._MAX_WZ` — фильтр “ширина*bbox_depth” (эффективно, но требует стабильной depth‑оценки).

Практика по стенду:

- слишком жёсткий `BBOX_MIN` легко убивает recall (как в `office_2p_stand_bbox28_move0.18_r6`), поэтому затягиваем постепенно.

### 6) Трекинг и ассоциация (чтобы 2 рядом не превращались в 1)

- `CAM_DEPTH_COUNT_MATCH_IOU_MIN` — минимум IoU для IoU‑first matching (host backend).
- `CAM_DEPTH_COUNT_MATCH_DIST_PX` — максимум расстояния (px) для связывания det→track.
- `CAM_DEPTH_COUNT_MAX_JUMP_PX` — дополнительный cap “прыжка” (если включён), снижает ложные события от резких “телепортов” ID.

### 7) Guard’ы подсчёта (борьба с ложными при стоянии/топтании)

- `CAM_DEPTH_COUNT_MIN_TRACK_AGE` — минимальный возраст трека до события (уменьшает “первокадровые” ложные).
- `CAM_DEPTH_COUNT_MAX_LOST_FRAMES` — сколько кадров трек может “пропасть” и всё ещё считаться тем же.
- `CAM_DEPTH_COUNT_MIN_MOVE_NORM` — минимальный сдвиг по оси (0..1) для зачёта пересечения (анти‑дрожание).
- `CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC` — глобальный анти‑дубль (частые события подряд).
- `CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC` — анти‑дубль на один track_id (особенно важно при разворотах и “туда‑сюда”).
- `CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC` — если застрял в mid‑зоне слишком долго → не считаем.
- `CAM_DEPTH_COUNT_INFER_MIDDLE_FROM_SPAN` — см. выше (лучше `0` для транспорта, если много стояния).
- `CAM_DEPTH_COUNT_MIN_SIDE_FRAMES_BEFORE_MIDDLE` — требует “стабильного старта” на одной стороне перед arming middle.

### 8) ROI (уменьшить ложные объекты и нагрузку)

- `CAM_DEPTH_COUNT_ROI` — `x1,y1,x2,y2` в нормализованных координатах (0..1).
- `CAM_DEPTH_COUNT_ROI_MODE`:
  - `soft` — игнорируем вне ROI, не сбрасываем состояние (лучше для тестов).
  - `hard` — вне ROI сбрасываем состояние (строже, но может недосчитывать при краевых траекториях).

### 9) Depth gate (опционально, но желателен для транспорта)

- `CAM_DEPTH_ENABLE=1` — включить.
- `CAM_DEPTH_MIN_M`, `CAM_DEPTH_MAX_M` — допустимый диапазон глубины (метры по лучу от камеры).
- `CAM_DEPTH_HEAD_FRACTION`, `CAM_DEPTH_HEAD_REGION`, `CAM_DEPTH_MIN_VALID_PX` — как и где берём depth‑оценку внутри bbox.

Рекомендация:

- включать depth‑gate после того, как детектор+линии уже стабильно считают (иначе тяжело дебажить).

### 10) Preview/MJPEG (только для калибровки)

- `CAM_PREVIEW_ENABLED` — включить/выключить MJPEG.
- `CAM_PREVIEW_SIZE` — размер превью (уменьшать для стабильности USB2).
- `CAM_PREVIEW_FPS` — частота превью (в проде держать низкой или выключать).
- `CAM_JPEG_QUALITY` — качество JPEG (меньше → меньше CPU/трафик).

### 11) Как правильно калибровать (итерации + фиксация результатов)

1. Применить пресет/настройки:
   - `./scripts/camera_depth_calibrate.sh --camera-ip <IP> --preset <name> --health`
2. Открыть UI: `http://127.0.0.1:8091/`
3. Запустить прогон (создаёт отдельную папку с результатами):
   - `./scripts/camera_tuning_run.sh --camera-ip <IP> --label <label> --seconds 180 --notes \"...\"`
4. Смотреть `summary.md` (дельты `events_total`, `zone_*`, `*_reject`) и затягивать **по одному параметру за раз**.
