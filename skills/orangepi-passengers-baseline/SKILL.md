---
name: orangepi-passengers-baseline
description: Baseline verification and auto-documentation for the OrangePi_passangers project (Orange Pi Zero 3 door nodes + central-gw). Use when asked to check “are settings correct?”, compare PC Ethernet vs central-gw LAN 192.168.10.0/24, generate baseline reports in Docs/auto, or align documentation with the actual deployed configuration before continuing setup.
---

# OrangePi Passengers Baseline

## Workflow (baseline first)

Goal: quickly confirm we follow the project’s canonical LAN (`192.168.10.0/24`) and capture “ground truth” from PC + Central into versionable Markdown, before proceeding with time sync / services / application work.

### Expected baseline (canonical)

- LAN: `192.168.10.0/24`
- Central (4GB): `central-gw` / `192.168.10.1` on `end0` via NetworkManager profile `opizero3-static`
- Doors (1GB): `door-1`=`192.168.10.11`, `door-2`=`192.168.10.12`
- No default route via the LAN interface (Wi‑Fi default route is OK if intentionally enabled)

### 1) Generate automatic baseline documentation

Run in the repo root:

```bash
python3 scripts/opizero_baseline.py --host 192.168.10.1 --user orangepi
```

Review:

- `Docs/auto/baseline-summary.md`
- `Docs/auto/baseline-pc.md`
- `Docs/auto/baseline-central-gw.md`

This script is intentionally “non-sudo” (remote sudo often requires a password, which should not be automated).

### 2) Decide: fix config vs fix docs

Rule: docs describe the canonical target state; if the system is intentionally different, update docs to match. If it’s accidental drift, fix the system.

Common actions:

- PC has extra legacy address (e.g. `192.168.50.0/24`): remove it from the Ethernet profile (keep only `192.168.10.x/24`).
- Central time not synchronized: proceed with `Docs/настройка ПО/План/3. Синхронизация времени (критично для данных).md`.
- Unexpected listening ports on Central (e.g. `rpcbind` `111`, `iperf3` `5201`): confirm they’re needed; otherwise disable and/or close in firewall docs/config.

### 3) Re-run baseline

After changes, re-run the baseline script and confirm the warnings are gone (or explicitly justified in docs).

