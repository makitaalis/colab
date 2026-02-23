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


def parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def tracker_type_from_name(name: str) -> dai.TrackerType:
    mapping = {
        "short_term_imageless": dai.TrackerType.SHORT_TERM_IMAGELESS,
        "short_term_kcf": dai.TrackerType.SHORT_TERM_KCF,
        "zero_term_imageless": dai.TrackerType.ZERO_TERM_IMAGELESS,
        "zero_term_color_histogram": dai.TrackerType.ZERO_TERM_COLOR_HISTOGRAM,
    }
    return mapping[name]


def clamp_pixel(value: float, max_value: int) -> int:
    if value <= 1.5:
        value = value * max_value
    return int(max(0, min(max_value - 1, round(value))))


def estimate_head_shoulders_depth_m(
    tracklet: dai.Tracklet,
    depth_frame: np.ndarray | None,
    head_fraction: float,
    min_valid_px: int,
) -> float | None:
    if depth_frame is None or depth_frame.ndim != 2:
        return None

    frame_h, frame_w = depth_frame.shape[:2]
    x1 = clamp_pixel(float(tracklet.roi.topLeft().x), frame_w)
    y1 = clamp_pixel(float(tracklet.roi.topLeft().y), frame_h)
    x2 = clamp_pixel(float(tracklet.roi.bottomRight().x), frame_w)
    y2 = clamp_pixel(float(tracklet.roi.bottomRight().y), frame_h)

    if x2 <= x1 or y2 <= y1:
        return None

    bbox_h = y2 - y1
    head_h = max(1, int(round(bbox_h * head_fraction)))
    y_head = min(y2, y1 + head_h)
    if y_head <= y1:
        return None

    roi = depth_frame[y1:y_head, x1:x2]
    if roi.size == 0:
        return None

    valid = roi[(roi >= 200) & (roi <= 10000)]
    if valid.size < min_valid_px:
        return None

    depth_mm = float(np.median(valid))
    if depth_mm <= 0:
        return None

    return depth_mm / 1000.0


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
    if hasattr(stereo, "setDepthAlign"):
        try:
            stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)
        except Exception:
            pass
    if hasattr(stereo, "setLeftRightCheck"):
        try:
            stereo.setLeftRightCheck(True)
        except Exception:
            pass
    if hasattr(stereo, "setSubpixel"):
        try:
            stereo.setSubpixel(True)
        except Exception:
            pass


