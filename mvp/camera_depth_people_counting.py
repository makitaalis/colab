#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import threading
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import cv2
import depthai as dai
import numpy as np

from common import load_env_file, utc_now_iso


@dataclass
class SharedState:
    lock: threading.Lock
    jpg: bytes
    last_frame_ts: float
    stats: dict[str, Any]


@dataclass
class ActiveTrack:
    center: tuple[int, int]
    side: int
    last_seen: float
    last_count_ts: float


def parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def clamp_pixel(value: float, max_value: int) -> int:
    if value <= 1.5:
        value = value * max_value
    return int(max(0, min(max_value - 1, round(value))))


def parse_roi(value: str, width: int, height: int) -> tuple[int, int, int, int]:
    parts = [piece.strip() for piece in value.split(",") if piece.strip()]
    if len(parts) != 4:
        return 0, 0, width - 1, height - 1
    vals = [float(piece) for piece in parts]

    if all(v <= 1.5 for v in vals):
        x1 = clamp_pixel(vals[0], width)
        y1 = clamp_pixel(vals[1], height)
        x2 = clamp_pixel(vals[2], width)
        y2 = clamp_pixel(vals[3], height)
    else:
        x1 = int(max(0, min(width - 1, round(vals[0]))))
        y1 = int(max(0, min(height - 1, round(vals[1]))))
        x2 = int(max(0, min(width - 1, round(vals[2]))))
        y2 = int(max(0, min(height - 1, round(vals[3]))))

    if x2 <= x1:
        x2 = min(width - 1, x1 + 1)
    if y2 <= y1:
        y2 = min(height - 1, y1 + 1)

    return x1, y1, x2, y2


def side_from_value(value: float, line_value: float, hysteresis: float) -> int:
    if value < (line_value - hysteresis):
        return -1
    if value > (line_value + hysteresis):
        return 1
    return 0


def transition_to_counts(prev_side: int, new_side: int, invert_direction: bool) -> tuple[int, int, str]:
    if prev_side == -1 and new_side == 1:
        in_count, out_count = (1, 0)
        direction = "neg_to_pos"
    elif prev_side == 1 and new_side == -1:
        in_count, out_count = (0, 1)
        direction = "pos_to_neg"
    else:
        return 0, 0, "no_cross"

    if invert_direction:
        in_count, out_count = out_count, in_count
        direction = f"{direction}_inverted"

    return in_count, out_count, direction


def configure_stereo(stereo: dai.node.StereoDepth) -> None:
    if hasattr(stereo, "setDefaultProfilePreset"):
        try:
            stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        except Exception:
            pass
    if hasattr(stereo, "setOutputSize"):
        try:
            stereo.setOutputSize(640, 400)
        except Exception:
            pass
    if hasattr(stereo, "setLeftRightCheck"):
        try:
            stereo.setLeftRightCheck(True)
        except Exception:
            pass
    if hasattr(stereo, "setSubpixel"):
        try:
            stereo.setSubpixel(False)
        except Exception:
            pass


def resolve_imu_sensor(candidates: list[str]) -> Any | None:
    for name in candidates:
        sensor = getattr(dai.IMUSensor, name, None)
        if sensor is not None:
            return sensor
    return None


def read_imu_vector(sample: Any) -> tuple[float, float, float] | None:
    if sample is None:
        return None
    try:
        x = float(getattr(sample, "x"))
        y = float(getattr(sample, "y"))
        z = float(getattr(sample, "z"))
    except Exception:
        return None
    return x, y, z


def format_norm(vector: tuple[float, float, float] | None) -> float | None:
    if vector is None:
        return None
    x, y, z = vector
    return float((x * x + y * y + z * z) ** 0.5)


