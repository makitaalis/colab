---
name: orangepi-passengers-camera-calibration
description: Calibration workflow for OAK-D Lite depth-counting mode on a camera node (central-gw or door-1/door-2). Use when tuning CAM_DEPTH_COUNT_* parameters, validating track_id/two-line counting behavior, and syncing camera runbook docs.
---

# OrangePi Passengers Camera Calibration

## Canon

- Camera runbook: `Docs/Проект/Операции/Камера OAK-D Lite (Luxonis).md`
- Central module: `Docs/Проект/Модули/Central (шлюз).md`
- Doc governance: `Docs/Проект/Документация (архитектура и правила).md`
- Official Luxonis docs (source of truth): `https://docs.luxonis.com/` (and v3 index: `https://docs.luxonis.com/software-v3/depthai/`)

## Workflow

1) Ensure depth-counting mode is active:

```bash
./scripts/camera_mode_switch.sh --mode depth-counting --camera-ip 192.168.10.11 --user orangepi
```

2) Capture current state:

```bash
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --show --health
```

3) First-pass tuning (recommended):

```bash
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --preset wide-scan --health
```

4) Apply transport strict profile (priority: fewer false positives):

```bash
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --preset transport-strict --health
```

5) Refine with targeted overrides:

```bash
./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi \
  --set CAM_DEPTH_COUNT_LINE_GAP_NORM=0.22 \
  --set CAM_DEPTH_COUNT_MIN_MOVE_NORM=0.16 \
  --health
```

6) Validate stability:

```bash
./scripts/camera_mode_menu.sh --camera-ip 192.168.10.11 --user orangepi --debug-port 8091
# menu: 17 (health snapshot), 13 (depth logs)
```

7) Return to production counter when calibration session is done:

```bash
./scripts/camera_mode_switch.sh --mode prod --camera-ip 192.168.10.11 --user orangepi
```

## Constraints

- Do not tune both `camera-counter` and `depth-counting` simultaneously on one camera.
- Keep depth mode bound to `127.0.0.1` for regular diagnostics; expose LAN bind only in trusted local network.
- After each calibration change, update docs in the same iteration.
- In stage summary always include: next step and why.
- If OPi load/X_LINK errors appear during browser streaming, reduce preview load first:
  - `CAM_PREVIEW_SIZE=480x300`
  - `CAM_PREVIEW_FPS=5`
  - `CAM_JPEG_QUALITY=60`
  - Note: `CAM_PREVIEW_FPS` throttles MJPEG updates; counting stays controlled by `CAM_DEPTH_COUNT_FPS`.

## UI quick modes

- Full (video + stats): `http://127.0.0.1:8091/`
- Stats-only (big counter, auto-disables preview): `http://127.0.0.1:8091/?view=stats`

## Luxonis Docs (how to use)

Rule: if any camera behavior is unclear, verify it in official docs before changing code/presets.

What to look up on `https://docs.luxonis.com/` for our pipeline:

- `DetectionNetwork` / model input & labels (person label = `0`).
- `ObjectTracker` node (tracker types, tracklet statuses, occlusion parameters).
- `Tracklets` message structure (fields: `id`, `age`, `roi`, `srcImgDetection.confidence`).
- Depth/stereo alignment (mono cameras → `StereoDepth`, align to RGB).
- `oak-viewer` diagnostics and device reconnect issues.

## IMU Check

For OAK-D Lite diagnostics in depth mode:

```bash
ssh orangepi@192.168.10.11 'curl -sS http://127.0.0.1:8091/health'
```

Confirm fields:

- `imu_present=true`
- `imu_updates` increasing
- `imu_accel_norm` and `imu_gyro_norm` are not null
