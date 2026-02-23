#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from typing import Any

from common import http_post_json, load_env_file, sleep_backoff, utc_now_iso
from sqlite_store import connect, init_central_db, mark_batch_attempt, mark_batch_sent


def main() -> int:
    parser = argparse.ArgumentParser(description="Central uplink sender (SQLite outbox -> Backend HTTP).")
    parser.add_argument("--db", default="/var/lib/passengers/central.sqlite3")
    parser.add_argument("--env", default="/etc/passengers/passengers.env")
    parser.add_argument("--backend-url", default=None)
    parser.add_argument("--backend-api-key", default=None)
    args = parser.parse_args()

    env_file = load_env_file(args.env)
    backend_url = args.backend_url or env_file.get("BACKEND_URL")
    backend_api_key = args.backend_api_key or env_file.get("BACKEND_API_KEY")
    if not backend_url or not backend_api_key:
        raise SystemExit("Missing BACKEND_URL/BACKEND_API_KEY (see /etc/passengers/passengers.env)")

    conn = connect(args.db)
    init_central_db(conn)

    attempt = 0
    while True:
        row = conn.execute(
            "SELECT batch_id, payload_json, attempts FROM batches_outbox WHERE status='pending' ORDER BY created_at ASC LIMIT 1;"
        ).fetchone()
        if not row:
            attempt = 0
            import time

            time.sleep(1.0)
            continue

        batch_id = str(row[0])
        payload_json = str(row[1])

        try:
            payload: dict[str, Any] = json.loads(payload_json)
        except Exception:
            # malformed; mark attempt and skip forever by setting sent
            now = utc_now_iso()
            mark_batch_attempt(conn, batch_id=batch_id, attempt_at=now, error="bad_json")
            mark_batch_sent(conn, batch_id=batch_id, sent_at=now)
            conn.commit()
            attempt = 0
            continue

        now = utc_now_iso()
        headers = {"Authorization": f"Bearer {backend_api_key}"}
        resp = http_post_json(backend_url, payload, headers=headers, timeout_sec=10)
        if resp.status == 200:
            mark_batch_sent(conn, batch_id=batch_id, sent_at=utc_now_iso())
            conn.commit()
            attempt = 0
            continue

        mark_batch_attempt(conn, batch_id=batch_id, attempt_at=utc_now_iso(), error=f"http_{resp.status}")
        conn.commit()
        attempt += 1
        sleep_backoff(attempt)


if __name__ == "__main__":
    raise SystemExit(main())

