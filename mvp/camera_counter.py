#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import time
from dataclasses import dataclass

import depthai as dai
import numpy as np

from common import load_env_file, utc_now_iso
from sqlite_store import connect, edge_next_seq, init_central_db, init_edge_db, meta_get, meta_set, store_event


@dataclass
class TrackState:
    side: int
    last_seen: float
    depth_m: float | None = None


def parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def side_from_value(value: float, line: float, hysteresis: float) -> int:
    if value < (line - hysteresis):
        return -1
    if value > (line + hysteresis):
        return 1
    return 0


def centroid_from_tracklet(tracklet: dai.Tracklet) -> tuple[float, float]:
    x1 = float(tracklet.roi.topLeft().x)
    y1 = float(tracklet.roi.topLeft().y)
    x2 = float(tracklet.roi.bottomRight().x)
    y2 = float(tracklet.roi.bottomRight().y)
    return ((x2 - x1) / 2.0 + x1, (y2 - y1) / 2.0 + y1)


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


def status_name(status: dai.Tracklet.TrackingStatus) -> str:
    if status == dai.Tracklet.TrackingStatus.NEW:
        return "NEW"
    if status == dai.Tracklet.TrackingStatus.TRACKED:
        return "TRACKED"
    if status == dai.Tracklet.TrackingStatus.LOST:
        return "LOST"
    if status == dai.Tracklet.TrackingStatus.REMOVED:
        return "REMOVED"
    return str(status)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Passengers camera counter (DepthAI v3).")
    parser.add_argument("--env", default="/etc/passengers/passengers.env")
    parser.add_argument("--db", default="/var/lib/passengers/central.sqlite3")
    parser.add_argument(
        "--store",
        choices=["central", "edge"],
        default="central",
        help="Where to store events: central=events table; edge=outbox for edge_sender",
    )
    parser.add_argument("--node-id", default=None)
    parser.add_argument("--door-id", type=int, default=1)
    parser.add_argument("--axis", choices=["x", "y"], default="y")
    parser.add_argument("--line", type=float, default=0.5)
    parser.add_argument("--hysteresis", type=float, default=0.04)
    parser.add_argument("--invert-direction", action="store_true")
    parser.add_argument("--min-track-age", type=int, default=3)
    parser.add_argument("--prune-sec", type=float, default=8.0)
    parser.add_argument("--fps", type=float, default=10.0)
    parser.add_argument("--confidence", type=float, default=0.45)
    parser.add_argument("--model", default="yolov6-nano")
    parser.add_argument(
        "--tracker-type",
        choices=["short_term_imageless", "short_term_kcf", "zero_term_imageless", "zero_term_color_histogram"],
        default="short_term_imageless",
    )
    parser.add_argument("--birth-threshold", type=int, default=4)
    parser.add_argument("--max-lifespan", type=int, default=15)
    parser.add_argument("--occlusion-threshold", type=float, default=0.4)
    parser.add_argument("--depth-enable", dest="depth_enable", action="store_true")
    parser.add_argument("--no-depth-enable", dest="depth_enable", action="store_false")
    parser.add_argument("--depth-min-m", type=float, default=0.40)
    parser.add_argument("--depth-max-m", type=float, default=1.50)
    parser.add_argument("--depth-head-fraction", type=float, default=0.45)
    parser.add_argument("--depth-min-valid-px", type=int, default=25)
    parser.set_defaults(depth_enable=True)
    parser.add_argument("--log-interval-sec", type=float, default=15.0)
    parser.add_argument("--run-seconds", type=float, default=0.0, help="0 = infinite")
    parser.add_argument("--dry-run", action="store_true", help="Do not write events into SQLite")
    return parser


def tracker_type_from_name(name: str) -> dai.TrackerType:
    mapping = {
        "short_term_imageless": dai.TrackerType.SHORT_TERM_IMAGELESS,
        "short_term_kcf": dai.TrackerType.SHORT_TERM_KCF,
        "zero_term_imageless": dai.TrackerType.ZERO_TERM_IMAGELESS,
        "zero_term_color_histogram": dai.TrackerType.ZERO_TERM_COLOR_HISTOGRAM,
    }
    return mapping[name]


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


