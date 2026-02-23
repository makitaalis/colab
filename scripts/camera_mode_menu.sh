#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SWITCH_SCRIPT="${SCRIPT_DIR}/camera_mode_switch.sh"
CALIB_SCRIPT="${SCRIPT_DIR}/camera_depth_calibrate.sh"

CAMERA_IP="${CAMERA_IP:-192.168.10.1}"
OPI_USER="${OPI_USER:-orangepi}"
DEBUG_PORT="${DEBUG_PORT:-8091}"
DEBUG_BIND_LOCAL="127.0.0.1"
DEBUG_BIND_LAN="0.0.0.0"

CONFIG_FILE_DEFAULT="${HOME}/.config/passengers/camera_menu.env"
CONFIG_FILE="${CAMERA_MENU_CONFIG:-${CONFIG_FILE_DEFAULT}}"

# Optional persisted defaults (per-PC).
if [[ -f "${CONFIG_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${CONFIG_FILE}" || true
fi

CONTROL_SOCKET="/tmp/passengers-camera-tunnel-${OPI_USER}@${CAMERA_IP}-${DEBUG_PORT}.sock"

usage() {
  cat <<USAGE
camera_mode_menu.sh — interactive camera mode menu for an OAK-D Lite node (Central or Door)

Usage:
  ./scripts/camera_mode_menu.sh [options]

Options:
  --camera-ip <ip>    Camera node IP (default: ${CAMERA_IP})
  --central-ip <ip>   Alias for --camera-ip (backward compatible)
  --user <name>       SSH user (default: ${OPI_USER})
  --debug-port <n>    Debug stream port (default: ${DEBUG_PORT})
  -h, --help          Show help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --camera-ip) CAMERA_IP="${2:-}"; shift 2 ;;
    --central-ip) CAMERA_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --debug-port) DEBUG_PORT="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

refresh_connection_context() {
  HOST="${OPI_USER}@${CAMERA_IP}"
  CONTROL_SOCKET="/tmp/passengers-camera-tunnel-${OPI_USER}@${CAMERA_IP}-${DEBUG_PORT}.sock"
}

refresh_connection_context

if [[ ! -x "${SWITCH_SCRIPT}" ]]; then
  echo "ERROR: required script not found: ${SWITCH_SCRIPT}" >&2
  exit 1
fi

if [[ ! -x "${CALIB_SCRIPT}" ]]; then
  echo "WARN: calibration script not found/executable: ${CALIB_SCRIPT}"
fi

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

can_ssh() {
  ssh -n -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new "${HOST}" "true" >/dev/null 2>&1
}

open_url() {
  local url="$1"
  if has_cmd xdg-open; then
    nohup xdg-open "${url}" >/dev/null 2>&1 || true
    echo "Browser open requested: ${url}"
  elif has_cmd sensible-browser; then
    nohup sensible-browser "${url}" >/dev/null 2>&1 || true
    echo "Browser open requested: ${url}"
  else
    echo "Open in browser manually: ${url}"
  fi
}

tunnel_status() {
  if [[ -S "${CONTROL_SOCKET}" ]] && ssh -n -S "${CONTROL_SOCKET}" -O check "${HOST}" >/dev/null 2>&1; then
    echo "running"
  else
    echo "stopped"
  fi
}

start_tunnel() {
  if [[ "$(tunnel_status)" == "running" ]]; then
    echo "Tunnel already running on localhost:${DEBUG_PORT}"
    return 0
  fi

  if ! ssh -fN -M -S "${CONTROL_SOCKET}" \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -L "${DEBUG_PORT}:127.0.0.1:${DEBUG_PORT}" "${HOST}"; then
    echo "ERROR: failed to start tunnel (check SSH/IP/user)"
    return 1
  fi

  echo "Tunnel started: localhost:${DEBUG_PORT} -> ${HOST}:127.0.0.1:${DEBUG_PORT}"
  return 0
}

