#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
enable_passwordless_sudo.sh — включить/выключить passwordless sudo на узлах OPi

Требование: SSH по ключу уже настроен. На каждом узле потребуется 1 раз ввести пароль sudo.

Что делает (enable):
  - Создаёт /etc/sudoers.d/010-orangepi-nopasswd
  - Добавляет правило: orangepi ALL=(ALL) NOPASSWD:ALL
  - Проверяет синтаксис через visudo
  - Проверяет, что sudo работает без пароля: sudo -n true

Что делает (disable):
  - Удаляет /etc/sudoers.d/010-orangepi-nopasswd

Примеры:
  ./scripts/enable_passwordless_sudo.sh enable 192.168.10.1 192.168.10.11 192.168.10.12
  ./scripts/enable_passwordless_sudo.sh disable 192.168.10.11

Опции:
  --user USER     SSH user (default: orangepi)
EOF
}

die() { echo "ERROR: $*" >&2; exit 1; }

[[ $# -ge 2 ]] || { usage; exit 2; }

action="$1"
shift

user="orangepi"
hosts=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --user) user="${2:-}"; shift 2 ;;
    *) hosts+=("$1"); shift ;;
  esac
done

[[ ${#hosts[@]} -gt 0 ]] || die "Не указаны хосты"

case "$action" in
  enable|disable) ;;
  *) die "Action должен быть enable или disable" ;;
esac

sudoers_file="/etc/sudoers.d/010-orangepi-nopasswd"

for host in "${hosts[@]}"; do
  echo
  echo "==> ${host} (${user})"

  if [[ "$action" = "enable" ]]; then
    ssh -tt -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new "${user}@${host}" bash -lc \
      "set -euo pipefail
       echo 'Writing ${sudoers_file} ...'
       echo 'orangepi ALL=(ALL) NOPASSWD:ALL' | sudo tee '${sudoers_file}' >/dev/null
       sudo chmod 0440 '${sudoers_file}'
       echo 'Validating sudoers ...'
       sudo visudo -c -f '${sudoers_file}'
       echo 'Testing passwordless sudo ...'
       sudo -n true
       echo 'OK: passwordless sudo enabled'"
  else
    ssh -tt -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new "${user}@${host}" bash -lc \
      "set -euo pipefail
       echo 'Removing ${sudoers_file} ...'
       sudo rm -f '${sudoers_file}'
       echo 'Testing sudo -n true (expected to fail) ...'
       if sudo -n true 2>/dev/null; then
         echo 'WARN: sudo still passwordless (another rule may exist)'
       else
         echo 'OK: passwordless rule removed (or sudo requires password)'
       fi"
  fi
done

echo
echo "Done."

