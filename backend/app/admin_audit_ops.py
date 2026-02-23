from __future__ import annotations

from typing import Any

from app.db import list_admin_audit


async def build_admin_audit_response(
    *,
    db_path: str,
    actor: str | None,
    role: str | None,
    action: str | None,
    path: str | None,
    status: str | None,
    since_ts: str | None,
    q: str | None,
    limit: int,
) -> dict[str, Any]:
    items = await list_admin_audit(
        db_path,
        actor=actor,
        role=role,
        action=action,
        path=path,
        status=status,
        since_ts=since_ts,
        q=q,
        limit=limit,
    )
    return {
        "status": "ok",
        "total": len(items),
        "audit": items,
    }
