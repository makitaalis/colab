from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import aiosqlite


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


@dataclass(frozen=True)
class IngestResult:
    status: str  # "stored" | "duplicate"
    ts_received: str


@dataclass(frozen=True)
class HeartbeatResult:
    status: str  # "stored"
    ts_received: str


async def init_db(db_path: str) -> None:
    ensure_parent_dir(db_path)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA synchronous=NORMAL;")
        await db.execute("PRAGMA foreign_keys=ON;")

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS stops (
              batch_id TEXT PRIMARY KEY,
              schema_ver INTEGER NOT NULL,
              vehicle_id TEXT NOT NULL,
              ts_sent TEXT,
              ts_received TEXT NOT NULL,
              stop_id TEXT,
              ts_start TEXT,
              ts_end TEXT,
              gps_lat REAL,
              gps_lon REAL,
              raw_json TEXT NOT NULL
            );
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS stop_door_counts (
              batch_id TEXT NOT NULL,
              door_id INTEGER NOT NULL,
              in_count INTEGER NOT NULL,
              out_count INTEGER NOT NULL,
              PRIMARY KEY(batch_id, door_id),
              FOREIGN KEY(batch_id) REFERENCES stops(batch_id) ON DELETE CASCADE
            );
            """
        )

        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_stops_vehicle_ts ON stops(vehicle_id, ts_received);"
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS central_heartbeats (
              central_id TEXT PRIMARY KEY,
              vehicle_id TEXT,
              schema_ver INTEGER NOT NULL,
              ts_sent TEXT,
              ts_received TEXT NOT NULL,
              time_sync TEXT,
              collector_state TEXT,
              uplink_state TEXT,
              flush_timer_state TEXT,
              wg_state TEXT,
              events_total INTEGER NOT NULL DEFAULT 0,
              pending_batches INTEGER NOT NULL DEFAULT 0,
              sent_batches INTEGER NOT NULL DEFAULT 0,
              last_event_ts_received TEXT,
              doors_json TEXT NOT NULL,
              raw_json TEXT NOT NULL
            );
            """
        )

        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_central_heartbeats_ts ON central_heartbeats(ts_received);"
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS central_heartbeat_history (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              central_id TEXT NOT NULL,
              vehicle_id TEXT,
              schema_ver INTEGER NOT NULL,
              ts_sent TEXT,
              ts_received TEXT NOT NULL,
              time_sync TEXT,
              collector_state TEXT,
              uplink_state TEXT,
              flush_timer_state TEXT,
              wg_state TEXT,
              events_total INTEGER NOT NULL DEFAULT 0,
              pending_batches INTEGER NOT NULL DEFAULT 0,
              sent_batches INTEGER NOT NULL DEFAULT 0,
              last_event_ts_received TEXT,
              doors_json TEXT NOT NULL,
              raw_json TEXT NOT NULL
            );
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_central_heartbeat_history_central_ts
            ON central_heartbeat_history(central_id, ts_received DESC);
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_states (
              central_id TEXT NOT NULL,
              code TEXT NOT NULL,
              acked_at TEXT,
              acked_by TEXT,
              ack_note TEXT,
              silenced_until TEXT,
              silenced_by TEXT,
              silence_note TEXT,
              updated_at TEXT NOT NULL,
              PRIMARY KEY(central_id, code)
            );
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alert_states_silenced_until
            ON alert_states(silenced_until);
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_actions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts TEXT NOT NULL,
              action TEXT NOT NULL,
              central_id TEXT NOT NULL,
              code TEXT NOT NULL,
              actor TEXT,
              note TEXT,
              silenced_until TEXT
            );
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alert_actions_central_ts
            ON alert_actions(central_id, ts DESC);
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alert_actions_code_ts
            ON alert_actions(code, ts DESC);
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
              central_id TEXT NOT NULL,
              code TEXT NOT NULL,
              vehicle_id TEXT,
              severity TEXT NOT NULL,
              status TEXT NOT NULL,
              message TEXT,
              first_seen_ts TEXT NOT NULL,
              last_seen_ts TEXT NOT NULL,
              resolved_ts TEXT,
              occurrences INTEGER NOT NULL DEFAULT 1,
              acked_at TEXT,
              acked_by TEXT,
              silenced_until TEXT,
              silenced_by TEXT,
              updated_at TEXT NOT NULL,
              PRIMARY KEY(central_id, code)
            );
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_incidents_status_severity
            ON incidents(status, severity, updated_at DESC);
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_incidents_central_updated
            ON incidents(central_id, updated_at DESC);
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS incident_notifications (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts TEXT NOT NULL,
              central_id TEXT NOT NULL,
              code TEXT NOT NULL,
              severity TEXT NOT NULL,
              event TEXT NOT NULL,
              channel TEXT NOT NULL,
              destination TEXT,
              status TEXT NOT NULL,
              message TEXT,
              error TEXT
            );
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_incident_notifications_central_ts
            ON incident_notifications(central_id, ts DESC);
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_incident_notifications_status_ts
            ON incident_notifications(status, channel, ts DESC);
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS notification_settings (
              key TEXT PRIMARY KEY,
              value TEXT,
              updated_at TEXT NOT NULL
            );
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS client_profiles (
              client_id TEXT PRIMARY KEY,
              full_name TEXT,
              company TEXT,
              email TEXT,
              phone TEXT,
              locale TEXT NOT NULL DEFAULT 'uk',
              updated_at TEXT NOT NULL
            );
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS client_notification_settings (
              client_id TEXT PRIMARY KEY,
              notify_email INTEGER NOT NULL DEFAULT 1,
              notify_sms INTEGER NOT NULL DEFAULT 0,
              notify_push INTEGER NOT NULL DEFAULT 0,
              notify_level TEXT NOT NULL DEFAULT 'all',
              digest_window TEXT NOT NULL DEFAULT '24h',
              updated_at TEXT NOT NULL
            );
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_client_notification_settings_updated
            ON client_notification_settings(updated_at DESC);
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS monitor_policy_overrides (
              central_id TEXT PRIMARY KEY,
              warn_heartbeat_age_sec INTEGER,
              bad_heartbeat_age_sec INTEGER,
              warn_pending_batches INTEGER,
              bad_pending_batches INTEGER,
              warn_wg_age_sec INTEGER,
              bad_wg_age_sec INTEGER,
              updated_at TEXT NOT NULL
            );
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_monitor_policy_overrides_updated
            ON monitor_policy_overrides(updated_at DESC);
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_audit_log (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts TEXT NOT NULL,
              actor TEXT,
              role TEXT NOT NULL,
              action TEXT NOT NULL,
              method TEXT NOT NULL,
              path TEXT NOT NULL,
              status TEXT NOT NULL,
              status_code INTEGER NOT NULL,
              client_ip TEXT,
              details_json TEXT
            );
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_admin_audit_ts
            ON admin_audit_log(ts DESC);
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_admin_audit_action_ts
            ON admin_audit_log(action, ts DESC);
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_admin_audit_role_ts
            ON admin_audit_log(role, ts DESC);
            """
        )

        defaults = {
            "notify_telegram": "1",
            "notify_email": "0",
            "mute_until": "",
            "rate_limit_sec": "300",
            "min_severity": "bad",
            "stale_always_notify": "1",
            "escalation_sec": "1800",
        }
        ts_now = utc_now_iso()
        for key, value in defaults.items():
            await db.execute(
                """
                INSERT OR IGNORE INTO notification_settings(key, value, updated_at)
                VALUES (?, ?, ?);
                """,
                (key, value, ts_now),
            )
        await db.commit()


async def ingest_stop(db_path: str, payload: dict[str, Any]) -> IngestResult:
    ts_received = utc_now_iso()
    batch_id = str(payload["batch_id"])
    vehicle_id = str(payload["vehicle_id"])
    schema_ver = int(payload.get("schema_ver", 1))

    stop = payload.get("stop") or {}
    gps = stop.get("gps") or {}

    doors = payload.get("doors") or []
    raw_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys=ON;")
        try:
            await db.execute("BEGIN;")
            await db.execute(
                """
                INSERT INTO stops(
                  batch_id, schema_ver, vehicle_id, ts_sent, ts_received,
                  stop_id, ts_start, ts_end, gps_lat, gps_lon, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    batch_id,
                    schema_ver,
                    vehicle_id,
                    payload.get("ts_sent"),
                    ts_received,
                    stop.get("stop_id"),
                    stop.get("ts_start"),
                    stop.get("ts_end"),
                    gps.get("lat"),
                    gps.get("lon"),
                    raw_json,
                ),
            )

            for door_item in doors:
                await db.execute(
                    """
                    INSERT INTO stop_door_counts(batch_id, door_id, in_count, out_count)
                    VALUES (?, ?, ?, ?);
                    """,
                    (
                        batch_id,
                        int(door_item["door_id"]),
                        int(door_item["in"]),
                        int(door_item["out"]),
                    ),
                )

            await db.commit()
            return IngestResult(status="stored", ts_received=ts_received)
        except sqlite3.IntegrityError:
            await db.rollback()
            return IngestResult(status="duplicate", ts_received=ts_received)


