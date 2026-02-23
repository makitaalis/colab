from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from app.db import get_notification_settings


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _parse_iso_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _resolve_bool_setting(
    settings: dict[str, str],
    *,
    key: str,
    env_key: str,
    default: bool,
) -> bool:
    raw = settings.get(key)
    if raw is None or str(raw).strip() == "":
        return _bool_env(env_key, default)
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


async def load_notification_runtime_settings(db_path: str) -> dict[str, Any]:
    settings = await get_notification_settings(db_path)
    mute_until_raw = str(settings.get("mute_until") or "").strip()
    min_severity_raw = str(settings.get("min_severity") or "bad").strip().lower()
    if min_severity_raw not in {"good", "warn", "bad"}:
        min_severity_raw = "bad"
    return {
        "notify_telegram": _resolve_bool_setting(
            settings,
            key="notify_telegram",
            env_key="ALERT_NOTIFY_TELEGRAM",
            default=True,
        ),
        "notify_email": _resolve_bool_setting(
            settings,
            key="notify_email",
            env_key="ALERT_NOTIFY_EMAIL",
            default=False,
        ),
        "mute_until": mute_until_raw,
        "mute_until_dt": _parse_iso_utc(mute_until_raw),
        "rate_limit_sec": max(30, min(_to_int(settings.get("rate_limit_sec"), 300), 86400)),
        "escalation_sec": max(60, min(_to_int(settings.get("escalation_sec"), 1800), 86400 * 7)),
        "min_severity": min_severity_raw,
        "stale_always_notify": _resolve_bool_setting(
            settings,
            key="stale_always_notify",
            env_key="ALERT_STALE_ALWAYS_NOTIFY",
            default=True,
        ),
        "raw": settings,
    }


def normalize_notification_settings(settings: dict[str, str]) -> dict[str, Any]:
    runtime: dict[str, Any] = {}
    runtime["notify_telegram"] = str(settings.get("notify_telegram", "1")).strip().lower() in {"1", "true", "yes", "on"}
    runtime["notify_email"] = str(settings.get("notify_email", "0")).strip().lower() in {"1", "true", "yes", "on"}
    runtime["mute_until"] = str(settings.get("mute_until", "") or "")
    runtime["rate_limit_sec"] = max(30, min(_to_int(settings.get("rate_limit_sec"), 300), 86400))
    min_severity = str(settings.get("min_severity", "bad")).strip().lower()
    runtime["min_severity"] = min_severity if min_severity in {"good", "warn", "bad"} else "bad"
    runtime["stale_always_notify"] = str(settings.get("stale_always_notify", "1")).strip().lower() in {"1", "true", "yes", "on"}
    runtime["escalation_sec"] = max(60, min(_to_int(settings.get("escalation_sec"), 1800), 86400 * 7))
    return runtime


def normalize_monitor_policy_settings(settings: dict[str, str]) -> dict[str, Any]:
    def clamp(value: Any, *, lower: int, upper: int, default: int) -> int:
        return max(lower, min(_to_int(value, default), upper))

    warn_heartbeat_age_sec = clamp(
        settings.get("monitor_warn_heartbeat_age_sec"),
        lower=30,
        upper=3600,
        default=120,
    )
    bad_heartbeat_age_sec = clamp(
        settings.get("monitor_bad_heartbeat_age_sec"),
        lower=60,
        upper=7200,
        default=600,
    )
    if bad_heartbeat_age_sec <= warn_heartbeat_age_sec:
        bad_heartbeat_age_sec = min(7200, warn_heartbeat_age_sec + 30)

    warn_pending_batches = clamp(
        settings.get("monitor_warn_pending_batches"),
        lower=1,
        upper=1000,
        default=1,
    )
    bad_pending_batches = clamp(
        settings.get("monitor_bad_pending_batches"),
        lower=1,
        upper=5000,
        default=50,
    )
    if bad_pending_batches <= warn_pending_batches:
        bad_pending_batches = min(5000, warn_pending_batches + 1)

    warn_wg_age_sec = clamp(
        settings.get("monitor_warn_wg_age_sec"),
        lower=30,
        upper=3600,
        default=300,
    )
    bad_wg_age_sec = clamp(
        settings.get("monitor_bad_wg_age_sec"),
        lower=60,
        upper=7200,
        default=1200,
    )
    if bad_wg_age_sec <= warn_wg_age_sec:
        bad_wg_age_sec = min(7200, warn_wg_age_sec + 30)

    min_severity_raw = str(settings.get("fleet_health_auto_min_severity") or "bad").strip().lower()
    if min_severity_raw not in {"good", "warn", "bad"}:
        min_severity_raw = "bad"

    channel_mode = str(settings.get("fleet_health_auto_channel") or "auto").strip().lower()
    if channel_mode not in {"auto", "telegram", "email", "all"}:
        channel_mode = "auto"

    window_raw = str(settings.get("fleet_health_auto_window") or "24h").strip().lower()
    if window_raw not in {"1h", "6h", "24h", "7d"}:
        window_raw = "24h"

    return {
        "warn_heartbeat_age_sec": warn_heartbeat_age_sec,
        "bad_heartbeat_age_sec": bad_heartbeat_age_sec,
        "warn_pending_batches": warn_pending_batches,
        "bad_pending_batches": bad_pending_batches,
        "warn_wg_age_sec": warn_wg_age_sec,
        "bad_wg_age_sec": bad_wg_age_sec,
        "fleet_health_auto_enabled": _resolve_bool_setting(
            settings,
            key="fleet_health_auto_enabled",
            env_key="FLEET_HEALTH_AUTO_ENABLED",
            default=False,
        ),
        "fleet_health_auto_notify_recovery": _resolve_bool_setting(
            settings,
            key="fleet_health_auto_notify_recovery",
            env_key="FLEET_HEALTH_AUTO_NOTIFY_RECOVERY",
            default=True,
        ),
        "fleet_health_auto_min_interval_sec": clamp(
            settings.get("fleet_health_auto_min_interval_sec"),
            lower=60,
            upper=86400,
            default=900,
        ),
        "fleet_health_auto_min_severity": min_severity_raw,
        "fleet_health_auto_channel": channel_mode,
        "fleet_health_auto_window": window_raw,
    }


def resolve_health_notify_channels(*, channel_mode: str, runtime: dict[str, Any]) -> list[str]:
    mode = str(channel_mode or "auto").strip().lower()
    if mode == "auto":
        channels: list[str] = []
        if bool(runtime.get("notify_telegram")):
            channels.append("telegram")
        if bool(runtime.get("notify_email")):
            channels.append("email")
        return channels
    if mode == "all":
        return ["telegram", "email"]
    if mode in {"telegram", "email"}:
        return [mode]
    return []
