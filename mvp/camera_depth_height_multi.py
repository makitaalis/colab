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
    stats: dict[str, Any]


@dataclass
class Detection:
    cx: float
    cy: float
    x: int
    y: int
    w: int
    h: int
    area: float
    depth_m: float | None


@dataclass
class TrackState:
    track_id: int
    cx: float
    cy: float
    age: int
    last_seen: float
    side_start: int | None
    seen_middle: bool
    entered_middle_ts: float | None
    last_event_ts: float


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def clamp_norm(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def clamp_pixel(value: float, max_value: int) -> int:
    if value <= 1.5:
        value = value * max_value
    return int(max(0, min(max_value - 1, round(value))))


def parse_roi(value: str, width: int, height: int) -> tuple[int, int, int, int]:
    pieces = [piece.strip() for piece in value.split(",") if piece.strip()]
    if len(pieces) != 4:
        return 0, 0, width - 1, height - 1
    vals = [float(piece) for piece in pieces]
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


def parse_size(value: str) -> tuple[int, int]:
    clean = (value or "").strip().lower().replace(" ", "")
    if "x" not in clean:
        raise ValueError("size must be like 320x200")
    w_s, h_s = clean.split("x", 1)
    width = int(w_s)
    height = int(h_s)
    if not (160 <= width <= 1920 and 120 <= height <= 1080):
        raise ValueError("size out of range")
    return width, height


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


def distance_px(a: tuple[float, float], b: tuple[float, float]) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return float((dx * dx + dy * dy) ** 0.5)


def assign_detections(
    tracks: dict[int, TrackState],
    detections: list[Detection],
    max_match_distance_px: float,
) -> tuple[dict[int, int], set[int], set[int]]:
    pairs: list[tuple[float, int, int]] = []
    for track_id, track in tracks.items():
        for det_index, detection in enumerate(detections):
            dist = distance_px((track.cx, track.cy), (detection.cx, detection.cy))
            if dist <= max_match_distance_px:
                pairs.append((dist, track_id, det_index))

    pairs.sort(key=lambda row: row[0])
    matched_track_to_det: dict[int, int] = {}
    used_tracks: set[int] = set()
    used_detections: set[int] = set()
    for _, track_id, det_index in pairs:
        if track_id in used_tracks or det_index in used_detections:
            continue
        matched_track_to_det[track_id] = det_index
        used_tracks.add(track_id)
        used_detections.add(det_index)

    unmatched_tracks = set(tracks.keys()) - used_tracks
    unmatched_detections = set(range(len(detections))) - used_detections
    return matched_track_to_det, unmatched_tracks, unmatched_detections


def normalize_depth_for_preview(depth_frame: np.ndarray, min_mm: int, max_mm: int) -> np.ndarray:
    clipped = np.clip(depth_frame, min_mm, max_mm)
    span = max(1, max_mm - min_mm)
    scaled = ((clipped.astype(np.float32) - float(min_mm)) * (255.0 / float(span))).astype(np.uint8)
    scaled = cv2.bitwise_not(scaled)
    return cv2.applyColorMap(scaled, cv2.COLORMAP_TURBO)


def configure_stereo(stereo: dai.node.StereoDepth, output_size: tuple[int, int]) -> None:
    if hasattr(stereo, "setDefaultProfilePreset"):
        try:
            stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        except Exception:
            pass
    if hasattr(stereo, "setOutputSize"):
        try:
            stereo.setOutputSize(int(output_size[0]), int(output_size[1]))
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


def build_mask(
    depth_frame: np.ndarray,
    roi: tuple[int, int, int, int],
    depth_min_mm: int,
    depth_max_mm: int,
    kernel_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    x1, y1, x2, y2 = roi
    mask = np.zeros(depth_frame.shape, dtype=np.uint8)
    roi_depth = depth_frame[y1:y2, x1:x2]
    roi_mask = ((roi_depth >= depth_min_mm) & (roi_depth <= depth_max_mm)).astype(np.uint8) * 255
    if kernel_size < 3:
        kernel_size = 3
    if kernel_size % 2 == 0:
        kernel_size += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    roi_mask = cv2.morphologyEx(roi_mask, cv2.MORPH_OPEN, kernel)
    roi_mask = cv2.morphologyEx(roi_mask, cv2.MORPH_CLOSE, kernel)
    mask[y1:y2, x1:x2] = roi_mask
    return mask, roi_mask


def split_components(
    roi_mask: np.ndarray,
    watershed_enabled: bool,
    watershed_distance_ratio: float,
) -> np.ndarray:
    if roi_mask.size == 0:
        return np.zeros((1, 1), dtype=np.int32)
    if not watershed_enabled:
        labels_count, labels, _, _ = cv2.connectedComponentsWithStats(roi_mask, connectivity=8)
        if labels_count <= 1:
            return labels
        return labels

    distance = cv2.distanceTransform(roi_mask, cv2.DIST_L2, 5)
    max_distance = float(np.max(distance)) if distance.size else 0.0
    if max_distance <= 0.0:
        _, labels, _, _ = cv2.connectedComponentsWithStats(roi_mask, connectivity=8)
        return labels

    threshold_ratio = clamp_norm(watershed_distance_ratio, 0.10, 0.90)
    _, sure_fg = cv2.threshold(distance, threshold_ratio * max_distance, 255, 0)
    sure_fg_u8 = np.uint8(sure_fg)
    labels_count, labels, _, _ = cv2.connectedComponentsWithStats(sure_fg_u8, connectivity=8)
    if labels_count <= 1:
        _, labels, _, _ = cv2.connectedComponentsWithStats(roi_mask, connectivity=8)
    return labels


def extract_detections(
    depth_frame: np.ndarray,
    roi: tuple[int, int, int, int],
    labels_roi: np.ndarray,
    depth_min_mm: int,
    depth_max_mm: int,
    area_min: float,
) -> list[Detection]:
    x1, y1, _, _ = roi
    detections: list[Detection] = []
    label_ids = np.unique(labels_roi)
    for label_id in label_ids:
        if int(label_id) <= 0:
            continue
        label_mask = (labels_roi == label_id).astype(np.uint8) * 255
        contours, _ = cv2.findContours(label_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue
        contour = max(contours, key=cv2.contourArea)
        area = float(cv2.contourArea(contour))
        if area < area_min:
            continue
        bx, by, bw, bh = cv2.boundingRect(contour)
        abs_x = int(x1 + bx)
        abs_y = int(y1 + by)
        center_x = float(abs_x + bw / 2.0)
        center_y = float(abs_y + bh / 2.0)

        roi_depth = depth_frame[abs_y : abs_y + bh, abs_x : abs_x + bw]
        valid_depth = roi_depth[(roi_depth >= depth_min_mm) & (roi_depth <= depth_max_mm)]
        depth_m = float(np.median(valid_depth)) / 1000.0 if valid_depth.size > 0 else None

        detections.append(
            Detection(
                cx=center_x,
                cy=center_y,
                x=abs_x,
                y=abs_y,
                w=int(bw),
                h=int(bh),
                area=area,
                depth_m=depth_m,
            )
        )
    return detections


class Handler(BaseHTTPRequestHandler):
    server_version = "PassengersDepthHeightMulti/1.0"

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
        auto_disable_preview = stats_only
        grid_class = "grid statsOnly" if stats_only else "grid"
        video_block = (
            ""
            if stats_only
            else "<div class='card' id='video_card'>"
            "<div class='toolbarRow'>"
            "<div class='toolbarLeft'>"
            "<div class='toolbarTitle'>Depth Video</div>"
            "<div class='toolbarHint'>StereoDepth colormap (debug)</div>"
            "</div>"
            "<div class='toolbarRight'>"
            "<button class='btn' id='preview_toggle_btn'>...</button>"
            "</div></div>"
            "<img id='video_img' src='/mjpeg' alt='depth height multi stream'/>"
            "</div>"
        )

        body = (
            "<html><head><meta charset='utf-8'><title>Depth Height Multi</title>"
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
            "<div class='head'><h2 style='margin:0'>Depth Height Multi (stereo-only)</h2>"
            "<div><span id='status_badge' class='badge'>loading</span> "
            "<a href='/health' target='_blank'>health json</a> | "
            "<a href='/snapshot.jpg' target='_blank'>snapshot</a> | "
            "<a href='/?view=stats'>stats only</a> | "
            "<a href='/'>full</a></div></div>"
            f"<div class='{grid_class}'>"
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
            "<div class='bigItem'><div class='bigK'>OUT</div><div class='bigV' id='count_out_big'>-</div><div class='bigSub'>tracks: <span id='active_tracks_big'>-</span></div></div>"
            "</div>"
            "<div style='height:10px'></div>"
            "<h3 style='margin:0 0 10px 0;font-size:15px'>Live Stats</h3><div class='stats'>"
            "<div class='k'>Status</div><div class='v' id='status'>-</div>"
            "<div class='k'>Device</div><div class='v' id='device'>-</div>"
            "<div class='k'>USB</div><div class='v' id='usb_speed'>-</div>"
            "<div class='k'>Messages</div><div class='v' id='messages'>-</div>"
            "<div class='k'>Detections</div><div class='v' id='detections'>-</div>"
            "<div class='k'>Tracks active</div><div class='v' id='active_tracks'>-</div>"
            "<div class='k'>IN</div><div class='v' id='count_in'>-</div>"
            "<div class='k'>OUT</div><div class='v' id='count_out'>-</div>"
            "<div class='k'>Events</div><div class='v' id='events_total'>-</div>"
            "<div class='k'>Line A/B</div><div class='v'><span id='line_a'>-</span> .. <span id='line_b'>-</span></div>"
            "<div class='k'>Depth m</div><div class='v'><span id='depth_min_m'>-</span> .. <span id='depth_max_m'>-</span></div>"
            "<div class='k'>Min age/lost</div><div class='v'><span id='min_track_age'>-</span>/<span id='max_lost_frames'>-</span></div>"
            "<div class='k'>Preview</div><div class='v'><span id='preview_size'>-</span> @ <span id='preview_fps'>-</span></div>"
            "<div class='k'>Depth pass/reject</div><div class='v'><span id='depth_pass'>-</span>/<span id='depth_reject'>-</span></div>"
            "<div class='k'>Reject age/hang</div><div class='v'><span id='age_reject'>-</span>/<span id='hang_reject'>-</span></div>"
            "<div class='k'>Reject dup/rearm</div><div class='v'><span id='dup_reject'>-</span>/<span id='rearm_reject'>-</span></div>"
            "<div class='k'>Zone -/0/+</div><div class='v'><span id='zone_neg_hits'>-</span>/<span id='zone_mid_hits'>-</span>/<span id='zone_pos_hits'>-</span></div>"
            "<div class='k'>Middle/flip</div><div class='v'><span id='middle_entries'>-</span>/<span id='zone_flip_no_middle'>-</span></div>"
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
            "['status','device','usb_speed','messages','detections','active_tracks','count_in','count_out','events_total','line_a','line_b','depth_min_m','depth_max_m','min_track_age','max_lost_frames','preview_size','preview_fps','depth_pass','depth_reject','age_reject','hang_reject','dup_reject','rearm_reject','zone_neg_hits','zone_mid_hits','zone_pos_hits','middle_entries','zone_flip_no_middle','ts'].forEach(k=>setVal(k,j[k]));"
            "setVal('count_in_big',j.count_in);setVal('count_out_big',j.count_out);setVal('events_total_big',j.events_total);setVal('active_tracks_big',j.active_tracks);"
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
    parser = argparse.ArgumentParser(description="Depth height multi counting (stereo-only).")
    parser.add_argument("--env", default="/etc/passengers/passengers.env")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--fps", type=float, default=10.0)
    parser.add_argument("--axis", choices=["x", "y"], default="x")
    parser.add_argument("--axis-pos", type=float, default=0.50)
    parser.add_argument("--axis-hyst", type=float, default=0.01)
    parser.add_argument("--line-gap-norm", type=float, default=0.22)
    parser.add_argument("--roi", default="0.06,0.06,0.94,0.98")
    parser.add_argument("--area-min", type=float, default=180.0)
    parser.add_argument("--kernel-size", type=int, default=7)
    parser.add_argument("--max-objects", type=int, default=20)
    parser.add_argument("--max-match-dist-px", type=float, default=40.0)
    parser.add_argument("--min-track-age", type=int, default=3)
    parser.add_argument("--max-lost-frames", type=int, default=6)
    parser.add_argument("--hang-timeout-sec", type=float, default=3.0)
    parser.add_argument("--count-cooldown-sec", type=float, default=1.0)
    parser.add_argument("--per-track-rearm-sec", type=float, default=1.2)
    parser.add_argument("--invert-direction", action="store_true")
    parser.add_argument("--depth-min-m", type=float, default=0.35)
    parser.add_argument("--depth-max-m", type=float, default=0.95)
    parser.add_argument("--watershed-enable", action="store_true", default=True)
    parser.add_argument("--watershed-dist-ratio", type=float, default=0.38)
    parser.add_argument("--preview-size", default="416x256")
    parser.add_argument("--preview-fps", type=float, default=5.0)
    parser.add_argument("--output-size", default="320x200")
    parser.add_argument("--jpeg-quality", type=int, default=58)
    parser.add_argument("--log-interval-sec", type=float, default=10.0)
    return parser


def load_runtime(args: argparse.Namespace) -> argparse.Namespace:
    env = load_env_file(args.env)

    args.fps = float(env.get("CAM_DEPTH_MULTI_FPS", env.get("CAM_DEPTH_COUNT_FPS", str(args.fps))))
    args.axis = env.get("CAM_DEPTH_MULTI_AXIS", env.get("CAM_DEPTH_COUNT_AXIS", args.axis)).strip().lower()
    args.axis_pos = float(env.get("CAM_DEPTH_MULTI_AXIS_POS", env.get("CAM_DEPTH_COUNT_AXIS_POS", str(args.axis_pos))))
    args.axis_hyst = float(env.get("CAM_DEPTH_MULTI_AXIS_HYST", env.get("CAM_DEPTH_COUNT_AXIS_HYST", str(args.axis_hyst))))
    args.line_gap_norm = float(
        env.get("CAM_DEPTH_MULTI_LINE_GAP_NORM", env.get("CAM_DEPTH_COUNT_LINE_GAP_NORM", str(args.line_gap_norm)))
    )
    args.roi = env.get("CAM_DEPTH_MULTI_ROI", env.get("CAM_DEPTH_COUNT_ROI", args.roi))
    args.area_min = float(env.get("CAM_DEPTH_MULTI_AREA_MIN", env.get("CAM_DEPTH_COUNT_AREA_MIN", str(args.area_min))))
    args.kernel_size = int(env.get("CAM_DEPTH_MULTI_KERNEL_SIZE", env.get("CAM_DEPTH_COUNT_KERNEL_SIZE", str(args.kernel_size))))
    args.max_objects = int(env.get("CAM_DEPTH_MULTI_MAX_OBJECTS", str(args.max_objects)))
    args.max_match_dist_px = float(env.get("CAM_DEPTH_MULTI_MATCH_DIST_PX", str(args.max_match_dist_px)))
    args.min_track_age = int(
        env.get("CAM_DEPTH_MULTI_MIN_TRACK_AGE", env.get("CAM_DEPTH_COUNT_MIN_TRACK_AGE", str(args.min_track_age)))
    )
    args.max_lost_frames = int(
        env.get("CAM_DEPTH_MULTI_MAX_LOST_FRAMES", env.get("CAM_DEPTH_COUNT_MAX_LOST_FRAMES", str(args.max_lost_frames)))
    )
    args.hang_timeout_sec = float(
        env.get("CAM_DEPTH_MULTI_HANG_TIMEOUT_SEC", env.get("CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC", str(args.hang_timeout_sec)))
    )
    args.count_cooldown_sec = float(
        env.get(
            "CAM_DEPTH_MULTI_COUNT_COOLDOWN_SEC",
            env.get("CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC", str(args.count_cooldown_sec)),
        )
    )
    args.per_track_rearm_sec = float(
        env.get(
            "CAM_DEPTH_MULTI_PER_TRACK_REARM_SEC",
            env.get("CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC", str(args.per_track_rearm_sec)),
        )
    )
    args.invert_direction = parse_bool(env.get("CAM_DEPTH_MULTI_INVERT", env.get("CAM_DEPTH_COUNT_INVERT")), args.invert_direction)
    args.depth_min_m = float(env.get("CAM_DEPTH_MULTI_MIN_M", env.get("CAM_DEPTH_MIN_M", str(args.depth_min_m))))
    args.depth_max_m = float(env.get("CAM_DEPTH_MULTI_MAX_M", env.get("CAM_DEPTH_MAX_M", str(args.depth_max_m))))
    args.watershed_enable = parse_bool(env.get("CAM_DEPTH_MULTI_WATERSHED_ENABLE"), args.watershed_enable)
    args.watershed_dist_ratio = float(env.get("CAM_DEPTH_MULTI_WATERSHED_DIST_RATIO", str(args.watershed_dist_ratio)))
    args.preview_size = env.get("CAM_DEPTH_MULTI_PREVIEW_SIZE", env.get("CAM_PREVIEW_SIZE", args.preview_size))
    args.preview_fps = float(env.get("CAM_DEPTH_MULTI_PREVIEW_FPS", env.get("CAM_PREVIEW_FPS", str(args.preview_fps))))
    args.output_size = env.get("CAM_DEPTH_MULTI_OUTPUT_SIZE", env.get("CAM_DEPTH_OUTPUT_SIZE", args.output_size))
    args.jpeg_quality = int(env.get("CAM_JPEG_QUALITY", str(args.jpeg_quality)))
    args.debug_bind = env.get("CAM_DEBUG_BIND", args.bind)
    args.debug_port = int(env.get("CAM_DEBUG_PORT", str(args.port)))

    if args.axis not in {"x", "y"}:
        raise ValueError(f"axis must be x|y (got {args.axis})")
    if not (0.05 <= args.axis_pos <= 0.95):
        raise ValueError(f"axis-pos must be in [0.05..0.95] (got {args.axis_pos})")
    if not (0.00 <= args.axis_hyst <= 0.25):
        raise ValueError(f"axis-hyst must be in [0.00..0.25] (got {args.axis_hyst})")
    if not (0.02 <= args.line_gap_norm <= 0.80):
        raise ValueError(f"line-gap-norm must be in [0.02..0.80] (got {args.line_gap_norm})")
    if not (0.10 <= args.depth_min_m < args.depth_max_m <= 5.00):
        raise ValueError("invalid depth range")
    if not (1 <= args.max_objects <= 128):
        raise ValueError("max-objects must be in [1..128]")
    if not (1 <= args.min_track_age <= 60):
        raise ValueError("min-track-age must be in [1..60]")
    if not (1 <= args.max_lost_frames <= 120):
        raise ValueError("max-lost-frames must be in [1..120]")
    if not (0.0 <= args.max_match_dist_px <= 400.0):
        raise ValueError("max-match-dist-px must be in [0..400]")
    if not (0.0 <= args.count_cooldown_sec <= 30.0):
        raise ValueError("count-cooldown-sec must be in [0..30]")
    if not (0.0 <= args.per_track_rearm_sec <= 30.0):
        raise ValueError("per-track-rearm-sec must be in [0..30]")
    if not (0.0 <= args.hang_timeout_sec <= 30.0):
        raise ValueError("hang-timeout-sec must be in [0..30]")
    if not (10 <= args.jpeg_quality <= 95):
        raise ValueError("jpeg-quality must be in [10..95]")
    if not (0.5 <= args.preview_fps <= 30.0):
        raise ValueError("preview-fps must be in [0.5..30]")

    _ = parse_size(args.preview_size)
    _ = parse_size(args.output_size)
    return args


def main() -> int:
    args = load_runtime(build_parser().parse_args())

    preview_w, preview_h = parse_size(args.preview_size)
    output_w, output_h = parse_size(args.output_size)

    half_gap = args.line_gap_norm / 2.0
    line_a = clamp_norm(args.axis_pos - half_gap, 0.02, 0.98)
    line_b = clamp_norm(args.axis_pos + half_gap, 0.02, 0.98)
    if line_a > line_b:
        line_a, line_b = line_b, line_a

    shared = SharedState(
        lock=threading.Lock(),
        jpg=b"",
        last_frame_ts=0.0,
        stats={
            "status": "starting",
            "device": "",
            "usb_speed": "",
            "preview_enabled": True,
            "messages": 0,
            "detections": 0,
            "active_tracks": 0,
            "events_total": 0,
            "count_in": 0,
            "count_out": 0,
            "axis": args.axis,
            "line_a": round(line_a, 4),
            "line_b": round(line_b, 4),
            "line_gap_norm": round(args.line_gap_norm, 4),
            "axis_hyst": round(args.axis_hyst, 4),
            "roi": args.roi,
            "area_min": args.area_min,
            "min_track_age": args.min_track_age,
            "max_lost_frames": args.max_lost_frames,
            "max_match_dist_px": args.max_match_dist_px,
            "count_cooldown_sec": args.count_cooldown_sec,
            "per_track_rearm_sec": args.per_track_rearm_sec,
            "hang_timeout_sec": args.hang_timeout_sec,
            "depth_min_m": args.depth_min_m,
            "depth_max_m": args.depth_max_m,
            "watershed_enabled": args.watershed_enable,
            "watershed_dist_ratio": args.watershed_dist_ratio,
            "preview_size": f"{preview_w}x{preview_h}",
            "preview_fps": args.preview_fps,
            "output_size": f"{output_w}x{output_h}",
            "jpeg_quality": args.jpeg_quality,
            "depth_pass": 0,
            "depth_reject": 0,
            "age_reject": 0,
            "hang_reject": 0,
            "dup_reject": 0,
            "rearm_reject": 0,
            "zone_neg_hits": 0,
            "zone_mid_hits": 0,
            "zone_pos_hits": 0,
            "middle_entries": 0,
            "zone_flip_no_middle": 0,
            "lost_prune": 0,
            "bind": args.debug_bind,
            "port": args.debug_port,
        },
    )

    httpd = ThreadingHTTPServer((args.debug_bind, args.debug_port), Handler)
    httpd.shared_state = shared  # type: ignore[attr-defined]
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    print(
        f"depth-height-multi: listening http://{args.debug_bind}:{args.debug_port} "
        f"(use SSH tunnel if bind=127.0.0.1)",
        flush=True,
    )

    with dai.Pipeline() as pipeline:
        left_camera = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_B)
        right_camera = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_C)
        stereo = pipeline.create(dai.node.StereoDepth)
        configure_stereo(stereo, output_size=(output_w, output_h))
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
            f"depth-height-multi: device={device.getDeviceName()} usb_speed={device.getUsbSpeed().name} "
            f"axis={args.axis} line_a={line_a:.3f} line_b={line_b:.3f} fps={args.fps:.1f} "
            f"depth={args.depth_min_m:.2f}-{args.depth_max_m:.2f}m preview={preview_w}x{preview_h}@{args.preview_fps:.1f} "
            f"output={output_w}x{output_h} watershed={args.watershed_enable}",
            flush=True,
        )

        tracks: dict[int, TrackState] = {}
        next_track_id = 1
        count_in = 0
        count_out = 0
        events_total = 0
        depth_min_mm = int(round(args.depth_min_m * 1000.0))
        depth_max_mm = int(round(args.depth_max_m * 1000.0))
        lost_timeout_sec = args.max_lost_frames / max(1.0, args.fps)
        last_global_event_ts = 0.0
        last_preview_ts = 0.0
        last_log_ts = time.monotonic()

        while pipeline.isRunning():
            depth_msg = depth_queue.tryGet()
            if depth_msg is None:
                now_sleep = time.monotonic()
                if now_sleep - last_log_ts >= args.log_interval_sec:
                    with shared.lock:
                        messages = int(shared.stats.get("messages", 0))
                        detections = int(shared.stats.get("detections", 0))
                        active_tracks = int(shared.stats.get("active_tracks", 0))
                        depth_pass = int(shared.stats.get("depth_pass", 0))
                        depth_reject = int(shared.stats.get("depth_reject", 0))
                    print(
                        f"depth-height-multi heartbeat: messages={messages} detections={detections} "
                        f"active={active_tracks} in={count_in} out={count_out} events={events_total} "
                        f"depth_pass={depth_pass} depth_reject={depth_reject}",
                        flush=True,
                    )
                    last_log_ts = now_sleep
                time.sleep(0.01)
                continue

            now = time.monotonic()
            depth_frame = depth_msg.getFrame()
            if depth_frame is None or depth_frame.size == 0:
                continue

            with shared.lock:
                shared.stats["messages"] = int(shared.stats["messages"]) + 1

            height, width = depth_frame.shape[:2]
            roi = parse_roi(args.roi, width, height)
            _, roi_mask = build_mask(
                depth_frame=depth_frame,
                roi=roi,
                depth_min_mm=depth_min_mm,
                depth_max_mm=depth_max_mm,
                kernel_size=args.kernel_size,
            )
            labels_roi = split_components(
                roi_mask=roi_mask,
                watershed_enabled=args.watershed_enable,
                watershed_distance_ratio=args.watershed_dist_ratio,
            )
            detections = extract_detections(
                depth_frame=depth_frame,
                roi=roi,
                labels_roi=labels_roi,
                depth_min_mm=depth_min_mm,
                depth_max_mm=depth_max_mm,
                area_min=args.area_min,
            )
            candidate_components = max(0, int(np.max(labels_roi)) if labels_roi.size else 0)

            with shared.lock:
                shared.stats["detections"] = int(shared.stats["detections"]) + len(detections)

            matched, unmatched_tracks, unmatched_detections = assign_detections(
                tracks=tracks,
                detections=detections,
                max_match_distance_px=args.max_match_dist_px,
            )

            for track_id in list(unmatched_tracks):
                track_state = tracks.get(track_id)
                if track_state is None:
                    continue
                if now - track_state.last_seen > lost_timeout_sec:
                    tracks.pop(track_id, None)
                    with shared.lock:
                        shared.stats["lost_prune"] = int(shared.stats["lost_prune"]) + 1

            for track_id, det_index in matched.items():
                track_state = tracks.get(track_id)
                if track_state is None:
                    continue
                detection = detections[det_index]
                track_state.cx = detection.cx
                track_state.cy = detection.cy
                track_state.last_seen = now
                track_state.age += 1

            for det_index in unmatched_detections:
                if len(tracks) >= args.max_objects:
                    continue
                detection = detections[det_index]
                track_id = next_track_id
                next_track_id += 1
                tracks[track_id] = TrackState(
                    track_id=track_id,
                    cx=detection.cx,
                    cy=detection.cy,
                    age=1,
                    last_seen=now,
                    side_start=None,
                    seen_middle=False,
                    entered_middle_ts=None,
                    last_event_ts=0.0,
                )
                matched[track_id] = det_index

            for track_id, det_index in matched.items():
                track_state = tracks.get(track_id)
                if track_state is None:
                    continue
                detection = detections[det_index]
                axis_norm = (detection.cx / float(width)) if args.axis == "y" else (detection.cy / float(height))
                zone = classify_zone(axis_norm, line_a, line_b, args.axis_hyst)
                if zone == -1:
                    with shared.lock:
                        shared.stats["zone_neg_hits"] = int(shared.stats["zone_neg_hits"]) + 1
                elif zone == 0:
                    with shared.lock:
                        shared.stats["zone_mid_hits"] = int(shared.stats["zone_mid_hits"]) + 1
                else:
                    with shared.lock:
                        shared.stats["zone_pos_hits"] = int(shared.stats["zone_pos_hits"]) + 1

                if track_state.side_start is None and zone != 0:
                    track_state.side_start = zone

                if zone == 0:
                    if not track_state.seen_middle:
                        track_state.seen_middle = True
                        track_state.entered_middle_ts = now
                        with shared.lock:
                            shared.stats["middle_entries"] = int(shared.stats["middle_entries"]) + 1
                elif (
                    track_state.seen_middle
                    and track_state.entered_middle_ts is not None
                    and (now - track_state.entered_middle_ts) > args.hang_timeout_sec
                ):
                    track_state.side_start = None
                    track_state.seen_middle = False
                    track_state.entered_middle_ts = None
                    with shared.lock:
                        shared.stats["hang_reject"] = int(shared.stats["hang_reject"]) + 1

                if track_state.side_start is None or zone == 0 or zone == track_state.side_start:
                    continue

                if not track_state.seen_middle:
                    track_state.side_start = zone
                    with shared.lock:
                        shared.stats["zone_flip_no_middle"] = int(shared.stats["zone_flip_no_middle"]) + 1
                    continue

                if track_state.age < args.min_track_age:
                    with shared.lock:
                        shared.stats["age_reject"] = int(shared.stats["age_reject"]) + 1
                    continue

                if (now - last_global_event_ts) < args.count_cooldown_sec:
                    with shared.lock:
                        shared.stats["dup_reject"] = int(shared.stats["dup_reject"]) + 1
                    continue

                if args.per_track_rearm_sec > 0.0 and (now - track_state.last_event_ts) < args.per_track_rearm_sec:
                    with shared.lock:
                        shared.stats["rearm_reject"] = int(shared.stats["rearm_reject"]) + 1
                    continue

                in_inc, out_inc, direction = transition_to_counts(track_state.side_start, zone, args.invert_direction)
                if in_inc == 0 and out_inc == 0:
                    continue

                count_in += in_inc
                count_out += out_inc
                events_total += 1
                last_global_event_ts = now
                track_state.last_event_ts = now
                track_state.side_start = zone
                track_state.seen_middle = False
                track_state.entered_middle_ts = None

                depth_value = detection.depth_m if detection.depth_m is not None else -1.0
                print(
                    f"depth-height-multi event: seq={events_total} track_id={track_id} direction={direction} "
                    f"in={in_inc} out={out_inc} depth_m={depth_value:.3f} age={track_state.age} area={detection.area:.1f}",
                    flush=True,
                )

            with shared.lock:
                shared.stats["active_tracks"] = len(tracks)
                shared.stats["events_total"] = events_total
                shared.stats["count_in"] = count_in
                shared.stats["count_out"] = count_out
                shared.stats["depth_pass"] = int(shared.stats["depth_pass"]) + len(detections)
                shared.stats["depth_reject"] = int(shared.stats["depth_reject"]) + max(0, candidate_components - len(detections))

            with shared.lock:
                preview_enabled = bool(shared.stats.get("preview_enabled", True))

            if preview_enabled and args.preview_fps > 0.0:
                min_interval = 1.0 / max(0.1, args.preview_fps)
                if last_preview_ts <= 0.0 or (now - last_preview_ts) >= min_interval:
                    overlay = normalize_depth_for_preview(depth_frame, depth_min_mm, depth_max_mm)
                    if (overlay.shape[1], overlay.shape[0]) != (preview_w, preview_h):
                        overlay = cv2.resize(overlay, (preview_w, preview_h), interpolation=cv2.INTER_AREA)
                    sx = preview_w / float(width)
                    sy = preview_h / float(height)
                    x1, y1, x2, y2 = roi
                    cv2.rectangle(
                        overlay,
                        (int(round(x1 * sx)), int(round(y1 * sy))),
                        (int(round(x2 * sx)), int(round(y2 * sy))),
                        (255, 200, 0),
                        2,
                    )
                    if args.axis == "y":
                        line_ax = int(round(line_a * preview_w))
                        line_bx = int(round(line_b * preview_w))
                        cv2.line(overlay, (line_ax, 0), (line_ax, preview_h - 1), (80, 180, 255), 2)
                        cv2.line(overlay, (line_bx, 0), (line_bx, preview_h - 1), (255, 220, 80), 2)
                    else:
                        line_ay = int(round(line_a * preview_h))
                        line_by = int(round(line_b * preview_h))
                        cv2.line(overlay, (0, line_ay), (preview_w - 1, line_ay), (80, 180, 255), 2)
                        cv2.line(overlay, (0, line_by), (preview_w - 1, line_by), (255, 220, 80), 2)

                    for track_id, det_index in matched.items():
                        if track_id not in tracks:
                            continue
                        detection = detections[det_index]
                        rx1 = int(round(detection.x * sx))
                        ry1 = int(round(detection.y * sy))
                        rx2 = int(round((detection.x + detection.w) * sx))
                        ry2 = int(round((detection.y + detection.h) * sy))
                        cv2.rectangle(overlay, (rx1, ry1), (rx2, ry2), (60, 255, 120), 2)
                        depth_label = "n/a" if detection.depth_m is None else f"{detection.depth_m:.2f}m"
                        cv2.putText(
                            overlay,
                            f"id={track_id} z={depth_label}",
                            (rx1 + 2, max(14, ry1 - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.45,
                            (255, 255, 255),
                            1,
                            cv2.LINE_AA,
                        )

                    cv2.putText(
                        overlay,
                        f"IN={count_in} OUT={count_out} events={events_total}",
                        (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA,
                    )
                    cv2.putText(
                        overlay,
                        f"depth={args.depth_min_m:.2f}-{args.depth_max_m:.2f}m fps={args.fps:.1f}",
                        (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.45,
                        (230, 230, 230),
                        1,
                        cv2.LINE_AA,
                    )

                    ok, encoded = cv2.imencode(
                        ".jpg",
                        overlay,
                        [int(cv2.IMWRITE_JPEG_QUALITY), int(max(10, min(95, args.jpeg_quality)))],
                    )
                    if ok:
                        with shared.lock:
                            shared.jpg = encoded.tobytes()
                            shared.last_frame_ts = now
                    last_preview_ts = now

            if now - last_log_ts >= args.log_interval_sec:
                with shared.lock:
                    messages = int(shared.stats.get("messages", 0))
                    detections_total = int(shared.stats.get("detections", 0))
                    active_tracks = int(shared.stats.get("active_tracks", 0))
                    zone_mid = int(shared.stats.get("zone_mid_hits", 0))
                    flip_no_middle = int(shared.stats.get("zone_flip_no_middle", 0))
                print(
                    f"depth-height-multi heartbeat: messages={messages} detections={detections_total} "
                    f"active={active_tracks} in={count_in} out={count_out} events={events_total} "
                    f"zone_mid={zone_mid} flip_no_middle={flip_no_middle}",
                    flush=True,
                )
                last_log_ts = now

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
