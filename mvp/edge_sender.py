#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import time
from typing import Any

from common import http_post_json, load_env_file, sleep_backoff
from sqlite_store import connect, init_edge_db


def hostname_default() -> str:
    return socket.gethostname()


def parse_payload(raw_json: str) -> dict[str, Any]:
    payload = json.loads(raw_json)
    if not isinstance(payload, dict):
        raise ValueError("payload is not object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Passengers edge sender (SQLite outbox → Central HTTP).")
    parser.add_argument("--db", default="/var/lib/passengers/edge.sqlite3")
    parser.add_argument("--env", default="/etc/passengers/passengers.env")
    parser.add_argument("--central-url", default=None)
    parser.add_argument("--node-id", default=None)
    args = parser.parse_args()

    env_file = load_env_file(args.env)
    central_url_raw = args.central_url or env_file.get("CENTRAL_URLS") or env_file.get("CENTRAL_URL")
    central_urls = [u.strip() for u in (central_url_raw or "").split(",") if u.strip()]
    if not central_urls:
        central_urls = ["http://192.168.10.1:8080/api/v1/edge/events"]
    # Prefer the first URL (usually Ethernet), but keep Wi‑Fi always available as fallback.
    # To avoid slow retries on a down primary link, cache failures briefly and re-check
    # the primary periodically so it becomes preferred again after recovery.
    url_cooldown_sec = int(env_file.get("CENTRAL_URL_COOLDOWN_SEC", "5") or "5")
    url_down_until = [0.0 for _ in central_urls]
    node_id = args.node_id or env_file.get("NODE_ID") or hostname_default()
    door_id_override = env_file.get("DOOR_ID")

    conn = connect(args.db)
    init_edge_db(conn)

    attempt = 0
    while True:
        row = conn.execute("SELECT id, payload_json FROM outbox ORDER BY id ASC LIMIT 1;").fetchone()
        if not row:
            attempt = 0
            time.sleep(0.5)
            continue

        item_id = int(row[0])
        raw_json = str(row[1])
        try:
            payload = parse_payload(raw_json)
            payload["node_id"] = node_id
            if door_id_override:
                payload["door_id"] = int(door_id_override)
        except Exception:
            conn.execute("DELETE FROM outbox WHERE id = ?;", (item_id,))
            attempt = 0
            continue

        now = time.monotonic()
        for idx, url in enumerate(central_urls):
            if now < url_down_until[idx]:
                continue
            timeout_sec = 1 if idx == 0 else 3
            resp = http_post_json(url, payload, timeout_sec=timeout_sec)
            if resp.status == 200:
                conn.execute("DELETE FROM outbox WHERE id = ?;", (item_id,))
                attempt = 0
                break
            url_down_until[idx] = time.monotonic() + max(1, url_cooldown_sec)
        else:
            attempt += 1
            sleep_backoff(attempt)
            continue

        continue


if __name__ == "__main__":
    raise SystemExit(main())