stop_tunnel() {
  if [[ "$(tunnel_status)" != "running" ]]; then
    echo "Tunnel already stopped"
    return 0
  fi
  ssh -n -S "${CONTROL_SOCKET}" -O exit "${HOST}" >/dev/null 2>&1 || true
  rm -f "${CONTROL_SOCKET}" || true
  echo "Tunnel stopped"
}

switch_mode() {
  local mode="$1"
  local bind="$2"

  if ! can_ssh; then
    echo "ERROR: ${HOST} is unreachable via SSH"
    return 1
  fi

  if ! "${SWITCH_SCRIPT}" --mode "${mode}" --camera-ip "${CAMERA_IP}" --user "${OPI_USER}" --debug-bind "${bind}" --debug-port "${DEBUG_PORT}"; then
    echo "ERROR: failed to switch mode=${mode}"
    return 1
  fi

  return 0
}

show_status() {
  echo
  echo "=== Camera Menu Status ==="
  echo "Camera node: ${HOST}"
  echo "Debug port: ${DEBUG_PORT}"
  echo "Tunnel: $(tunnel_status)"
  echo "Control socket: ${CONTROL_SOCKET}"
  if can_ssh; then
    echo "SSH: reachable"
    echo
    if ! "${SWITCH_SCRIPT}" --status --camera-ip "${CAMERA_IP}" --user "${OPI_USER}"; then
      echo "WARN: status command failed"
    fi
  else
    echo "SSH: unreachable"
    echo "Hint: check power/cable/IP, then try menu option 15"
  fi
  echo
}

print_menu() {
  cat <<MENU
=============================
Camera Modes (OAK-D Node)
=============================
1) Status (services + tunnel)
2) Switch PROD mode (counter)
3) Switch DEBUG local (127.0.0.1) + start tunnel + open video
4) Switch DEBUG LAN (0.0.0.0) + open video by node IP
5) Switch DEPTH-COUNT local (transport strict) + start tunnel + open video
6) Switch DEPTH-COUNT LAN (transport strict) + open video by node IP
7) Switch DEPTH-HEIGHT-MULTI local (stereo-only) + start tunnel + open video
8) Switch DEPTH-HEIGHT-MULTI LAN (stereo-only) + open video by node IP
9) Switch OAK-VIEWER mode (free camera)
10) Start SSH tunnel only
11) Stop SSH tunnel
12) Open video page
13) Open health page
14) Show debug-stream logs (last 80)
15) Show depth-counting logs (last 80)
16) Show depth-height-multi logs (last 80)
17) Show counter logs (last 80)
18) Edit connection settings (IP/user/port)
19) Depth calibration helper (preset/manual + restart)
20) Depth health snapshot (5 samples)
0) Exit
MENU
}

edit_settings() {
  read -r -p "Camera node IP [${CAMERA_IP}]: " new_ip
  read -r -p "SSH user [${OPI_USER}]: " new_user
  read -r -p "Debug port [${DEBUG_PORT}]: " new_port

  if [[ -n "${new_ip}" ]]; then
    CAMERA_IP="${new_ip}"
  fi
  if [[ -n "${new_user}" ]]; then
    OPI_USER="${new_user}"
  fi
  if [[ -n "${new_port}" ]]; then
    if [[ "${new_port}" =~ ^[0-9]+$ ]]; then
      DEBUG_PORT="${new_port}"
    else
      echo "WARN: invalid port, keeping: ${DEBUG_PORT}"
    fi
  fi

  refresh_connection_context
  echo "Updated settings: host=${HOST}, port=${DEBUG_PORT}"

  mkdir -p "$(dirname "${CONFIG_FILE}")"
  cat > "${CONFIG_FILE}" <<EOF
# Passengers camera mode menu — local defaults (generated)
CAMERA_IP="${CAMERA_IP}"
OPI_USER="${OPI_USER}"
DEBUG_PORT="${DEBUG_PORT}"
EOF
  echo "Saved defaults: ${CONFIG_FILE}"
}