async def stats_vehicle(db_path: str, vehicle_id: str) -> dict[str, Any]:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys=ON;")
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT COUNT(*) AS batches FROM stops WHERE vehicle_id = ?;",
            (vehicle_id,),
        ) as cursor:
            row = await cursor.fetchone()
            batches = int(row["batches"]) if row else 0

        async with db.execute(
            """
            SELECT
              COALESCE(SUM(d.in_count), 0) AS total_in,
              COALESCE(SUM(d.out_count), 0) AS total_out
            FROM stop_door_counts d
            JOIN stops s ON s.batch_id = d.batch_id
            WHERE s.vehicle_id = ?;
            """,
            (vehicle_id,),
        ) as cursor:
            row = await cursor.fetchone()
            total_in = int(row["total_in"]) if row else 0
            total_out = int(row["total_out"]) if row else 0

        return {"vehicle_id": vehicle_id, "batches": batches, "total_in": total_in, "total_out": total_out}


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


async def ingest_central_heartbeat(db_path: str, payload: dict[str, Any]) -> HeartbeatResult:
    ts_received = utc_now_iso()
    central_id = str(payload["central_id"])
    schema_ver = _to_int(payload.get("schema_ver", 1), 1)
    vehicle_id = payload.get("vehicle_id")
    ts_sent = payload.get("ts_sent")
    time_sync = payload.get("time_sync")
    services = payload.get("services") if isinstance(payload.get("services"), dict) else {}
    queue = payload.get("queue") if isinstance(payload.get("queue"), dict) else {}
    doors = payload.get("doors") if isinstance(payload.get("doors"), list) else []

    collector_state = str(services.get("passengers-collector", "unknown"))
    uplink_state = str(services.get("passengers-central-uplink", "unknown"))
    flush_timer_state = str(services.get("passengers-central-flush.timer", "unknown"))
    wg_state = str(services.get("wg-quick@wg0", "unknown"))
    events_total = _to_int(queue.get("events_total"), 0)
    pending_batches = _to_int(queue.get("pending_batches"), 0)
    sent_batches = _to_int(queue.get("sent_batches"), 0)
    last_event_ts_received = queue.get("last_event_ts_received")
    doors_json = json.dumps(doors, ensure_ascii=False, separators=(",", ":"))
    raw_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO central_heartbeats(
              central_id, vehicle_id, schema_ver, ts_sent, ts_received, time_sync,
              collector_state, uplink_state, flush_timer_state, wg_state,
              events_total, pending_batches, sent_batches, last_event_ts_received,
              doors_json, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(central_id) DO UPDATE SET
              vehicle_id=excluded.vehicle_id,
              schema_ver=excluded.schema_ver,
              ts_sent=excluded.ts_sent,
              ts_received=excluded.ts_received,
              time_sync=excluded.time_sync,
              collector_state=excluded.collector_state,
              uplink_state=excluded.uplink_state,
              flush_timer_state=excluded.flush_timer_state,
              wg_state=excluded.wg_state,
              events_total=excluded.events_total,
              pending_batches=excluded.pending_batches,
              sent_batches=excluded.sent_batches,
              last_event_ts_received=excluded.last_event_ts_received,
              doors_json=excluded.doors_json,
              raw_json=excluded.raw_json;
            """,
            (
                central_id,
                vehicle_id,
                schema_ver,
                ts_sent,
                ts_received,
                time_sync,
                collector_state,
                uplink_state,
                flush_timer_state,
                wg_state,
                events_total,
                pending_batches,
                sent_batches,
                last_event_ts_received,
                doors_json,
                raw_json,
            ),
        )
        await db.execute(
            """
            INSERT INTO central_heartbeat_history(
              central_id, vehicle_id, schema_ver, ts_sent, ts_received, time_sync,
              collector_state, uplink_state, flush_timer_state, wg_state,
              events_total, pending_batches, sent_batches, last_event_ts_received,
              doors_json, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                central_id,
                vehicle_id,
                schema_ver,
                ts_sent,
                ts_received,
                time_sync,
                collector_state,
                uplink_state,
                flush_timer_state,
                wg_state,
                events_total,
                pending_batches,
                sent_batches,
                last_event_ts_received,
                doors_json,
                raw_json,
            ),
        )
        await db.commit()

    return HeartbeatResult(status="stored", ts_received=ts_received)


def _parse_iso_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _silence_active(*, silenced_until: str | None, now_dt: datetime) -> bool:
    dt = _parse_iso_utc(silenced_until)
    return dt is not None and dt > now_dt


def _state_to_dict(row: aiosqlite.Row, now_dt: datetime) -> dict[str, Any]:
    silenced_until = row["silenced_until"]
    return {
        "acked_at": row["acked_at"],
        "acked_by": row["acked_by"],
        "ack_note": row["ack_note"],
        "silenced_until": silenced_until,
        "silenced_by": row["silenced_by"],
        "silence_note": row["silence_note"],
        "silenced": _silence_active(silenced_until=silenced_until, now_dt=now_dt),
        "updated_at": row["updated_at"],
    }