def load_runtime_config(args: argparse.Namespace) -> argparse.Namespace:
    env = load_env_file(args.env)

    if args.node_id is None:
        args.node_id = env.get("CAM_COUNTER_NODE_ID") or env.get("NODE_ID") or f"{socket.gethostname()}-cam"

    args.store = env.get("CAM_COUNTER_STORE", args.store).strip().lower()
    if args.store not in {"central", "edge"}:
        raise ValueError(f"store must be central|edge (got {args.store})")

    args.door_id = int(env.get("CAM_COUNTER_DOOR_ID", str(args.door_id)))
    args.axis = env.get("CAM_COUNTER_AXIS", args.axis).strip().lower()
    args.line = float(env.get("CAM_COUNTER_AXIS_POS", str(args.line)))
    args.hysteresis = float(env.get("CAM_COUNTER_HYSTERESIS", str(args.hysteresis)))
    args.invert_direction = parse_bool(env.get("CAM_COUNTER_INVERT"), args.invert_direction)
    args.min_track_age = int(env.get("CAM_COUNTER_MIN_TRACK_AGE", str(args.min_track_age)))
    args.prune_sec = float(env.get("CAM_COUNTER_PRUNE_SEC", str(args.prune_sec)))
    args.fps = float(env.get("CAM_COUNTER_FPS", str(args.fps)))
    args.confidence = float(env.get("CAM_COUNTER_CONFIDENCE", str(args.confidence)))
    args.model = env.get("CAM_COUNTER_MODEL", args.model)
    args.tracker_type = env.get("CAM_COUNTER_TRACKER_TYPE", args.tracker_type)
    args.birth_threshold = int(env.get("CAM_COUNTER_TRACKER_BIRTH", str(args.birth_threshold)))
    args.max_lifespan = int(env.get("CAM_COUNTER_TRACKER_LIFESPAN", str(args.max_lifespan)))
    args.occlusion_threshold = float(env.get("CAM_COUNTER_TRACKER_OCCLUSION", str(args.occlusion_threshold)))
    args.log_interval_sec = float(env.get("CAM_COUNTER_LOG_INTERVAL_SEC", str(args.log_interval_sec)))

    args.depth_enable = parse_bool(env.get("CAM_DEPTH_ENABLE"), args.depth_enable)
    args.depth_min_m = float(env.get("CAM_DEPTH_MIN_M", str(args.depth_min_m)))
    args.depth_max_m = float(env.get("CAM_DEPTH_MAX_M", str(args.depth_max_m)))
    args.depth_head_fraction = float(env.get("CAM_DEPTH_HEAD_FRACTION", str(args.depth_head_fraction)))
    args.depth_min_valid_px = int(env.get("CAM_DEPTH_MIN_VALID_PX", str(args.depth_min_valid_px)))

    if args.axis not in {"x", "y"}:
        raise ValueError(f"axis must be x|y (got {args.axis})")
    if not (0.05 <= args.line <= 0.95):
        raise ValueError(f"line must be in [0.05..0.95] (got {args.line})")
    if not (0.0 <= args.hysteresis <= 0.25):
        raise ValueError(f"hysteresis must be in [0..0.25] (got {args.hysteresis})")
    if args.depth_min_m <= 0.0 or args.depth_max_m <= 0.0:
        raise ValueError("depth min/max must be > 0")
    if args.depth_min_m >= args.depth_max_m:
        raise ValueError("depth min must be < depth max")
    if not (0.2 <= args.depth_head_fraction <= 1.0):
        raise ValueError("depth head fraction must be in [0.2..1.0]")
    if args.depth_min_valid_px < 1:
        raise ValueError("depth min valid px must be >= 1")

    return args


