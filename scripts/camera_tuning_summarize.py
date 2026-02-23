#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RunSummary:
    samples: int
    start_ts: str | None
    end_ts: str | None
    deltas: dict[str, int]
    max_active_tracks: int
    max_tracklets_total: int
    dominant_rejects: list[tuple[str, int]]


DEFAULT_KEYS: list[str] = [
    "events_total",
    "count_in",
    "count_out",
    "zone_neg_hits",
    "zone_mid_hits",
    "zone_pos_hits",
    "middle_entries",
    "middle_inferred",
    "zone_flip_no_middle",
    "roi_reject",
    "bbox_reject_size",
    "bbox_reject_ar",
    "bbox_reject_wz",
    "conf_reject",
    "age_reject",
    "move_reject",
    "hang_reject",
    "dup_reject",
    "rearm_reject",
    "depth_pass",
    "depth_reject",
    "depth_missing",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            rows.append(json.loads(s))
        except Exception:
            continue
    return rows


def as_int(x: Any) -> int | None:
    try:
        if x is None:
            return None
        return int(x)
    except Exception:
        return None


def summarize(rows: list[dict[str, Any]]) -> RunSummary:
    if not rows:
        return RunSummary(
            samples=0,
            start_ts=None,
            end_ts=None,
            deltas={},
            max_active_tracks=0,
            max_tracklets_total=0,
            dominant_rejects=[],
        )

    first = rows[0]
    last = rows[-1]

    deltas: dict[str, int] = {}
    for key in DEFAULT_KEYS:
        a = as_int(first.get(key))
        b = as_int(last.get(key))
        if a is None or b is None:
            continue
        deltas[key] = b - a

    max_active_tracks = 0
    max_tracklets_total = 0
    for r in rows:
        a = as_int(r.get("active_tracks"))
        if a is not None:
            max_active_tracks = max(max_active_tracks, a)
        t = as_int(r.get("tracklets_total"))
        if t is not None:
            max_tracklets_total = max(max_tracklets_total, t)

    reject_keys = [
        "roi_reject",
        "bbox_reject_size",
        "bbox_reject_ar",
        "bbox_reject_wz",
        "conf_reject",
        "age_reject",
        "move_reject",
        "hang_reject",
        "dup_reject",
        "rearm_reject",
        "depth_reject",
        "depth_missing",
    ]
    rejects: list[tuple[str, int]] = []
    for k in reject_keys:
        if k in deltas:
            rejects.append((k, deltas[k]))
    rejects.sort(key=lambda kv: kv[1], reverse=True)

    return RunSummary(
        samples=len(rows),
        start_ts=str(first.get("ts")) if first.get("ts") is not None else None,
        end_ts=str(last.get("ts")) if last.get("ts") is not None else None,
        deltas=deltas,
        max_active_tracks=max_active_tracks,
        max_tracklets_total=max_tracklets_total,
        dominant_rejects=rejects[:6],
    )


def md_table(d: dict[str, int], keys: list[str]) -> str:
    lines = ["| Metric | Δ |", "|---|---:|"]
    for k in keys:
        if k in d:
            lines.append(f"| `{k}` | {d[k]} |")
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: camera_tuning_summarize.py <health.jsonl>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    rows = load_jsonl(path)
    s = summarize(rows)

    print("# Camera tuning run summary")
    print()
    print(f"- samples: `{s.samples}`")
    if s.start_ts or s.end_ts:
        print(f"- window: `{s.start_ts}` → `{s.end_ts}`")
    print(f"- max active tracks: `{s.max_active_tracks}`")
    print(f"- max tracklets_total: `{s.max_tracklets_total}`")
    print()

    core = [
        "events_total",
        "count_in",
        "count_out",
        "zone_neg_hits",
        "zone_mid_hits",
        "zone_pos_hits",
        "middle_entries",
        "middle_inferred",
        "zone_flip_no_middle",
    ]
    print("## Core deltas")
    print(md_table(s.deltas, core))
    print()

    rej_keys = [k for k, _ in s.dominant_rejects]
    if rej_keys:
        print("## Dominant rejects (top)")
        print(md_table(s.deltas, rej_keys))
        print()

    # Hints
    d_events = s.deltas.get("events_total", 0)
    d_mid = s.deltas.get("zone_mid_hits", 0)
    d_flip = s.deltas.get("zone_flip_no_middle", 0)
    d_roi = s.deltas.get("roi_reject", 0)
    d_conf = s.deltas.get("conf_reject", 0)

    print("## Quick interpretation")
    if d_events > 0:
        print("- events are increasing: OK (continue tightening step-by-step).")
    else:
        if d_mid == 0:
            print("- `zone_mid_hits` stays 0: lines/axis/axis_pos likely miss the trajectory.")
        if d_flip > 0 and s.deltas.get("middle_entries", 0) == 0:
            print("- flips without middle: increase `LINE_GAP_NORM` and keep `ANCHOR_MODE=center`.")
        if d_roi > 0:
            print("- many `roi_reject`: ROI is too tight (or people leave ROI before crossing).")
        if d_conf > 0 and d_mid > 0:
            print("- many `conf_reject` with mid hits: lower confidence or improve lighting/model.")
        if d_events == 0 and d_mid > 0:
            print("- mid hits exist but no events: check `MIN_TRACK_AGE`, `MIN_MOVE_NORM`, cooldown/rearm.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