async def _get_alert_states(db_path: str) -> dict[tuple[str, str], dict[str, Any]]:
    now_dt = datetime.now(timezone.utc)
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
              central_id, code, acked_at, acked_by, ack_note,
              silenced_until, silenced_by, silence_note, updated_at
            FROM alert_states;
            """
        ) as cursor:
            rows = await cursor.fetchall()

    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["central_id"]), str(row["code"]))
        result[key] = _state_to_dict(row, now_dt)
    return result


def _severity_rank(level: str) -> int:
    ranks = {"good": 0, "warn": 1, "bad": 2}
    return ranks.get(level, 2)


def _merge_severity(current: str, new_level: str) -> str:
    return new_level if _severity_rank(new_level) > _severity_rank(current) else current


def _incident_status_from_alert(alert: dict[str, Any]) -> str:
    if bool(alert.get("silenced")):
        return "silenced"
    if bool(alert.get("acked_at")):
        return "acked"
    return "open"


def _incident_is_active_status(status: str | None) -> bool:
    return str(status or "").strip().lower() in {"open", "acked", "silenced"}


def _incident_notify_candidate(*, severity: str, code: str) -> bool:
    normalized_code = str(code or "").strip().lower()
    normalized_severity = str(severity or "bad").strip().lower()
    return normalized_severity == "bad" or "stale" in normalized_code


def _incident_sla_target_sec(severity: str) -> int:
    normalized = str(severity or "bad").strip().lower()
    if normalized == "bad":
        return 300
    if normalized == "warn":
        return 1800
    return 3600


def _new_alert(*, severity: str, code: str, message: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message}


def _is_active_state(value: Any) -> bool:
    return str(value).strip().lower() == "active"


def _normalize_door_item(raw: Any) -> dict[str, Any]:
    item = raw if isinstance(raw, dict) else {}
    node_id = str(item.get("node_id") or "?")
    door_id = _to_int(item.get("door_id"), 0)
    reachable_raw = item.get("reachable")
    reachable = reachable_raw if isinstance(reachable_raw, bool) else None
    last_event_ts_received = item.get("last_event_ts_received")

    age_raw = item.get("last_event_age_sec")
    if age_raw is None:
        last_event_age_sec: int | None = None
    else:
        age_val = _to_int(age_raw, -1)
        last_event_age_sec = age_val if age_val >= 0 else None

    return {
        "node_id": node_id,
        "door_id": door_id,
        "ip": item.get("ip"),
        "reachable": reachable,
        "last_event_ts_received": last_event_ts_received,
        "last_event_age_sec": last_event_age_sec,
    }


def _build_central_alerts(
    *,
    age_sec: int | None,
    time_sync: str | None,
    services: dict[str, str],
    queue: dict[str, Any],
    doors: list[dict[str, Any]],
) -> tuple[list[dict[str, str]], str]:
    alerts: list[dict[str, str]] = []
    severity = "good"

    if age_sec is None:
        alerts.append(_new_alert(severity="bad", code="heartbeat_missing", message="Heartbeat timestamp missing or invalid"))
        severity = _merge_severity(severity, "bad")
    elif age_sec > 240:
        alerts.append(_new_alert(severity="bad", code="heartbeat_stale", message=f"Last heartbeat is {age_sec}s old"))
        severity = _merge_severity(severity, "bad")
    elif age_sec > 90:
        alerts.append(_new_alert(severity="warn", code="heartbeat_slow", message=f"Last heartbeat is {age_sec}s old"))
        severity = _merge_severity(severity, "warn")

    if str(time_sync or "").strip().lower() != "synced":
        alerts.append(
            _new_alert(
                severity="bad",
                code="time_unsynced",
                message=f"Time sync state is '{time_sync or 'unknown'}'",
            )
        )
        severity = _merge_severity(severity, "bad")

    required_bad = ("passengers-collector", "passengers-central-uplink")
    stop_mode = str(queue.get("stop_mode") or "timer").strip().lower()
    required_warn: list[str] = ["wg-quick@wg0"]
    if stop_mode == "timer":
        required_warn.append("passengers-central-flush.timer")
    elif stop_mode != "manual":
        alerts.append(
            _new_alert(
                severity="warn",
                code="stop_mode_unknown",
                message=f"Unknown stop_mode '{stop_mode}'",
            )
        )
        severity = _merge_severity(severity, "warn")
    for service_name in required_bad:
        state = services.get(service_name, "unknown")
        if not _is_active_state(state):
            alerts.append(
                _new_alert(
                    severity="bad",
                    code="service_inactive",
                    message=f"{service_name} is '{state}'",
                )
            )
            severity = _merge_severity(severity, "bad")

    for service_name in required_warn:
        state = services.get(service_name, "unknown")
        if not _is_active_state(state):
            alerts.append(
                _new_alert(
                    severity="warn",
                    code="service_not_active",
                    message=f"{service_name} is '{state}'",
                )
            )
            severity = _merge_severity(severity, "warn")

    pending_batches = _to_int(queue.get("pending_batches"), 0)
    pending_oldest_age_raw = queue.get("pending_oldest_age_sec")
    pending_oldest_age_sec: int | None = None
    if pending_oldest_age_raw is not None:
        parsed = _to_int(pending_oldest_age_raw, -1)
        if parsed >= 0:
            pending_oldest_age_sec = parsed

    if pending_batches >= 20:
        alerts.append(
            _new_alert(
                severity="bad",
                code="queue_backlog_high",
                message=f"Pending batches = {pending_batches}",
            )
        )
        severity = _merge_severity(severity, "bad")
    elif pending_batches >= 5:
        alerts.append(
            _new_alert(
                severity="warn",
                code="queue_backlog",
                message=f"Pending batches = {pending_batches}",
            )
        )
        severity = _merge_severity(severity, "warn")

    if pending_batches > 0:
        if pending_oldest_age_sec is None:
            alerts.append(
                _new_alert(
                    severity="warn",
                    code="queue_pending_age_unknown",
                    message="Pending batches exist but oldest pending age is unknown",
                )
            )
            severity = _merge_severity(severity, "warn")
        elif pending_oldest_age_sec >= 7200:
            alerts.append(
                _new_alert(
                    severity="bad",
                    code="queue_pending_stale",
                    message=f"Oldest pending batch age is {pending_oldest_age_sec}s",
                )
            )
            severity = _merge_severity(severity, "bad")
        elif pending_oldest_age_sec >= 1800:
            alerts.append(
                _new_alert(
                    severity="warn",
                    code="queue_pending_aging",
                    message=f"Oldest pending batch age is {pending_oldest_age_sec}s",
                )
            )
            severity = _merge_severity(severity, "warn")

    wg_state = services.get("wg-quick@wg0", "unknown")
    wg_hs_raw = queue.get("wg_latest_handshake_age_sec")
    wg_hs_age: int | None = None
    if wg_hs_raw is not None:
        parsed = _to_int(wg_hs_raw, -1)
        if parsed >= 0:
            wg_hs_age = parsed
    if _is_active_state(wg_state):
        if wg_hs_age is None:
            alerts.append(
                _new_alert(
                    severity="warn",
                    code="wg_handshake_unknown",
                    message="WireGuard is active but latest handshake age is unknown",
                )
            )
            severity = _merge_severity(severity, "warn")
        elif wg_hs_age >= 900:
            alerts.append(
                _new_alert(
                    severity="bad",
                    code="wg_handshake_stale",
                    message=f"WireGuard latest handshake age is {wg_hs_age}s",
                )
            )
            severity = _merge_severity(severity, "bad")
        elif wg_hs_age >= 300:
            alerts.append(
                _new_alert(
                    severity="warn",
                    code="wg_handshake_slow",
                    message=f"WireGuard latest handshake age is {wg_hs_age}s",
                )
            )
            severity = _merge_severity(severity, "warn")

    for door in doors:
        node_id = str(door.get("node_id") or "?")
        reachable = door.get("reachable")
        last_event_age_sec = door.get("last_event_age_sec")

        if reachable is False:
            alerts.append(
                _new_alert(
                    severity="bad",
                    code="door_unreachable",
                    message=f"{node_id} is unreachable",
                )
            )
            severity = _merge_severity(severity, "bad")
            continue

        if reachable is None:
            alerts.append(
                _new_alert(
                    severity="warn",
                    code="door_reachability_unknown",
                    message=f"{node_id} reachability is unknown",
                )
            )
            severity = _merge_severity(severity, "warn")

        if last_event_age_sec is None:
            alerts.append(
                _new_alert(
                    severity="warn",
                    code="door_no_events",
                    message=f"{node_id} has no recent event timestamp",
                )
            )
            severity = _merge_severity(severity, "warn")
        elif int(last_event_age_sec) > 1800:
            alerts.append(
                _new_alert(
                    severity="warn",
                    code="door_events_stale",
                    message=f"{node_id} last event age is {last_event_age_sec}s",
                )
            )
            severity = _merge_severity(severity, "warn")

    return alerts, severity


async def list_central_heartbeats(db_path: str) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    states_map = await _get_alert_states(db_path)
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
              central_id, vehicle_id, schema_ver, ts_sent, ts_received, time_sync,
              collector_state, uplink_state, flush_timer_state, wg_state,
              events_total, pending_batches, sent_batches, last_event_ts_received,
              doors_json, raw_json
            FROM central_heartbeats
            ORDER BY ts_received DESC;
            """
        ) as cursor:
            rows = await cursor.fetchall()

    result: list[dict[str, Any]] = []
    for row in rows:
        ts_received = row["ts_received"]
        ts_dt = _parse_iso_utc(ts_received)
        age_sec = int((now - ts_dt).total_seconds()) if ts_dt else None
        doors_raw = row["doors_json"] or "[]"
        try:
            doors = json.loads(doors_raw)
            if not isinstance(doors, list):
                doors = []
        except Exception:
            doors = []
        normalized_doors = [_normalize_door_item(item) for item in doors]

        services = {
            "passengers-collector": row["collector_state"],
            "passengers-central-uplink": row["uplink_state"],
            "passengers-central-flush.timer": row["flush_timer_state"],
            "wg-quick@wg0": row["wg_state"],
        }
        stop_mode = "timer"
        pending_oldest_age_sec: int | None = None
        pending_oldest_created_at: str | None = None
        wg_latest_handshake_age_sec: int | None = None
        gps: dict[str, Any] | None = None
        try:
            raw_payload = json.loads(row["raw_json"] or "{}")
            if isinstance(raw_payload, dict):
                raw_queue = raw_payload.get("queue")
                if isinstance(raw_queue, dict):
                    parsed_mode = str(raw_queue.get("stop_mode") or "").strip().lower()
                    if parsed_mode:
                        stop_mode = parsed_mode
                    pending_oldest_created_at = raw_queue.get("pending_oldest_created_at")
                    parsed_pending_age = _to_int(raw_queue.get("pending_oldest_age_sec"), -1)
                    if parsed_pending_age >= 0:
                        pending_oldest_age_sec = parsed_pending_age
                    parsed_wg_age = _to_int(raw_queue.get("wg_latest_handshake_age_sec"), -1)
                    if parsed_wg_age >= 0:
                        wg_latest_handshake_age_sec = parsed_wg_age
                raw_gps = raw_payload.get("gps")
                if isinstance(raw_gps, dict):
                    gps = {
                        "fix": bool(raw_gps.get("fix", False)),
                        "lat": raw_gps.get("lat"),
                        "lon": raw_gps.get("lon"),
                        "updated_at": raw_gps.get("updated_at"),
                        "age_sec": raw_gps.get("age_sec"),
                        "source": raw_gps.get("source"),
                    }
        except Exception:
            pass
        queue = {
            "events_total": row["events_total"],
            "pending_batches": row["pending_batches"],
            "sent_batches": row["sent_batches"],
            "last_event_ts_received": row["last_event_ts_received"],
            "pending_oldest_created_at": pending_oldest_created_at,
            "pending_oldest_age_sec": pending_oldest_age_sec,
            "wg_latest_handshake_age_sec": wg_latest_handshake_age_sec,
            "stop_mode": stop_mode,
        }
        alerts, severity = _build_central_alerts(
            age_sec=age_sec,
            time_sync=row["time_sync"],
            services=services,
            queue=queue,
            doors=normalized_doors,
        )
        del severity

        central_id = str(row["central_id"])
        alerts_enriched: list[dict[str, Any]] = []
        for alert in alerts:
            code = str(alert.get("code") or "alert")
            state = states_map.get((central_id, code), {})
            alerts_enriched.append(
                {
                    "severity": str(alert.get("severity") or "bad"),
                    "code": code,
                    "message": str(alert.get("message") or ""),
                    "acked_at": state.get("acked_at"),
                    "acked_by": state.get("acked_by"),
                    "ack_note": state.get("ack_note"),
                    "silenced_until": state.get("silenced_until"),
                    "silenced_by": state.get("silenced_by"),
                    "silence_note": state.get("silence_note"),
                    "silenced": bool(state.get("silenced", False)),
                }
            )

        active_alerts = [item for item in alerts_enriched if not item.get("silenced")]
        severity = "good"
        for alert in active_alerts:
            severity = _merge_severity(severity, str(alert.get("severity") or "bad"))

        by_severity = {"good": 0, "warn": 0, "bad": 0}
        for alert in active_alerts:
            alert_level = str(alert.get("severity") or "bad")
            if alert_level in by_severity:
                by_severity[alert_level] += 1

        result.append(
            {
                "central_id": central_id,
                "vehicle_id": row["vehicle_id"],
                "schema_ver": row["schema_ver"],
                "ts_sent": row["ts_sent"],
                "ts_received": ts_received,
                "age_sec": age_sec,
                "time_sync": row["time_sync"],
                "gps": gps,
                "services": services,
                "queue": queue,
                "doors": normalized_doors,
                "alerts": alerts_enriched,
                "health": {
                    "severity": severity,
                    "alerts_total": len(active_alerts),
                    "alerts_all_total": len(alerts_enriched),
                    "alerts_silenced": len(alerts_enriched) - len(active_alerts),
                    "alerts_warn": by_severity["warn"],
                    "alerts_bad": by_severity["bad"],
                },
            }
        )

    return result


