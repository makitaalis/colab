#!/usr/bin/env bash
set -euo pipefail

CAMERA_IP="192.168.10.11"
OPI_USER="orangepi"
SINCE=""
BOOTSTRAP_SINCE="today"
SHOW_HEARTBEAT="1"

usage() {
  cat <<'USAGE'
camera_counter_io_watch.sh — watch only IN/OUT from camera-counter events

Usage:
  ./scripts/camera_counter_io_watch.sh [options]

Options:
  --camera-ip <ip>    Camera node IP (default: 192.168.10.11)
  --central-ip <ip>   Alias for --camera-ip
  --user <name>       SSH user (default: orangepi)
  --since <expr>      journalctl --since value (example: "5 minutes ago")
  --bootstrap-since <expr>
                      Initial totals window (default: "today")
  --no-heartbeat
                      Do not print heartbeat lines with current totals
  -h, --help          Show help

Examples:
  ./scripts/camera_counter_io_watch.sh
  ./scripts/camera_counter_io_watch.sh --camera-ip 192.168.10.11 --user orangepi
  ./scripts/camera_counter_io_watch.sh --since "10 minutes ago"
  ./scripts/camera_counter_io_watch.sh --bootstrap-since "2 hours ago"
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --camera-ip) CAMERA_IP="${2:-}"; shift 2 ;;
    --central-ip) CAMERA_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --since) SINCE="${2:-}"; shift 2 ;;
    --bootstrap-since) BOOTSTRAP_SINCE="${2:-}"; shift 2 ;;
    --no-heartbeat) SHOW_HEARTBEAT="0"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

HOST="${OPI_USER}@${CAMERA_IP}"

echo "Watching IN/OUT on ${HOST} (Ctrl+C to stop)"
echo "Format: HH:MM:SS IN_TOTAL=<n> OUT_TOTAL=<n> (+in/+out)"

ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "${HOST}" "true"

bootstrap_cmd="journalctl -u passengers-camera-counter.service -o cat --no-pager"
if [[ -n "${BOOTSTRAP_SINCE}" ]]; then
  bootstrap_cmd+=" --since $(printf '%q' "${BOOTSTRAP_SINCE}")"
fi

bootstrap_raw="$(
  # shellcheck disable=SC2029
  ssh "${HOST}" "${bootstrap_cmd}" \
    | awk '
      /camera-counter event:/ {
        in_inc=0; out_inc=0;
        for (i=1; i<=NF; i++) {
          if ($i ~ /^in=/)  { split($i,a,"="); in_inc=a[2]+0; }
          if ($i ~ /^out=/) { split($i,b,"="); out_inc=b[2]+0; }
        }
        in_total += in_inc;
        out_total += out_inc;
      }
      END { printf "%d %d", in_total+0, out_total+0 }
    '
)"

bootstrap_in="$(echo "${bootstrap_raw}" | awk '{print $1+0}')"
bootstrap_out="$(echo "${bootstrap_raw}" | awk '{print $2+0}')"
echo "Initial totals since '${BOOTSTRAP_SINCE}': IN=${bootstrap_in} OUT=${bootstrap_out}"

follow_cmd="journalctl -u passengers-camera-counter.service -f -o cat --no-pager"
if [[ -n "${SINCE}" ]]; then
  follow_cmd+=" --since $(printf '%q' "${SINCE}")"
fi

# shellcheck disable=SC2029
ssh "${HOST}" "${follow_cmd}" \
  | awk '
    BEGIN {
      in_total = '"${bootstrap_in}"';
      out_total = '"${bootstrap_out}"';
      show_hb = '"${SHOW_HEARTBEAT}"';
    }
    /camera-counter event:/ {
      in_inc=0; out_inc=0;
      for (i=1; i<=NF; i++) {
        if ($i ~ /^in=/)  { split($i,a,"="); in_inc=a[2]+0; }
        if ($i ~ /^out=/) { split($i,b,"="); out_inc=b[2]+0; }
      }
      in_total += in_inc;
      out_total += out_inc;
      printf "%s IN_TOTAL=%d OUT_TOTAL=%d (+%d/+%d)\n", strftime("%H:%M:%S"), in_total, out_total, in_inc, out_inc;
      fflush();
    }
    /camera-counter heartbeat:/ {
      if (show_hb == 1) {
        events_total = "";
        for (i=1; i<=NF; i++) {
          if ($i ~ /^events=/) { split($i,e,"="); events_total=e[2]+0; }
        }
        if (events_total == "") {
          printf "%s HB IN_TOTAL=%d OUT_TOTAL=%d\n", strftime("%H:%M:%S"), in_total, out_total;
        } else {
          printf "%s HB IN_TOTAL=%d OUT_TOTAL=%d events=%d\n", strftime("%H:%M:%S"), in_total, out_total, events_total;
        }
        fflush();
      }
    }
  '