def poll_imu_queue(imu_queue: Any, shared: SharedState) -> tuple[float | None, float | None]:
    if imu_queue is None:
        return None, None

    last_acc = None
    last_gyro = None
    packets_read = 0

    while True:
        imu_msg = imu_queue.tryGet()
        if imu_msg is None:
            break

        packets = list(getattr(imu_msg, "packets", []) or getattr(imu_msg, "imuPackets", []))
        for packet in packets:
            accel = read_imu_vector(getattr(packet, "acceleroMeter", None) or getattr(packet, "accelerometer", None))
            gyro = read_imu_vector(getattr(packet, "gyroscope", None))
            if accel is None and gyro is None:
                continue
            packets_read += 1
            if accel is not None:
                last_acc = accel
            if gyro is not None:
                last_gyro = gyro

    if packets_read == 0:
        return None, None

    acc_norm = format_norm(last_acc)
    gyro_norm = format_norm(last_gyro)
    now_ms = int(time.time() * 1000)

    with shared.lock:
        stats = shared.stats
        stats["imu_present"] = True
        stats["imu_updates"] = int(stats.get("imu_updates", 0)) + packets_read
        stats["imu_last_ms"] = now_ms
        if last_acc is not None:
            ax, ay, az = last_acc
            stats["imu_accel_x"] = round(ax, 5)
            stats["imu_accel_y"] = round(ay, 5)
            stats["imu_accel_z"] = round(az, 5)
            stats["imu_accel_norm"] = round(float(acc_norm), 5) if acc_norm is not None else None
        if last_gyro is not None:
            gx, gy, gz = last_gyro
            stats["imu_gyro_x"] = round(gx, 5)
            stats["imu_gyro_y"] = round(gy, 5)
            stats["imu_gyro_z"] = round(gz, 5)
            stats["imu_gyro_norm"] = round(float(gyro_norm), 5) if gyro_norm is not None else None

    return acc_norm, gyro_norm