async def get_central_heartbeat_history(db_path: str, central_id: str, *, limit: int = 120) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    states_map = await _get_alert_states(db_path)
    bounded_limit = max(1, min(int(limit), 1000))

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
              central_id, vehicle_id, schema_ver, ts_sent, ts_received, time_sync,
              collector_state, uplink_state, flush_timer_state, wg_state,
              events_total, pending_batches, sent_batches, last_event_ts_received,
              doors_json, raw_json
            FROM central_heartbeat_history
            WHERE central_id = ?
            ORDER BY ts_received DESC
            LIMIT ?;
            """,
            (central_id, bounded_limit),
        ) as cursor:
            rows = await cursor.fetchall()

    result: list[dict[str, Any]] = []
    for row in rows:
        ts_received = row["ts_received"]
        ts_dt = _parse_iso_utc(ts_received)
        age_sec = int((now - ts_dt).total_seconds()) if ts_dt else None

        doors_raw = row["doors_json"] or "[]"
        try:
            doors = json.loads(doors_raw)
            if not isinstance(doors, list):
                doors = []
        except Exception:
            doors = []
        normalized_doors = [_normalize_door_item(item) for item in doors]

        services = {
            "passengers-collector": row["collector_state"],
            "passengers-central-uplink": row["uplink_state"],
            "passengers-central-flush.timer": row["flush_timer_state"],
            "wg-quick@wg0": row["wg_state"],
        }

        stop_mode = "timer"
        pending_oldest_age_sec: int | None = None
        pending_oldest_created_at: str | None = None
        wg_latest_handshake_age_sec: int | None = None
        try:
            raw_payload = json.loads(row["raw_json"] or "{}")
            if isinstance(raw_payload, dict):
                raw_queue = raw_payload.get("queue")
                if isinstance(raw_queue, dict):
                    parsed_mode = str(raw_queue.get("stop_mode") or "").strip().lower()
                    if parsed_mode:
                        stop_mode = parsed_mode
                    pending_oldest_created_at = raw_queue.get("pending_oldest_created_at")
                    parsed_pending_age = _to_int(raw_queue.get("pending_oldest_age_sec"), -1)
                    if parsed_pending_age >= 0:
                        pending_oldest_age_sec = parsed_pending_age
                    parsed_wg_age = _to_int(raw_queue.get("wg_latest_handshake_age_sec"), -1)
                    if parsed_wg_age >= 0:
                        wg_latest_handshake_age_sec = parsed_wg_age
        except Exception:
            pass

        queue = {
            "events_total": row["events_total"],
            "pending_batches": row["pending_batches"],
            "sent_batches": row["sent_batches"],
            "last_event_ts_received": row["last_event_ts_received"],
            "pending_oldest_created_at": pending_oldest_created_at,
            "pending_oldest_age_sec": pending_oldest_age_sec,
            "wg_latest_handshake_age_sec": wg_latest_handshake_age_sec,
            "stop_mode": stop_mode,
        }

        alerts_raw, _severity = _build_central_alerts(
            age_sec=0,
            time_sync=row["time_sync"],
            services=services,
            queue=queue,
            doors=normalized_doors,
        )

        alerts_enriched: list[dict[str, Any]] = []
        for alert in alerts_raw:
            code = str(alert.get("code") or "alert")
            state = states_map.get((central_id, code), {})
            alerts_enriched.append(
                {
                    "severity": str(alert.get("severity") or "bad"),
                    "code": code,
                    "message": str(alert.get("message") or ""),
                    "acked_at": state.get("acked_at"),
                    "acked_by": state.get("acked_by"),
                    "ack_note": state.get("ack_note"),
                    "silenced_until": state.get("silenced_until"),
                    "silenced_by": state.get("silenced_by"),
                    "silence_note": state.get("silence_note"),
                    "silenced": bool(state.get("silenced", False)),
                }
            )

        active_alerts = [item for item in alerts_enriched if not item.get("silenced")]
        severity = "good"
        for alert in active_alerts:
            severity = _merge_severity(severity, str(alert.get("severity") or "bad"))

        warn_count = sum(1 for item in active_alerts if str(item.get("severity")) == "warn")
        bad_count = sum(1 for item in active_alerts if str(item.get("severity")) == "bad")

        result.append(
            {
                "central_id": central_id,
                "vehicle_id": row["vehicle_id"],
                "schema_ver": row["schema_ver"],
                "ts_sent": row["ts_sent"],
                "ts_received": ts_received,
                "age_sec": age_sec,
                "time_sync": row["time_sync"],
                "services": services,
                "queue": queue,
                "doors": normalized_doors,
                "alerts": alerts_enriched,
                "health": {
                    "severity": severity,
                    "alerts_total": len(active_alerts),
                    "alerts_all_total": len(alerts_enriched),
                    "alerts_silenced": len(alerts_enriched) - len(active_alerts),
                    "alerts_warn": warn_count,
                    "alerts_bad": bad_count,
                },
            }
        )
    return result


async def list_fleet_health_history_samples(
    db_path: str,
    *,
    since_ts: str | None = None,
    limit: int = 50_000,
) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(int(limit), 200_000))
    query = """
        SELECT
          central_id, ts_received, time_sync,
          collector_state, uplink_state, flush_timer_state, wg_state,
          events_total, pending_batches, sent_batches, last_event_ts_received,
          doors_json, raw_json
        FROM central_heartbeat_history
    """
    where_parts: list[str] = []
    params: list[Any] = []
    if since_ts:
        parsed = _parse_iso_utc(str(since_ts))
        if parsed is not None:
            where_parts.append("ts_received >= ?")
            params.append(parsed.isoformat().replace("+00:00", "Z"))
    if where_parts:
        query += " WHERE " + " AND ".join(where_parts)
    query += " ORDER BY ts_received ASC, central_id ASC LIMIT ?;"
    params.append(bounded_limit)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()

    samples: list[dict[str, Any]] = []
    for row in rows:
        doors_raw = row["doors_json"] or "[]"
        try:
            doors = json.loads(doors_raw)
            if not isinstance(doors, list):
                doors = []
        except Exception:
            doors = []
        normalized_doors = [_normalize_door_item(item) for item in doors]

        services = {
            "passengers-collector": row["collector_state"],
            "passengers-central-uplink": row["uplink_state"],
            "passengers-central-flush.timer": row["flush_timer_state"],
            "wg-quick@wg0": row["wg_state"],
        }
        stop_mode = "timer"
        pending_oldest_age_sec: int | None = None
        pending_oldest_created_at: str | None = None
        wg_latest_handshake_age_sec: int | None = None
        try:
            raw_payload = json.loads(row["raw_json"] or "{}")
            if isinstance(raw_payload, dict):
                raw_queue = raw_payload.get("queue")
                if isinstance(raw_queue, dict):
                    parsed_mode = str(raw_queue.get("stop_mode") or "").strip().lower()
                    if parsed_mode:
                        stop_mode = parsed_mode
                    pending_oldest_created_at = raw_queue.get("pending_oldest_created_at")
                    parsed_pending_age = _to_int(raw_queue.get("pending_oldest_age_sec"), -1)
                    if parsed_pending_age >= 0:
                        pending_oldest_age_sec = parsed_pending_age
                    parsed_wg_age = _to_int(raw_queue.get("wg_latest_handshake_age_sec"), -1)
                    if parsed_wg_age >= 0:
                        wg_latest_handshake_age_sec = parsed_wg_age
        except Exception:
            pass

        queue = {
            "events_total": row["events_total"],
            "pending_batches": row["pending_batches"],
            "sent_batches": row["sent_batches"],
            "last_event_ts_received": row["last_event_ts_received"],
            "pending_oldest_created_at": pending_oldest_created_at,
            "pending_oldest_age_sec": pending_oldest_age_sec,
            "wg_latest_handshake_age_sec": wg_latest_handshake_age_sec,
            "stop_mode": stop_mode,
        }
        alerts, severity = _build_central_alerts(
            age_sec=0,
            time_sync=row["time_sync"],
            services=services,
            queue=queue,
            doors=normalized_doors,
        )
        warn_count = sum(1 for item in alerts if str(item.get("severity") or "") == "warn")
        bad_count = sum(1 for item in alerts if str(item.get("severity") or "") == "bad")
        samples.append(
            {
                "central_id": str(row["central_id"]),
                "ts_received": row["ts_received"],
                "severity": severity,
                "alerts_total": len(alerts),
                "alerts_warn": warn_count,
                "alerts_bad": bad_count,
                "pending_batches": _to_int(row["pending_batches"], 0),
                "wg_latest_handshake_age_sec": wg_latest_handshake_age_sec,
            }
        )
    return samples


async def sync_incidents(
    db_path: str,
    *,
    centrals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if centrals is None:
        centrals = await list_central_heartbeats(db_path)

    now_iso = utc_now_iso()
    aggregated: dict[tuple[str, str], dict[str, Any]] = {}
    status_rank = {"open": 0, "acked": 1, "silenced": 2}

    for central in centrals:
        central_id = str(central.get("central_id") or "")
        if not central_id:
            continue
        vehicle_id = str(central.get("vehicle_id") or "")
        alerts = central.get("alerts")
        if not isinstance(alerts, list):
            continue
        for raw_alert in alerts:
            if not isinstance(raw_alert, dict):
                continue
            code = str(raw_alert.get("code") or "alert")
            if not code:
                continue
            severity = str(raw_alert.get("severity") or "bad")
            status = _incident_status_from_alert(raw_alert)
            message = str(raw_alert.get("message") or "")
            key = (central_id, code)
            entry = aggregated.get(key)
            if entry is None:
                entry = {
                    "central_id": central_id,
                    "code": code,
                    "vehicle_id": vehicle_id or None,
                    "severity": severity,
                    "status": status,
                    "messages": [],
                    "acked_at": raw_alert.get("acked_at"),
                    "acked_by": raw_alert.get("acked_by"),
                    "silenced_until": raw_alert.get("silenced_until"),
                    "silenced_by": raw_alert.get("silenced_by"),
                }
                aggregated[key] = entry
            if message and message not in entry["messages"] and len(entry["messages"]) < 5:
                entry["messages"].append(message)
            if _severity_rank(severity) > _severity_rank(str(entry["severity"] or "bad")):
                entry["severity"] = severity
            if status_rank.get(status, 0) > status_rank.get(str(entry["status"]), 0):
                entry["status"] = status
            if raw_alert.get("acked_at"):
                entry["acked_at"] = raw_alert.get("acked_at")
            if raw_alert.get("acked_by"):
                entry["acked_by"] = raw_alert.get("acked_by")
            if raw_alert.get("silenced_until"):
                entry["silenced_until"] = raw_alert.get("silenced_until")
            if raw_alert.get("silenced_by"):
                entry["silenced_by"] = raw_alert.get("silenced_by")

    for entry in aggregated.values():
        messages = [str(item) for item in entry.pop("messages", []) if str(item).strip()]
        entry["message"] = " | ".join(messages)

    inserted = 0
    updated = 0
    resolved = 0
    notify_events: list[dict[str, Any]] = []

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT central_id, code, status, severity, first_seen_ts, occurrences
            FROM incidents;
            """
        ) as cursor:
            existing_rows = await cursor.fetchall()

        existing_map: dict[tuple[str, str], aiosqlite.Row] = {}
        for row in existing_rows:
            existing_map[(str(row["central_id"]), str(row["code"]))] = row

        for key, entry in aggregated.items():
            central_id, code = key
            severity = str(entry.get("severity") or "bad")
            status = str(entry.get("status") or "open")
            vehicle_id = entry.get("vehicle_id")
            message = str(entry.get("message") or "")
            acked_at = entry.get("acked_at")
            acked_by = entry.get("acked_by")
            silenced_until = entry.get("silenced_until")
            silenced_by = entry.get("silenced_by")

            previous = existing_map.get(key)
            prev_status = str(previous["status"]) if previous else None
            prev_severity = str(previous["severity"]) if previous else None
            first_seen_ts = str(previous["first_seen_ts"]) if previous else now_iso
            prev_occurrences = _to_int(previous["occurrences"], 0) if previous else 0
            occurrences = max(1, prev_occurrences + 1)

            if previous:
                await db.execute(
                    """
                    UPDATE incidents
                    SET vehicle_id = ?,
                        severity = ?,
                        status = ?,
                        message = ?,
                        last_seen_ts = ?,
                        resolved_ts = NULL,
                        occurrences = ?,
                        acked_at = ?,
                        acked_by = ?,
                        silenced_until = ?,
                        silenced_by = ?,
                        updated_at = ?
                    WHERE central_id = ? AND code = ?;
                    """,
                    (
                        vehicle_id,
                        severity,
                        status,
                        message,
                        now_iso,
                        occurrences,
                        acked_at,
                        acked_by,
                        silenced_until,
                        silenced_by,
                        now_iso,
                        central_id,
                        code,
                    ),
                )
                updated += 1
            else:
                await db.execute(
                    """
                    INSERT INTO incidents(
                      central_id, code, vehicle_id, severity, status, message,
                      first_seen_ts, last_seen_ts, resolved_ts, occurrences,
                      acked_at, acked_by, silenced_until, silenced_by, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        central_id,
                        code,
                        vehicle_id,
                        severity,
                        status,
                        message,
                        now_iso,
                        now_iso,
                        1,
                        acked_at,
                        acked_by,
                        silenced_until,
                        silenced_by,
                        now_iso,
                    ),
                )
                inserted += 1

            candidate = _incident_notify_candidate(severity=severity, code=code)
            opened = previous is None or not _incident_is_active_status(prev_status)
            escalated_to_bad = (
                previous is not None
                and _incident_is_active_status(prev_status)
                and _severity_rank(severity) > _severity_rank(prev_severity)
                and str(severity).strip().lower() == "bad"
            )
            if candidate and (opened or escalated_to_bad):
                event = "opened" if opened else "escalated_bad"
                notify_events.append(
                    {
                        "event": event,
                        "central_id": central_id,
                        "code": code,
                        "vehicle_id": vehicle_id,
                        "severity": severity,
                        "status": status,
                        "message": message,
                        "first_seen_ts": first_seen_ts,
                        "last_seen_ts": now_iso,
                    }
                )

        current_keys = set(aggregated.keys())
        for key, previous in existing_map.items():
            if key in current_keys:
                continue
            prev_status = str(previous["status"] or "")
            if not _incident_is_active_status(prev_status):
                continue
            await db.execute(
                """
                UPDATE incidents
                SET status = 'resolved',
                    resolved_ts = ?,
                    updated_at = ?
                WHERE central_id = ? AND code = ?;
                """,
                (now_iso, now_iso, key[0], key[1]),
            )
            resolved += 1

        await db.commit()

    return {
        "status": "ok",
        "ts_synced": now_iso,
        "active_total": len(aggregated),
        "inserted": inserted,
        "updated": updated,
        "resolved": resolved,
        "notify": notify_events,
    }


async def list_incidents(
    db_path: str,
    *,
    status: str | None = None,
    severity: str | None = None,
    central_id: str | None = None,
    code: str | None = None,
    q: str | None = None,
    include_resolved: bool = True,
    limit: int = 200,
) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(int(limit), 2000))
    query = """
        SELECT
          central_id, code, vehicle_id, severity, status, message,
          first_seen_ts, last_seen_ts, resolved_ts, occurrences,
          acked_at, acked_by, silenced_until, silenced_by, updated_at
        FROM incidents
    """
    where_parts: list[str] = []
    params: list[Any] = []

    if not include_resolved:
        where_parts.append("status != 'resolved'")
    if status:
        normalized_status = str(status).strip().lower()
        if normalized_status in {"open", "acked", "silenced", "resolved"}:
            where_parts.append("status = ?")
            params.append(normalized_status)
    if severity:
        normalized_severity = str(severity).strip().lower()
        if normalized_severity in {"good", "warn", "bad"}:
            where_parts.append("severity = ?")
            params.append(normalized_severity)
    if central_id:
        where_parts.append("central_id = ?")
        params.append(str(central_id))
    if code:
        where_parts.append("code = ?")
        params.append(str(code))
    if q:
        query_text = str(q).strip().lower()
        if query_text:
            like = f"%{query_text}%"
            where_parts.append(
                "(LOWER(COALESCE(central_id,'')) LIKE ? OR LOWER(COALESCE(code,'')) LIKE ? OR LOWER(COALESCE(vehicle_id,'')) LIKE ? OR LOWER(COALESCE(message,'')) LIKE ? OR LOWER(COALESCE(acked_by,'')) LIKE ? OR LOWER(COALESCE(silenced_by,'')) LIKE ?)"
            )
            params.extend([like, like, like, like, like, like])
    if where_parts:
        query += " WHERE " + " AND ".join(where_parts)
    query += """
        ORDER BY
          CASE status
            WHEN 'open' THEN 0
            WHEN 'acked' THEN 1
            WHEN 'silenced' THEN 2
            ELSE 3
          END ASC,
          CASE severity
            WHEN 'bad' THEN 0
            WHEN 'warn' THEN 1
            ELSE 2
          END ASC,
          updated_at DESC
        LIMIT ?;
    """
    params.append(bounded_limit)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()

    now_dt = datetime.now(timezone.utc)
    result: list[dict[str, Any]] = []
    for row in rows:
        row_status = str(row["status"] or "open")
        row_severity = str(row["severity"] or "bad")
        first_seen_dt = _parse_iso_utc(row["first_seen_ts"])
        last_seen_dt = _parse_iso_utc(row["last_seen_ts"])
        resolved_dt = _parse_iso_utc(row["resolved_ts"])

        if row_status == "resolved" and first_seen_dt and resolved_dt:
            age_sec = max(0, int((resolved_dt - first_seen_dt).total_seconds()))
        elif first_seen_dt:
            age_sec = max(0, int((now_dt - first_seen_dt).total_seconds()))
        else:
            age_sec = None

        last_seen_age_sec = max(0, int((now_dt - last_seen_dt).total_seconds())) if last_seen_dt else None
        sla_target_sec = _incident_sla_target_sec(row_severity)
        sla_breached = bool(age_sec is not None and row_status != "resolved" and age_sec > sla_target_sec)

        result.append(
            {
                "central_id": row["central_id"],
                "code": row["code"],
                "vehicle_id": row["vehicle_id"],
                "severity": row_severity,
                "status": row_status,
                "message": row["message"],
                "first_seen_ts": row["first_seen_ts"],
                "last_seen_ts": row["last_seen_ts"],
                "resolved_ts": row["resolved_ts"],
                "occurrences": _to_int(row["occurrences"], 0),
                "acked_at": row["acked_at"],
                "acked_by": row["acked_by"],
                "silenced_until": row["silenced_until"],
                "silenced_by": row["silenced_by"],
                "updated_at": row["updated_at"],
                "age_sec": age_sec,
                "last_seen_age_sec": last_seen_age_sec,
                "sla_target_sec": sla_target_sec,
                "sla_breached": sla_breached,
            }
        )
    return result


async def get_incident_by_key(db_path: str, *, central_id: str, code: str) -> dict[str, Any] | None:
    items = await list_incidents(
        db_path,
        central_id=central_id,
        code=code,
        include_resolved=True,
        limit=5,
    )
    for item in items:
        if str(item.get("central_id") or "") == central_id and str(item.get("code") or "") == code:
            return item
    return None


async def get_notification_settings(db_path: str) -> dict[str, str]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT key, value
            FROM notification_settings;
            """
        ) as cursor:
            rows = await cursor.fetchall()
    result: dict[str, str] = {}
    for row in rows:
        result[str(row["key"])] = str(row["value"] or "")
    return result