class Handler(BaseHTTPRequestHandler):
    server_version = "PassengersCameraDebug/1.1"

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
            "<html><head><meta charset='utf-8'><title>Camera Debug</title>"
            "<style>"
            "body{background:#101217;color:#eceff4;font-family:Arial,sans-serif;margin:12px;}"
            ".head{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;}"
            ".badge{padding:2px 8px;border-radius:999px;background:#293241;color:#fff;font-size:12px;}"
            ".ok{background:#1f7a44;} .warn{background:#9a3d00;}"
            ".grid{display:grid;grid-template-columns:1fr 340px;gap:12px;align-items:start;}"
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
            "<h2 style='margin:0'>Passengers Camera Debug Stream</h2>"
            "<div><span id='status_badge' class='badge'>loading</span> "
            "<a href='/health' target='_blank'>health json</a> | "
            "<a href='/snapshot.jpg' target='_blank'>snapshot</a></div>"
            "</div>"
            "<div class='grid'>"
            "<div class='card'><img src='/mjpeg' alt='camera stream'/></div>"
            "<div class='card'>"
            "<h3 style='margin:0 0 10px 0;font-size:15px'>Live Stats</h3>"
            "<div class='stats'>"
            "<div class='k'>Status</div><div class='v' id='status'>-</div>"
            "<div class='k'>Device</div><div class='v' id='device'>-</div>"
            "<div class='k'>USB</div><div class='v' id='usb_speed'>-</div>"
            "<div class='k'>Messages</div><div class='v' id='messages'>-</div>"
            "<div class='k'>Tracklets</div><div class='v' id='tracklets_total'>-</div>"
            "<div class='k'>Active</div><div class='v' id='active_tracklets'>-</div>"
            "<div class='k'>Depth pass</div><div class='v' id='depth_pass'>-</div>"
            "<div class='k'>Depth reject</div><div class='v' id='depth_reject'>-</div>"
            "<div class='k'>Depth missing</div><div class='v' id='depth_missing'>-</div>"
            "<div class='k'>Depth range</div><div class='v'><span id='depth_min_m'>-</span> .. <span id='depth_max_m'>-</span> m</div>"
            "<div class='k'>Updated</div><div class='v' id='ts'>-</div>"
            "</div>"
            "<pre id='raw_json'>{}</pre>"
            "</div>"
            "</div>"
            "<script>"
            "function setVal(id,val){const el=document.getElementById(id); if(el) el.textContent=(val===undefined||val===null)?'-':String(val);}"
            "function setBadge(status){const b=document.getElementById('status_badge'); if(!b) return; b.textContent=status||'unknown'; b.className='badge '+((status==='running')?'ok':'warn');}"
            "async function refresh(){"
            "try{"
            "const r=await fetch('/health',{cache:'no-store'});"
            "const j=await r.json();"
            "['status','device','usb_speed','messages','tracklets_total','active_tracklets','depth_pass','depth_reject','depth_missing','depth_min_m','depth_max_m','ts'].forEach(k=>setVal(k,j[k]));"
            "setBadge(j.status);"
            "setVal('raw_json', JSON.stringify(j,null,2));"
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
    parser = argparse.ArgumentParser(description="OAK-D Lite debug MJPEG stream with tracker overlays.")
    parser.add_argument("--env", default="/etc/passengers/passengers.env")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--fps", type=float, default=10.0)
    parser.add_argument("--confidence", type=float, default=0.45)
    parser.add_argument("--model", default="yolov6-nano")
    parser.add_argument(
        "--tracker-type",
        choices=["short_term_imageless", "short_term_kcf", "zero_term_imageless", "zero_term_color_histogram"],
        default="short_term_imageless",
    )
    parser.add_argument("--line-axis", choices=["x", "y"], default="y")
    parser.add_argument("--line-pos", type=float, default=0.5)
    parser.add_argument("--line-hyst", type=float, default=0.04)
    parser.add_argument("--depth-enable", dest="depth_enable", action="store_true")
    parser.add_argument("--no-depth-enable", dest="depth_enable", action="store_false")
    parser.add_argument("--depth-min-m", type=float, default=0.40)
    parser.add_argument("--depth-max-m", type=float, default=1.50)
    parser.add_argument("--depth-head-fraction", type=float, default=0.45)
    parser.add_argument("--depth-min-valid-px", type=int, default=25)
    parser.set_defaults(depth_enable=True)
    parser.add_argument("--jpeg-quality", type=int, default=85)
    parser.add_argument("--log-interval-sec", type=float, default=10.0)
    return parser


def load_runtime(args: argparse.Namespace) -> argparse.Namespace:
    env = load_env_file(args.env)
    args.fps = float(env.get("CAM_COUNTER_FPS", str(args.fps)))
    args.confidence = float(env.get("CAM_COUNTER_CONFIDENCE", str(args.confidence)))
    args.model = env.get("CAM_COUNTER_MODEL", args.model)
    args.tracker_type = env.get("CAM_COUNTER_TRACKER_TYPE", args.tracker_type)
    args.line_axis = env.get("CAM_COUNTER_AXIS", args.line_axis)
    args.line_pos = float(env.get("CAM_COUNTER_AXIS_POS", str(args.line_pos)))
    args.line_hyst = float(env.get("CAM_COUNTER_HYSTERESIS", str(args.line_hyst)))

    args.depth_enable = parse_bool(env.get("CAM_DEPTH_ENABLE"), args.depth_enable)
    args.depth_min_m = float(env.get("CAM_DEPTH_MIN_M", str(args.depth_min_m)))
    args.depth_max_m = float(env.get("CAM_DEPTH_MAX_M", str(args.depth_max_m)))
    args.depth_head_fraction = float(env.get("CAM_DEPTH_HEAD_FRACTION", str(args.depth_head_fraction)))
    args.depth_min_valid_px = int(env.get("CAM_DEPTH_MIN_VALID_PX", str(args.depth_min_valid_px)))

    args.debug_bind = env.get("CAM_DEBUG_BIND", args.bind)
    args.debug_port = int(env.get("CAM_DEBUG_PORT", str(args.port)))
    args.show_ids = parse_bool(env.get("CAM_DEBUG_SHOW_IDS"), True)

    return args


