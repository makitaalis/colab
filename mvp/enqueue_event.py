#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3

from common import utc_now_iso
from sqlite_store import connect, edge_next_seq, init_edge_db


def main() -> int:
    parser = argparse.ArgumentParser(description="Enqueue a test event into edge outbox SQLite.")
    parser.add_argument("--db", default="/var/lib/passengers/edge.sqlite3")
    parser.add_argument("--door-id", type=int, required=True)
    parser.add_argument("--in", dest="in_count", type=int, default=0)
    parser.add_argument("--out", dest="out_count", type=int, default=0)
    parser.add_argument("--confidence", type=float, default=0.9)
    parser.add_argument("--ts", default=None, help="ISO timestamp; default=now UTC")
    parser.add_argument("--seq", type=int, default=None, help="Override seq; default=auto increment")
    args = parser.parse_args()

    conn = connect(args.db)
    init_edge_db(conn)

    seq = args.seq or edge_next_seq(conn)
    payload = {
        "door_id": args.door_id,
        "ts": args.ts or utc_now_iso(),
        "in": max(0, int(args.in_count)),
        "out": max(0, int(args.out_count)),
        "confidence": float(args.confidence),
        "seq": int(seq),
    }
    conn.execute(
        "INSERT INTO outbox(created_at, seq, payload_json) VALUES (?, ?, ?);",
        (utc_now_iso(), int(seq), json.dumps(payload, ensure_ascii=False, separators=(",", ":"))),
    )
    print(f"enqueued seq={seq}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