async def update_notification_settings(
    db_path: str,
    *,
    updates: dict[str, str],
) -> dict[str, str]:
    allowed = {
        "notify_telegram",
        "notify_email",
        "mute_until",
        "rate_limit_sec",
        "min_severity",
        "stale_always_notify",
        "escalation_sec",
        "monitor_warn_heartbeat_age_sec",
        "monitor_bad_heartbeat_age_sec",
        "monitor_warn_pending_batches",
        "monitor_bad_pending_batches",
        "monitor_warn_wg_age_sec",
        "monitor_bad_wg_age_sec",
        "fleet_health_auto_enabled",
        "fleet_health_auto_notify_recovery",
        "fleet_health_auto_min_interval_sec",
        "fleet_health_auto_min_severity",
        "fleet_health_auto_channel",
        "fleet_health_auto_window",
    }
    ts = utc_now_iso()
    async with aiosqlite.connect(db_path) as db:
        for key, value in updates.items():
            if key not in allowed:
                continue
            await db.execute(
                """
                INSERT INTO notification_settings(key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                  value=excluded.value,
                  updated_at=excluded.updated_at;
                """,
                (key, str(value), ts),
            )
        await db.commit()
    return await get_notification_settings(db_path)


def _default_client_profile() -> dict[str, Any]:
    return {
        "full_name": "",
        "company": "",
        "email": "",
        "phone": "",
        "locale": "uk",
        "updated_at": None,
    }


