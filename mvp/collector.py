#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from common import utc_now_iso
from sqlite_store import connect, init_central_db, store_event


class Handler(BaseHTTPRequestHandler):
    server_version = "PassengersCollector/0.1"

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/v1/edge/events":
            self._send_json(404, {"error": "not_found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8", errors="replace")
            payload = json.loads(raw)
        except Exception:
            self._send_json(400, {"error": "bad_json"})
            return

        try:
            ts_received = utc_now_iso()
            with self.server.db_lock:  # type: ignore[attr-defined]
                result = store_event(self.server.db, payload, ts_received=ts_received)  # type: ignore[attr-defined]
        except (KeyError, ValueError, TypeError):
            self._send_json(422, {"error": "invalid_payload"})
            return
        except sqlite3.Error:
            self._send_json(500, {"error": "db_error"})
            return

        self._send_json(200, {"status": result.status, "ts_received": ts_received})

    def log_message(self, fmt: str, *args: Any) -> None:
        if self.path == "/health":
            return
        super().log_message(fmt, *args)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Passengers Central collector (HTTP → SQLite).")
    parser.add_argument("--bind", default="192.168.10.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--db", default="/var/lib/passengers/central.sqlite3")
    args = parser.parse_args()

    db = connect(args.db)
    init_central_db(db)

    httpd = ThreadingHTTPServer((args.bind, args.port), Handler)
    httpd.db = db  # type: ignore[attr-defined]
    httpd.db_lock = threading.Lock()  # type: ignore[attr-defined]

    try:
        httpd.serve_forever()
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

