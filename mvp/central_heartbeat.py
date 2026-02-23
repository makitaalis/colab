#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

from common import http_post_json, load_env_file, utc_now_iso
from sqlite_store import connect, init_central_db

EXPECTED_DOORS: list[tuple[str, int, str]] = [
    ("door-1", 2, "192.168.10.11"),
    ("door-2", 3, "192.168.10.12"),
]

SERVICES: list[tuple[str, str]] = [
    ("passengers-collector", "passengers-collector.service"),
    ("passengers-central-uplink", "passengers-central-uplink.service"),
    ("passengers-central-flush.timer", "passengers-central-flush.timer"),
    ("wg-quick@wg0", "wg-quick@wg0.service"),
]


def normalize_stop_mode(value: str | None) -> str:
    mode = str(value or "").strip().lower()
    if mode in {"manual", "timer"}:
        return mode
    return "timer"


def systemd_state(unit: str) -> str:
    try:
        out = subprocess.check_output(["systemctl", "is-active", unit], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"
    if not out:
        return "unknown"
    return out


def hostname_static() -> str:
    try:
        out = subprocess.check_output(["hostnamectl", "--static"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        out = socket.gethostname().strip()
    return out or "central-gw"


def time_sync_state() -> str:
    commands = [
        ["timedatectl", "show", "--property=SystemClockSynchronized", "--value"],
        ["timedatectl", "show", "--property=NTPSynchronized", "--value"],
    ]
    observed: list[str] = []
    for cmd in commands:
        try:
            value = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip().lower()
        except Exception:
            continue
        observed.append(value or "unknown")
        if value in {"yes", "true", "1"}:
            return "synced"
    if observed:
        return "unsynced"
    return "unknown"


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def age_sec(value: str | None) -> int | None:
    dt = parse_iso(value)
    if not dt:
        return None
    return int((datetime.now(timezone.utc) - dt).total_seconds())


def ping_reachable(ip: str) -> bool:
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except Exception:
        return False
    return result.returncode == 0


def wg_latest_handshake_age_sec() -> int | None:
    try:
        out = subprocess.check_output(["wg", "show", "wg0", "latest-handshakes"], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return None

    now = int(time.time())
    best_age: int | None = None
    for raw in out.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            epoch = int(parts[1])
        except Exception:
            continue
        if epoch <= 0:
            continue
        age = max(0, now - epoch)
        if best_age is None or age < best_age:
            best_age = age
    return best_age


def load_gps_snapshot(path: str = "/var/lib/passengers/gps/latest.json") -> dict[str, Any] | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None

    updated_at = data.get("updated_at")
    age: int | None = None
    if isinstance(updated_at, str) and updated_at.strip():
        try:
            ts = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            age = max(0, int((datetime.now(timezone.utc) - ts).total_seconds()))
        except Exception:
            age = None

    gps = {
        "source": str(data.get("source") or "mmcli"),
        "updated_at": updated_at,
        "age_sec": age,
        "fix": bool(data.get("fix", False)),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
    }
    # Keep payload small and predictable.
    if not gps["fix"]:
        gps["lat"] = None
        gps["lon"] = None
    return gps


def derive_heartbeat_url(explicit: str | None, backend_url: str | None) -> str | None:
    if explicit:
        return explicit
    if not backend_url:
        return None
    suffix = "/api/v1/ingest/stops"
    if backend_url.endswith(suffix):
        return backend_url[: -len(suffix)] + "/api/v1/ingest/central-heartbeat"
    return None


def queue_snapshot(conn: sqlite3.Connection) -> dict[str, Any]:
    events_total = int(conn.execute("SELECT COUNT(*) FROM events;").fetchone()[0])
    last_event_ts = conn.execute("SELECT MAX(ts_received) FROM events;").fetchone()[0]
    pending_batches = int(conn.execute("SELECT COUNT(*) FROM batches_outbox WHERE status='pending';").fetchone()[0])
    sent_batches = int(conn.execute("SELECT COUNT(*) FROM batches_outbox WHERE status='sent';").fetchone()[0])
    pending_oldest = conn.execute(
        "SELECT MIN(created_at) FROM batches_outbox WHERE status='pending';"
    ).fetchone()[0]

    rows = conn.execute(
        """
        SELECT node_id, door_id, MAX(ts_received) AS last_ts
        FROM events
        GROUP BY node_id, door_id
        ORDER BY door_id ASC, node_id ASC;
        """
    ).fetchall()

    by_node_door: dict[tuple[str, int], str | None] = {}
    for row in rows:
        by_node_door[(str(row[0]), int(row[1]))] = row[2]

    doors: list[dict[str, Any]] = []
    consumed: set[tuple[str, int]] = set()
    for node_id, door_id, ip in EXPECTED_DOORS:
        last_ts = by_node_door.get((node_id, door_id))
        consumed.add((node_id, door_id))
        doors.append(
            {
                "node_id": node_id,
                "door_id": door_id,
                "ip": ip,
                "reachable": ping_reachable(ip),
                "last_event_ts_received": last_ts,
                "last_event_age_sec": age_sec(last_ts),
            }
        )

    for (node_id, door_id), last_ts in by_node_door.items():
        if (node_id, door_id) in consumed:
            continue
        doors.append(
            {
                "node_id": node_id,
                "door_id": door_id,
                "ip": None,
                "reachable": None,
                "last_event_ts_received": last_ts,
                "last_event_age_sec": age_sec(last_ts),
            }
        )

    return {
        "events_total": events_total,
        "pending_batches": pending_batches,
        "sent_batches": sent_batches,
        "last_event_ts_received": last_event_ts,
        "pending_oldest_created_at": pending_oldest,
        "pending_oldest_age_sec": age_sec(pending_oldest),
        "wg_latest_handshake_age_sec": wg_latest_handshake_age_sec(),
        "doors": doors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Send central heartbeat to backend.")
    parser.add_argument("--db", default="/var/lib/passengers/central.sqlite3")
    parser.add_argument("--env", default="/etc/passengers/passengers.env")
    parser.add_argument("--backend-heartbeat-url", default=None)
    parser.add_argument("--backend-api-key", default=None)
    parser.add_argument("--central-id", default=None)
    parser.add_argument("--timeout-sec", type=int, default=8)
    args = parser.parse_args()

    env_file = load_env_file(args.env)
    backend_heartbeat_url = derive_heartbeat_url(
        args.backend_heartbeat_url or env_file.get("BACKEND_HEARTBEAT_URL"),
        env_file.get("BACKEND_URL"),
    )
    backend_api_key = args.backend_api_key or env_file.get("BACKEND_API_KEY")
    vehicle_id = env_file.get("VEHICLE_ID")
    central_id = args.central_id or env_file.get("CENTRAL_ID") or hostname_static()
    stop_mode = normalize_stop_mode(env_file.get("STOP_MODE"))

    if not backend_heartbeat_url or not backend_api_key:
        raise SystemExit("Missing BACKEND_HEARTBEAT_URL/BACKEND_API_KEY (see /etc/passengers/passengers.env)")

    services = {name: systemd_state(unit) for name, unit in SERVICES}
    conn = connect(args.db)
    try:
        init_central_db(conn)
        queue = queue_snapshot(conn)
    finally:
        conn.close()

    payload: dict[str, Any] = {
        "schema_ver": 1,
        "central_id": central_id,
        "vehicle_id": vehicle_id,
        "ts_sent": utc_now_iso(),
        "time_sync": time_sync_state(),
        "gps": load_gps_snapshot() if os.path.exists("/var/lib/passengers/gps/latest.json") else None,
        "services": services,
        "queue": {
            "events_total": queue["events_total"],
            "pending_batches": queue["pending_batches"],
            "sent_batches": queue["sent_batches"],
            "last_event_ts_received": queue["last_event_ts_received"],
            "pending_oldest_created_at": queue["pending_oldest_created_at"],
            "pending_oldest_age_sec": queue["pending_oldest_age_sec"],
            "wg_latest_handshake_age_sec": queue["wg_latest_handshake_age_sec"],
            "stop_mode": stop_mode,
        },
        "doors": queue["doors"],
    }

    headers = {"Authorization": f"Bearer {backend_api_key}"}
    resp = http_post_json(
        backend_heartbeat_url,
        payload,
        headers=headers,
        timeout_sec=max(1, int(args.timeout_sec)),
    )
    if resp.status == 200:
        print(json.dumps({"status": "sent", "central_id": central_id, "ts_sent": payload["ts_sent"]}, ensure_ascii=False))
        return 0

    print(
        json.dumps(
            {
                "status": "error",
                "central_id": central_id,
                "http_status": resp.status,
                "response": resp.body[:400],
            },
            ensure_ascii=False,
        )
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