def main() -> int:
    args = build_parser().parse_args()
    args = load_runtime(args)

    shared = SharedState(
        lock=threading.Lock(),
        jpg=b"",
        last_frame_ts=0.0,
        stats={
            "status": "starting",
            "device": "",
            "usb_speed": "",
            "messages": 0,
            "tracklets_total": 0,
            "active_tracklets": 0,
            "depth_pass": 0,
            "depth_reject": 0,
            "depth_missing": 0,
            "fps": args.fps,
            "model": args.model,
            "line_axis": args.line_axis,
            "line_pos": args.line_pos,
            "depth_enable": args.depth_enable,
            "depth_min_m": args.depth_min_m,
            "depth_max_m": args.depth_max_m,
            "bind": args.debug_bind,
            "port": args.debug_port,
        },
    )

    httpd = ThreadingHTTPServer((args.debug_bind, args.debug_port), Handler)
    httpd.shared_state = shared  # type: ignore[attr-defined]

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    print(
        f"camera-debug-stream: listening http://{args.debug_bind}:{args.debug_port} "
        f"(use SSH tunnel if bind=127.0.0.1)",
        flush=True,
    )

    with dai.Pipeline() as pipeline:
        camera = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_A)

        det = pipeline.create(dai.node.DetectionNetwork).build(
            camera,
            dai.NNModelDescription(args.model),
            fps=args.fps,
        )
        det.setConfidenceThreshold(args.confidence)

        tracker = pipeline.create(dai.node.ObjectTracker)
        tracker.setDetectionLabelsToTrack([0])
        tracker.setTrackerType(tracker_type_from_name(args.tracker_type))
        tracker.setTrackerIdAssignmentPolicy(dai.TrackerIdAssignmentPolicy.UNIQUE_ID)

        det.out.link(tracker.inputDetections)
        det.passthrough.link(tracker.inputDetectionFrame)
        det.passthrough.link(tracker.inputTrackerFrame)

        frame_queue = camera.requestOutput(size=(640, 400), type=dai.ImgFrame.Type.BGR888p, fps=args.fps).createOutputQueue(
            maxSize=6,
            blocking=False,
        )
        track_queue = tracker.out.createOutputQueue(maxSize=6, blocking=False)

        depth_queue = None
        if args.depth_enable:
            left_camera = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_B)
            right_camera = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_C)
            stereo = pipeline.create(dai.node.StereoDepth)
            configure_stereo(stereo)

            left_camera.requestOutput(size=(640, 400), type=dai.ImgFrame.Type.RAW8, fps=args.fps).link(stereo.left)
            right_camera.requestOutput(size=(640, 400), type=dai.ImgFrame.Type.RAW8, fps=args.fps).link(stereo.right)
            depth_queue = stereo.depth.createOutputQueue(maxSize=4, blocking=False)

        pipeline.start()
        device = pipeline.getDefaultDevice()

        with shared.lock:
            shared.stats["status"] = "running"
            shared.stats["device"] = device.getDeviceName()
            shared.stats["usb_speed"] = device.getUsbSpeed().name

        print(
            f"camera-debug-stream: device={device.getDeviceName()} usb_speed={device.getUsbSpeed().name} "
            f"depth_enable={args.depth_enable} depth_range={args.depth_min_m:.2f}-{args.depth_max_m:.2f}m",
            flush=True,
        )

        last_tracklets: list[dai.Tracklet] = []
        latest_depth_frame: np.ndarray | None = None
        t0 = time.monotonic()
        last_log = t0
        frames = 0

        try:
            while pipeline.isRunning():
                frame_msg = frame_queue.tryGet()
                track_msg = track_queue.tryGet()
                if depth_queue is not None:
                    depth_msg = depth_queue.tryGet()
                    if depth_msg is not None:
                        latest_depth_frame = depth_msg.getFrame()

                if track_msg is not None:
                    last_tracklets = list(track_msg.tracklets)
                    active = [
                        t
                        for t in last_tracklets
                        if t.status in {dai.Tracklet.TrackingStatus.NEW, dai.Tracklet.TrackingStatus.TRACKED}
                    ]
                    with shared.lock:
                        shared.stats["messages"] = int(shared.stats["messages"]) + 1
                        shared.stats["tracklets_total"] = int(shared.stats["tracklets_total"]) + len(last_tracklets)
                        shared.stats["active_tracklets"] = len(active)

                if frame_msg is None:
                    now = time.monotonic()
                    if now - last_log >= args.log_interval_sec:
                        with shared.lock:
                            active = shared.stats["active_tracklets"]
                            messages = shared.stats["messages"]
                            depth_pass = shared.stats["depth_pass"]
                            depth_reject = shared.stats["depth_reject"]
                            depth_missing = shared.stats["depth_missing"]
                        print(
                            f"camera-debug-stream heartbeat: frames={frames} messages={messages} active_tracklets={active} "
                            f"depth_pass={depth_pass} depth_reject={depth_reject} depth_missing={depth_missing}",
                            flush=True,
                        )
                        last_log = now
                    time.sleep(0.01)
                    continue

                frame = frame_msg.getCvFrame()
                height, width = frame.shape[:2]

                if args.line_axis == "y":
                    line_x = clamp_pixel(args.line_pos, width)
                    cv2.line(frame, (line_x, 0), (line_x, height - 1), (0, 255, 255), 2)
                else:
                    line_y = clamp_pixel(args.line_pos, height)
                    cv2.line(frame, (0, line_y), (width - 1, line_y), (0, 255, 255), 2)

                depth_pass_frame = 0
                depth_reject_frame = 0
                depth_missing_frame = 0

                for tracklet in last_tracklets:
                    if tracklet.status not in {dai.Tracklet.TrackingStatus.NEW, dai.Tracklet.TrackingStatus.TRACKED}:
                        continue

                    depth_m = None
                    depth_ok = True
                    if args.depth_enable:
                        depth_m = estimate_head_shoulders_depth_m(
                            tracklet,
                            latest_depth_frame,
                            args.depth_head_fraction,
                            args.depth_min_valid_px,
                        )
                        if depth_m is None:
                            depth_ok = False
                            depth_missing_frame += 1
                        elif depth_m < args.depth_min_m or depth_m > args.depth_max_m:
                            depth_ok = False
                            depth_reject_frame += 1
                        else:
                            depth_pass_frame += 1

                    x1 = clamp_pixel(tracklet.roi.topLeft().x, width)
                    y1 = clamp_pixel(tracklet.roi.topLeft().y, height)
                    x2 = clamp_pixel(tracklet.roi.bottomRight().x, width)
                    y2 = clamp_pixel(tracklet.roi.bottomRight().y, height)

                    if args.depth_enable:
                        color = (0, 200, 0) if depth_ok else (0, 80, 255)
                    else:
                        color = (0, 200, 0) if tracklet.status == dai.Tracklet.TrackingStatus.TRACKED else (0, 200, 200)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                    if args.show_ids:
                        if depth_m is None:
                            depth_text = "z=n/a"
                        else:
                            depth_text = f"z={depth_m:.2f}m"

                        if args.depth_enable:
                            gate_text = "ok" if depth_ok else "reject"
                            label = f"id={tracklet.id} age={tracklet.age} {depth_text} {gate_text}"
                        else:
                            label = f"id={tracklet.id} age={tracklet.age}"

                        cv2.putText(frame, label, (x1 + 2, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

                if args.depth_enable:
                    with shared.lock:
                        shared.stats["depth_pass"] = int(shared.stats["depth_pass"]) + depth_pass_frame
                        shared.stats["depth_reject"] = int(shared.stats["depth_reject"]) + depth_reject_frame
                        shared.stats["depth_missing"] = int(shared.stats["depth_missing"]) + depth_missing_frame

                overlay = f"model={args.model} fps={args.fps:.1f} tracklets={len(last_tracklets)}"
                if args.depth_enable:
                    overlay += f" depth={args.depth_min_m:.2f}-{args.depth_max_m:.2f}m"

                cv2.putText(
                    frame,
                    overlay,
                    (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    1,
                )

                ok, encoded = cv2.imencode(
                    ".jpg",
                    frame,
                    [int(cv2.IMWRITE_JPEG_QUALITY), int(max(10, min(95, args.jpeg_quality)))],
                )
                if not ok:
                    continue

                now = time.monotonic()
                frames += 1
                with shared.lock:
                    shared.jpg = encoded.tobytes()
                    shared.last_frame_ts = now

                if now - last_log >= args.log_interval_sec:
                    with shared.lock:
                        active = shared.stats["active_tracklets"]
                        messages = shared.stats["messages"]
                        depth_pass = shared.stats["depth_pass"]
                        depth_reject = shared.stats["depth_reject"]
                        depth_missing = shared.stats["depth_missing"]
                    print(
                        f"camera-debug-stream heartbeat: frames={frames} messages={messages} active_tracklets={active} "
                        f"depth_pass={depth_pass} depth_reject={depth_reject} depth_missing={depth_missing}",
                        flush=True,
                    )
                    last_log = now
        finally:
            with shared.lock:
                shared.stats["status"] = "stopping"
            httpd.shutdown()
            httpd.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
