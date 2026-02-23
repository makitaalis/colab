#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
flash_opizero3_sd.sh — прошивка microSD образом Orange Pi + офлайн-настройка LAN+SSH

Зачем:
  - Записать .img на microSD
  - Офлайн задать статический IP (LAN 192.168.10.0/24) через NetworkManager
  - Офлайн включить ssh.service
  - (опционально) записать SSH public key в /home/orangepi/.ssh/authorized_keys
  - (опционально) задать hostname + /etc/hosts + /etc/node_id

Примеры:
  sudo ./scripts/flash_opizero3_sd.sh \
    --img ./orangepizero3_1_0_4_debian_bookworm/Orangepizero3_1.0.4_debian_bookworm_server_linux6.1.31/Orangepizero3_1.0.4_debian_bookworm_server_linux6.1.31.img \
    --dev /dev/sda --node door-1 --yes

  sudo ./scripts/flash_opizero3_sd.sh --img /path/to/image.img --dev /dev/sdX --ip 192.168.10.12 --hostname door-2 --yes

Опции:
  --img PATH         Путь к .img
  --dev /dev/sdX     Устройство microSD (ВНИМАНИЕ: будет полностью перезаписано)
  --node NAME        central-gw, door-1 или door-2 (автоматически подставит IP/hostname)
  --ip A.B.C.D       IP адрес (если не используете --node)
  --hostname NAME    hostname (если не используете --node)
  --iface IFACE      Имя Ethernet интерфейса на OPi (default: end0)
  --nm NAME          Имя NM профиля (default: opizero3-static)
  --user USER        Логин для SSH key (default: orangepi)
  --pubkey PATH      SSH public key (default: /home/$SUDO_USER/.ssh/id_ed25519.pub)
  --no-pubkey        Не писать authorized_keys
  --no-hostname      Не менять /etc/hostname и /etc/hosts
  --no-node-id       Не создавать /etc/node_id
  --dry-run          Только показать план действий (ничего не писать на диск)
  --yes              Не спрашивать подтверждение
EOF
}

die() { echo "ERROR: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "Не найдено: $1"; }

IMG=""
DEV=""
NODE=""
IP=""
HOSTNAME=""
OPI_IFACE="end0"
NM_PROFILE="opizero3-static"
SSH_USER="orangepi"
PUBKEY=""
WRITE_PUBKEY=1
SET_HOSTNAME=1
SET_NODE_ID=1
DRY_RUN=0
YES=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --img) IMG="${2:-}"; shift 2 ;;
    --dev) DEV="${2:-}"; shift 2 ;;
    --node) NODE="${2:-}"; shift 2 ;;
    --ip) IP="${2:-}"; shift 2 ;;
    --hostname) HOSTNAME="${2:-}"; shift 2 ;;
    --iface) OPI_IFACE="${2:-}"; shift 2 ;;
    --nm) NM_PROFILE="${2:-}"; shift 2 ;;
    --user) SSH_USER="${2:-}"; shift 2 ;;
    --pubkey) PUBKEY="${2:-}"; shift 2 ;;
    --no-pubkey) WRITE_PUBKEY=0; shift ;;
    --no-hostname) SET_HOSTNAME=0; shift ;;
    --no-node-id) SET_NODE_ID=0; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --yes) YES=1; shift ;;
    *) die "Неизвестная опция: $1 (см. --help)" ;;
  esac
done

need lsblk
need dd
need awk
need sed
need grep
need mount
need umount
need uuidgen
need udevadm
need partprobe
need install
need readlink

[[ -n "$IMG" ]] || die "Укажите --img PATH"
[[ -f "$IMG" ]] || die "Файл образа не найден: $IMG"
[[ -n "$DEV" ]] || die "Укажите --dev /dev/sdX"
[[ -b "$DEV" ]] || die "Устройство не является блочным: $DEV"

if [[ -n "$NODE" ]]; then
  case "$NODE" in
    central|central-gw) IP="${IP:-192.168.10.1}"; HOSTNAME="${HOSTNAME:-central-gw}" ;;
    door-1) IP="${IP:-192.168.10.11}"; HOSTNAME="${HOSTNAME:-door-1}" ;;
    door-2) IP="${IP:-192.168.10.12}"; HOSTNAME="${HOSTNAME:-door-2}" ;;
    *) die "--node должен быть central-gw, door-1 или door-2" ;;
  esac
