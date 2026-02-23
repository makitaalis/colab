#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import threading
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import cv2
import depthai as dai
import numpy as np

from common import load_env_file, utc_now_iso


@dataclass
class SharedState:
    lock: threading.Lock
    jpg: bytes
    last_frame_ts: float
    preview_frame: np.ndarray | None
    preview_items: list[dict[str, Any]]
    stats: dict[str, Any]


@dataclass
class TrackCrossState:
    last_seen: float
    side_start: int | None
    first_side_axis: float
    seen_middle: bool
    entered_middle_ts: float | None
    side_frames: int
    middle_frames: int
    last_event_ts: float
    last_event_direction: str | None
    age: int


@dataclass
class HostTrackState:
    last_seen: float
    x1n: float
    y1n: float
    x2n: float
    y2n: float
    cxn: float
    cyn: float
    confidence: float
    age: int


def bbox_iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0.0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    denom = area_a + area_b - inter
    if denom <= 0.0:
        return 0.0
    return float(inter / denom)


@dataclass
class _NormPoint:
    x: float
    y: float


class _NormRoi:
    def __init__(self, x1n: float, y1n: float, x2n: float, y2n: float) -> None:
        self._tl = _NormPoint(float(x1n), float(y1n))
        self._br = _NormPoint(float(x2n), float(y2n))

    def topLeft(self) -> _NormPoint:  # noqa: N802
        return self._tl

    def bottomRight(self) -> _NormPoint:  # noqa: N802
        return self._br


@dataclass
class _SrcImgDetection:
    confidence: float


class HostTrackletLike:
    """Minimal Tracklet-like object to reuse existing strict logic + drawing."""

    def __init__(self, tid: int, x1n: float, y1n: float, x2n: float, y2n: float, confidence: float, age: int) -> None:
        self.id = int(tid)
        self.status = dai.Tracklet.TrackingStatus.TRACKED
        self.roi = _NormRoi(x1n, y1n, x2n, y2n)
        self.srcImgDetection = _SrcImgDetection(float(confidence))
        self.age = int(age)


def sigmoid(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, -50.0, 50.0)
    return 1.0 / (1.0 + np.exp(-x))


def softmax_last_axis(x: np.ndarray) -> np.ndarray:
    x = x - np.max(x, axis=-1, keepdims=True)
    exp = np.exp(np.clip(x, -50.0, 50.0))
    denom = np.sum(exp, axis=-1, keepdims=True)
    denom = np.where(denom == 0.0, 1.0, denom)
    return exp / denom


def decode_yolov8_dfl_outputs(
    outputs: list[np.ndarray],
    input_size: tuple[int, int],
    confidence_min: float,
    nms_iou: float,
    max_det: int,
) -> list[tuple[float, float, float, float, float]]:
    """Decode YOLOv8 (DFL) raw outputs into XYXY boxes in *input pixel space*.

    Returns: list of (x1, y1, x2, y2, conf)
    """
    input_w, input_h = input_size
    reg_max = 15
    bins = np.arange(reg_max + 1, dtype=np.float32)
    boxes_xywh: list[list[float]] = []
    scores: list[float] = []

    for out in outputs:
        if out.ndim != 4 or out.shape[0] != 1 or out.shape[1] < 5:
            continue
        _, ch, h, w = out.shape
        if ch != 4 * (reg_max + 1) + 1:
            continue
        stride_w = input_w / float(w)
        stride_h = input_h / float(h)
        if abs(stride_w - stride_h) > 1e-3:
            continue
        stride = float(stride_w)

        raw = out[0]  # (65, H, W)
        box_raw = raw[: 4 * (reg_max + 1), :, :]  # (64, H, W)
        cls_raw = raw[4 * (reg_max + 1) :, :, :]  # (1, H, W) for 1 class
        cls_logits = cls_raw[0]  # (H, W)
        cls_scores = sigmoid(cls_logits)

        keep = cls_scores >= float(confidence_min)
        if not np.any(keep):
            continue

        ys, xs = np.where(keep)
        conf_sel = cls_scores[ys, xs].astype(np.float32)

        # box_raw -> (4, 16, H, W) -> (H, W, 4, 16)
        box_d = box_raw.reshape(4, reg_max + 1, h, w).transpose(2, 3, 0, 1)
        dist_sel = box_d[ys, xs, :, :]  # (N, 4, 16)
        probs = softmax_last_axis(dist_sel)
        dist = (probs * bins).sum(axis=-1) * stride  # (N, 4) in pixels

        cx = (xs.astype(np.float32) + 0.5) * stride
        cy = (ys.astype(np.float32) + 0.5) * stride
        l = dist[:, 0]
        t = dist[:, 1]
        r = dist[:, 2]
        b = dist[:, 3]

        x1 = np.clip(cx - l, 0.0, float(input_w - 1))
        y1 = np.clip(cy - t, 0.0, float(input_h - 1))
        x2 = np.clip(cx + r, 0.0, float(input_w - 1))
        y2 = np.clip(cy + b, 0.0, float(input_h - 1))

        w_px = np.maximum(0.0, x2 - x1)
        h_px = np.maximum(0.0, y2 - y1)

        for i in range(conf_sel.shape[0]):
            if w_px[i] <= 1.0 or h_px[i] <= 1.0:
                continue
            boxes_xywh.append([float(x1[i]), float(y1[i]), float(w_px[i]), float(h_px[i])])
            scores.append(float(conf_sel[i]))

    if not boxes_xywh:
        return []

    indices = cv2.dnn.NMSBoxes(boxes_xywh, scores, float(confidence_min), float(nms_iou), top_k=int(max_det))
    if indices is None:
        return []
    if isinstance(indices, (tuple, list)) and len(indices) == 0:
        return []

    flat: list[int] = []
    try:
        # OpenCV may return [[i],[j],...] or [i,j,...]
        for item in indices:
            if isinstance(item, (tuple, list, np.ndarray)):
                flat.append(int(item[0]))
            else:
                flat.append(int(item))
    except Exception:
        flat = [int(i) for i in np.array(indices).reshape(-1).tolist()]

    dets: list[tuple[float, float, float, float, float]] = []
    for i in flat:
        x, y, w_px, h_px = boxes_xywh[i]
        conf = scores[i]
        dets.append((x, y, x + w_px, y + h_px, conf))

    return dets


def parse_bool(value: str | None, default: bool = False) -> bool:
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


