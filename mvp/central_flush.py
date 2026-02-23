#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import subprocess
import time
from collections import defaultdict
from typing import Any

from common import http_post_json, load_env_file, utc_now_iso
from sqlite_store import connect, enqueue_batch, init_central_db, mark_batch_sent, meta_get, meta_set


def hostname_static() -> str:
    try:
        out = subprocess.check_output(["hostnamectl", "--static"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        out = socket.gethostname().strip()
    return out or "central-gw"

def _parse_iso_epoch(value: str | None) -> float | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        # Support both "...Z" and "+00:00"
        from datetime import datetime

        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def load_latest_gps(
    path: str = "/var/lib/passengers/gps/latest.json",
    max_age_sec: int = 120,
) -> dict[str, float] | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None

    if not bool(data.get("fix")):
        return None

    lat = data.get("lat")
    lon = data.get("lon")
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except Exception:
        return None

    updated_at = data.get("updated_at")
    epoch = _parse_iso_epoch(updated_at)
    if epoch is not None:
        age = max(0, int(time.time() - epoch))
        if age > int(max_age_sec):
            return None

    return {"lat": lat_f, "lon": lon_f}


def normalize_stop_mode(value: str | None) -> str:
    mode = str(value or "").strip().lower()
    if mode in {"manual", "timer"}:
        return mode
    if mode:
        return mode
    return "timer"


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate Central events into stop batch and enqueue/send to backend.")
    parser.add_argument("--db", default="/var/lib/passengers/central.sqlite3")
    parser.add_argument("--env", default="/etc/passengers/passengers.env")
    parser.add_argument("--vehicle-id", default=None)
    parser.add_argument("--central-id", default=None)
    parser.add_argument("--stop-mode", default=None, help="manual|timer (default: from env STOP_MODE or timer)")
    parser.add_argument("--backend-url", default=None)
    parser.add_argument("--backend-api-key", default=None)
    parser.add_argument("--send-now", action="store_true", help="Try to send immediately (default)")
    parser.add_argument("--no-send", action="store_true", help="Only enqueue batch locally")
    args = parser.parse_args()

    env_file = load_env_file(args.env)
    vehicle_id = args.vehicle_id or env_file.get("VEHICLE_ID")
    central_id = args.central_id or env_file.get("CENTRAL_ID") or hostname_static()
    stop_mode = normalize_stop_mode(args.stop_mode or env_file.get("STOP_MODE"))
    backend_url = args.backend_url or env_file.get("BACKEND_URL")
    backend_api_key = args.backend_api_key or env_file.get("BACKEND_API_KEY")

    send_now = True
    if args.no_send:
        send_now = False
    if args.send_now:
        send_now = True

    if not vehicle_id:
        raise SystemExit("Missing VEHICLE_ID (see /etc/passengers/passengers.env)")
    if send_now and (not backend_url or not backend_api_key):
        raise SystemExit("Missing BACKEND_URL/BACKEND_API_KEY (see /etc/passengers/passengers.env)")

    conn = connect(args.db)
    init_central_db(conn)

    last_flushed_id = int(meta_get(conn, "last_flushed_event_id", "0"))
    stop_counter = int(meta_get(conn, "stop_counter", "0")) + 1

    rows = conn.execute(
        "SELECT id, door_id, in_count, out_count FROM events WHERE id > ? ORDER BY id ASC;",
        (last_flushed_id,),
    ).fetchall()

    if not rows:
        print("nothing_to_flush")
        return 0

    totals: dict[int, dict[str, int]] = defaultdict(lambda: {"in": 0, "out": 0})
    max_id = last_flushed_id
    for row in rows:
        event_id = int(row[0])
        door_id = int(row[1])
        totals[door_id]["in"] += int(row[2])
        totals[door_id]["out"] += int(row[3])
        max_id = max(max_id, event_id)

    ts_sent = utc_now_iso()
    batch_id = f"{central_id}:{ts_sent}:{stop_mode}:{stop_counter:04d}"
    gps = load_latest_gps()
    payload: dict[str, Any] = {
        "schema_ver": 1,
        "vehicle_id": vehicle_id,
        "batch_id": batch_id,
        "ts_sent": ts_sent,
        "stop": {
            "stop_id": f"{stop_counter:04d}",
            "method": stop_mode,
            "ts_start": None,
            "ts_end": ts_sent,
            "gps": gps,
        },
        "doors": [{"door_id": d, "in": v["in"], "out": v["out"]} for d, v in sorted(totals.items())],
    }

    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    enqueue_batch(conn, batch_id=batch_id, created_at=ts_sent, payload_json=payload_json)

    if send_now:
        headers = {"Authorization": f"Bearer {backend_api_key}"}
        resp = http_post_json(backend_url, payload, headers=headers, timeout_sec=8)
        if resp.status != 200:
            print(json.dumps({"status": "queued", "batch_id": batch_id, "error": f"http_{resp.status}"}, ensure_ascii=False))
        else:
            mark_batch_sent(conn, batch_id=batch_id, sent_at=utc_now_iso())

    meta_set(conn, "last_flushed_event_id", str(max_id))
    meta_set(conn, "stop_counter", str(stop_counter))
    conn.commit()

    print(json.dumps({"status": "queued", "batch_id": batch_id, "max_event_id": max_id}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
