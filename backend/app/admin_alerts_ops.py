from __future__ import annotations

from typing import Any, Callable


def build_alerts_response(
    *,
    filtered_alerts: list[dict[str, Any]],
    ts_generated: str,
    limit: int,
) -> dict[str, Any]:
    bounded_limit = max(1, min(int(limit), 1000))
    return {
        "status": "ok",
        "ts_generated": ts_generated,
        "total": len(filtered_alerts),
        "alerts": filtered_alerts[:bounded_limit],
    }


def build_alert_groups_response(
    *,
    filtered_alerts: list[dict[str, Any]],
    ts_generated: str,
    limit: int,
    normalize_severity: Callable[[Any], str],
    severity_rank: Callable[[Any], int],
    to_int: Callable[[Any, int], int],
) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {}
    for item in filtered_alerts:
        group_code = str(item.get("code") or "alert")
        row = groups.get(group_code)
        if row is None:
            row = {
                "code": group_code,
                "total": 0,
                "centrals": set(),
                "silenced": 0,
                "good": 0,
                "warn": 0,
                "bad": 0,
                "latest_ts": "",
                "sample_message": str(item.get("message") or ""),
            }
            groups[group_code] = row
        row["total"] += 1
        row["centrals"].add(str(item.get("central_id") or ""))
        if bool(item.get("silenced")):
            row["silenced"] += 1
        sev = normalize_severity(item.get("severity"))
        if sev in {"good", "warn", "bad"}:
            row[sev] += 1
        current_ts = str(item.get("ts_received") or "")
        if current_ts and (not row["latest_ts"] or current_ts > row["latest_ts"]):
            row["latest_ts"] = current_ts

    grouped_rows: list[dict[str, Any]] = []
    for row in groups.values():
        dominant = "good"
        if int(row.get("bad", 0)) > 0:
            dominant = "bad"
        elif int(row.get("warn", 0)) > 0:
            dominant = "warn"
        grouped_rows.append(
            {
                "code": row["code"],
                "total": int(row["total"]),
                "centrals_total": len(row["centrals"]),
                "silenced": int(row["silenced"]),
                "good": int(row["good"]),
                "warn": int(row["warn"]),
                "bad": int(row["bad"]),
                "dominant_severity": dominant,
                "latest_ts": row["latest_ts"],
                "sample_message": row["sample_message"],
            }
        )

    grouped_rows.sort(
        key=lambda item: (
            -severity_rank(item.get("dominant_severity")),
            -to_int(item.get("total"), 0),
            str(item.get("code") or ""),
        )
    )
    bounded_limit = max(1, min(int(limit), 1000))
    severity_totals = {
        "good": sum(1 for item in filtered_alerts if normalize_severity(item.get("severity")) == "good"),
        "warn": sum(1 for item in filtered_alerts if normalize_severity(item.get("severity")) == "warn"),
        "bad": sum(1 for item in filtered_alerts if normalize_severity(item.get("severity")) == "bad"),
    }
    return {
        "status": "ok",
        "ts_generated": ts_generated,
        "alerts_total": len(filtered_alerts),
        "groups_total": len(grouped_rows),
        "silenced_total": sum(1 for item in filtered_alerts if bool(item.get("silenced"))),
        "severity_totals": severity_totals,
        "groups": grouped_rows[:bounded_limit],
    }
