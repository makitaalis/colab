from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Any


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def connect(db_path: str) -> sqlite3.Connection:
    ensure_parent_dir(db_path)
    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_edge_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS outbox (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          created_at TEXT NOT NULL,
          seq INTEGER NOT NULL,
          payload_json TEXT NOT NULL
        );
        """
    )
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_outbox_seq ON outbox(seq);")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
          k TEXT PRIMARY KEY,
          v TEXT NOT NULL
        );
        """
    )


def edge_next_seq(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT v FROM meta WHERE k='next_seq';").fetchone()
    next_seq = int(row[0]) if row else 1
    conn.execute(
        "INSERT INTO meta(k, v) VALUES ('next_seq', ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v;",
        (str(next_seq + 1),),
    )
    return next_seq


def init_central_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts_received TEXT NOT NULL,
          node_id TEXT NOT NULL,
          door_id INTEGER NOT NULL,
          seq INTEGER NOT NULL,
          ts_event TEXT,
          in_count INTEGER NOT NULL,
          out_count INTEGER NOT NULL,
          confidence REAL,
          raw_json TEXT NOT NULL,
          UNIQUE(node_id, seq)
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
          k TEXT PRIMARY KEY,
          v TEXT NOT NULL
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS batches_outbox (
          batch_id TEXT PRIMARY KEY,
          created_at TEXT NOT NULL,
          payload_json TEXT NOT NULL,
          status TEXT NOT NULL, -- pending|sent
          attempts INTEGER NOT NULL DEFAULT 0,
          last_attempt_at TEXT,
          last_error TEXT,
          sent_at TEXT
        );
        """
    )


@dataclass(frozen=True)
class StoreResult:
    status: str  # "stored" | "duplicate"
    id: int | None


def store_event(conn: sqlite3.Connection, payload: dict[str, Any], *, ts_received: str) -> StoreResult:
    raw_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    node_id = str(payload["node_id"])
    door_id = int(payload["door_id"])
    seq = int(payload["seq"])
    ts_event = payload.get("ts")
    in_count = int(payload.get("in", 0))
    out_count = int(payload.get("out", 0))
    confidence = payload.get("confidence")
    try:
        cur = conn.execute(
            """
            INSERT INTO events(ts_received, node_id, door_id, seq, ts_event, in_count, out_count, confidence, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (ts_received, node_id, door_id, seq, ts_event, in_count, out_count, confidence, raw_json),
        )
        return StoreResult(status="stored", id=int(cur.lastrowid))
    except sqlite3.IntegrityError:
        return StoreResult(status="duplicate", id=None)


def meta_get(conn: sqlite3.Connection, key: str, default: str) -> str:
    row = conn.execute("SELECT v FROM meta WHERE k = ?;", (key,)).fetchone()
    if not row:
        return default
    return str(row[0])


def meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT INTO meta(k, v) VALUES (?, ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v;", (key, value))


def enqueue_batch(conn: sqlite3.Connection, *, batch_id: str, created_at: str, payload_json: str) -> None:
    conn.execute(
        """
        INSERT INTO batches_outbox(batch_id, created_at, payload_json, status)
        VALUES (?, ?, ?, 'pending')
        ON CONFLICT(batch_id) DO NOTHING;
        """,
        (batch_id, created_at, payload_json),
    )


def mark_batch_attempt(
    conn: sqlite3.Connection,
    *,
    batch_id: str,
    attempt_at: str,
    error: str | None,
) -> None:
    conn.execute(
        """
        UPDATE batches_outbox
        SET attempts = attempts + 1,
            last_attempt_at = ?,
            last_error = ?
        WHERE batch_id = ?;
        """,
        (attempt_at, error, batch_id),
    )


def mark_batch_sent(conn: sqlite3.Connection, *, batch_id: str, sent_at: str) -> None:
    conn.execute(
        """
        UPDATE batches_outbox
        SET status='sent',
            sent_at=?,
            last_error=NULL
        WHERE batch_id = ?;
        """,
        (sent_at, batch_id),
    )