class Handler(BaseHTTPRequestHandler):
    server_version = "PassengersDepthCounting/1.1"

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"}:
            self._send_html()
            return
        if self.path == "/health":
            self._send_health()
            return
        if self.path == "/snapshot.jpg":
            self._send_snapshot()
            return
        if self.path == "/mjpeg":
            self._send_mjpeg()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "not found")

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _state(self) -> SharedState:
        return self.server.shared_state  # type: ignore[attr-defined]

    def _send_html(self) -> None:
        body = (
            "<html><head><meta charset='utf-8'><title>Depth People Counting</title>"
            "<style>"
            "body{background:#101217;color:#eceff4;font-family:Arial,sans-serif;margin:12px;}"
            ".head{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;}"
            ".badge{padding:2px 8px;border-radius:999px;background:#293241;color:#fff;font-size:12px;}"
            ".ok{background:#1f7a44;} .warn{background:#9a3d00;}"
            ".grid{display:grid;grid-template-columns:1fr 390px;gap:12px;align-items:start;}"
            ".card{border:1px solid #2d3748;border-radius:8px;padding:10px;background:#151923;}"
            ".stats{display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;font-size:13px;}"
            ".k{color:#9fb3c8;} .v{font-weight:700;}"
            "a{color:#8ec9ff;text-decoration:none;} a:hover{text-decoration:underline;}"
            "img{max-width:100%;border:1px solid #3a4354;border-radius:8px;display:block;}"
            "pre{font-size:11px;white-space:pre-wrap;word-break:break-word;max-height:210px;overflow:auto;}"
            "@media (max-width: 980px){.grid{grid-template-columns:1fr;}}"
            "</style></head>"
            "<body>"
            "<div class='head'>"
            "<h2 style='margin:0'>Depth People Counting (Luxonis style)</h2>"
            "<div><span id='status_badge' class='badge'>loading</span> "
            "<a href='/health' target='_blank'>health json</a> | "
            "<a href='/snapshot.jpg' target='_blank'>snapshot</a></div>"
            "</div>"
            "<div class='grid'>"
            "<div class='card'><img src='/mjpeg' alt='depth counting stream'/></div>"
            "<div class='card'>"
            "<h3 style='margin:0 0 10px 0;font-size:15px'>Live Stats</h3>"
            "<div class='stats'>"
            "<div class='k'>Status</div><div class='v' id='status'>-</div>"
            "<div class='k'>Device</div><div class='v' id='device'>-</div>"
            "<div class='k'>USB</div><div class='v' id='usb_speed'>-</div>"
            "<div class='k'>Messages</div><div class='v' id='messages'>-</div>"
            "<div class='k'>Detections</div><div class='v' id='detections'>-</div>"
            "<div class='k'>Track active</div><div class='v' id='track_active'>-</div>"
            "<div class='k'>IN</div><div class='v' id='count_in'>-</div>"
            "<div class='k'>OUT</div><div class='v' id='count_out'>-</div>"
            "<div class='k'>Axis</div><div class='v' id='axis'>-</div>"
            "<div class='k'>Threshold</div><div class='v'><span id='threshold_low'>-</span>..<span id='threshold_high'>-</span></div>"
            "<div class='k'>Area min</div><div class='v' id='area_min'>-</div>"
            "<div class='k'>IMU enabled</div><div class='v' id='imu_enabled'>-</div>"
            "<div class='k'>IMU type</div><div class='v' id='imu_type'>-</div>"
            "<div class='k'>IMU updates</div><div class='v' id='imu_updates'>-</div>"
            "<div class='k'>Accel |a|</div><div class='v' id='imu_accel_norm'>-</div>"
            "<div class='k'>Gyro |g|</div><div class='v' id='imu_gyro_norm'>-</div>"
            "<div class='k'>Updated</div><div class='v' id='ts'>-</div>"
            "</div>"
            "<pre id='raw_json'>{}</pre>"
            "</div>"
            "</div>"
            "<script>"
            "function setVal(id,val){const el=document.getElementById(id); if(el) el.textContent=(val===undefined||val===null)?'-':String(val);}"
            "function setBadge(status){const b=document.getElementById('status_badge'); if(!b) return; b.textContent=status||'unknown'; b.className='badge '+((status==='running')?'ok':'warn');}"
            "async function refresh(){"
            "try{const r=await fetch('/health',{cache:'no-store'}); const j=await r.json();"
            "['status','device','usb_speed','messages','detections','track_active','count_in','count_out','axis','threshold_low','threshold_high','area_min','imu_enabled','imu_type','imu_updates','imu_accel_norm','imu_gyro_norm','ts'].forEach(k=>setVal(k,j[k]));"
            "setBadge(j.status); setVal('raw_json', JSON.stringify(j,null,2));"
            "}catch(e){setBadge('error'); setVal('raw_json','health fetch error: '+e);}"
            "}"
            "refresh(); setInterval(refresh,1000);"
            "</script>"
            "</body></html>"
        ).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_health(self) -> None:
        state = self._state()
        with state.lock:
            payload = dict(state.stats)
        payload["ts"] = utc_now_iso()
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_snapshot(self) -> None:
        state = self._state()
        with state.lock:
            jpg = state.jpg
        if not jpg:
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "no frame yet")
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(jpg)))
        self.end_headers()
        self.wfile.write(jpg)

    def _send_mjpeg(self) -> None:
        boundary = b"frame"
        self.send_response(HTTPStatus.OK)
        self.send_header("Age", "0")
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={boundary.decode()}")
        self.end_headers()

        state = self._state()
        last_sent_ts = 0.0
        try:
            while True:
                with state.lock:
                    jpg = state.jpg
                    frame_ts = state.last_frame_ts
                if jpg and frame_ts != last_sent_ts:
                    self.wfile.write(b"--" + boundary + b"\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(jpg)}\r\n\r\n".encode("ascii"))
                    self.wfile.write(jpg)
                    self.wfile.write(b"\r\n")
                    last_sent_ts = frame_ts
                time.sleep(0.03)
        except (BrokenPipeError, ConnectionResetError):
            return


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Depth people counting (Luxonis example style).")
    parser.add_argument("--env", default="/etc/passengers/passengers.env")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--fps", type=float, default=10.0)
    parser.add_argument("--axis", choices=["x", "y"], default="y")
    parser.add_argument("--axis-pos", type=float, default=0.5)
    parser.add_argument("--axis-hyst", type=float, default=0.04)
    parser.add_argument("--roi", default="0.05,0.10,0.95,0.95")
    parser.add_argument("--threshold-low", type=int, default=125)
    parser.add_argument("--threshold-high", type=int, default=145)
    parser.add_argument("--area-min", type=float, default=5000.0)
    parser.add_argument("--kernel-size", type=int, default=37)
    parser.add_argument("--track-gap-sec", type=float, default=0.8)
    parser.add_argument("--count-cooldown-sec", type=float, default=0.6)
    parser.add_argument("--invert-direction", action="store_true")
    parser.add_argument("--imu-enable", action="store_true", default=True)
    parser.add_argument("--imu-rate-hz", type=int, default=100)
    parser.add_argument("--jpeg-quality", type=int, default=85)
    parser.add_argument("--log-interval-sec", type=float, default=10.0)
    return parser