def _default_client_notification_settings() -> dict[str, Any]:
    return {
        "notify_email": True,
        "notify_sms": False,
        "notify_push": False,
        "notify_level": "all",
        "digest_window": "24h",
        "updated_at": None,
    }


async def get_client_profile(db_path: str, *, client_id: str) -> dict[str, Any]:
    normalized_client_id = str(client_id or "").strip()
    if not normalized_client_id:
        return _default_client_profile()

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT full_name, company, email, phone, locale, updated_at
            FROM client_profiles
            WHERE client_id = ?
            LIMIT 1;
            """,
            (normalized_client_id,),
        ) as cursor:
            row = await cursor.fetchone()

    if row is None:
        return _default_client_profile()

    return {
        "full_name": str(row["full_name"] or ""),
        "company": str(row["company"] or ""),
        "email": str(row["email"] or ""),
        "phone": str(row["phone"] or ""),
        "locale": str(row["locale"] or "uk"),
        "updated_at": row["updated_at"],
    }


async def upsert_client_profile(
    db_path: str,
    *,
    client_id: str,
    profile: dict[str, Any],
) -> dict[str, Any]:
    normalized_client_id = str(client_id or "").strip()
    if not normalized_client_id:
        return _default_client_profile()

    current = await get_client_profile(db_path, client_id=normalized_client_id)
    merged = _default_client_profile()
    merged.update(current)

    for key in ("full_name", "company", "email", "phone", "locale"):
        if key not in profile:
            continue
        raw_value = profile.get(key)
        value = str(raw_value or "").strip()
        if key == "locale":
            merged[key] = value if value in {"uk", "en"} else "uk"
        else:
            merged[key] = value[:255]

    ts = utc_now_iso()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO client_profiles(
              client_id, full_name, company, email, phone, locale, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(client_id) DO UPDATE SET
              full_name=excluded.full_name,
              company=excluded.company,
              email=excluded.email,
              phone=excluded.phone,
              locale=excluded.locale,
              updated_at=excluded.updated_at;
            """,
            (
                normalized_client_id,
                merged["full_name"],
                merged["company"],
                merged["email"],
                merged["phone"],
                merged["locale"],
                ts,
            ),
        )
        await db.commit()

    return await get_client_profile(db_path, client_id=normalized_client_id)


async def get_client_notification_settings(db_path: str, *, client_id: str) -> dict[str, Any]:
    normalized_client_id = str(client_id or "").strip()
    if not normalized_client_id:
        return _default_client_notification_settings()

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT notify_email, notify_sms, notify_push, notify_level, digest_window, updated_at
            FROM client_notification_settings
            WHERE client_id = ?
            LIMIT 1;
            """,
            (normalized_client_id,),
        ) as cursor:
            row = await cursor.fetchone()

    if row is None:
        return _default_client_notification_settings()

    return {
        "notify_email": bool(_to_int(row["notify_email"], 0)),
        "notify_sms": bool(_to_int(row["notify_sms"], 0)),
        "notify_push": bool(_to_int(row["notify_push"], 0)),
        "notify_level": str(row["notify_level"] or "all"),
        "digest_window": str(row["digest_window"] or "24h"),
        "updated_at": row["updated_at"],
    }


async def upsert_client_notification_settings(
    db_path: str,
    *,
    client_id: str,
    settings: dict[str, Any],
) -> dict[str, Any]:
    normalized_client_id = str(client_id or "").strip()
    if not normalized_client_id:
        return _default_client_notification_settings()

    current = await get_client_notification_settings(db_path, client_id=normalized_client_id)
    merged = _default_client_notification_settings()
    merged.update(current)

    if "notify_email" in settings:
        merged["notify_email"] = bool(settings.get("notify_email"))
    if "notify_sms" in settings:
        merged["notify_sms"] = bool(settings.get("notify_sms"))
    if "notify_push" in settings:
        merged["notify_push"] = bool(settings.get("notify_push"))
    if "notify_level" in settings:
        level = str(settings.get("notify_level") or "").strip().lower()
        merged["notify_level"] = level if level in {"all", "critical"} else "all"
    if "digest_window" in settings:
        digest = str(settings.get("digest_window") or "").strip().lower()
        merged["digest_window"] = digest if digest in {"off", "1h", "24h"} else "24h"

    ts = utc_now_iso()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO client_notification_settings(
              client_id, notify_email, notify_sms, notify_push, notify_level, digest_window, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(client_id) DO UPDATE SET
              notify_email=excluded.notify_email,
              notify_sms=excluded.notify_sms,
              notify_push=excluded.notify_push,
              notify_level=excluded.notify_level,
              digest_window=excluded.digest_window,
              updated_at=excluded.updated_at;
            """,
            (
                normalized_client_id,
                1 if merged["notify_email"] else 0,
                1 if merged["notify_sms"] else 0,
                1 if merged["notify_push"] else 0,
                merged["notify_level"],
                merged["digest_window"],
                ts,
            ),
        )
        await db.commit()

    return await get_client_notification_settings(db_path, client_id=normalized_client_id)