video_url_local() {
  echo "http://127.0.0.1:${DEBUG_PORT}/"
}

video_url_lan() {
  echo "http://${CAMERA_IP}:${DEBUG_PORT}/"
}

health_url_local() {
  echo "http://127.0.0.1:${DEBUG_PORT}/health"
}

health_url_lan() {
  echo "http://${CAMERA_IP}:${DEBUG_PORT}/health"
}

depth_calibration_menu() {
  if [[ ! -x "${CALIB_SCRIPT}" ]]; then
    echo "ERROR: calibration script unavailable: ${CALIB_SCRIPT}"
    return 1
  fi

  echo "Depth calibration presets:"
  echo "  1) baseline"
  echo "  2) wide-scan (recommended first)"
  echo "  3) door-tight"
  echo "  4) transport-strict (public transport, low false-positive)"
  echo "  5) transport-fast-pass (public transport, faster detection)"
  echo "  6) commissioning-no-depth (debug only, depth off)"
  echo "  7) commissioning-depth-soft (depth on, soft thresholds)"
  echo "  8) custom KEY=VALUE"
  echo "  9) head-yolov8-host (YOLOv8 head, host decode; commissioning)"
  read -r -p "Select preset/action: " depth_choice

  case "${depth_choice}" in
    1)
      "${CALIB_SCRIPT}" --camera-ip "${CAMERA_IP}" --user "${OPI_USER}" --preset baseline --health
      ;;
    2)
      "${CALIB_SCRIPT}" --camera-ip "${CAMERA_IP}" --user "${OPI_USER}" --preset wide-scan --health
      ;;
    3)
      "${CALIB_SCRIPT}" --camera-ip "${CAMERA_IP}" --user "${OPI_USER}" --preset door-tight --health
      ;;
    4)
      "${CALIB_SCRIPT}" --camera-ip "${CAMERA_IP}" --user "${OPI_USER}" --preset transport-strict --health
      ;;
    5)
      "${CALIB_SCRIPT}" --camera-ip "${CAMERA_IP}" --user "${OPI_USER}" --preset transport-fast-pass --health
      ;;
    6)
      "${CALIB_SCRIPT}" --camera-ip "${CAMERA_IP}" --user "${OPI_USER}" --preset commissioning-no-depth --health
      ;;
    7)
      "${CALIB_SCRIPT}" --camera-ip "${CAMERA_IP}" --user "${OPI_USER}" --preset commissioning-depth-soft --health
      ;;
    8)
      read -r -p "Enter KEY=VALUE (example CAM_DEPTH_COUNT_ROI=0.10,0.12,0.90,0.95): " kv1
      read -r -p "Enter second KEY=VALUE or blank: " kv2
      if [[ -z "${kv1}" ]]; then
        echo "No values entered."
        return 0
      fi
      if [[ -n "${kv2}" ]]; then
        "${CALIB_SCRIPT}" --camera-ip "${CAMERA_IP}" --user "${OPI_USER}" --set "${kv1}" --set "${kv2}" --health
      else
        "${CALIB_SCRIPT}" --camera-ip "${CAMERA_IP}" --user "${OPI_USER}" --set "${kv1}" --health
      fi
      ;;
    9)
      "${CALIB_SCRIPT}" --camera-ip "${CAMERA_IP}" --user "${OPI_USER}" --preset head-yolov8-host --health
      ;;
    *)
      echo "Unknown depth calibration action: ${depth_choice}"
      ;;
  esac
}

depth_health_snapshot() {
  if ! can_ssh; then
    echo "ERROR: ${HOST} is unreachable via SSH"
    return 1
  fi
  local i
  for i in 1 2 3 4 5; do
    echo "-- sample ${i}/5 --"
    ssh -n "${HOST}" "curl -sS http://127.0.0.1:${DEBUG_PORT}/health || true"
    sleep 1
  done
}