def load_runtime(args: argparse.Namespace) -> argparse.Namespace:
    env = load_env_file(args.env)
    args.fps = float(env.get("CAM_DEPTH_COUNT_FPS", str(args.fps)))
    args.axis = env.get("CAM_DEPTH_COUNT_AXIS", args.axis).strip().lower()
    args.axis_pos = float(env.get("CAM_DEPTH_COUNT_AXIS_POS", str(args.axis_pos)))
    args.axis_hyst = float(env.get("CAM_DEPTH_COUNT_AXIS_HYST", str(args.axis_hyst)))
    args.roi = env.get("CAM_DEPTH_COUNT_ROI", args.roi)
    args.threshold_low = int(env.get("CAM_DEPTH_COUNT_THRESHOLD_LOW", str(args.threshold_low)))
    args.threshold_high = int(env.get("CAM_DEPTH_COUNT_THRESHOLD_HIGH", str(args.threshold_high)))
    args.area_min = float(env.get("CAM_DEPTH_COUNT_AREA_MIN", str(args.area_min)))
    args.kernel_size = int(env.get("CAM_DEPTH_COUNT_KERNEL_SIZE", str(args.kernel_size)))
    args.track_gap_sec = float(env.get("CAM_DEPTH_COUNT_TRACK_GAP_SEC", str(args.track_gap_sec)))
    args.count_cooldown_sec = float(env.get("CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC", str(args.count_cooldown_sec)))
    args.invert_direction = parse_bool(env.get("CAM_DEPTH_COUNT_INVERT"), args.invert_direction)

    args.imu_enable = parse_bool(env.get("CAM_IMU_ENABLE"), args.imu_enable)
    args.imu_rate_hz = int(env.get("CAM_IMU_RATE_HZ", str(args.imu_rate_hz)))

    args.debug_bind = env.get("CAM_DEBUG_BIND", args.bind)
    args.debug_port = int(env.get("CAM_DEBUG_PORT", str(args.port)))

    if args.axis not in {"x", "y"}:
        raise ValueError(f"axis must be x|y (got {args.axis})")
    if not (0.05 <= args.axis_pos <= 0.95):
        raise ValueError(f"axis-pos must be in [0.05..0.95] (got {args.axis_pos})")
    if not (0.0 <= args.axis_hyst <= 0.25):
        raise ValueError(f"axis-hyst must be in [0..0.25] (got {args.axis_hyst})")
    if args.threshold_low < 0 or args.threshold_high > 255 or args.threshold_low >= args.threshold_high:
        raise ValueError("invalid threshold range")

    if args.kernel_size < 3:
        args.kernel_size = 3
    if args.kernel_size % 2 == 0:
        args.kernel_size += 1

    if args.imu_rate_hz < 1:
        args.imu_rate_hz = 1

    return args


def to_u8_disparity(frame: np.ndarray) -> np.ndarray:
    if frame.dtype == np.uint8:
        return frame
    if frame.size == 0:
        return np.zeros((1, 1), dtype=np.uint8)
    max_val = float(np.max(frame))
    if max_val <= 0:
        return np.zeros_like(frame, dtype=np.uint8)
    scale = 255.0 / max_val
    return cv2.convertScaleAbs(frame, alpha=scale)