async def list_monitor_policy_overrides(
    db_path: str,
    *,
    central_id: str | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(int(limit), 5000))
    query = """
        SELECT
          central_id,
          warn_heartbeat_age_sec,
          bad_heartbeat_age_sec,
          warn_pending_batches,
          bad_pending_batches,
          warn_wg_age_sec,
          bad_wg_age_sec,
          updated_at
        FROM monitor_policy_overrides
    """
    params: list[Any] = []
    if central_id:
        query += " WHERE central_id = ?"
        params.append(str(central_id))
    query += " ORDER BY central_id ASC LIMIT ?"
    params.append(bounded_limit)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()

    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "central_id": str(row["central_id"] or ""),
                "warn_heartbeat_age_sec": _to_int(row["warn_heartbeat_age_sec"], -1) if row["warn_heartbeat_age_sec"] is not None else None,
                "bad_heartbeat_age_sec": _to_int(row["bad_heartbeat_age_sec"], -1) if row["bad_heartbeat_age_sec"] is not None else None,
                "warn_pending_batches": _to_int(row["warn_pending_batches"], -1) if row["warn_pending_batches"] is not None else None,
                "bad_pending_batches": _to_int(row["bad_pending_batches"], -1) if row["bad_pending_batches"] is not None else None,
                "warn_wg_age_sec": _to_int(row["warn_wg_age_sec"], -1) if row["warn_wg_age_sec"] is not None else None,
                "bad_wg_age_sec": _to_int(row["bad_wg_age_sec"], -1) if row["bad_wg_age_sec"] is not None else None,
                "updated_at": row["updated_at"],
            }
        )
    return result


async def get_monitor_policy_override(db_path: str, *, central_id: str) -> dict[str, Any] | None:
    rows = await list_monitor_policy_overrides(db_path, central_id=central_id, limit=1)
    if not rows:
        return None
    return rows[0]


async def upsert_monitor_policy_override(
    db_path: str,
    *,
    central_id: str,
    values: dict[str, int | None],
) -> dict[str, Any]:
    allowed_keys = (
        "warn_heartbeat_age_sec",
        "bad_heartbeat_age_sec",
        "warn_pending_batches",
        "bad_pending_batches",
        "warn_wg_age_sec",
        "bad_wg_age_sec",
    )
    current = await get_monitor_policy_override(db_path, central_id=central_id)
    merged: dict[str, Any] = {}
    for key in allowed_keys:
        merged[key] = current.get(key) if isinstance(current, dict) else None
        if key in values:
            merged[key] = values[key]

    ts = utc_now_iso()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO monitor_policy_overrides(
              central_id,
              warn_heartbeat_age_sec,
              bad_heartbeat_age_sec,
              warn_pending_batches,
              bad_pending_batches,
              warn_wg_age_sec,
              bad_wg_age_sec,
              updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(central_id) DO UPDATE SET
              warn_heartbeat_age_sec=excluded.warn_heartbeat_age_sec,
              bad_heartbeat_age_sec=excluded.bad_heartbeat_age_sec,
              warn_pending_batches=excluded.warn_pending_batches,
              bad_pending_batches=excluded.bad_pending_batches,
              warn_wg_age_sec=excluded.warn_wg_age_sec,
              bad_wg_age_sec=excluded.bad_wg_age_sec,
              updated_at=excluded.updated_at;
            """,
            (
                str(central_id),
                merged["warn_heartbeat_age_sec"],
                merged["bad_heartbeat_age_sec"],
                merged["warn_pending_batches"],
                merged["bad_pending_batches"],
                merged["warn_wg_age_sec"],
                merged["bad_wg_age_sec"],
                ts,
            ),
        )
        await db.commit()

    row = await get_monitor_policy_override(db_path, central_id=central_id)
    if row is None:
        raise RuntimeError("failed_to_upsert_monitor_policy_override")
    return row


async def delete_monitor_policy_override(db_path: str, *, central_id: str) -> bool:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "DELETE FROM monitor_policy_overrides WHERE central_id = ?;",
            (str(central_id),),
        )
        await db.commit()
        return int(cursor.rowcount or 0) > 0


async def get_incident_last_notification_state(
    db_path: str,
    *,
    central_id: str | None = None,
    code: str | None = None,
) -> dict[tuple[str, str], dict[str, Any]]:
    query = """
        SELECT n.central_id, n.code, n.ts, n.event, n.status, n.channel
        FROM incident_notifications n
        JOIN (
          SELECT central_id, code, MAX(id) AS max_id
          FROM incident_notifications
          GROUP BY central_id, code
        ) latest ON latest.max_id = n.id
    """
    where_parts: list[str] = []
    params: list[Any] = []
    if central_id:
        where_parts.append("n.central_id = ?")
        params.append(str(central_id))
    if code:
        where_parts.append("n.code = ?")
        params.append(str(code))
    if where_parts:
        query += " WHERE " + " AND ".join(where_parts)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()

    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["central_id"]), str(row["code"]))
        result[key] = {
            "ts": row["ts"],
            "event": row["event"],
            "status": row["status"],
            "channel": row["channel"],
        }
    return result


async def record_incident_notification(
    db_path: str,
    *,
    central_id: str,
    code: str,
    severity: str,
    event: str,
    channel: str,
    destination: str | None,
    status: str,
    message: str | None,
    error: str | None,
) -> None:
    ts = utc_now_iso()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO incident_notifications(
              ts, central_id, code, severity, event, channel, destination, status, message, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                ts,
                str(central_id),
                str(code),
                str(severity or "bad"),
                str(event or "opened"),
                str(channel or "unknown"),
                destination,
                str(status or "unknown"),
                message,
                error,
            ),
        )
        await db.commit()


async def list_incident_notifications(
    db_path: str,
    *,
    central_id: str | None = None,
    code: str | None = None,
    channel: str | None = None,
    status: str | None = None,
    since_ts: str | None = None,
    q: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(int(limit), 2000))
    query = """
        SELECT
          id, ts, central_id, code, severity, event, channel, destination, status, message, error
        FROM incident_notifications
    """
    where_parts: list[str] = []
    params: list[Any] = []
    if central_id:
        where_parts.append("central_id = ?")
        params.append(str(central_id))
    if code:
        where_parts.append("code = ?")
        params.append(str(code))
    if channel:
        normalized_channel = str(channel).strip().lower()
        if normalized_channel in {"telegram", "email"}:
            where_parts.append("channel = ?")
            params.append(normalized_channel)
    if status:
        normalized_status = str(status).strip().lower()
        if normalized_status in {"sent", "failed", "skipped"}:
            where_parts.append("status = ?")
            params.append(normalized_status)
    if since_ts:
        parsed = _parse_iso_utc(str(since_ts))
        if parsed is not None:
            where_parts.append("ts >= ?")
            params.append(parsed.isoformat().replace("+00:00", "Z"))
    if q:
        query_text = str(q).strip().lower()
        if query_text:
            like = f"%{query_text}%"
            where_parts.append(
                "(LOWER(COALESCE(central_id,'')) LIKE ? OR LOWER(COALESCE(code,'')) LIKE ? OR LOWER(COALESCE(channel,'')) LIKE ? OR LOWER(COALESCE(destination,'')) LIKE ? OR LOWER(COALESCE(message,'')) LIKE ? OR LOWER(COALESCE(error,'')) LIKE ?)"
            )
            params.extend([like, like, like, like, like, like])
    if where_parts:
        query += " WHERE " + " AND ".join(where_parts)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(bounded_limit)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()

    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "id": row["id"],
                "ts": row["ts"],
                "central_id": row["central_id"],
                "code": row["code"],
                "severity": row["severity"],
                "event": row["event"],
                "channel": row["channel"],
                "destination": row["destination"],
                "status": row["status"],
                "message": row["message"],
                "error": row["error"],
            }
        )
    return result


async def get_incident_notification_by_id(db_path: str, *, notification_id: int) -> dict[str, Any] | None:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
              id, ts, central_id, code, severity, event, channel, destination, status, message, error
            FROM incident_notifications
            WHERE id = ?
            LIMIT 1;
            """,
            (int(notification_id),),
        ) as cursor:
            row = await cursor.fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "ts": row["ts"],
        "central_id": row["central_id"],
        "code": row["code"],
        "severity": row["severity"],
        "event": row["event"],
        "channel": row["channel"],
        "destination": row["destination"],
        "status": row["status"],
        "message": row["message"],
        "error": row["error"],
    }


async def record_admin_audit(
    db_path: str,
    *,
    actor: str | None,
    role: str,
    action: str,
    method: str,
    path: str,
    status: str,
    status_code: int,
    client_ip: str | None,
    details: dict[str, Any] | None,
) -> None:
    ts = utc_now_iso()
    payload = None
    if details:
        payload = json.dumps(details, ensure_ascii=False, separators=(",", ":"))
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO admin_audit_log(
              ts, actor, role, action, method, path, status, status_code, client_ip, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                ts,
                (actor or "").strip() or None,
                str(role or "viewer"),
                str(action or "unknown"),
                str(method or "GET"),
                str(path or ""),
                str(status or "ok"),
                int(status_code),
                (client_ip or "").strip() or None,
                payload,
            ),
        )
        await db.commit()


