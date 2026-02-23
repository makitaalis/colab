#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
camera_depth_live_probe.sh — live diagnostics window for depth-counting

Usage:
  ./scripts/camera_depth_live_probe.sh [options]

Options:
  --camera-ip <ip>   Camera node IP (default: 192.168.10.11)
  --user <name>      SSH user (default: orangepi)
  --port <port>      Debug HTTP port (default: 8091)
  --seconds <n>      Capture duration in seconds (default: 60)
  --out <path>       Optional file for raw JSONL samples
  -h, --help         Show help

Example:
  ./scripts/camera_depth_live_probe.sh --camera-ip 192.168.10.11 --seconds 45 --out /tmp/door1-live.jsonl
USAGE
}

CAMERA_IP="192.168.10.11"
OPI_USER="orangepi"
PORT="8091"
SECONDS_CAPTURE="60"
OUT_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --camera-ip) CAMERA_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --port) PORT="${2:-}"; shift 2 ;;
    --seconds) SECONDS_CAPTURE="${2:-}"; shift 2 ;;
    --out) OUT_FILE="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required" >&2
  exit 1
fi

if ! [[ "$SECONDS_CAPTURE" =~ ^[0-9]+$ ]] || [[ "$SECONDS_CAPTURE" -lt 5 ]]; then
  echo "ERROR: --seconds must be integer >= 5" >&2
  exit 2
fi

HOST="${OPI_USER}@${CAMERA_IP}"
HEALTH_CMD="curl -sS --max-time 2 http://127.0.0.1:${PORT}/health"

echo "== camera_depth_live_probe =="
echo "host=${HOST} port=${PORT} seconds=${SECONDS_CAPTURE}"

ssh -o ConnectTimeout=5 "${HOST}" "echo ok" >/dev/null
start_json="$(ssh "${HOST}" "${HEALTH_CMD}")"

if [[ -n "${OUT_FILE}" ]]; then
  : > "${OUT_FILE}"
fi

echo "Walk through the counting corridor now..."
end_epoch="$(( $(date -u +%s) + SECONDS_CAPTURE ))"
while true; do
  now_epoch="$(date -u +%s)"
  if [[ "${now_epoch}" -ge "${end_epoch}" ]]; then
    break
  fi

  iter_start_epoch="${now_epoch}"
  ts="$(date -u +%H:%M:%S)"
  sample="$(ssh "${HOST}" "${HEALTH_CMD}")"
  if [[ -n "${OUT_FILE}" ]]; then
    printf '%s\n' "${sample}" >> "${OUT_FILE}"
  fi
  echo "${sample}" | jq -rc --arg ts "${ts}" \
    '{ts:$ts,events_total,count_in,count_out,zone_neg_hits,zone_mid_hits,zone_pos_hits,middle_entries,middle_inferred,zone_flip_no_middle,age_reject,move_reject,hang_reject,conf_reject,depth_reject,depth_missing}'

  iter_end_epoch="$(date -u +%s)"
  elapsed="$(( iter_end_epoch - iter_start_epoch ))"
  if [[ "${elapsed}" -lt 1 ]]; then
    sleep "$(( 1 - elapsed ))"
  fi
done

end_json="$(ssh "${HOST}" "${HEALTH_CMD}")"

echo "== delta =="
jq -n --argjson s "${start_json}" --argjson e "${end_json}" '{
  d_events: ($e.events_total-$s.events_total),
  d_in: ($e.count_in-$s.count_in),
  d_out: ($e.count_out-$s.count_out),
  d_zone_neg: ($e.zone_neg_hits-$s.zone_neg_hits),
  d_zone_mid: ($e.zone_mid_hits-$s.zone_mid_hits),
  d_zone_pos: ($e.zone_pos_hits-$s.zone_pos_hits),
  d_middle_entries: ($e.middle_entries-$s.middle_entries),
  d_middle_inferred: (($e.middle_inferred // 0)-($s.middle_inferred // 0)),
  d_flip_no_middle: ($e.zone_flip_no_middle-$s.zone_flip_no_middle),
  d_age_reject: ($e.age_reject-$s.age_reject),
  d_move_reject: ($e.move_reject-$s.move_reject),
  d_hang_reject: ($e.hang_reject-$s.hang_reject),
  d_conf_reject: ($e.conf_reject-$s.conf_reject),
  d_depth_reject: ($e.depth_reject-$s.depth_reject),
  d_depth_missing: ($e.depth_missing-$s.depth_missing)
}'

echo "== hints =="
jq -n --argjson s "${start_json}" --argjson e "${end_json}" '
def d(k): ($e[k]-$s[k]);
if d("events_total") > 0 then
  "OK: events are increasing."
elif d("zone_mid_hits") == 0 and (d("zone_neg_hits") > 0 or d("zone_pos_hits") > 0) then
  "No middle hits: tune AXIS/AXIS_POS/LINE_GAP."
elif d("zone_flip_no_middle") > 0 and d("middle_entries") == 0 then
  "Side flip without middle: keep ANCHOR_MODE=center, then tune AXIS_HYST/LINE_GAP."
elif d("age_reject") > 0 then
  "age_reject grows: lower CAM_DEPTH_COUNT_MIN_TRACK_AGE."
elif d("move_reject") > 0 then
  "move_reject grows: lower CAM_DEPTH_COUNT_MIN_MOVE_NORM."
elif (d("depth_reject")+d("depth_missing")) > (d("zone_neg_hits")+d("zone_mid_hits")+d("zone_pos_hits"))/2 then
  "Depth gate rejects many detections: check camera angle and CAM_DEPTH_MIN_M/MAX_M."
else
  "No single dominant reject reason; share output for manual analysis."
end'

if [[ -n "${OUT_FILE}" ]]; then
  echo "raw samples saved: ${OUT_FILE}"
fi