fi

[[ -n "$IP" ]] || die "Укажите --ip (или используйте --node door-1/door-2)"
[[ -n "$HOSTNAME" ]] || die "Укажите --hostname (или используйте --node door-1/door-2)"

if [[ -z "$PUBKEY" ]]; then
  if [[ -n "${SUDO_USER:-}" ]]; then
    PUBKEY="/home/${SUDO_USER}/.ssh/id_ed25519.pub"
  else
    PUBKEY="${HOME}/.ssh/id_ed25519.pub"
  fi
fi

if [[ $DRY_RUN -eq 0 ]] && [[ $EUID -ne 0 ]]; then
  die "Запустите через sudo (нужны права для записи на $DEV и монтирования): sudo $0 ..."
fi

dev_base="$(basename "$DEV")"
rm_flag="$(lsblk -dn -o RM "$DEV" | tr -d ' ')"
[[ "$rm_flag" = "1" ]] || die "$DEV не помечен как removable (RM=1). Прерываю для безопасности."

root_dev="$(findmnt -n -o SOURCE / || true)"
if [[ -n "$root_dev" ]] && [[ "$root_dev" == "$DEV"* ]]; then
  die "$DEV выглядит как диск с текущей системой ($root_dev). Прерываю."
fi

echo "План:"
echo "  1) Размонтировать разделы $DEV (если смонтированы)"
echo "  2) Перезаписать $DEV образом: $IMG"
echo "  3) Смонтировать rootfs раздел образа"
echo "  4) Создать NM профиль $NM_PROFILE для $OPI_IFACE: $IP/24 (never-default)"
echo "  5) Включить ssh.service офлайн"
if [[ $WRITE_PUBKEY -eq 1 ]]; then
  echo "  6) Записать SSH key: $PUBKEY -> /home/$SSH_USER/.ssh/authorized_keys"
fi
if [[ $SET_HOSTNAME -eq 1 ]]; then
  echo "  7) Установить hostname=$HOSTNAME и /etc/hosts (central/doors)"
fi
if [[ $SET_NODE_ID -eq 1 ]]; then
  echo "  8) Создать /etc/node_id (UUID) и chmod 444"
fi
echo

if [[ $DRY_RUN -eq 1 ]]; then
  echo "DRY RUN: ничего не записываю."
  exit 0
fi

if [[ $YES -ne 1 ]]; then
  echo "ВНИМАНИЕ: $DEV будет полностью перезаписан. Чтобы продолжить, введите: YES"
  read -r confirm
  [[ "$confirm" = "YES" ]] || die "Отменено."
fi

echo "Размонтирование разделов $DEV ..."
while read -r mp; do
  [[ -n "$mp" ]] || continue
  umount "$mp" || true
done < <(lsblk -ln -o MOUNTPOINTS "$DEV" | awk 'NF{print $0}')

sync
echo "Запись образа на $DEV ..."
dd if="$IMG" of="$DEV" bs=4M status=progress conv=fsync
sync

partprobe "$DEV" || true
udevadm settle || true

echo "Поиск rootfs раздела ..."
# Выбираем последний ext4/ btrfs? обычно ext4. Если нет — берём самый большой раздел.
root_part="$(lsblk -ln -o NAME,FSTYPE,SIZE -p "$DEV" | awk '$2=="ext4"{print $1}' | tail -n1 || true)"
if [[ -z "$root_part" ]]; then
  root_part="$(lsblk -ln -o NAME,SIZE -p "$DEV" | sort -k2 -h | tail -n1 | awk '{print $1}' || true)"
fi
[[ -n "$root_part" ]] || die "Не смог определить rootfs раздел на $DEV"

mnt="$(mktemp -d /tmp/opizero3-rootfs.XXXXXX)"
trap 'set +e; sync; umount "$mnt" >/dev/null 2>&1 || true; rmdir "$mnt" >/dev/null 2>&1 || true' EXIT

mount "$root_part" "$mnt"

echo "Настройка NetworkManager ($NM_PROFILE, $OPI_IFACE, $IP/24) ..."
uuid="$(uuidgen)"
install -d -m 0755 "$mnt/etc/NetworkManager/system-connections"
cat >"$mnt/etc/NetworkManager/system-connections/${NM_PROFILE}.nmconnection" <<EOF
[connection]
id=${NM_PROFILE}
uuid=${uuid}
type=ethernet
interface-name=${OPI_IFACE}
autoconnect=true