async def list_admin_audit(
    db_path: str,
    *,
    actor: str | None = None,
    role: str | None = None,
    action: str | None = None,
    path: str | None = None,
    status: str | None = None,
    since_ts: str | None = None,
    q: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(int(limit), 5000))
    query = """
        SELECT
          id, ts, actor, role, action, method, path, status, status_code, client_ip, details_json
        FROM admin_audit_log
    """
    where_parts: list[str] = []
    params: list[Any] = []
    if actor:
        where_parts.append("actor = ?")
        params.append(str(actor))
    if role:
        normalized_role = str(role).strip().lower()
        if normalized_role in {"viewer", "operator", "admin"}:
            where_parts.append("role = ?")
            params.append(normalized_role)
    if action:
        where_parts.append("action = ?")
        params.append(str(action))
    if path:
        where_parts.append("path = ?")
        params.append(str(path))
    if status:
        normalized_status = str(status).strip().lower()
        if normalized_status in {"ok", "forbidden", "error"}:
            where_parts.append("status = ?")
            params.append(normalized_status)
    if since_ts:
        parsed = _parse_iso_utc(str(since_ts))
        if parsed is not None:
            where_parts.append("ts >= ?")
            params.append(parsed.isoformat().replace("+00:00", "Z"))
    if q:
        query_text = str(q).strip().lower()
        if query_text:
            like = f"%{query_text}%"
            where_parts.append(
                "(LOWER(COALESCE(actor,'')) LIKE ? OR LOWER(COALESCE(action,'')) LIKE ? OR LOWER(COALESCE(path,'')) LIKE ? OR LOWER(COALESCE(status,'')) LIKE ? OR LOWER(COALESCE(details_json,'')) LIKE ?)"
            )
            params.extend([like, like, like, like, like])
    if where_parts:
        query += " WHERE " + " AND ".join(where_parts)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(bounded_limit)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()

    result: list[dict[str, Any]] = []
    for row in rows:
        details: dict[str, Any] | None = None
        raw_details = row["details_json"]
        if raw_details:
            try:
                parsed = json.loads(str(raw_details))
                if isinstance(parsed, dict):
                    details = parsed
            except Exception:
                details = {"raw": str(raw_details)}
        result.append(
            {
                "id": row["id"],
                "ts": row["ts"],
                "actor": row["actor"],
                "role": row["role"],
                "action": row["action"],
                "method": row["method"],
                "path": row["path"],
                "status": row["status"],
                "status_code": row["status_code"],
                "client_ip": row["client_ip"],
                "details": details,
            }
        )
    return result


async def set_alert_ack(
    db_path: str,
    *,
    central_id: str,
    code: str,
    actor: str | None,
    note: str | None,
) -> dict[str, Any]:
    ts = utc_now_iso()
    actor_val = (actor or "").strip() or None
    note_val = (note or "").strip() or None
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO alert_states(
              central_id, code, acked_at, acked_by, ack_note,
              silenced_until, silenced_by, silence_note, updated_at
            ) VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, ?)
            ON CONFLICT(central_id, code) DO UPDATE SET
              acked_at=excluded.acked_at,
              acked_by=excluded.acked_by,
              ack_note=excluded.ack_note,
              updated_at=excluded.updated_at;
            """,
            (central_id, code, ts, actor_val, note_val, ts),
        )
        await db.execute(
            """
            INSERT INTO alert_actions(ts, action, central_id, code, actor, note, silenced_until)
            VALUES (?, 'ack', ?, ?, ?, ?, NULL);
            """,
            (ts, central_id, code, actor_val, note_val),
        )
        await db.commit()
    return await get_alert_state(db_path, central_id=central_id, code=code)


async def set_alert_silence(
    db_path: str,
    *,
    central_id: str,
    code: str,
    duration_sec: int,
    actor: str | None,
    note: str | None,
) -> dict[str, Any]:
    now_dt = datetime.now(timezone.utc)
    until = (now_dt + timedelta(seconds=max(60, int(duration_sec)))).isoformat().replace("+00:00", "Z")
    ts = now_dt.isoformat().replace("+00:00", "Z")
    actor_val = (actor or "").strip() or None
    note_val = (note or "").strip() or None
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO alert_states(
              central_id, code, acked_at, acked_by, ack_note,
              silenced_until, silenced_by, silence_note, updated_at
            ) VALUES (?, ?, NULL, NULL, NULL, ?, ?, ?, ?)
            ON CONFLICT(central_id, code) DO UPDATE SET
              silenced_until=excluded.silenced_until,
              silenced_by=excluded.silenced_by,
              silence_note=excluded.silence_note,
              updated_at=excluded.updated_at;
            """,
            (central_id, code, until, actor_val, note_val, ts),
        )
        await db.execute(
            """
            INSERT INTO alert_actions(ts, action, central_id, code, actor, note, silenced_until)
            VALUES (?, 'silence', ?, ?, ?, ?, ?);
            """,
            (ts, central_id, code, actor_val, note_val, until),
        )
        await db.commit()
    return await get_alert_state(db_path, central_id=central_id, code=code)


async def clear_alert_silence(
    db_path: str,
    *,
    central_id: str,
    code: str,
    actor: str | None,
    note: str | None,
) -> dict[str, Any]:
    ts = utc_now_iso()
    actor_val = (actor or "").strip() or None
    note_val = (note or "").strip() or None
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO alert_states(
              central_id, code, acked_at, acked_by, ack_note,
              silenced_until, silenced_by, silence_note, updated_at
            ) VALUES (?, ?, NULL, NULL, NULL, NULL, ?, ?, ?)
            ON CONFLICT(central_id, code) DO UPDATE SET
              silenced_until=NULL,
              silenced_by=excluded.silenced_by,
              silence_note=excluded.silence_note,
              updated_at=excluded.updated_at;
            """,
            (central_id, code, actor_val, note_val, ts),
        )
        await db.execute(
            """
            INSERT INTO alert_actions(ts, action, central_id, code, actor, note, silenced_until)
            VALUES (?, 'unsilence', ?, ?, ?, ?, NULL);
            """,
            (ts, central_id, code, actor_val, note_val),
        )
        await db.commit()
    return await get_alert_state(db_path, central_id=central_id, code=code)


async def get_alert_state(db_path: str, *, central_id: str, code: str) -> dict[str, Any]:
    now_dt = datetime.now(timezone.utc)
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
              central_id, code, acked_at, acked_by, ack_note,
              silenced_until, silenced_by, silence_note, updated_at
            FROM alert_states
            WHERE central_id = ? AND code = ?
            LIMIT 1;
            """,
            (central_id, code),
        ) as cursor:
            row = await cursor.fetchone()
    if not row:
        return {
            "central_id": central_id,
            "code": code,
            "acked_at": None,
            "acked_by": None,
            "ack_note": None,
            "silenced_until": None,
            "silenced_by": None,
            "silence_note": None,
            "silenced": False,
            "updated_at": None,
        }
    payload = _state_to_dict(row, now_dt)
    payload["central_id"] = central_id
    payload["code"] = code
    return payload


async def list_alert_actions(
    db_path: str,
    *,
    central_id: str | None = None,
    code: str | None = None,
    action: str | None = None,
    since_ts: str | None = None,
    q: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(int(limit), 1000))
    query = """
        SELECT id, ts, action, central_id, code, actor, note, silenced_until
        FROM alert_actions
    """
    where_parts: list[str] = []
    params: list[Any] = []
    if central_id:
        where_parts.append("central_id = ?")
        params.append(central_id)
    if code:
        where_parts.append("code = ?")
        params.append(code)
    if action:
        normalized_action = str(action).strip().lower()
        if normalized_action in {"ack", "silence", "unsilence"}:
            where_parts.append("action = ?")
            params.append(normalized_action)
    if since_ts:
        parsed = _parse_iso_utc(str(since_ts))
        if parsed is not None:
            where_parts.append("ts >= ?")
            params.append(parsed.isoformat().replace("+00:00", "Z"))
    if q:
        query_text = str(q).strip().lower()
        if query_text:
            where_parts.append(
                "(LOWER(COALESCE(central_id,'')) LIKE ? OR LOWER(COALESCE(code,'')) LIKE ? OR LOWER(COALESCE(actor,'')) LIKE ? OR LOWER(COALESCE(note,'')) LIKE ?)"
            )
            like = f"%{query_text}%"
            params.extend([like, like, like, like])
    if where_parts:
        query += " WHERE " + " AND ".join(where_parts)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(bounded_limit)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()

    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "id": row["id"],
                "ts": row["ts"],
                "action": row["action"],
                "central_id": row["central_id"],
                "code": row["code"],
                "actor": row["actor"],
                "note": row["note"],
                "silenced_until": row["silenced_until"],
            }
        )
    return result