def clamp_norm(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def clamp_pixel(value: float, max_value: int) -> int:
    if value <= 1.5:
        value = value * max_value
    return int(max(0, min(max_value - 1, round(value))))


def centroid_norm(tracklet: dai.Tracklet) -> tuple[float, float]:
    x1 = float(tracklet.roi.topLeft().x)
    y1 = float(tracklet.roi.topLeft().y)
    x2 = float(tracklet.roi.bottomRight().x)
    y2 = float(tracklet.roi.bottomRight().y)
    return ((x2 - x1) / 2.0 + x1, (y2 - y1) / 2.0 + y1)


def axis_span_from_tracklet(tracklet: dai.Tracklet, axis: str) -> tuple[float, float, float]:
    x1 = float(tracklet.roi.topLeft().x)
    y1 = float(tracklet.roi.topLeft().y)
    x2 = float(tracklet.roi.bottomRight().x)
    y2 = float(tracklet.roi.bottomRight().y)
    if axis == "y":
        axis_min = min(x1, x2)
        axis_max = max(x1, x2)
    else:
        axis_min = min(y1, y2)
        axis_max = max(y1, y2)
    axis_center = (axis_min + axis_max) / 2.0
    return axis_min, axis_max, axis_center


def estimate_head_shoulders_depth_m(
    tracklet: dai.Tracklet,
    depth_frame: np.ndarray | None,
    head_fraction: float,
    min_valid_px: int,
    head_region: str,
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
    if head_region == "bottom":
        y0 = max(y1, y2 - head_h)
        y1_roi, y2_roi = y0, y2
    else:
        y1_roi, y2_roi = y1, min(y2, y1 + head_h)
    if y2_roi <= y1_roi:
        return None

    roi = depth_frame[y1_roi:y2_roi, x1:x2]
    if roi.size == 0:
        return None

    valid = roi[(roi >= 200) & (roi <= 10000)]
    if valid.size < min_valid_px:
        return None

    depth_mm = float(np.median(valid))
    if depth_mm <= 0:
        return None
    return depth_mm / 1000.0


def configure_stereo(stereo: dai.node.StereoDepth, output_size: tuple[int, int]) -> None:
    if hasattr(stereo, "setDefaultProfilePreset"):
        try:
            stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        except Exception:
            pass
    if hasattr(stereo, "setOutputSize"):
        try:
            out_w, out_h = output_size
            stereo.setOutputSize(int(out_w), int(out_h))
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


def classify_zone(axis_value: float, line_a: float, line_b: float, hysteresis: float) -> int:
    if axis_value <= (line_a - hysteresis):
        return -1
    if axis_value >= (line_b + hysteresis):
        return 1
    if (line_a + hysteresis) <= axis_value <= (line_b - hysteresis):
        return 0
    return 0


def transition_to_counts(start_side: int, end_side: int, invert_direction: bool) -> tuple[int, int, str]:
    if start_side == -1 and end_side == 1:
        in_count, out_count, direction = 1, 0, "a_to_b"
    elif start_side == 1 and end_side == -1:
        in_count, out_count, direction = 0, 1, "b_to_a"
    else:
        return 0, 0, "no_cross"
    if invert_direction:
        in_count, out_count = out_count, in_count
        direction = f"{direction}_inverted"
    return in_count, out_count, direction


class Handler(BaseHTTPRequestHandler):
    server_version = "PassengersTransportStrict/1.0"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path in {"/", "/index.html"}:
            self._send_html(qs)
            return
        if path == "/health":
            self._send_health()
            return
        if path == "/snapshot.jpg":
            self._send_snapshot()
            return
        if path == "/mjpeg":
            self._send_mjpeg()
            return
        if path == "/api/preview":
            self._send_preview_toggle(qs)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "not found")

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _state(self) -> SharedState:
        return self.server.shared_state  # type: ignore[attr-defined]

    def _send_html(self, qs: dict[str, list[str]] | None = None) -> None:
        qs = qs or {}
        stats_only = (qs.get("view", [""])[0] or "").strip().lower() in {"stats", "counter"}
        # In stats-only view we auto-disable preview to reduce CPU usage on OPi.
        auto_disable_preview = stats_only

        grid_cls = "grid statsOnly" if stats_only else "grid"
        video_block = (
            ""
            if stats_only
            else "<div class='card' id='video_card'>"
            "<div class='toolbarRow'>"
            "<div class='toolbarLeft'>"
            "<div class='toolbarTitle'>Video</div>"
            "<div class='toolbarHint'>MJPEG stream (optional)</div>"
            "</div>"
            "<div class='toolbarRight'>"
            "<button class='btn' id='preview_toggle_btn'>...</button>"
            "</div></div>"
            "<img id='video_img' src='/mjpeg' alt='strict counting stream'/>"
            "</div>"
        )

        body = (
            "<html><head><meta charset='utf-8'><title>Transport Strict Counting</title>"
            "<style>"
            "body{background:#101217;color:#eceff4;font-family:Arial,sans-serif;margin:12px;}"
            ".head{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;}"
            ".badge{padding:2px 8px;border-radius:999px;background:#293241;color:#fff;font-size:12px;}"
            ".ok{background:#1f7a44;} .warn{background:#9a3d00;}"
            ".grid{display:grid;grid-template-columns:1fr 430px;gap:12px;align-items:start;}"
            ".statsOnly{grid-template-columns:1fr;}"
            ".card{border:1px solid #2d3748;border-radius:8px;padding:10px;background:#151923;}"
            ".stats{display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;font-size:13px;}"
            ".k{color:#9fb3c8;} .v{font-weight:700;}"
            "a{color:#8ec9ff;text-decoration:none;} a:hover{text-decoration:underline;}"
            "img{max-width:100%;border:1px solid #3a4354;border-radius:8px;display:block;}"
            ".btn{border:1px solid #2d3748;background:#101217;color:#eceff4;border-radius:8px;padding:6px 10px;cursor:pointer;}"
            ".btn:hover{border-color:#3a4354;}"
            ".toolbarRow{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:8px;}"
            ".toolbarTitle{font-weight:700;font-size:14px;}"
            ".toolbarHint{color:#9fb3c8;font-size:12px;margin-top:2px;}"
            ".big{display:flex;gap:10px;flex-wrap:wrap;align-items:baseline;}"
            ".bigItem{flex:1 1 120px;border:1px solid #2d3748;border-radius:10px;padding:12px;background:#0f1320;}"
            ".bigK{color:#9fb3c8;font-size:12px;text-transform:uppercase;letter-spacing:0.05em;}"
            ".bigV{font-weight:800;font-size:46px;line-height:1.0;margin-top:4px;}"
            ".bigSub{color:#9fb3c8;font-size:12px;margin-top:6px;}"
            "pre{font-size:11px;white-space:pre-wrap;word-break:break-word;max-height:210px;overflow:auto;}"
            "@media (max-width: 980px){.grid{grid-template-columns:1fr;}}"
            "</style></head><body>"
            "<div class='head'><h2 style='margin:0'>Transport Strict Counting (ID + 2 lines)</h2>"
            "<div><span id='status_badge' class='badge'>loading</span> "
            "<a href='/health' target='_blank'>health json</a> | "
            "<a href='/snapshot.jpg' target='_blank'>snapshot</a> | "
            "<a href='/?view=stats'>stats only</a> | "
            "<a href='/'>full</a></div></div>"
            f"<div class='{grid_cls}'>"
            f"{video_block}"
            "<div class='card'>"
            "<div class='toolbarRow'>"
            "<div class='toolbarLeft'>"
            "<div class='toolbarTitle'>Counter</div>"
            "<div class='toolbarHint'>Live totals (updates every 1s)</div>"
            "</div>"
            "<div class='toolbarRight'>"
            "<button class='btn' id='stats_only_btn'>...</button>"
            "</div></div>"
            "<div class='big'>"
            "<div class='bigItem'><div class='bigK'>IN</div><div class='bigV' id='count_in_big'>-</div><div class='bigSub'>events: <span id='events_total_big'>-</span></div></div>"
            "<div class='bigItem'><div class='bigK'>OUT</div><div class='bigV' id='count_out_big'>-</div><div class='bigSub'>status: <span id='status'>-</span></div></div>"
            "</div>"
            "<div style='height:10px'></div>"
            "<h3 style='margin:0 0 10px 0;font-size:15px'>Live Stats</h3><div class='stats'>"
            "<div class='k'>Status</div><div class='v' id='status'>-</div>"
            "<div class='k'>Device</div><div class='v' id='device'>-</div>"
            "<div class='k'>USB</div><div class='v' id='usb_speed'>-</div>"
            "<div class='k'>Messages</div><div class='v' id='messages'>-</div>"
            "<div class='k'>Tracklets</div><div class='v' id='tracklets_total'>-</div>"
            "<div class='k'>Active tracks</div><div class='v' id='active_tracks'>-</div>"
            "<div class='k'>IN</div><div class='v' id='count_in'>-</div>"
            "<div class='k'>OUT</div><div class='v' id='count_out'>-</div>"
            "<div class='k'>Events</div><div class='v' id='events_total'>-</div>"
            "<div class='k'>Line A/B</div><div class='v'><span id='line_a'>-</span> .. <span id='line_b'>-</span></div>"
            "<div class='k'>Anchor mode</div><div class='v' id='anchor_mode'>-</div>"
            "<div class='k'>Conf min</div><div class='v' id='confidence_min'>-</div>"
            "<div class='k'>Min age</div><div class='v' id='min_track_age'>-</div>"
            "<div class='k'>Lost frames</div><div class='v' id='max_lost_frames'>-</div>"
            "<div class='k'>JPEG q</div><div class='v' id='jpeg_quality'>-</div>"
            "<div class='k'>Preview</div><div class='v'><span id='preview_size'>-</span> @ <span id='preview_fps'>-</span></div>"
            "<div class='k'>Depth pass</div><div class='v' id='depth_pass'>-</div>"
            "<div class='k'>Depth reject</div><div class='v' id='depth_reject'>-</div>"
            "<div class='k'>Depth missing</div><div class='v' id='depth_missing'>-</div>"
            "<div class='k'>Reject conf/age</div><div class='v'><span id='conf_reject'>-</span>/<span id='age_reject'>-</span></div>"
            "<div class='k'>Reject hang/move</div><div class='v'><span id='hang_reject'>-</span>/<span id='move_reject'>-</span></div>"
            "<div class='k'>Reject dup/rearm</div><div class='v'><span id='dup_reject'>-</span>/<span id='rearm_reject'>-</span></div>"
            "<div class='k'>Zone -/0/+</div><div class='v'><span id='zone_neg_hits'>-</span>/<span id='zone_mid_hits'>-</span>/<span id='zone_pos_hits'>-</span></div>"
            "<div class='k'>Middle (center)</div><div class='v' id='middle_entries'>-</div>"
            "<div class='k'>Middle (span)</div><div class='v' id='middle_inferred'>-</div>"
            "<div class='k'>Flip no-middle</div><div class='v' id='zone_flip_no_middle'>-</div>"
            "<div class='k'>IMU updates</div><div class='v' id='imu_updates'>-</div>"
            "<div class='k'>Updated</div><div class='v' id='ts'>-</div>"
            "</div><pre id='raw_json'>{}</pre></div></div>"
            "<script>"
            f"const STATS_ONLY={( 'true' if stats_only else 'false' )};"
            f"const AUTO_DISABLE_PREVIEW={( 'true' if auto_disable_preview else 'false' )};"
            "function setVal(id,val){const el=document.getElementById(id);if(el)el.textContent=(val===undefined||val===null)?'-':String(val);}"
            "function setBadge(status){const b=document.getElementById('status_badge');if(!b)return;b.textContent=status||'unknown';b.className='badge '+((status==='running')?'ok':'warn');}"
            "async function setPreviewEnabled(enabled){"
            " try{const r=await fetch('/api/preview?enabled='+(enabled?'1':'0'),{cache:'no-store'});"
            " await r.json();return true;}catch(e){return false;}"
            "}"
            "function applyPreviewUi(enabled){"
            " const btn=document.getElementById('preview_toggle_btn');"
            " if(btn) btn.textContent = enabled ? 'Video: ON' : 'Video: OFF';"
            " const img=document.getElementById('video_img');"
            " const card=document.getElementById('video_card');"
            " if(!img || !card) return;"
            " if(enabled){ card.style.display='block'; if(!img.src || img.src.endsWith('#off')) img.src='/mjpeg'; }"
            " else { img.src=''; card.style.display='none'; }"
            "}"
            "async function refresh(){try{const r=await fetch('/health',{cache:'no-store'});const j=await r.json();"
            "['status','device','usb_speed','messages','tracklets_total','active_tracks','count_in','count_out','events_total','line_a','line_b','anchor_mode','confidence_min','min_track_age','max_lost_frames','jpeg_quality','preview_size','preview_fps','depth_pass','depth_reject','depth_missing','conf_reject','age_reject','hang_reject','move_reject','dup_reject','rearm_reject','zone_neg_hits','zone_mid_hits','zone_pos_hits','middle_entries','middle_inferred','zone_flip_no_middle','imu_updates','ts'].forEach(k=>setVal(k,j[k]));"
            "setVal('count_in_big',j.count_in);setVal('count_out_big',j.count_out);setVal('events_total_big',j.events_total);"
            "applyPreviewUi(Boolean(j.preview_enabled));"
            "setBadge(j.status);setVal('raw_json',JSON.stringify(j,null,2));}catch(e){setBadge('error');setVal('raw_json','health fetch error: '+e);}}"
            "const statsBtn=document.getElementById('stats_only_btn');"
            "if(statsBtn){statsBtn.textContent = STATS_ONLY ? 'Full view' : 'Stats only';"
            "statsBtn.addEventListener('click',()=>{window.location = STATS_ONLY ? '/' : '/?view=stats';});}"
            "document.getElementById('preview_toggle_btn')?.addEventListener('click',async()=>{"
            " const r=await fetch('/health',{cache:'no-store'}); const j=await r.json();"
            " const next = !Boolean(j.preview_enabled);"
            " const ok = await setPreviewEnabled(next);"
            " if(ok){ applyPreviewUi(next); if(STATS_ONLY && next){ window.location='/'; } }"
            "});"
            "if(AUTO_DISABLE_PREVIEW){ setPreviewEnabled(false).then(()=>refresh()); }"
            "refresh();setInterval(refresh,1000);</script></body></html>"
        ).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_preview_toggle(self, qs: dict[str, list[str]] | None = None) -> None:
        qs = qs or {}
        enabled_raw = (qs.get("enabled", [""])[0] or "").strip().lower()
        if enabled_raw not in {"0", "1", "true", "false", "on", "off", "yes", "no"}:
            self.send_error(HTTPStatus.BAD_REQUEST, "enabled must be 0|1")
            return

        enabled = enabled_raw in {"1", "true", "on", "yes"}
        state = self._state()
        with state.lock:
            state.stats["preview_enabled"] = bool(enabled)
            payload = {"preview_enabled": bool(enabled)}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
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
        state = self._state()
        with state.lock:
            if not bool(state.stats.get("preview_enabled", True)):
                self.send_error(HTTPStatus.CONFLICT, "preview disabled")
                return
        self.send_response(HTTPStatus.OK)
        self.send_header("Age", "0")
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={boundary.decode()}")
        self.end_headers()
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
    parser = argparse.ArgumentParser(description="Transport strict counting (person+tracker+2 lines).")
    parser.add_argument("--env", default="/etc/passengers/passengers.env")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--backend", default="device", help="device (DetectionNetwork+ObjectTracker) | host-yolov8-raw")
    parser.add_argument("--fps", type=float, default=10.0)
    parser.add_argument("--model", default="yolov6-nano")
    parser.add_argument("--tracker-type", default="short_term_imageless")
    parser.add_argument("--track-labels", default="0")
    parser.add_argument("--tracker-occlusion-ratio", type=float, default=0.45)
    parser.add_argument("--tracker-max-objects", type=int, default=10)
    parser.add_argument("--confidence-min", type=float, default=0.65)
    parser.add_argument("--nms-iou", type=float, default=0.5)
    parser.add_argument("--max-det", type=int, default=80)
    parser.add_argument("--match-dist-px", type=float, default=80.0)
    parser.add_argument("--match-iou-min", type=float, default=0.10)
    parser.add_argument("--axis", choices=["x", "y"], default="y")
    parser.add_argument("--axis-pos", type=float, default=0.50)
    parser.add_argument("--axis-hyst", type=float, default=0.04)
    parser.add_argument("--line-gap-norm", type=float, default=0.25)
    parser.add_argument("--anchor-mode", choices=["center", "leading_edge"], default="center")
    parser.add_argument("--min-track-age", type=int, default=8)
    parser.add_argument("--max-lost-frames", type=int, default=5)
    parser.add_argument("--hang-timeout-sec", type=float, default=2.5)
    parser.add_argument("--count-cooldown-sec", type=float, default=1.8)
    parser.add_argument("--per-track-rearm-sec", type=float, default=0.0)
    parser.add_argument("--min-move-norm", type=float, default=0.18)
    parser.add_argument("--invert-direction", action="store_true")
    parser.add_argument("--depth-enable", action="store_true", default=True)
    parser.add_argument("--depth-min-m", type=float, default=0.40)
    parser.add_argument("--depth-max-m", type=float, default=1.50)
    parser.add_argument("--depth-head-fraction", type=float, default=0.45)
    parser.add_argument("--depth-min-valid-px", type=int, default=25)
    parser.add_argument("--depth-head-region", choices=["top", "bottom"], default="top")
    parser.add_argument("--imu-enable", action="store_true", default=True)
    parser.add_argument("--imu-rate-hz", type=int, default=100)
    parser.add_argument("--jpeg-quality", type=int, default=85)
    parser.add_argument("--preview-fps", type=float, default=10.0)
    parser.add_argument("--preview-size", default="640x400")
    parser.add_argument("--depth-output-size", default="320x200")
    parser.add_argument("--model-input-size", default="512x288")
    parser.add_argument("--roi", default="")
    parser.add_argument(
        "--roi-mode",
        choices=["hard", "soft"],
        default="hard",
        help="ROI handling: hard=reset state when leaving ROI; soft=ignore frames outside ROI without resetting",
    )
    parser.add_argument(
        "--infer-middle-from-span",
        action="store_true",
        default=True,
        help="Infer 'middle seen' when bbox spans both lines even if anchor never entered zone=0.",
    )
    parser.add_argument(
        "--no-infer-middle-from-span",
        dest="infer_middle_from_span",
        action="store_false",
        help="Disable middle inference from bbox span (reduces false counts when standing between lines).",
    )
    parser.add_argument(
        "--min-side-frames-before-middle",
        type=int,
        default=2,
        help="Require a track to be stable on one side for N frames before 'arming' middle entry (reduces jitter false counts).",
    )
    parser.add_argument(
        "--max-jump-px",
        type=float,
        default=0.0,
        help="Optional extra cap on host association jump distance in pixels (0 disables; used in host-yolov8-raw).",
    )
    parser.add_argument("--log-interval-sec", type=float, default=10.0)
    return parser


def parse_preview_size(value: str) -> tuple[int, int]:
    s = (value or "").strip().lower().replace(" ", "")
    if "x" not in s:
        raise ValueError("preview-size must be like 640x400")
    w_s, h_s = s.split("x", 1)
    w = int(w_s)
    h = int(h_s)
    if not (160 <= w <= 1920 and 120 <= h <= 1080):
        raise ValueError("preview-size must be in [160x120 .. 1920x1080]")
    return w, h


def parse_roi(value: str) -> tuple[float, float, float, float] | None:
    s = str(value or "").strip().replace(" ", "")
    if not s:
        return None
    parts = [p for p in s.split(",") if p]
    if len(parts) != 4:
        raise ValueError("roi must be like x1,y1,x2,y2 (normalized 0..1)")
    x1, y1, x2, y2 = (float(p) for p in parts)
    if not (0.0 <= x1 < x2 <= 1.0 and 0.0 <= y1 < y2 <= 1.0):
        raise ValueError("roi must satisfy 0<=x1<x2<=1 and 0<=y1<y2<=1")
    return x1, y1, x2, y2


def parse_optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return int(s)


def parse_optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return float(s)


def is_local_blob_model(model: str) -> bool:
    model_s = str(model or "").strip()
    return model_s.lower().endswith(".blob") and Path(model_s).is_file()


def is_local_nnarchive_model(model: str) -> bool:
    model_s = str(model or "").strip()
    if not model_s:
        return False
    path = Path(model_s)
    if not path.is_file():
        return False
    return model_s.endswith(".rvc2.tar.xz") or model_s.endswith(".tar.xz")


def load_runtime(args: argparse.Namespace) -> argparse.Namespace:
    env = load_env_file(args.env)
    args.backend = env.get("CAM_DEPTH_COUNT_BACKEND", args.backend).strip()
    args.fps = float(env.get("CAM_DEPTH_COUNT_FPS", env.get("CAM_COUNTER_FPS", str(args.fps))))
    args.model = env.get("CAM_DEPTH_COUNT_MODEL", env.get("CAM_COUNTER_MODEL", args.model))
    args.track_labels = env.get("CAM_DEPTH_COUNT_TRACK_LABELS", env.get("CAM_COUNTER_TRACK_LABELS", args.track_labels))
    args.tracker_type = env.get(
        "CAM_DEPTH_COUNT_TRACKER_TYPE",
        env.get("CAM_COUNTER_TRACKER_TYPE", args.tracker_type),
    )
    args.tracker_occlusion_ratio = float(
        env.get("CAM_DEPTH_COUNT_TRACKER_OCCLUSION_RATIO", str(args.tracker_occlusion_ratio)),
    )
    args.tracker_max_objects = int(env.get("CAM_DEPTH_COUNT_TRACKER_MAX_OBJECTS", str(args.tracker_max_objects)))
    args.confidence_min = float(
        env.get("CAM_DEPTH_COUNT_CONFIDENCE", env.get("CAM_COUNTER_CONFIDENCE", str(args.confidence_min))),
    )
    args.nms_iou = float(env.get("CAM_DEPTH_COUNT_NMS_IOU", str(args.nms_iou)))
    args.max_det = int(env.get("CAM_DEPTH_COUNT_MAX_DET", str(args.max_det)))
    args.match_dist_px = float(env.get("CAM_DEPTH_COUNT_MATCH_DIST_PX", str(args.match_dist_px)))
    args.match_iou_min = float(env.get("CAM_DEPTH_COUNT_MATCH_IOU_MIN", str(args.match_iou_min)))
    args.dnn_confidence_min = parse_optional_float(env.get("CAM_DEPTH_COUNT_DNN_CONFIDENCE"))
    args.axis = env.get("CAM_DEPTH_COUNT_AXIS", args.axis).strip().lower()
    args.axis_pos = float(env.get("CAM_DEPTH_COUNT_AXIS_POS", str(args.axis_pos)))
    args.axis_hyst = float(env.get("CAM_DEPTH_COUNT_AXIS_HYST", str(args.axis_hyst)))
    args.line_gap_norm = float(env.get("CAM_DEPTH_COUNT_LINE_GAP_NORM", str(args.line_gap_norm)))
    args.anchor_mode = env.get("CAM_DEPTH_COUNT_ANCHOR_MODE", args.anchor_mode).strip().lower()
    args.min_track_age = int(env.get("CAM_DEPTH_COUNT_MIN_TRACK_AGE", str(args.min_track_age)))
    args.max_lost_frames = int(env.get("CAM_DEPTH_COUNT_MAX_LOST_FRAMES", str(args.max_lost_frames)))
    args.hang_timeout_sec = float(env.get("CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC", str(args.hang_timeout_sec)))
    args.count_cooldown_sec = float(env.get("CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC", str(args.count_cooldown_sec)))
    args.per_track_rearm_sec = float(
        env.get("CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC", str(args.per_track_rearm_sec)),
    )
    args.min_move_norm = float(env.get("CAM_DEPTH_COUNT_MIN_MOVE_NORM", str(args.min_move_norm)))
    args.invert_direction = parse_bool(env.get("CAM_DEPTH_COUNT_INVERT"), args.invert_direction)

    args.depth_enable = parse_bool(env.get("CAM_DEPTH_ENABLE"), args.depth_enable)
    args.depth_min_m = float(env.get("CAM_DEPTH_MIN_M", str(args.depth_min_m)))
    args.depth_max_m = float(env.get("CAM_DEPTH_MAX_M", str(args.depth_max_m)))
    args.depth_head_fraction = float(env.get("CAM_DEPTH_HEAD_FRACTION", str(args.depth_head_fraction)))
    args.depth_min_valid_px = int(env.get("CAM_DEPTH_MIN_VALID_PX", str(args.depth_min_valid_px)))
    args.depth_head_region = env.get("CAM_DEPTH_HEAD_REGION", args.depth_head_region).strip().lower()
    args.imu_enable = parse_bool(env.get("CAM_IMU_ENABLE"), args.imu_enable)
    args.imu_rate_hz = int(env.get("CAM_IMU_RATE_HZ", str(args.imu_rate_hz)))
    args.jpeg_quality = int(env.get("CAM_JPEG_QUALITY", str(args.jpeg_quality)))
    args.preview_fps = float(env.get("CAM_PREVIEW_FPS", str(args.preview_fps)))
    args.preview_size = env.get("CAM_PREVIEW_SIZE", args.preview_size)
    args.preview_enabled_default = parse_bool(env.get("CAM_PREVIEW_ENABLED"), default=True)
    args.depth_output_size = env.get("CAM_DEPTH_OUTPUT_SIZE", args.depth_output_size)
    args.model_input_size = env.get("CAM_DEPTH_COUNT_MODEL_INPUT_SIZE", args.model_input_size)
    args.roi = env.get("CAM_DEPTH_COUNT_ROI", args.roi)
    args.roi_mode = env.get("CAM_DEPTH_COUNT_ROI_MODE", args.roi_mode).strip().lower()
    args.infer_middle_from_span = parse_bool(
        env.get("CAM_DEPTH_COUNT_INFER_MIDDLE_FROM_SPAN"),
        default=bool(getattr(args, "infer_middle_from_span", True)),
    )
    args.min_side_frames_before_middle = int(
        env.get("CAM_DEPTH_COUNT_MIN_SIDE_FRAMES_BEFORE_MIDDLE", str(args.min_side_frames_before_middle)),
    )
    args.max_jump_px = float(env.get("CAM_DEPTH_COUNT_MAX_JUMP_PX", str(args.max_jump_px)))
    args.bbox_min_w_px = parse_optional_int(env.get("CAM_DEPTH_COUNT_BBOX_MIN_W_PX"))
    args.bbox_min_h_px = parse_optional_int(env.get("CAM_DEPTH_COUNT_BBOX_MIN_H_PX"))
    args.bbox_max_w_px = parse_optional_int(env.get("CAM_DEPTH_COUNT_BBOX_MAX_W_PX"))
    args.bbox_max_h_px = parse_optional_int(env.get("CAM_DEPTH_COUNT_BBOX_MAX_H_PX"))
    args.bbox_min_area_px2 = parse_optional_int(env.get("CAM_DEPTH_COUNT_BBOX_MIN_AREA_PX2"))
    args.bbox_max_area_px2 = parse_optional_int(env.get("CAM_DEPTH_COUNT_BBOX_MAX_AREA_PX2"))
    args.bbox_min_ar = parse_optional_float(env.get("CAM_DEPTH_COUNT_BBOX_MIN_AR"))
    args.bbox_max_ar = parse_optional_float(env.get("CAM_DEPTH_COUNT_BBOX_MAX_AR"))
    args.bbox_min_wz = parse_optional_float(env.get("CAM_DEPTH_COUNT_BBOX_MIN_WZ"))
    args.bbox_max_wz = parse_optional_float(env.get("CAM_DEPTH_COUNT_BBOX_MAX_WZ"))

    args.debug_bind = env.get("CAM_DEBUG_BIND", args.bind)
    args.debug_port = int(env.get("CAM_DEBUG_PORT", str(args.port)))

    if args.backend not in {"device", "host-yolov8-raw"}:
        raise ValueError("backend must be device|host-yolov8-raw")
    if args.tracker_type not in {
        "short_term_imageless",
        "short_term_kcf",
        "zero_term_imageless",
        "zero_term_color_histogram",
    }:
        raise ValueError(f"invalid tracker type: {args.tracker_type}")
    track_labels: list[int] = []
    for part in str(args.track_labels).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            track_labels.append(int(part))
        except ValueError as exc:
            raise ValueError(f"invalid track label in track-labels: {part!r}") from exc
    if not track_labels:
        raise ValueError("track-labels must contain at least one integer label")
    args.track_labels = track_labels
    if not (0.05 <= args.tracker_occlusion_ratio <= 0.95):
        raise ValueError("tracker-occlusion-ratio must be in [0.05..0.95]")
    if not (1 <= args.tracker_max_objects <= 50):
        raise ValueError("tracker-max-objects must be in [1..50]")
    if args.axis not in {"x", "y"}:
        raise ValueError(f"axis must be x|y (got {args.axis})")
    if not (0.05 <= args.axis_pos <= 0.95):
        raise ValueError(f"axis-pos must be in [0.05..0.95] (got {args.axis_pos})")
    if not (0.0 <= args.axis_hyst <= 0.20):
        raise ValueError(f"axis-hyst must be in [0.00..0.20] (got {args.axis_hyst})")
    if not (0.05 <= args.line_gap_norm <= 0.60):
        raise ValueError(f"line-gap-norm must be in [0.05..0.60] (got {args.line_gap_norm})")
    if args.anchor_mode not in {"center", "leading_edge"}:
        raise ValueError(f"anchor-mode must be center|leading_edge (got {args.anchor_mode})")
    if not (1 <= args.min_track_age <= 100):
        raise ValueError("min-track-age must be in [1..100]")
    if not (1 <= args.max_lost_frames <= 50):
        raise ValueError("max-lost-frames must be in [1..50]")
    if not (0.5 <= args.hang_timeout_sec <= 10.0):
        raise ValueError("hang-timeout-sec must be in [0.5..10.0]")
    if not (0.2 <= args.count_cooldown_sec <= 10.0):
        raise ValueError("count-cooldown-sec must be in [0.2..10.0]")
    if not (0.0 <= args.per_track_rearm_sec <= 30.0):
        raise ValueError("per-track-rearm-sec must be in [0.0..30.0]")
    if not (0.02 <= args.min_move_norm <= 0.80):
        raise ValueError("min-move-norm must be in [0.02..0.80]")
    if not (0.01 <= args.confidence_min <= 0.99):
        raise ValueError("confidence-min must be in [0.01..0.99]")
    if not (0.01 <= float(args.nms_iou) <= 0.99):
        raise ValueError("nms-iou must be in [0.01..0.99]")
    if not (1 <= int(args.max_det) <= 5000):
        raise ValueError("max-det must be in [1..5000]")
    if not (5.0 <= float(args.match_dist_px) <= 500.0):
        raise ValueError("match-dist-px must be in [5..500]")
    if not (0.0 <= float(args.match_iou_min) <= 0.95):
        raise ValueError("match-iou-min must be in [0.0..0.95]")
    if args.dnn_confidence_min is not None and not (0.01 <= float(args.dnn_confidence_min) <= 0.99):
        raise ValueError("dnn-confidence-min must be in [0.01..0.99]")
    if not (10 <= args.jpeg_quality <= 95):
        raise ValueError("jpeg-quality must be in [10..95]")
    if not (1.0 <= args.preview_fps <= 30.0):
        raise ValueError("preview-fps must be in [1..30]")
    _ = parse_preview_size(args.preview_size)
    _ = parse_preview_size(args.depth_output_size)
    _ = parse_preview_size(args.model_input_size)
    args.roi = parse_roi(args.roi)
    if args.roi_mode not in {"hard", "soft"}:
        raise ValueError("roi-mode must be hard|soft")
    if not isinstance(getattr(args, "infer_middle_from_span", True), bool):
        raise ValueError("infer-middle-from-span must be boolean")
    if not (0 <= int(args.min_side_frames_before_middle) <= 20):
        raise ValueError("min-side-frames-before-middle must be in [0..20]")
    if float(args.max_jump_px) < 0.0:
        raise ValueError("max-jump-px must be >= 0.0")
    for name, val in {
        "bbox_min_w_px": args.bbox_min_w_px,
        "bbox_min_h_px": args.bbox_min_h_px,
        "bbox_max_w_px": args.bbox_max_w_px,
        "bbox_max_h_px": args.bbox_max_h_px,
        "bbox_min_area_px2": args.bbox_min_area_px2,
        "bbox_max_area_px2": args.bbox_max_area_px2,
    }.items():
        if val is not None and val < 0:
            raise ValueError(f"{name} must be >= 0")
    for name, val in {
        "bbox_min_ar": args.bbox_min_ar,
        "bbox_max_ar": args.bbox_max_ar,
        "bbox_min_wz": args.bbox_min_wz,
        "bbox_max_wz": args.bbox_max_wz,
    }.items():
        if val is not None and val < 0:
            raise ValueError(f"{name} must be >= 0")
    if args.depth_head_region not in {"top", "bottom"}:
        raise ValueError("depth-head-region must be top|bottom")
    return args


def main() -> int:
    args = load_runtime(build_parser().parse_args())
    line_a = clamp_norm(args.axis_pos - args.line_gap_norm / 2.0, 0.05, 0.95)
    line_b = clamp_norm(args.axis_pos + args.line_gap_norm / 2.0, 0.05, 0.95)
    preview_w, preview_h = parse_preview_size(args.preview_size)
    depth_out_w, depth_out_h = parse_preview_size(args.depth_output_size)
    model_in_w, model_in_h = parse_preview_size(args.model_input_size)
    roi = args.roi

    shared = SharedState(
        lock=threading.Lock(),
        jpg=b"",
        last_frame_ts=0.0,
        preview_frame=None,
        preview_items=[],
        stats={
            "status": "starting",
            "device": "",
            "usb_speed": "",
            "preview_enabled": bool(getattr(args, "preview_enabled_default", True)),
            "preview_frames": 0,
            "messages": 0,
            "tracklets_total": 0,
            "active_tracks": 0,
            "events_total": 0,
            "count_in": 0,
            "count_out": 0,
            "axis": args.axis,
            "line_a": round(line_a, 4),
            "line_b": round(line_b, 4),
            "line_gap_norm": args.line_gap_norm,
            "anchor_mode": args.anchor_mode,
            "confidence_min": args.confidence_min,
            "min_track_age": args.min_track_age,
            "max_lost_frames": args.max_lost_frames,
            "hang_timeout_sec": args.hang_timeout_sec,
            "count_cooldown_sec": args.count_cooldown_sec,
            "per_track_rearm_sec": args.per_track_rearm_sec,
            "min_move_norm": args.min_move_norm,
            "depth_pass": 0,
            "depth_reject": 0,
            "depth_missing": 0,
            "conf_reject": 0,
            "age_reject": 0,
            "hang_reject": 0,
            "move_reject": 0,
            "dup_reject": 0,
            "rearm_reject": 0,
            "lost_prune": 0,
            "zone_neg_hits": 0,
            "zone_mid_hits": 0,
            "zone_pos_hits": 0,
            "zone_flip_no_middle": 0,
            "middle_entries": 0,
            "middle_inferred": 0,
            "fps": args.fps,
            "backend": args.backend,
            "model": args.model,
            "tracker_type": args.tracker_type,
            "track_labels": args.track_labels,
            "tracker_occlusion_ratio": args.tracker_occlusion_ratio,
            "tracker_max_objects": args.tracker_max_objects,
            "nms_iou": args.nms_iou,
            "max_det": args.max_det,
            "match_dist_px": args.match_dist_px,
            "match_iou_min": args.match_iou_min,
            "jpeg_quality": args.jpeg_quality,
            "preview_fps": args.preview_fps,
            "preview_size": f"{preview_w}x{preview_h}",
            "depth_output_size": f"{depth_out_w}x{depth_out_h}",
            "model_input_size": f"{model_in_w}x{model_in_h}",
            "roi": "" if roi is None else f"{roi[0]:.3f},{roi[1]:.3f},{roi[2]:.3f},{roi[3]:.3f}",
            "roi_mode": args.roi_mode,
            "infer_middle_from_span": bool(getattr(args, "infer_middle_from_span", True)),
            "min_side_frames_before_middle": int(args.min_side_frames_before_middle),
            "max_jump_px": float(args.max_jump_px),
            "roi_reject": 0,
            "middle_reject_side_frames": 0,
            "bbox_min_w_px": args.bbox_min_w_px,
            "bbox_min_h_px": args.bbox_min_h_px,
            "bbox_max_w_px": args.bbox_max_w_px,
            "bbox_max_h_px": args.bbox_max_h_px,
            "bbox_min_area_px2": args.bbox_min_area_px2,
            "bbox_max_area_px2": args.bbox_max_area_px2,
            "bbox_min_ar": args.bbox_min_ar,
            "bbox_max_ar": args.bbox_max_ar,
            "bbox_min_wz": args.bbox_min_wz,
            "bbox_max_wz": args.bbox_max_wz,
            "bbox_reject_size": 0,
            "bbox_reject_ar": 0,
            "bbox_reject_wz": 0,
            "depth_min_m": args.depth_min_m,
            "depth_max_m": args.depth_max_m,
            "depth_head_region": args.depth_head_region,
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
            "bind": args.debug_bind,
            "port": args.debug_port,
        },
    )

    httpd = ThreadingHTTPServer((args.debug_bind, args.debug_port), Handler)
    httpd.shared_state = shared  # type: ignore[attr-defined]
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    print(
        f"transport-strict: listening http://{args.debug_bind}:{args.debug_port} "
        f"(use SSH tunnel if bind=127.0.0.1)",
        flush=True,
    )

    stop_event = threading.Event()

    def preview_worker() -> None:
        last_send_ts = 0.0
        while not stop_event.is_set():
            with shared.lock:
                preview_enabled = bool(shared.stats.get("preview_enabled", True))
                preview_fps = float(shared.stats.get("preview_fps", args.preview_fps))
                jpeg_quality = int(shared.stats.get("jpeg_quality", args.jpeg_quality))
                axis = str(shared.stats.get("axis", args.axis))
                line_a_norm = float(shared.stats.get("line_a", line_a))
                line_b_norm = float(shared.stats.get("line_b", line_b))
                in_count = int(shared.stats.get("count_in", 0))
                out_count = int(shared.stats.get("count_out", 0))
                event_count = int(shared.stats.get("events_total", 0))
                imu_acc_norm = shared.stats.get("imu_acc_norm")
                imu_gyro_norm = shared.stats.get("imu_gyro_norm")
                items = list(shared.preview_items)
                frame = shared.preview_frame

            if not preview_enabled or preview_fps <= 0.0 or frame is None:
                time.sleep(0.12)
                continue

            now = time.monotonic()
            min_interval = 1.0 / max(0.1, preview_fps)
            if last_send_ts > 0.0 and (now - last_send_ts) < min_interval:
                time.sleep(0.02)
                continue

            draw = frame.copy()
            height, width = draw.shape[:2]
            if axis == "y":
                line_ax = clamp_pixel(line_a_norm, width)
                line_bx = clamp_pixel(line_b_norm, width)
                cv2.line(draw, (line_ax, 0), (line_ax, height - 1), (80, 180, 255), 2)
                cv2.line(draw, (line_bx, 0), (line_bx, height - 1), (255, 220, 80), 2)
            else:
                line_ay = clamp_pixel(line_a_norm, height)
                line_by = clamp_pixel(line_b_norm, height)
                cv2.line(draw, (0, line_ay), (width - 1, line_ay), (80, 180, 255), 2)
                cv2.line(draw, (0, line_by), (width - 1, line_by), (255, 220, 80), 2)

            for item in items:
                try:
                    x1 = int(item["x1"])
                    y1 = int(item["y1"])
                    x2 = int(item["x2"])
                    y2 = int(item["y2"])
                    color = item.get("color", (0, 200, 0))
                    label = str(item.get("label", ""))
                except Exception:
                    continue
                cv2.rectangle(draw, (x1, y1), (x2, y2), color, 2)
                if label:
                    cv2.putText(draw, label, (x1 + 2, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1)

            overlay = f"IN={in_count} OUT={out_count} events={event_count}"
            cv2.putText(draw, overlay, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (255, 255, 255), 1)

            if isinstance(imu_acc_norm, (int, float)) and isinstance(imu_gyro_norm, (int, float)):
                cv2.putText(
                    draw,
                    f"IMU a={float(imu_acc_norm):.2f} g={float(imu_gyro_norm):.2f}",
                    (10, 42),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (180, 255, 180),
                    1,
                )

            ok, encoded = cv2.imencode(
                ".jpg",
                draw,
                [int(cv2.IMWRITE_JPEG_QUALITY), int(max(10, min(95, jpeg_quality)))],
            )
            if ok:
                with shared.lock:
                    shared.jpg = encoded.tobytes()
                    shared.last_frame_ts = now
                    shared.stats["preview_frames"] = int(shared.stats.get("preview_frames", 0)) + 1
                last_send_ts = now
            else:
                time.sleep(0.05)

    preview_thread = threading.Thread(target=preview_worker, daemon=True)
    preview_thread.start()

    tracks: dict[int, TrackCrossState] = {}
    overlay_meta: dict[int, dict[str, Any]] = {}
    last_tracklets: list[dai.Tracklet] = []
    host_tracks: dict[int, HostTrackState] = {}
    next_host_track_id = 1
    latest_depth_frame: np.ndarray | None = None
    in_count = 0
    out_count = 0
    event_count = 0
    last_log = time.monotonic()
    imu_acc_norm = None
    imu_gyro_norm = None
    last_preview_ts = 0.0

    with dai.Pipeline() as pipeline:
        camera = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_A)
        backend = str(args.backend).strip()
        using_local_archive = is_local_nnarchive_model(args.model)
        using_local_blob = is_local_blob_model(args.model)
        local_model_kind = "zoo"
        track_queue = None
        nn_queue = None

        if backend == "device":
            detection_network = pipeline.create(dai.node.DetectionNetwork)
            if using_local_archive:
                local_model_kind = "archive"
                nn_archive = dai.NNArchive(args.model)
                detection_network.build(
                    camera,
                    nn_archive,
                    fps=args.fps,
                )
            elif using_local_blob:
                local_model_kind = "blob"
                camera.requestOutput(
                    size=(model_in_w, model_in_h),
                    type=dai.ImgFrame.Type.BGR888p,
                    fps=args.fps,
                ).link(detection_network.input)
                detection_network.setBlobPath(args.model)
            else:
                detection_network.build(
                    camera,
                    dai.NNModelDescription(args.model),
                    fps=args.fps,
                )

            dnn_conf = args.dnn_confidence_min
            if dnn_conf is None:
                dnn_conf = float(args.confidence_min) * 0.75
            detection_network.setConfidenceThreshold(max(0.01, min(0.99, float(dnn_conf))))

            tracker = pipeline.create(dai.node.ObjectTracker)
            tracker.setDetectionLabelsToTrack(list(args.track_labels))
            tracker.setTrackerType(tracker_type_from_name(args.tracker_type))
            tracker.setTrackerIdAssignmentPolicy(dai.TrackerIdAssignmentPolicy.UNIQUE_ID)
            tracker.setTrackletBirthThreshold(max(1, args.min_track_age // 2))
            tracker.setTrackletMaxLifespan(max(10, args.max_lost_frames * 3))
            tracker.setOcclusionRatioThreshold(float(args.tracker_occlusion_ratio))
            if hasattr(tracker, "setMaxObjectsToTrack"):
                try:
                    tracker.setMaxObjectsToTrack(int(args.tracker_max_objects))
                except Exception:
                    pass

            detection_network.out.link(tracker.inputDetections)
            detection_network.passthrough.link(tracker.inputDetectionFrame)
            detection_network.passthrough.link(tracker.inputTrackerFrame)
            track_queue = tracker.out.createOutputQueue(maxSize=6, blocking=False)
        else:
            if not (using_local_archive or using_local_blob):
                raise SystemExit("host-yolov8-raw backend requires CAM_DEPTH_COUNT_MODEL to be a local file (.tar.xz/.blob)")
            if using_local_archive:
                local_model_kind = "archive"
            elif using_local_blob:
                local_model_kind = "blob"
            nn = pipeline.create(dai.node.NeuralNetwork)
            camera.requestOutput(
                size=(model_in_w, model_in_h),
                type=dai.ImgFrame.Type.BGR888p,
                fps=args.fps,
            ).link(nn.input)
            if using_local_archive:
                nn.setNNArchive(dai.NNArchive(args.model))
            else:
                nn.setBlobPath(args.model)
            nn_queue = nn.out.createOutputQueue(maxSize=4, blocking=False)

        preview_stream_fps = max(1.0, min(float(args.fps), float(args.preview_fps)))
        frame_queue = camera.requestOutput(
            size=(preview_w, preview_h),
            type=dai.ImgFrame.Type.BGR888p,
            fps=preview_stream_fps,
        ).createOutputQueue(
            maxSize=6,
            blocking=False,
        )

        depth_queue = None
        if args.depth_enable:
            left_camera = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_B)
            right_camera = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_C)
            stereo = pipeline.create(dai.node.StereoDepth)
            configure_stereo(stereo, output_size=(depth_out_w, depth_out_h))
            left_camera.requestOutput(size=(640, 400), type=dai.ImgFrame.Type.RAW8, fps=args.fps).link(stereo.left)
            right_camera.requestOutput(size=(640, 400), type=dai.ImgFrame.Type.RAW8, fps=args.fps).link(stereo.right)
            depth_queue = stereo.depth.createOutputQueue(maxSize=4, blocking=False)

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
            except Exception as exc:
                print(f"transport-strict: imu disabled: {exc}", flush=True)
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
            f"transport-strict: device={device.getDeviceName()} usb_speed={device.getUsbSpeed().name} "
            f"axis={args.axis} line_a={line_a:.3f} line_b={line_b:.3f} conf_min={args.confidence_min:.2f} "
            f"anchor={args.anchor_mode} min_age={args.min_track_age} max_lost={args.max_lost_frames} "
            f"cooldown={args.count_cooldown_sec:.2f}s rearm={args.per_track_rearm_sec:.2f}s "
            f"depth={args.depth_min_m:.2f}-{args.depth_max_m:.2f}m "
            f"jpeg_q={args.jpeg_quality} preview={preview_w}x{preview_h}@{args.preview_fps:.1f} "
            f"depth_out={depth_out_w}x{depth_out_h} model_input={model_in_w}x{model_in_h} "
            f"model_kind={local_model_kind} backend={backend}",
            flush=True,
        )

        try:
            while pipeline.isRunning():
                now = time.monotonic()

                new_acc_norm, new_gyro_norm = poll_imu_queue(imu_queue, shared)
                if new_acc_norm is not None:
                    imu_acc_norm = new_acc_norm
                if new_gyro_norm is not None:
                    imu_gyro_norm = new_gyro_norm

                if depth_queue is not None:
                    depth_msg = depth_queue.tryGet()
                    if depth_msg is not None:
                        latest_depth_frame = depth_msg.getFrame()

                incoming_tracklets: list[Any] | None = None
                if backend == "device":
                    track_msg = track_queue.tryGet() if track_queue is not None else None
                    if track_msg is not None:
                        incoming_tracklets = list(track_msg.tracklets)
                else:
                    nn_msg = nn_queue.tryGet() if nn_queue is not None else None
                    if nn_msg is not None:
                        det_conf = args.dnn_confidence_min
                        if det_conf is None:
                            det_conf = float(args.confidence_min) * 0.75
                        layer_names = list(getattr(nn_msg, "getAllLayerNames", lambda: [])())
                        outputs: list[np.ndarray] = []
                        for name in layer_names:
                            try:
                                outputs.append(np.asarray(nn_msg.getTensor(name), dtype=np.float32))
                            except Exception:
                                continue

                        dets = decode_yolov8_dfl_outputs(
                            outputs,
                            input_size=(model_in_w, model_in_h),
                            confidence_min=float(det_conf),
                            nms_iou=float(args.nms_iou),
                            max_det=int(args.max_det),
                        )

                        detections: list[tuple[float, float, float, float, float]] = []
                        for x1, y1, x2, y2, conf in dets:
                            x1n = max(0.0, min(1.0, float(x1) / float(model_in_w)))
                            y1n = max(0.0, min(1.0, float(y1) / float(model_in_h)))
                            x2n = max(0.0, min(1.0, float(x2) / float(model_in_w)))
                            y2n = max(0.0, min(1.0, float(y2) / float(model_in_h)))
                            if x2n <= x1n or y2n <= y1n:
                                continue
                            detections.append((x1n, y1n, x2n, y2n, float(conf)))

                        det_centers = [((d[0] + d[2]) / 2.0, (d[1] + d[3]) / 2.0) for d in detections]
                        det_boxes = [(d[0], d[1], d[2], d[3]) for d in detections]

                        matched_track_to_det: dict[int, int] = {}
                        used_tracks: set[int] = set()
                        used_dets: set[int] = set()

                        # Stage 1: IoU-first matching (reduces ID swaps on crossing).
                        iou_pairs: list[tuple[float, int, int]] = []
                        for tid, st in host_tracks.items():
                            t_box = (float(st.x1n), float(st.y1n), float(st.x2n), float(st.y2n))
                            for di, d_box in enumerate(det_boxes):
                                iou = bbox_iou(t_box, d_box)
                                if iou >= float(args.match_iou_min):
                                    iou_pairs.append((iou, tid, di))
                        iou_pairs.sort(key=lambda row: row[0], reverse=True)
                        for _, tid, di in iou_pairs:
                            if tid in used_tracks or di in used_dets:
                                continue
                            matched_track_to_det[tid] = di
                            used_tracks.add(tid)
                            used_dets.add(di)

                        # Stage 2: centroid distance matching for remaining.
                        jump_cap_px = float(args.match_dist_px)
                        if float(args.max_jump_px) > 0.0:
                            jump_cap_px = min(jump_cap_px, float(args.max_jump_px))
                        dist_pairs: list[tuple[float, int, int]] = []
                        for tid, st in host_tracks.items():
                            if tid in used_tracks:
                                continue
                            for di, (cxn, cyn) in enumerate(det_centers):
                                if di in used_dets:
                                    continue
                                dist_px = float(
                                    (((st.cxn - cxn) * float(model_in_w)) ** 2 + ((st.cyn - cyn) * float(model_in_h)) ** 2)
                                    ** 0.5
                                )
                                if dist_px <= float(jump_cap_px):
                                    dist_pairs.append((dist_px, tid, di))
                        dist_pairs.sort(key=lambda row: row[0])
                        for _, tid, di in dist_pairs:
                            if tid in used_tracks or di in used_dets:
                                continue
                            matched_track_to_det[tid] = di
                            used_tracks.add(tid)
                            used_dets.add(di)

                        updated_ids: set[int] = set()
                        for tid, di in matched_track_to_det.items():
                            x1n, y1n, x2n, y2n, conf = detections[di]
                            cxn, cyn = det_centers[di]
                            st = host_tracks[tid]
                            st.last_seen = now
                            st.x1n = x1n
                            st.y1n = y1n
                            st.x2n = x2n
                            st.y2n = y2n
                            st.cxn = cxn
                            st.cyn = cyn
                            st.confidence = float(conf)
                            st.age += 1
                            updated_ids.add(tid)

                        # Create new tracks for unmatched detections
                        for di in range(len(detections)):
                            if di in used_dets:
                                continue
                            x1n, y1n, x2n, y2n, conf = detections[di]
                            cxn, cyn = det_centers[di]
                            tid = next_host_track_id
                            next_host_track_id += 1
                            host_tracks[tid] = HostTrackState(
                                last_seen=now,
                                x1n=x1n,
                                y1n=y1n,
                                x2n=x2n,
                                y2n=y2n,
                                cxn=cxn,
                                cyn=cyn,
                                confidence=float(conf),
                                age=1,
                            )
                            updated_ids.add(tid)

                        # Prune stale host tracks and linked overlay/cross-states
                        lost_timeout_sec = float(args.max_lost_frames) / max(1.0, float(args.fps))
                        stale_ids = [tid for tid, st in host_tracks.items() if (now - float(st.last_seen)) > lost_timeout_sec]
                        for tid in stale_ids:
                            host_tracks.pop(tid, None)
                            tracks.pop(tid, None)
                            overlay_meta.pop(tid, None)
                        if stale_ids:
                            with shared.lock:
                                shared.stats["lost_prune"] = int(shared.stats["lost_prune"]) + len(stale_ids)

                        # Build "tracklets-like" objects for the existing strict logic/drawing.
                        incoming_tracklets = []
                        for tid in sorted(updated_ids):
                            st = host_tracks.get(tid)
                            if st is None:
                                continue
                            incoming_tracklets.append(
                                HostTrackletLike(
                                    tid=tid,
                                    x1n=float(st.x1n),
                                    y1n=float(st.y1n),
                                    x2n=float(st.x2n),
                                    y2n=float(st.y2n),
                                    confidence=float(st.confidence),
                                    age=int(st.age),
                                )
                            )

                if incoming_tracklets is not None:
                    last_tracklets = list(incoming_tracklets)
                    with shared.lock:
                        shared.stats["messages"] = int(shared.stats["messages"]) + 1

                    for tracklet in last_tracklets:
                        tid = int(tracklet.id)
                        if tracklet.status in {dai.Tracklet.TrackingStatus.LOST, dai.Tracklet.TrackingStatus.REMOVED}:
                            tracks.pop(tid, None)
                            overlay_meta.pop(tid, None)
                            continue
                        if tracklet.status not in {dai.Tracklet.TrackingStatus.NEW, dai.Tracklet.TrackingStatus.TRACKED}:
                            continue

                        with shared.lock:
                            shared.stats["tracklets_total"] = int(shared.stats["tracklets_total"]) + 1

                        confidence = float(getattr(tracklet.srcImgDetection, "confidence", 0.0))
                        track_age = int(getattr(tracklet, "age", 0))
                        state = tracks.get(tid)

                        if roi is not None:
                            cx, cy = centroid_norm(tracklet)
                            roi_ok = (roi[0] <= cx <= roi[2]) and (roi[1] <= cy <= roi[3])
                            if not roi_ok:
                                with shared.lock:
                                    shared.stats["roi_reject"] = int(shared.stats.get("roi_reject", 0)) + 1
                                if state is not None:
                                    state.last_seen = now
                                    state.age = track_age
                                    if args.roi_mode == "hard":
                                        state.side_start = None
                                        state.seen_middle = False
                                        state.entered_middle_ts = None
                                overlay_meta[tid] = {
                                    "zone": "roi_out",
                                    "depth_ok": False,
                                    "depth_m": None,
                                    "confidence": confidence,
                                    "conf_ok": confidence >= args.confidence_min,
                                    "age": track_age,
                                    "anchor_axis": None,
                                    "span_mid": False,
                                }
                                continue

                        x1n = float(tracklet.roi.topLeft().x)
                        y1n = float(tracklet.roi.topLeft().y)
                        x2n = float(tracklet.roi.bottomRight().x)
                        y2n = float(tracklet.roi.bottomRight().y)
                        w_norm = abs(x2n - x1n)
                        h_norm = abs(y2n - y1n)
                        bbox_w_px = float(w_norm) * float(model_in_w)
                        bbox_h_px = float(h_norm) * float(model_in_h)
                        bbox_area_px2 = bbox_w_px * bbox_h_px
                        bbox_ar = None if bbox_h_px <= 1e-6 else (bbox_w_px / bbox_h_px)

                        bbox_size_ok = True
                        if args.bbox_min_w_px is not None and bbox_w_px < float(args.bbox_min_w_px):
                            bbox_size_ok = False
                        if args.bbox_min_h_px is not None and bbox_h_px < float(args.bbox_min_h_px):
                            bbox_size_ok = False
                        if args.bbox_max_w_px is not None and bbox_w_px > float(args.bbox_max_w_px):
                            bbox_size_ok = False
                        if args.bbox_max_h_px is not None and bbox_h_px > float(args.bbox_max_h_px):
                            bbox_size_ok = False
                        if args.bbox_min_area_px2 is not None and bbox_area_px2 < float(args.bbox_min_area_px2):
                            bbox_size_ok = False
                        if args.bbox_max_area_px2 is not None and bbox_area_px2 > float(args.bbox_max_area_px2):
                            bbox_size_ok = False
                        if not bbox_size_ok:
                            with shared.lock:
                                shared.stats["bbox_reject_size"] = int(shared.stats.get("bbox_reject_size", 0)) + 1
                            if state is not None:
                                state.last_seen = now
                                state.age = track_age
                                state.side_start = None
                                state.seen_middle = False
                                state.entered_middle_ts = None
                            overlay_meta[tid] = {
                                "zone": "bbox_size",
                                "depth_ok": False,
                                "depth_m": None,
                                "confidence": confidence,
                                "conf_ok": confidence >= args.confidence_min,
                                "age": track_age,
                                "anchor_axis": None,
                                "span_mid": False,
                                "bbox_w_px": bbox_w_px,
                                "bbox_h_px": bbox_h_px,
                                "bbox_ar": bbox_ar,
                                "bbox_wz": None,
                                "bbox_size_ok": False,
                                "bbox_ar_ok": True,
                                "bbox_wz_ok": True,
                            }
                            continue

                        bbox_ar_ok = True
                        if args.bbox_min_ar is not None or args.bbox_max_ar is not None:
                            if bbox_ar is None:
                                bbox_ar_ok = False
                            else:
                                if args.bbox_min_ar is not None and bbox_ar < float(args.bbox_min_ar):
                                    bbox_ar_ok = False
                                if args.bbox_max_ar is not None and bbox_ar > float(args.bbox_max_ar):
                                    bbox_ar_ok = False
                        if not bbox_ar_ok:
                            with shared.lock:
                                shared.stats["bbox_reject_ar"] = int(shared.stats.get("bbox_reject_ar", 0)) + 1
                            if state is not None:
                                state.last_seen = now
                                state.age = track_age
                                state.side_start = None
                                state.seen_middle = False
                                state.entered_middle_ts = None
                            overlay_meta[tid] = {
                                "zone": "bbox_ar",
                                "depth_ok": False,
                                "depth_m": None,
                                "confidence": confidence,
                                "conf_ok": confidence >= args.confidence_min,
                                "age": track_age,
                                "anchor_axis": None,
                                "span_mid": False,
                                "bbox_w_px": bbox_w_px,
                                "bbox_h_px": bbox_h_px,
                                "bbox_ar": bbox_ar,
                                "bbox_wz": None,
                                "bbox_size_ok": True,
                                "bbox_ar_ok": False,
                                "bbox_wz_ok": True,
                            }
                            continue

                        axis_min, axis_max, axis_center = axis_span_from_tracklet(tracklet, args.axis)
                        axis_value = axis_center
                        if args.anchor_mode == "leading_edge" and state is not None and state.side_start in {-1, 1}:
                            axis_value = axis_max if state.side_start == -1 else axis_min
                        zone = classify_zone(axis_value, line_a, line_b, args.axis_hyst)
                        span_mid = (axis_min <= (line_b - args.axis_hyst)) and (axis_max >= (line_a + args.axis_hyst))
                        with shared.lock:
                            if zone == -1:
                                shared.stats["zone_neg_hits"] = int(shared.stats["zone_neg_hits"]) + 1
                            elif zone == 0:
                                shared.stats["zone_mid_hits"] = int(shared.stats["zone_mid_hits"]) + 1
                            else:
                                shared.stats["zone_pos_hits"] = int(shared.stats["zone_pos_hits"]) + 1

                        depth_m = None
                        depth_ok = True
                        if args.depth_enable:
                            depth_m = estimate_head_shoulders_depth_m(
                                tracklet,
                                latest_depth_frame,
                                args.depth_head_fraction,
                                args.depth_min_valid_px,
                                args.depth_head_region,
                            )
                            if depth_m is None:
                                depth_ok = False
                                with shared.lock:
                                    shared.stats["depth_missing"] = int(shared.stats["depth_missing"]) + 1
                            elif depth_m < args.depth_min_m or depth_m > args.depth_max_m:
                                depth_ok = False
                                with shared.lock:
                                    shared.stats["depth_reject"] = int(shared.stats["depth_reject"]) + 1
                            else:
                                with shared.lock:
                                    shared.stats["depth_pass"] = int(shared.stats["depth_pass"]) + 1

                        bbox_wz = None
                        bbox_wz_ok = True
                        if args.bbox_min_wz is not None or args.bbox_max_wz is not None:
                            if depth_m is None:
                                bbox_wz_ok = False
                            else:
                                bbox_wz = float(bbox_w_px) * float(depth_m)
                                if args.bbox_min_wz is not None and bbox_wz < float(args.bbox_min_wz):
                                    bbox_wz_ok = False
                                if args.bbox_max_wz is not None and bbox_wz > float(args.bbox_max_wz):
                                    bbox_wz_ok = False
                            if not bbox_wz_ok:
                                with shared.lock:
                                    shared.stats["bbox_reject_wz"] = int(shared.stats.get("bbox_reject_wz", 0)) + 1

                        conf_ok = confidence >= args.confidence_min
                        if not conf_ok:
                            with shared.lock:
                                shared.stats["conf_reject"] = int(shared.stats["conf_reject"]) + 1

                        if state is None:
                            side_frames = 1 if zone in {-1, 1} else 0
                            middle_frames = 1 if zone == 0 else 0
                            state = TrackCrossState(
                                last_seen=now,
                                side_start=zone if zone in {-1, 1} else None,
                                first_side_axis=axis_value,
                                seen_middle=(zone == 0),
                                entered_middle_ts=(now if zone == 0 else None),
                                side_frames=side_frames,
                                middle_frames=middle_frames,
                                last_event_ts=0.0,
                                last_event_direction=None,
                                age=track_age,
                            )
                            tracks[tid] = state
                        else:
                            state.last_seen = now
                            state.age = track_age

                        overlay_meta[tid] = {
                            "zone": zone,
                            "depth_ok": depth_ok,
                            "depth_m": depth_m,
                            "confidence": confidence,
                            "conf_ok": conf_ok,
                            "age": track_age,
                            "anchor_axis": axis_value,
                            "span_mid": span_mid,
                            "bbox_w_px": bbox_w_px,
                            "bbox_h_px": bbox_h_px,
                            "bbox_ar": bbox_ar,
                            "bbox_wz": bbox_wz,
                            "bbox_size_ok": bbox_size_ok,
                            "bbox_ar_ok": bbox_ar_ok,
                            "bbox_wz_ok": bbox_wz_ok,
                        }

                        if not conf_ok or not depth_ok or not bbox_wz_ok or zone is None:
                            continue

                        if zone == 0:
                            state.middle_frames = int(getattr(state, "middle_frames", 0)) + 1
                            if not state.seen_middle:
                                min_side_frames = int(args.min_side_frames_before_middle)
                                if state.side_start is not None and int(getattr(state, "side_frames", 0)) >= min_side_frames:
                                    state.seen_middle = True
                                    state.entered_middle_ts = now
                                    with shared.lock:
                                        shared.stats["middle_entries"] = int(shared.stats["middle_entries"]) + 1
                                else:
                                    with shared.lock:
                                        shared.stats["middle_reject_side_frames"] = int(
                                            shared.stats.get("middle_reject_side_frames", 0),
                                        ) + 1
                            elif state.entered_middle_ts is not None and (now - state.entered_middle_ts) > args.hang_timeout_sec:
                                with shared.lock:
                                    shared.stats["hang_reject"] = int(shared.stats["hang_reject"]) + 1
                                state.side_start = None
                                state.seen_middle = False
                                state.entered_middle_ts = None
                                state.side_frames = 0
                                state.middle_frames = 0
                            continue

                        if state.side_start is None:
                            state.side_start = zone
                            state.first_side_axis = axis_value
                            state.seen_middle = False
                            state.entered_middle_ts = None
                            state.side_frames = 1
                            state.middle_frames = 0
                            continue

                        if zone == state.side_start:
                            if state.seen_middle:
                                state.seen_middle = False
                                state.entered_middle_ts = None
                                state.middle_frames = 0
                            state.first_side_axis = axis_value
                            state.side_frames = int(getattr(state, "side_frames", 0)) + 1
                            continue

                        if not state.seen_middle:
                            if span_mid and bool(getattr(args, "infer_middle_from_span", True)):
                                with shared.lock:
                                    shared.stats["middle_inferred"] = int(shared.stats["middle_inferred"]) + 1
                                state.seen_middle = True
                                state.entered_middle_ts = now
                                state.middle_frames = 1
                            else:
                                with shared.lock:
                                    shared.stats["zone_flip_no_middle"] = int(shared.stats["zone_flip_no_middle"]) + 1
                                state.side_start = zone
                                state.first_side_axis = axis_value
                                state.entered_middle_ts = None
                                state.side_frames = 1
                                state.middle_frames = 0
                                continue

                        in_inc, out_inc, direction = transition_to_counts(state.side_start, zone, args.invert_direction)
                        if in_inc == 0 and out_inc == 0:
                            state.side_start = zone
                            state.first_side_axis = axis_value
                            state.seen_middle = False
                            state.entered_middle_ts = None
                            state.side_frames = 1
                            state.middle_frames = 0
                            continue

                        if track_age < args.min_track_age:
                            with shared.lock:
                                shared.stats["age_reject"] = int(shared.stats["age_reject"]) + 1
                            state.side_start = zone
                            state.first_side_axis = axis_value
                            state.seen_middle = False
                            state.entered_middle_ts = None
                            state.side_frames = 1
                            state.middle_frames = 0
                            continue

                        if state.entered_middle_ts is not None and (now - state.entered_middle_ts) > args.hang_timeout_sec:
                            with shared.lock:
                                shared.stats["hang_reject"] = int(shared.stats["hang_reject"]) + 1
                            state.side_start = zone
                            state.first_side_axis = axis_value
                            state.seen_middle = False
                            state.entered_middle_ts = None
                            state.side_frames = 1
                            state.middle_frames = 0
                            continue

                        if (
                            args.per_track_rearm_sec > 0.0
                            and state.last_event_direction is not None
                            and (now - state.last_event_ts) < args.per_track_rearm_sec
                        ):
                            with shared.lock:
                                shared.stats["rearm_reject"] = int(shared.stats["rearm_reject"]) + 1
                            state.side_start = zone
                            state.first_side_axis = axis_value
                            state.seen_middle = False
                            state.entered_middle_ts = None
                            state.side_frames = 1
                            state.middle_frames = 0
                            continue

                        if (now - state.last_event_ts) < args.count_cooldown_sec:
                            with shared.lock:
                                shared.stats["dup_reject"] = int(shared.stats["dup_reject"]) + 1
                            state.side_start = zone
                            state.first_side_axis = axis_value
                            state.seen_middle = False
                            state.entered_middle_ts = None
                            state.side_frames = 1
                            state.middle_frames = 0
                            continue

                        if abs(axis_value - state.first_side_axis) < args.min_move_norm:
                            with shared.lock:
                                shared.stats["move_reject"] = int(shared.stats["move_reject"]) + 1
                            state.side_start = zone
                            state.first_side_axis = axis_value
                            state.seen_middle = False
                            state.entered_middle_ts = None
                            state.side_frames = 1
                            state.middle_frames = 0
                            continue

                        if in_inc > 0 or out_inc > 0:
                            in_count += in_inc
                            out_count += out_inc
                            event_count += 1
                            state.last_event_ts = now
                            state.last_event_direction = direction
                            print(
                                f"transport-strict event: track_id={tid} direction={direction} in={in_inc} out={out_inc} "
                                f"conf={confidence:.3f} depth_m={depth_m if depth_m is None else round(depth_m, 3)} age={track_age}",
                                flush=True,
                            )

                        state.side_start = zone
                        state.first_side_axis = axis_value
                        state.seen_middle = False
                        state.entered_middle_ts = None
                        state.side_frames = 1
                        state.middle_frames = 0

                    lost_timeout_sec = args.max_lost_frames / max(1.0, args.fps)
                    stale = [tid for tid, state in tracks.items() if (now - state.last_seen) > lost_timeout_sec]
                    for tid in stale:
                        tracks.pop(tid, None)
                        overlay_meta.pop(tid, None)
                    if stale:
                        with shared.lock:
                            shared.stats["lost_prune"] = int(shared.stats["lost_prune"]) + len(stale)

                with shared.lock:
                    shared.stats["active_tracks"] = len(tracks)
                    shared.stats["count_in"] = in_count
                    shared.stats["count_out"] = out_count
                    shared.stats["events_total"] = event_count

                with shared.lock:
                    preview_enabled = bool(shared.stats.get("preview_enabled", True))

                frame_msg = None
                if preview_enabled and args.preview_fps > 0.0:
                    min_interval = 1.0 / max(0.1, float(args.preview_fps))
                    if last_preview_ts <= 0.0 or (now - last_preview_ts) >= min_interval:
                        frame_msg = frame_queue.tryGet()
                        while True:
                            nxt = frame_queue.tryGet()
                            if nxt is None:
                                break
                            frame_msg = nxt

                if frame_msg is not None:
                    frame = frame_msg.getCvFrame()
                    height, width = frame.shape[:2]
                    if roi is not None:
                        x1 = clamp_pixel(roi[0], width)
                        y1 = clamp_pixel(roi[1], height)
                        x2 = clamp_pixel(roi[2], width)
                        y2 = clamp_pixel(roi[3], height)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (120, 180, 255), 1)
                    preview_items: list[dict[str, Any]] = []
                    for tracklet in last_tracklets:
                        if tracklet.status not in {dai.Tracklet.TrackingStatus.NEW, dai.Tracklet.TrackingStatus.TRACKED}:
                            continue
                        tid = int(tracklet.id)
                        meta = overlay_meta.get(tid, {})
                        conf_ok = bool(meta.get("conf_ok", False))
                        depth_ok = bool(meta.get("depth_ok", False))
                        color = (0, 200, 0) if (conf_ok and depth_ok) else (0, 80, 255)
                        x1 = clamp_pixel(tracklet.roi.topLeft().x, width)
                        y1 = clamp_pixel(tracklet.roi.topLeft().y, height)
                        x2 = clamp_pixel(tracklet.roi.bottomRight().x, width)
                        y2 = clamp_pixel(tracklet.roi.bottomRight().y, height)
                        depth_m = meta.get("depth_m")
                        depth_label = "z=n/a" if depth_m is None else f"z={float(depth_m):.2f}m"
                        bbox_w = meta.get("bbox_w_px")
                        bbox_h = meta.get("bbox_h_px")
                        bbox_ar = meta.get("bbox_ar")
                        bbox_wz = meta.get("bbox_wz")
                        bbox_label = ""
                        if isinstance(bbox_w, (int, float)) and isinstance(bbox_h, (int, float)):
                            bbox_label = f" w={float(bbox_w):.0f} h={float(bbox_h):.0f}"
                            if isinstance(bbox_ar, (int, float)):
                                bbox_label += f" ar={float(bbox_ar):.2f}"
                            if isinstance(bbox_wz, (int, float)):
                                bbox_label += f" wz={float(bbox_wz):.1f}"
                        label = (
                            f"id={tid} age={int(meta.get('age', 0))} "
                            f"c={float(meta.get('confidence', 0.0)):.2f} {depth_label}{bbox_label} "
                            f"zone={meta.get('zone', 'na')}"
                        )
                        preview_items.append(
                            {
                                "x1": int(x1),
                                "y1": int(y1),
                                "x2": int(x2),
                                "y2": int(y2),
                                "color": color,
                                "label": label,
                            }
                        )

                    with shared.lock:
                        shared.preview_frame = frame
                        shared.preview_items = preview_items
                        shared.stats["imu_acc_norm"] = imu_acc_norm
                        shared.stats["imu_gyro_norm"] = imu_gyro_norm
                    last_preview_ts = now

                if now - last_log >= args.log_interval_sec:
                    with shared.lock:
                        preview_frames = int(shared.stats.get("preview_frames", 0))
                        messages = int(shared.stats["messages"])
                        tracklets_total = int(shared.stats["tracklets_total"])
                        active_tracks = int(shared.stats["active_tracks"])
                        depth_pass = int(shared.stats["depth_pass"])
                        depth_reject = int(shared.stats["depth_reject"])
                        depth_missing = int(shared.stats["depth_missing"])
                        conf_reject = int(shared.stats["conf_reject"])
                        age_reject = int(shared.stats["age_reject"])
                        hang_reject = int(shared.stats["hang_reject"])
                        move_reject = int(shared.stats["move_reject"])
                        dup_reject = int(shared.stats["dup_reject"])
                        rearm_reject = int(shared.stats["rearm_reject"])
                    print(
                        f"transport-strict heartbeat: frames={preview_frames} msgs={messages} tracklets={tracklets_total} "
                        f"active={active_tracks} in={in_count} out={out_count} events={event_count} "
                        f"depth_ok={depth_pass} depth_reject={depth_reject} depth_missing={depth_missing} "
                        f"reject_conf={conf_reject} reject_age={age_reject} reject_hang={hang_reject} "
                        f"reject_move={move_reject} reject_dup={dup_reject} reject_rearm={rearm_reject}",
                        flush=True,
                    )
                    last_log = now
        finally:
            stop_event.set()
            with shared.lock:
                shared.stats["status"] = "stopping"
            httpd.shutdown()
            httpd.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