def next_seq(conn, key: str) -> int:
    value = int(meta_get(conn, key, "1"))
    meta_set(conn, key, str(value + 1))
    return value


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    args = load_runtime_config(args)

    conn = connect(args.db)
    seq_key = f"camera_next_seq::{args.node_id}"
    if args.store == "central":
        init_central_db(conn)
    else:
        init_edge_db(conn)

    print(
        "camera-counter config: "
        f"store={args.store} db={args.db} node_id={args.node_id} door_id={args.door_id} axis={args.axis} line={args.line} "
        f"hyst={args.hysteresis} model={args.model} fps={args.fps} confidence={args.confidence} "
        f"tracker={args.tracker_type} depth_enable={args.depth_enable} "
        f"depth_range={args.depth_min_m:.2f}-{args.depth_max_m:.2f}m depth_head_frac={args.depth_head_fraction:.2f} "
        f"dry_run={args.dry_run}",
        flush=True,
    )

    tracks: dict[int, TrackState] = {}
    stats_msgs = 0
    stats_tracklets = 0
    stats_events = 0
    stats_depth_pass = 0
    stats_depth_reject = 0
    stats_depth_missing = 0
    started = time.monotonic()
    last_log = started

    with dai.Pipeline() as pipeline:
        camera_node = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_A)
        detection_network = pipeline.create(dai.node.DetectionNetwork).build(
            camera_node,
            dai.NNModelDescription(args.model),
            fps=args.fps,
        )
        detection_network.setConfidenceThreshold(args.confidence)

        tracker = pipeline.create(dai.node.ObjectTracker)
        tracker.setDetectionLabelsToTrack([0])
        tracker.setTrackerType(tracker_type_from_name(args.tracker_type))
        tracker.setTrackerIdAssignmentPolicy(dai.TrackerIdAssignmentPolicy.UNIQUE_ID)
        tracker.setTrackletBirthThreshold(args.birth_threshold)
        tracker.setTrackletMaxLifespan(args.max_lifespan)
        tracker.setOcclusionRatioThreshold(args.occlusion_threshold)

        detection_network.out.link(tracker.inputDetections)
        detection_network.passthrough.link(tracker.inputDetectionFrame)
        detection_network.passthrough.link(tracker.inputTrackerFrame)

        queue = tracker.out.createOutputQueue(maxSize=8, blocking=False)

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
        print(
            f"camera-counter device: name={device.getDeviceName()} usb_speed={device.getUsbSpeed().name}",
            flush=True,
        )

        latest_depth_frame: np.ndarray | None = None

        while pipeline.isRunning():
            if args.run_seconds > 0 and (time.monotonic() - started) >= args.run_seconds:
                print("camera-counter finished: run_seconds reached", flush=True)
                break

            if depth_queue is not None:
                depth_msg = depth_queue.tryGet()
                if depth_msg is not None:
                    latest_depth_frame = depth_msg.getFrame()

            msg = queue.tryGet()
            now = time.monotonic()
            if msg is None:
                if now - last_log >= args.log_interval_sec:
                    uptime = int(now - started)
                    depth_info = ""
                    if args.depth_enable:
                        depth_info = (
                            f" depth_pass={stats_depth_pass} depth_reject={stats_depth_reject} "
                            f"depth_missing={stats_depth_missing}"
                        )
                    print(
                        f"camera-counter heartbeat: uptime={uptime}s msgs={stats_msgs} tracklets={stats_tracklets} "
                        f"events={stats_events} active_tracks={len(tracks)}{depth_info}",
                        flush=True,
                    )
                    last_log = now
                time.sleep(0.01)
                continue

            stats_msgs += 1
            for tracklet in msg.tracklets:
                tid = int(tracklet.id)
                state = status_name(tracklet.status)

                if tracklet.status in {dai.Tracklet.TrackingStatus.LOST, dai.Tracklet.TrackingStatus.REMOVED}:
                    tracks.pop(tid, None)
                    continue

                if tracklet.status not in {dai.Tracklet.TrackingStatus.NEW, dai.Tracklet.TrackingStatus.TRACKED}:
                    continue

                stats_tracklets += 1
                centroid_x, centroid_y = centroid_from_tracklet(tracklet)
                axis_value = centroid_x if args.axis == "y" else centroid_y
                side = side_from_value(axis_value, args.line, args.hysteresis)

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
                        stats_depth_missing += 1
                        depth_ok = False
                    elif depth_m < args.depth_min_m or depth_m > args.depth_max_m:
                        stats_depth_reject += 1
                        depth_ok = False
                    else:
                        stats_depth_pass += 1

                current = tracks.get(tid)

                if not depth_ok:
                    if current is None:
                        tracks[tid] = TrackState(side=0, last_seen=now, depth_m=depth_m)
                    else:
                        current.side = 0
                        current.last_seen = now
                        current.depth_m = depth_m
                    continue

                if current is None:
                    tracks[tid] = TrackState(side=side, last_seen=now, depth_m=depth_m)
                    continue

                previous_side = current.side
                if side != 0:
                    current.side = side
                current.last_seen = now
                current.depth_m = depth_m

                if side == 0 or previous_side == 0 or side == previous_side:
                    continue

                if int(tracklet.age) < args.min_track_age:
                    continue

                in_count, out_count, direction = transition_to_counts(previous_side, side, args.invert_direction)
                if in_count == 0 and out_count == 0:
                    continue

                if args.dry_run:
                    stats_events += 1
                    print(
                        f"camera-counter dry-event: track_id={tid} direction={direction} in={in_count} out={out_count} "
                        f"status={state} depth_m={depth_m if depth_m is None else round(depth_m, 3)}",
                        flush=True,
                    )
                    continue

                if args.store == "central":
                    seq = next_seq(conn, seq_key)
                else:
                    seq = edge_next_seq(conn)
                confidence = float(getattr(tracklet.srcImgDetection, "confidence", 0.0))
                payload = {
                    "schema_ver": 1,
                    "source": "oakd-lite-v3",
                    "node_id": args.node_id,
                    "door_id": int(args.door_id),
                    "seq": int(seq),
                    "ts": utc_now_iso(),
                    "in": int(in_count),
                    "out": int(out_count),
                    "confidence": confidence,
                    "track_id": tid,
                    "direction": direction,
                    "axis": args.axis,
                    "line": args.line,
                }
                if args.depth_enable:
                    payload["depth_source"] = "stereo_head_shoulders"
                    payload["depth_min_m"] = round(args.depth_min_m, 3)
                    payload["depth_max_m"] = round(args.depth_max_m, 3)
                    payload["depth_head_fraction"] = round(args.depth_head_fraction, 3)
                if depth_m is not None:
                    payload["depth_m"] = round(depth_m, 3)

                stored = False
                if args.store == "central":
                    result = store_event(conn, payload, ts_received=utc_now_iso())
                    stored = result.status == "stored"
                else:
                    raw_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
                    conn.execute(
                        "INSERT INTO outbox(created_at, seq, payload_json) VALUES (?, ?, ?);",
                        (utc_now_iso(), int(seq), raw_json),
                    )
                    stored = True

                if stored:
                    stats_events += 1
                    print(
                        f"camera-counter event: seq={seq} track_id={tid} direction={direction} in={in_count} out={out_count} "
                        f"conf={confidence:.3f} depth_m={depth_m if depth_m is None else round(depth_m, 3)}",
                        flush=True,
                    )

            expired = [tid for tid, st in tracks.items() if now - st.last_seen > args.prune_sec]
            for tid in expired:
                tracks.pop(tid, None)

            if now - last_log >= args.log_interval_sec:
                uptime = int(now - started)
                depth_info = ""
                if args.depth_enable:
                    depth_info = (
                        f" depth_pass={stats_depth_pass} depth_reject={stats_depth_reject} "
                        f"depth_missing={stats_depth_missing}"
                    )
                print(
                    f"camera-counter heartbeat: uptime={uptime}s msgs={stats_msgs} tracklets={stats_tracklets} "
                    f"events={stats_events} active_tracks={len(tracks)}{depth_info}",
                    flush=True,
                )
                last_log = now

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