def main() -> int:
    args = load_runtime(build_parser().parse_args())

    shared = SharedState(
        lock=threading.Lock(),
        jpg=b"",
        last_frame_ts=0.0,
        stats={
            "status": "starting",
            "device": "",
            "usb_speed": "",
            "messages": 0,
            "detections": 0,
            "track_active": False,
            "count_in": 0,
            "count_out": 0,
            "axis": args.axis,
            "axis_pos": args.axis_pos,
            "threshold_low": args.threshold_low,
            "threshold_high": args.threshold_high,
            "area_min": args.area_min,
            "bind": args.debug_bind,
            "port": args.debug_port,
            "imu_enabled": args.imu_enable,
            "imu_type": "",
            "imu_present": False,
            "imu_updates": 0,
            "imu_last_ms": 0,
            "imu_accel_x": None,
            "imu_accel_y": None,
            "imu_accel_z": None,
            "imu_accel_norm": None,
            "imu_gyro_x": None,
            "imu_gyro_y": None,
            "imu_gyro_z": None,
            "imu_gyro_norm": None,
        },
    )

    httpd = ThreadingHTTPServer((args.debug_bind, args.debug_port), Handler)
    httpd.shared_state = shared  # type: ignore[attr-defined]

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    print(
        f"depth-counting: listening http://{args.debug_bind}:{args.debug_port} (use SSH tunnel if bind=127.0.0.1)",
        flush=True,
    )

    with dai.Pipeline() as pipeline:
        left_camera = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_B)
        right_camera = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_C)

        stereo = pipeline.create(dai.node.StereoDepth)
        configure_stereo(stereo)

        left_camera.requestOutput(size=(640, 400), type=dai.ImgFrame.Type.RAW8, fps=args.fps).link(stereo.left)
        right_camera.requestOutput(size=(640, 400), type=dai.ImgFrame.Type.RAW8, fps=args.fps).link(stereo.right)

        disparity_queue = stereo.disparity.createOutputQueue(maxSize=4, blocking=False)

        imu_queue = None
        imu_available = False
        if args.imu_enable:
            try:
                imu_node = pipeline.create(dai.node.IMU)
                accel_sensor = resolve_imu_sensor(["ACCELEROMETER_RAW", "ACCELEROMETER"])
                gyro_sensor = resolve_imu_sensor(["GYROSCOPE_RAW", "GYROSCOPE_CALIBRATED", "GYROSCOPE"])
                if accel_sensor is not None:
                    imu_node.enableIMUSensor(accel_sensor, args.imu_rate_hz)
                if gyro_sensor is not None:
                    imu_node.enableIMUSensor(gyro_sensor, args.imu_rate_hz)
                if accel_sensor is not None or gyro_sensor is not None:
                    imu_node.setBatchReportThreshold(1)
                    imu_node.setMaxBatchReports(10)
                    imu_queue = imu_node.out.createOutputQueue(maxSize=20, blocking=False)
                    imu_available = True
                else:
                    args.imu_enable = False
            except Exception as exc:
                print(f"depth-counting: imu init disabled: {exc}", flush=True)
                args.imu_enable = False

        pipeline.start()
        device = pipeline.getDefaultDevice()

        imu_type = ""
        if args.imu_enable:
            try:
                imu_type = str(device.getConnectedIMU())
            except Exception:
                imu_type = "unknown"

        with shared.lock:
            shared.stats["status"] = "running"
            shared.stats["device"] = device.getDeviceName()
            shared.stats["usb_speed"] = device.getUsbSpeed().name
            shared.stats["imu_enabled"] = bool(args.imu_enable)
            shared.stats["imu_type"] = imu_type
            shared.stats["imu_present"] = bool(imu_available)

        print(
            f"depth-counting: device={device.getDeviceName()} usb_speed={device.getUsbSpeed().name} "
            f"axis={args.axis} axis_pos={args.axis_pos} threshold={args.threshold_low}-{args.threshold_high} area_min={args.area_min} "
            f"imu_enable={args.imu_enable} imu_rate_hz={args.imu_rate_hz}",
            flush=True,
        )

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (args.kernel_size, args.kernel_size))
        active_track: ActiveTrack | None = None
        frames = 0
        last_log = time.monotonic()

        count_in = 0
        count_out = 0
        imu_acc_norm = None
        imu_gyro_norm = None

        while pipeline.isRunning():
            new_acc_norm, new_gyro_norm = poll_imu_queue(imu_queue, shared)
            if new_acc_norm is not None:
                imu_acc_norm = new_acc_norm
            if new_gyro_norm is not None:
                imu_gyro_norm = new_gyro_norm

            disparity_msg = disparity_queue.tryGet()
            if disparity_msg is None:
                now = time.monotonic()
                if now - last_log >= args.log_interval_sec:
                    with shared.lock:
                        messages = int(shared.stats["messages"])
                        detections = int(shared.stats["detections"])
                        track_active = bool(shared.stats["track_active"])
                        imu_updates = int(shared.stats.get("imu_updates", 0))
                    print(
                        f"depth-counting heartbeat: frames={frames} messages={messages} detections={detections} "
                        f"track_active={track_active} in={count_in} out={count_out} imu_updates={imu_updates}",
                        flush=True,
                    )
                    last_log = now
                time.sleep(0.01)
                continue

            frames += 1
            with shared.lock:
                shared.stats["messages"] = int(shared.stats["messages"]) + 1

            disparity = to_u8_disparity(disparity_msg.getFrame())
            h, w = disparity.shape[:2]

            x1, y1, x2, y2 = parse_roi(args.roi, w, h)
            roi = disparity[y1:y2, x1:x2]

            mask = cv2.inRange(roi, args.threshold_low, args.threshold_high)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            best_rect = None
            best_area = 0.0
            for contour in contours:
                area = float(cv2.contourArea(contour))
                if area < args.area_min or area <= best_area:
                    continue
                bx, by, bw, bh = cv2.boundingRect(contour)
                best_rect = (x1 + bx, y1 + by, bw, bh)
                best_area = area

            now = time.monotonic()
            detection_center = None
            if best_rect is not None:
                bx, by, bw, bh = best_rect
                detection_center = (bx + bw // 2, by + bh // 2)
                with shared.lock:
                    shared.stats["detections"] = int(shared.stats["detections"]) + 1

            line_coord = args.axis_pos * (w if args.axis == "y" else h)
            hyst_px = max(2.0, args.axis_hyst * (w if args.axis == "y" else h))

            if detection_center is None:
                if active_track is not None and (now - active_track.last_seen) > args.track_gap_sec:
                    active_track = None
            else:
                axis_value = float(detection_center[0] if args.axis == "y" else detection_center[1])
                new_side = side_from_value(axis_value, line_coord, hyst_px)

                if active_track is None:
                    active_track = ActiveTrack(center=detection_center, side=new_side, last_seen=now, last_count_ts=0.0)
                else:
                    prev_side = active_track.side
                    active_track.center = detection_center
                    active_track.last_seen = now
                    if new_side != 0:
                        active_track.side = new_side

                    if (
                        prev_side != 0
                        and new_side != 0
                        and prev_side != new_side
                        and (now - active_track.last_count_ts) >= args.count_cooldown_sec
                    ):
                        in_count, out_count, direction = transition_to_counts(prev_side, new_side, args.invert_direction)
                        if in_count > 0 or out_count > 0:
                            count_in += in_count
                            count_out += out_count
                            active_track.last_count_ts = now
                            print(
                                f"depth-counting event: direction={direction} in={in_count} out={out_count} "
                                f"center={detection_center} area={best_area:.1f}",
                                flush=True,
                            )

            color = cv2.applyColorMap(disparity, cv2.COLORMAP_TURBO)
            cv2.rectangle(color, (x1, y1), (x2, y2), (255, 200, 0), 2)

            if args.axis == "y":
                line_x = int(round(line_coord))
                cv2.line(color, (line_x, 0), (line_x, h - 1), (0, 255, 255), 2)
            else:
                line_y = int(round(line_coord))
                cv2.line(color, (0, line_y), (w - 1, line_y), (0, 255, 255), 2)

            if best_rect is not None:
                bx, by, bw, bh = best_rect
                cv2.rectangle(color, (bx, by), (bx + bw, by + bh), (0, 255, 0), 2)
                if detection_center is not None:
                    cx, cy = detection_center
                    cv2.circle(color, (cx, cy), 4, (255, 255, 255), -1)

            cv2.putText(color, f"IN={count_in} OUT={count_out}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(
                color,
                f"th={args.threshold_low}-{args.threshold_high} area>{int(args.area_min)}",
                (10, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (235, 235, 235),
                1,
            )
            if args.imu_enable:
                imu_line = f"IMU a={imu_acc_norm:.2f} g={imu_gyro_norm:.2f}" if imu_acc_norm is not None and imu_gyro_norm is not None else "IMU waiting"
                cv2.putText(color, imu_line, (10, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 255, 180), 1)

            ok, encoded = cv2.imencode(
                ".jpg",
                color,
                [int(cv2.IMWRITE_JPEG_QUALITY), int(max(10, min(95, args.jpeg_quality)))],
            )
            if not ok:
                continue

            with shared.lock:
                shared.jpg = encoded.tobytes()
                shared.last_frame_ts = now
                shared.stats["track_active"] = active_track is not None
                shared.stats["count_in"] = count_in
                shared.stats["count_out"] = count_out

            if now - last_log >= args.log_interval_sec:
                with shared.lock:
                    messages = int(shared.stats["messages"])
                    detections = int(shared.stats["detections"])
                    track_active = bool(shared.stats["track_active"])
                    imu_updates = int(shared.stats.get("imu_updates", 0))
                print(
                    f"depth-counting heartbeat: frames={frames} messages={messages} detections={detections} "
                    f"track_active={track_active} in={count_in} out={count_out} imu_updates={imu_updates}",
                    flush=True,
                )
                last_log = now

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
