#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import time
from typing import Any

from common import load_env_file
from sqlite_store import connect, init_central_db, init_edge_db


def to_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        parsed = int(str(value).strip())
        return parsed if parsed >= 0 else default
    except Exception:
        return default


def to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def resolve_mode(mode: str, env: dict[str, str]) -> str:
    if mode in {"edge", "central"}:
        return mode
    role = str(env.get("NODE_ROLE") or "").strip().lower()
    if role in {"edge", "central"}:
        return role
    return "central"


def sql_count(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> int:
    row = conn.execute(query, params).fetchone()
    if not row:
        return 0
    return int(row[0])


def prune_edge(conn: sqlite3.Connection, env: dict[str, str]) -> dict[str, int]:
    max_rows = to_int(env.get("EDGE_OUTBOX_MAX_ROWS"), 50000)
    max_age_sec = to_int(env.get("EDGE_OUTBOX_MAX_AGE_SEC"), 172800)
    now_epoch = int(time.time())
    min_epoch = max(0, now_epoch - max_age_sec)

    before = sql_count(conn, "SELECT COUNT(*) FROM outbox;")
    deleted_age = conn.execute(
        "DELETE FROM outbox WHERE created_at IS NOT NULL AND CAST(strftime('%s', created_at) AS INTEGER) < ?;",
        (min_epoch,),
    ).rowcount

    after_age = sql_count(conn, "SELECT COUNT(*) FROM outbox;")
    overflow = max(0, after_age - max_rows)
    deleted_overflow = 0
    if overflow > 0:
        deleted_overflow = conn.execute(
            "DELETE FROM outbox WHERE id IN (SELECT id FROM outbox ORDER BY id ASC LIMIT ?);",
            (overflow,),
        ).rowcount

    conn.commit()
    final_count = sql_count(conn, "SELECT COUNT(*) FROM outbox;")
    return {
        "before": before,
        "deleted_age": int(deleted_age or 0),
        "deleted_overflow": int(deleted_overflow or 0),
        "after": final_count,
        "max_rows": max_rows,
        "max_age_sec": max_age_sec,
    }


def prune_central(conn: sqlite3.Connection, env: dict[str, str]) -> dict[str, int]:
    events_max_rows = to_int(env.get("CENTRAL_EVENTS_MAX_ROWS"), 300000)
    events_max_age_sec = to_int(env.get("CENTRAL_EVENTS_MAX_AGE_SEC"), 1209600)
    sent_max_rows = to_int(env.get("CENTRAL_SENT_BATCHES_MAX_ROWS"), 50000)
    sent_max_age_sec = to_int(env.get("CENTRAL_SENT_BATCHES_MAX_AGE_SEC"), 2592000)
    pending_max_rows = max(1, to_int(env.get("CENTRAL_PENDING_BATCHES_MAX_ROWS"), 10000))
    pending_max_age_sec = to_int(env.get("CENTRAL_PENDING_BATCHES_MAX_AGE_SEC"), 2592000)
    pending_drop_age = to_bool(env.get("CENTRAL_PENDING_BATCHES_DROP_AGE"), False)

    now_epoch = int(time.time())
    events_min_epoch = max(0, now_epoch - events_max_age_sec)
    sent_min_epoch = max(0, now_epoch - sent_max_age_sec)
    pending_min_epoch = max(0, now_epoch - pending_max_age_sec)

    events_before = sql_count(conn, "SELECT COUNT(*) FROM events;")
    sent_before = sql_count(conn, "SELECT COUNT(*) FROM batches_outbox WHERE status='sent';")
    pending_before = sql_count(conn, "SELECT COUNT(*) FROM batches_outbox WHERE status='pending';")

    events_deleted_age = conn.execute(
        "DELETE FROM events WHERE ts_received IS NOT NULL AND CAST(strftime('%s', ts_received) AS INTEGER) < ?;",
        (events_min_epoch,),
    ).rowcount
    sent_deleted_age = conn.execute(
        "DELETE FROM batches_outbox WHERE status='sent' AND sent_at IS NOT NULL AND CAST(strftime('%s', sent_at) AS INTEGER) < ?;",
        (sent_min_epoch,),
    ).rowcount

    events_after_age = sql_count(conn, "SELECT COUNT(*) FROM events;")
    events_overflow = max(0, events_after_age - events_max_rows)
    events_deleted_overflow = 0
    if events_overflow > 0:
        events_deleted_overflow = conn.execute(
            "DELETE FROM events WHERE id IN (SELECT id FROM events ORDER BY id ASC LIMIT ?);",
            (events_overflow,),
        ).rowcount

    sent_after_age = sql_count(conn, "SELECT COUNT(*) FROM batches_outbox WHERE status='sent';")
    sent_overflow = max(0, sent_after_age - sent_max_rows)
    sent_deleted_overflow = 0
    if sent_overflow > 0:
        sent_deleted_overflow = conn.execute(
            "DELETE FROM batches_outbox WHERE batch_id IN ("
            "SELECT batch_id FROM batches_outbox WHERE status='sent' ORDER BY COALESCE(sent_at, created_at) ASC LIMIT ?"
            ");",
            (sent_overflow,),
        ).rowcount

    pending_deleted_age = 0
    if pending_drop_age:
        pending_deleted_age = conn.execute(
            "DELETE FROM batches_outbox WHERE status='pending' AND created_at IS NOT NULL "
            "AND CAST(strftime('%s', created_at) AS INTEGER) < ?;",
            (pending_min_epoch,),
        ).rowcount

    pending_after_age = sql_count(conn, "SELECT COUNT(*) FROM batches_outbox WHERE status='pending';")
    pending_overflow = max(0, pending_after_age - pending_max_rows)
    pending_deleted_overflow = 0
    if pending_overflow > 0:
        pending_deleted_overflow = conn.execute(
            "DELETE FROM batches_outbox WHERE batch_id IN ("
            "SELECT batch_id FROM batches_outbox WHERE status='pending' "
            "ORDER BY COALESCE(created_at, batch_id) ASC LIMIT ?"
            ");",
            (pending_overflow,),
        ).rowcount

    conn.commit()
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")

    return {
        "events_before": events_before,
        "events_deleted_age": int(events_deleted_age or 0),
        "events_deleted_overflow": int(events_deleted_overflow or 0),
        "events_after": sql_count(conn, "SELECT COUNT(*) FROM events;"),
        "events_max_rows": events_max_rows,
        "events_max_age_sec": events_max_age_sec,
        "sent_before": sent_before,
        "sent_deleted_age": int(sent_deleted_age or 0),
        "sent_deleted_overflow": int(sent_deleted_overflow or 0),
        "sent_after": sql_count(conn, "SELECT COUNT(*) FROM batches_outbox WHERE status='sent';"),
        "sent_max_rows": sent_max_rows,
        "sent_max_age_sec": sent_max_age_sec,
        "pending_before": pending_before,
        "pending_deleted_age": int(pending_deleted_age or 0),
        "pending_deleted_overflow": int(pending_deleted_overflow or 0),
        "pending_after": sql_count(conn, "SELECT COUNT(*) FROM batches_outbox WHERE status='pending';"),
        "pending_max_rows": pending_max_rows,
        "pending_max_age_sec": pending_max_age_sec,
        "pending_drop_age": 1 if pending_drop_age else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune Edge/Central SQLite queues by age and size limits.")
    parser.add_argument("--mode", default="auto", choices=["auto", "edge", "central"])
    parser.add_argument("--env", default="/etc/passengers/passengers.env")
    parser.add_argument("--edge-db", default="/var/lib/passengers/edge.sqlite3")
    parser.add_argument("--central-db", default="/var/lib/passengers/central.sqlite3")
    args = parser.parse_args()

    env = load_env_file(args.env)
    mode = resolve_mode(args.mode, env)
    report: dict[str, Any] = {"mode": mode, "status": "ok"}

    if mode == "edge":
        conn = connect(args.edge_db)
        try:
            init_edge_db(conn)
            report["queue"] = prune_edge(conn, env)
        finally:
            conn.close()
    else:
        conn = connect(args.central_db)
        try:
            init_central_db(conn)
            report["queue"] = prune_central(conn, env)
        finally:
            conn.close()

    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
