from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_env_file(path: str) -> dict[str, str]:
    env: dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    except FileNotFoundError:
        return {}
    return env


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: str


def http_post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    timeout_sec: int = 5,
) -> HttpResponse:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(url=url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return HttpResponse(status=getattr(resp, "status", 200), body=body)
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
        except Exception:
            body = str(e)
        return HttpResponse(status=e.code, body=body)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return HttpResponse(status=0, body=str(e))


def sleep_backoff(attempt: int, *, base_sec: float = 0.5, max_sec: float = 15.0) -> None:
    delay = min(max_sec, base_sec * (2**attempt))
    time.sleep(delay)
