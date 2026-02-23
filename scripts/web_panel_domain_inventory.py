#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.admin_domains.domain_catalog import ADMIN_PANEL_DOMAINS  # noqa: E402
from app.client_domains.domain_catalog import CLIENT_PANEL_DOMAINS  # noqa: E402


def _render_panel(title: str, domains) -> list[str]:
    lines: list[str] = [f"## {title}", ""]
    for domain in domains:
        lines.append(f"### {domain.title} (`{domain.key}`)")
        lines.append(f"- audience: `{domain.audience}`")
        lines.append(f"- owner: `{domain.owner}`")
        if domain.doc_path:
            lines.append(f"- doc: `{domain.doc_path}`")
        lines.append("- routes:")
        for route in domain.routes:
            route_meta = [
                f"`{route.key}` -> `{route.href}`",
            ]
            if route.page_file:
                route_meta.append(f"page `{route.page_file}`")
            if route.api_group:
                route_meta.append(f"api-group `{route.api_group}`")
            lines.append(f"  - {', '.join(route_meta)}")
        lines.append("")
    return lines


def build_markdown() -> str:
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    out: list[str] = [
        "# Web Panel Domain Inventory",
        "",
        f"- generated_at_utc: `{ts}`",
        "",
    ]
    out.extend(_render_panel("Admin Panel Domains", ADMIN_PANEL_DOMAINS))
    out.extend(_render_panel("Client Panel Domains", CLIENT_PANEL_DOMAINS))
    return "\n".join(out).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate web panel domain inventory markdown.")
    parser.add_argument(
        "--write",
        default="Docs/auto/web-panel/domain-inventory.md",
        help="Output markdown file path (default: Docs/auto/web-panel/domain-inventory.md)",
    )
    parser.add_argument("--stdout", action="store_true", help="Print markdown to stdout.")
    args = parser.parse_args()

    payload = build_markdown()
    out_path = (ROOT / args.write).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(payload, encoding="utf-8")
    if args.stdout:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

