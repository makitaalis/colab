# OPi и ОС

## Типовые сбои

- Время не синхронизировано.
- Узел недоступен по LAN/SSH.
- `venv` не создаётся.
- `pip`: `externally-managed-environment` (PEP 668).
- `system.journal corrupted` после жёсткого выключения.
- `systemctl is-system-running=degraded` после reboot.
- `passengers-central-flush.timer` не активен при `STOP_MODE=manual`.
- `depthai`: `X_LINK_UNBOOTED` / `available devices: 0`.

## Быстрый фикс: `depthai` не видит OAK-D Lite

Симптом:

- в Python `dai.Device.getAllAvailableDevices()` возвращает `0`;
- warning `Insufficient permissions ... X_LINK_UNBOOTED`.

Действия:

```bash
ssh orangepi@192.168.10.11 '
  echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"03e7\", MODE=\"0666\"" | sudo tee /etc/udev/rules.d/80-movidius.rules >/dev/null &&
  sudo udevadm control --reload-rules &&
  sudo udevadm trigger
'
ssh orangepi@192.168.10.11 'python3 /tmp/oakd_v3_smoke.py --duration-sec 5 --min-frames 5'
```

Ожидаемо: `SMOKE_OK`, `device=OAK-D-LITE`.

## pip: externally-managed-environment (PEP 668)

Симптом:

- `python3 -m pip install ...` падает с `error: externally-managed-environment`.

Решение:

- ставим Python‑зависимости камеры в venv (рекомендовано) через скрипт:

```bash
./scripts/install_edge_camera_counter.sh --edge-ip 192.168.10.11 --user orangepi --door-id 2
```

## Базовые проверки

```bash
ssh orangepi@192.168.10.1 'timedatectl status; systemctl is-system-running; systemctl --failed --no-legend'
ssh orangepi@192.168.10.11 'ip -br addr; nmcli con show --active'
ssh orangepi@192.168.10.12 'ip -br addr; nmcli con show --active'
```

## Источник подробных решений

- `Docs/Проект/Проблемы (подробно).md`

## Отдельный кейс: service не стартует из-за кеша модели

Симптом в `journalctl`:

- `Failed to create cache directory: .depthai_cached_models`

Причина:

- у systemd-сервиса не задан рабочий каталог/домашняя директория, и `depthai` пытается создать кеш в недоступном пути.

Фикс в unit:

- `Environment=HOME=/home/orangepi`
- `Environment=XDG_CACHE_HOME=/home/orangepi/.cache`
- `WorkingDirectory=/home/orangepi`

После правки:

```bash
ssh orangepi@192.168.10.1 'sudo systemctl daemon-reload && sudo systemctl restart passengers-camera-counter.service'
```


## Camera service stuck in preflight (time_sync=unknown)

Symptoms:

- `passengers-camera-depth-counting.service` or `passengers-camera-debug-stream.service` stays in `activating (start-pre)`.
- Logs show `preflight waiting ... time_sync=unknown`.

Cause:

- NTP not yet synchronized right after reboot.

Fix:

- Restart service after NTP sync, or use the updated units which start with `--skip-time-sync` for debug/depth modes.

Command:

```bash
ssh orangepi@192.168.10.1 'sudo systemctl restart passengers-camera-depth-counting.service'
```

## Camera depth-counting: intermittent X_LINK_ERROR

Symptoms:

- In `journalctl -u passengers-camera-depth-counting.service` appears:
  - `Couldn't read data from stream ... (X_LINK_ERROR)`
  - `Closed connection / Attempting to reconnect`.
- `/health` may temporarily show `messages=0` right after restart.

Cause:

- High pipeline load for OAK-D Lite when USB link is `HIGH` (not `SUPER`), especially in strict mode with RGB + tracker + depth + IMU.
- Physical USB instability / power issue (most common in the field):
  - in `dmesg` видно повторяющиеся `USB disconnect` / `new high-speed USB device` и переинициализацию `03e7:(2485|f63b)`;
  - в `journalctl` идут циклы `Closed connection -> Attempting to reconnect` + `X_LINK_ERROR`;
  - `/health` может зависать на `messages=0` (пайплайн не получает пакеты).

Fix (safe baseline):

1. Start strict profile with `FPS=10`.
2. Use `CAM_DEPTH_COUNT_TRACKER_TYPE=short_term_imageless`.
3. Keep two-line strict logic (`transport-strict`) and raise FPS only after stable run.
4. Если в `dmesg` идут USB disconnect:
   - заменить USB-кабель на короткий/качественный (data-capable), без удлинителей;
   - обеспечить питание OPi стабильное (желательно 5V/3A) и, при необходимости, использовать powered USB hub для камеры.

Command:

```bash
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --preset transport-strict --health
```

## Camera depth-counting: tracklets grow, but `count_in/out=0`

Symptoms:

- `/health`: `messages` and `tracklets_total` grow, `active_tracks` > 0;
- but `events_total=0`, `count_in=0`, `count_out=0` for real crossings.

Typical cause:

- axis/line geometry does not match real movement direction in frame (crossing never completes `A↔B`).

Fast fix for commissioning (relaxed profile):

```bash
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi \
  --set CAM_DEPTH_COUNT_AXIS=y \
  --set CAM_DEPTH_COUNT_LINE_GAP_NORM=0.10 \
  --set CAM_DEPTH_COUNT_CONFIDENCE=0.45 \
  --set CAM_DEPTH_COUNT_MIN_TRACK_AGE=3 \
  --set CAM_DEPTH_COUNT_MIN_MOVE_NORM=0.04 \
  --set CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC=8.0 \
  --set CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC=0.80 \
  --set CAM_DEPTH_MIN_M=0.30 \
  --set CAM_DEPTH_MAX_M=2.20 \
  --health
```

Note:

- if movement in frame is left↔right, use `CAM_DEPTH_COUNT_AXIS=y`;
- if movement in frame is top↕bottom, use `CAM_DEPTH_COUNT_AXIS=x`.

Additional check (without geometry change):

```bash
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi \
  --set CAM_DEPTH_COUNT_ANCHOR_MODE=leading_edge \
  --health
```

If `zone_mid_hits` still stays `0`:

- root cause is geometric mismatch of counting contour vs real traffic path;
- detector/tracker/depth are working, but tracked-point never enters A↔B middle band.

Minimal correction with one parameter:

```bash
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi \
  --set CAM_DEPTH_COUNT_AXIS_POS=0.78 \
  --health
```
