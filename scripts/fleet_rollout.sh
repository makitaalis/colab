#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
fleet_rollout.sh — orchestrate rollout steps for one system_id from fleet registry

Usage:
  ./scripts/fleet_rollout.sh --system-id <id> [options]

Options:
  --system-id <id>        Required, e.g. sys-0001
  --registry <path>       Registry CSV (default: fleet/registry.csv)
  --bundle-root <path>    Bundle root (default: fleet/out)
  --apply-wg-peer         Apply server peer config via scripts/fleet_apply_wg_peer.py
  --wg-fetch-central-pubkey  Fetch central public key automatically for WG peer apply
  --wg-ensure-central-key    Generate /etc/wireguard/central.key/.pub on central if missing
  --wg-allow-placeholder     Allow placeholder key (lab-only)
  --deploy-mvp            Run scripts/deploy_passengers_mvp.sh using bundle fleet.env
  --apply-central-env     Apply central env template via scripts/fleet_apply_central_env.py
  --smoke                 Run scripts/mvp_e2e_smoke.sh using bundle parameters
  --all-safe              Equivalent to: --deploy-mvp --apply-central-env --smoke
  -h, --help              Show help

Notes:
  - Script always runs: validate registry + generate bundle.
  - For production WG apply prefer --wg-fetch-central-pubkey (no manual key paste).
EOF
}

SYSTEM_ID=""
REGISTRY="fleet/registry.csv"
BUNDLE_ROOT="fleet/out"
DO_APPLY_WG=0
DO_DEPLOY_MVP=0
DO_APPLY_ENV=0
DO_SMOKE=0
WG_FETCH_CENTRAL_PUBKEY=0
WG_ENSURE_CENTRAL_KEY=0
WG_ALLOW_PLACEHOLDER=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --system-id) SYSTEM_ID="${2:-}"; shift 2 ;;
    --registry) REGISTRY="${2:-}"; shift 2 ;;
    --bundle-root) BUNDLE_ROOT="${2:-}"; shift 2 ;;
    --apply-wg-peer) DO_APPLY_WG=1; shift ;;
    --wg-fetch-central-pubkey) WG_FETCH_CENTRAL_PUBKEY=1; shift ;;
    --wg-ensure-central-key) WG_ENSURE_CENTRAL_KEY=1; shift ;;
    --wg-allow-placeholder) WG_ALLOW_PLACEHOLDER=1; shift ;;
    --deploy-mvp) DO_DEPLOY_MVP=1; shift ;;
    --apply-central-env) DO_APPLY_ENV=1; shift ;;
    --smoke) DO_SMOKE=1; shift ;;
    --all-safe) DO_DEPLOY_MVP=1; DO_APPLY_ENV=1; DO_SMOKE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "${SYSTEM_ID}" ]]; then
  echo "ERROR: --system-id is required" >&2
  usage
  exit 2
fi

echo "== Validate registry =="
python3 scripts/fleet_registry.py --registry "${REGISTRY}" validate

echo
echo "== Generate bundle =="
python3 scripts/fleet_registry.py --registry "${REGISTRY}" bundle --system-id "${SYSTEM_ID}" --out-root "${BUNDLE_ROOT}"

BUNDLE_DIR="${BUNDLE_ROOT%/}/${SYSTEM_ID}"
if [[ ! -f "${BUNDLE_DIR}/fleet.env" ]]; then
  echo "ERROR: bundle env not found: ${BUNDLE_DIR}/fleet.env" >&2
  exit 1
fi

source "${BUNDLE_DIR}/fleet.env"

if [[ ${DO_APPLY_WG} -eq 1 ]]; then
  echo
  echo "== Apply WireGuard peer on server =="
  wg_cmd=(python3 scripts/fleet_apply_wg_peer.py \
    --system-id "${SYSTEM_ID}" \
    --registry "${REGISTRY}" \
    --bundle-root "${BUNDLE_ROOT}")
  if [[ ${WG_FETCH_CENTRAL_PUBKEY} -eq 1 ]]; then
    wg_cmd+=(--fetch-central-pubkey --central-host "${CENTRAL_IP}" --central-user "${OPI_USER}")
  fi
  if [[ ${WG_ENSURE_CENTRAL_KEY} -eq 1 ]]; then
    wg_cmd+=(--ensure-central-key)
  fi
  if [[ ${WG_ALLOW_PLACEHOLDER} -eq 1 ]]; then
    wg_cmd+=(--allow-placeholder)
  fi
  "${wg_cmd[@]}"
fi

if [[ ${DO_DEPLOY_MVP} -eq 1 ]]; then
  echo
  echo "== Deploy MVP services to OPi =="
  ./scripts/deploy_passengers_mvp.sh \
    --central-ip "${CENTRAL_IP}" \
    --edge-ips "${EDGE_IPS_CSV}" \
    --user "${OPI_USER}" \
    --server-host "${SERVER_HOST}" \
    --server-user "${SERVER_SSH_USER}" \
    --backend-host "${BACKEND_HOST}" \
    --stop-mode "${STOP_MODE:-manual}" \
    --stop-flush-interval-sec "${STOP_FLUSH_INTERVAL_SEC:-120}"
fi

if [[ ${DO_APPLY_ENV} -eq 1 ]]; then
  echo
  echo "== Apply central passengers env =="
  python3 scripts/fleet_apply_central_env.py \
    --system-id "${SYSTEM_ID}" \
    --registry "${REGISTRY}" \
    --bundle-root "${BUNDLE_ROOT}"
fi

if [[ ${DO_SMOKE} -eq 1 ]]; then
  echo
  echo "== Run MVP smoke test =="
  IFS=',' read -r DOOR1_IP DOOR2_IP _ <<<"${EDGE_IPS_CSV},,"
  ./scripts/mvp_e2e_smoke.sh \
    --central-ip "${CENTRAL_IP}" \
    --door1-ip "${DOOR1_IP}" \
    --door2-ip "${DOOR2_IP}" \
    --server-host "${SERVER_HOST}"
fi

if [[ ${DO_APPLY_WG} -eq 0 && ${DO_DEPLOY_MVP} -eq 0 && ${DO_APPLY_ENV} -eq 0 && ${DO_SMOKE} -eq 0 ]]; then
  echo
  echo "No action flags selected."
  echo "Bundle is ready: ${BUNDLE_DIR}"
  echo "Next:"
  echo "  1) Re-run with --apply-wg-peer --wg-fetch-central-pubkey --all-safe"
  echo "  2) If central key missing add --wg-ensure-central-key"
fi