show_status

while true; do
  print_menu
  read -r -p "Select action: " choice
  echo
  case "${choice}" in
    1)
      show_status
      ;;
    2)
      switch_mode "prod" "${DEBUG_BIND_LOCAL}" || true
      ;;
    3)
      if switch_mode "debug-stream" "${DEBUG_BIND_LOCAL}"; then
        if start_tunnel; then
          open_url "$(video_url_local)"
          echo "If browser did not open: $(video_url_local)"
        fi
      fi
      ;;
    4)
      stop_tunnel
      if switch_mode "debug-stream" "${DEBUG_BIND_LAN}"; then
        open_url "$(video_url_lan)"
        echo "If browser did not open: $(video_url_lan)"
      fi
      ;;
    5)
      if switch_mode "depth-counting" "${DEBUG_BIND_LOCAL}"; then
        if start_tunnel; then
          open_url "$(video_url_local)"
          echo "If browser did not open: $(video_url_local)"
        fi
      fi
      ;;
    6)
      stop_tunnel
      if switch_mode "depth-counting" "${DEBUG_BIND_LAN}"; then
        open_url "$(video_url_lan)"
        echo "If browser did not open: $(video_url_lan)"
      fi
      ;;
    7)
      if switch_mode "depth-height-multi" "${DEBUG_BIND_LOCAL}"; then
        if start_tunnel; then
          open_url "$(video_url_local)"
          echo "If browser did not open: $(video_url_local)"
        fi
      fi
      ;;
    8)
      stop_tunnel
      if switch_mode "depth-height-multi" "${DEBUG_BIND_LAN}"; then
        open_url "$(video_url_lan)"
        echo "If browser did not open: $(video_url_lan)"
      fi
      ;;
    9)
      stop_tunnel
      switch_mode "oak-viewer" "${DEBUG_BIND_LOCAL}" || true
      ;;
    10)
      start_tunnel || true
      ;;
    11)
      stop_tunnel
      ;;
    12)
      if [[ "$(tunnel_status)" == "running" ]]; then
        open_url "$(video_url_local)"
        echo "Video URL: $(video_url_local)"
      else
        open_url "$(video_url_lan)"
        echo "Video URL: $(video_url_lan)"
      fi
      ;;
    13)
      if [[ "$(tunnel_status)" == "running" ]]; then
        open_url "$(health_url_local)"
        echo "Health URL: $(health_url_local)"
      else
        open_url "$(health_url_lan)"
        echo "Health URL: $(health_url_lan)"
      fi
      ;;
    14)
      if can_ssh; then
        ssh -n "${HOST}" "journalctl -u passengers-camera-debug-stream.service -n 80 --no-pager" || true
      else
        echo "ERROR: ${HOST} is unreachable via SSH"
      fi
      ;;
    15)
      if can_ssh; then
        ssh -n "${HOST}" "journalctl -u passengers-camera-depth-counting.service -n 80 --no-pager" || true
      else
        echo "ERROR: ${HOST} is unreachable via SSH"
      fi
      ;;
    16)
      if can_ssh; then
        ssh -n "${HOST}" "journalctl -u passengers-camera-depth-height-multi.service -n 80 --no-pager" || true
      else
        echo "ERROR: ${HOST} is unreachable via SSH"
      fi
      ;;
    17)
      if can_ssh; then
        ssh -n "${HOST}" "journalctl -u passengers-camera-counter.service -n 80 --no-pager" || true
      else
        echo "ERROR: ${HOST} is unreachable via SSH"
      fi
      ;;
    18)
      edit_settings
      ;;
    19)
      depth_calibration_menu
      ;;
    20)
      depth_health_snapshot
      ;;
    0)
      echo "Exit camera menu"
      exit 0
      ;;
    *)
      echo "Unknown action: ${choice}"
      ;;
  esac
  echo
done