[ipv4]
method=manual
address1=${IP}/24
never-default=true

[ipv6]
method=ignore
EOF
chmod 600 "$mnt/etc/NetworkManager/system-connections/${NM_PROFILE}.nmconnection"
chown root:root "$mnt/etc/NetworkManager/system-connections/${NM_PROFILE}.nmconnection"

echo "Офлайн-включение SSH (ssh.service) ..."
unit=""
if [[ -f "$mnt/usr/lib/systemd/system/ssh.service" ]]; then
  unit="/usr/lib/systemd/system/ssh.service"
elif [[ -f "$mnt/lib/systemd/system/ssh.service" ]]; then
  unit="/lib/systemd/system/ssh.service"
fi

if [[ -n "$unit" ]]; then
  install -d -m 0755 "$mnt/etc/systemd/system/multi-user.target.wants"
  ln -sf "$unit" "$mnt/etc/systemd/system/multi-user.target.wants/ssh.service"
  # Убираем возможные маски:
  if [[ -L "$mnt/etc/systemd/system/ssh.service" ]] && [[ "$(readlink "$mnt/etc/systemd/system/ssh.service")" == "/dev/null" ]]; then
    rm -f "$mnt/etc/systemd/system/ssh.service"
  fi
  if [[ -L "$mnt/etc/systemd/system/sshd.service" ]] && [[ "$(readlink "$mnt/etc/systemd/system/sshd.service")" == "/dev/null" ]]; then
    rm -f "$mnt/etc/systemd/system/sshd.service"
  fi
else
  echo "WARN: Не найден ssh.service в образе (openssh-server может быть не установлен)."
fi

if [[ $WRITE_PUBKEY -eq 1 ]]; then
  [[ -f "$PUBKEY" ]] || die "Не найден public key: $PUBKEY (переопределите --pubkey или используйте --no-pubkey)"

  echo "Установка SSH key для пользователя $SSH_USER ..."
  home_dir="$(awk -F: -v u="$SSH_USER" '$1==u{print $6}' "$mnt/etc/passwd" | head -n1 || true)"
  uid="$(awk -F: -v u="$SSH_USER" '$1==u{print $3}' "$mnt/etc/passwd" | head -n1 || true)"
  gid="$(awk -F: -v u="$SSH_USER" '$1==u{print $4}' "$mnt/etc/passwd" | head -n1 || true)"
  [[ -n "$home_dir" ]] || die "Пользователь $SSH_USER не найден в $mnt/etc/passwd"
  [[ -n "$uid" ]] || die "Не смог определить uid пользователя $SSH_USER"
  [[ -n "$gid" ]] || die "Не смог определить gid пользователя $SSH_USER"

  install -d -m 0700 "$mnt${home_dir}/.ssh"
  cat "$PUBKEY" >"$mnt${home_dir}/.ssh/authorized_keys"
  chmod 600 "$mnt${home_dir}/.ssh/authorized_keys"
  chown -R "$uid:$gid" "$mnt${home_dir}/.ssh"
fi

if [[ $SET_HOSTNAME -eq 1 ]]; then
  echo "Установка hostname=$HOSTNAME и /etc/hosts ..."
  echo "$HOSTNAME" >"$mnt/etc/hostname"
  cat >"$mnt/etc/hosts" <<'EOF'
127.0.0.1 localhost

192.168.10.1   central-gw
192.168.10.11  door-1
192.168.10.12  door-2

::1         localhost ip6-localhost ip6-loopback
fe00::0     ip6-localnet
ff00::0     ip6-mcastprefix
ff02::1     ip6-allnodes
ff02::2     ip6-allrouters
EOF
fi

if [[ $SET_NODE_ID -eq 1 ]]; then
  echo "Создание /etc/node_id ..."
  uuidgen >"$mnt/etc/node_id"
  chmod 444 "$mnt/etc/node_id"
  chown root:root "$mnt/etc/node_id"
fi

sync
umount "$mnt"
trap - EXIT
rmdir "$mnt"
sync

echo "Готово."
echo "Дальше:"
echo "  - Вставьте microSD в Orange Pi, подключите к свичу, включите питание."
echo "  - Проверьте с ПК:  ping -c 3 $IP"
echo "  - Подключитесь по SSH: ssh ${SSH_USER}@${IP}"
