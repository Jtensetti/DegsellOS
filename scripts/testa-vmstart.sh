#!/usr/bin/env bash
# Starta en qcow2 med UEFI. Alla gästskrivningar hamnar i en temporär overlay.
set -euo pipefail
disk=$(realpath "${1:?ange qcow2-fil}")
arch=${2:?ange amd64 eller arm64}
work=$(mktemp -d)
pid=''
cleanup() {
  if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; fi
  rm -rf "$work"
}
trap cleanup EXIT

case "$arch" in
  amd64) binary=qemu-system-x86_64; machine=q35; efi=/usr/share/OVMF/OVMF ;;
  arm64) binary=qemu-system-aarch64; machine=virt; efi=/usr/share/AAVMF/AAVMF ;;
  *) exit 2 ;;
esac
suffix=
[[ "$arch" == amd64 ]] && suffix=_4M
cp "${efi}_VARS${suffix}.fd" "$work/vars.fd"
accel=tcg
cpu=max
if [[ -r /dev/kvm && -w /dev/kvm ]]; then accel=kvm; cpu=host; fi
qemu-img create -q -f qcow2 -F qcow2 -b "$disk" "$work/guest.qcow2"
"$binary" -machine "$machine" -accel "$accel" -cpu "$cpu" -m 3072 -smp 2 \
  -drive "if=pflash,format=raw,readonly=on,file=${efi}_CODE${suffix}.fd" \
  -drive "if=pflash,format=raw,file=$work/vars.fd" \
  -drive "if=virtio,format=qcow2,file=$work/guest.qcow2" \
  -device virtio-serial-pci -chardev "socket,id=qa,path=$work/qa,server=on,wait=off" \
  -device virtserialport,chardev=qa,name=org.qemu.guest_agent.0 \
  -nic none -display none -serial "file:$work/console" -no-reboot &
pid=$!
# guest-get-osinfo besvaras av Linux i gästen, först när dess gästagent körs.
if ! python3 - "$work/qa" "$arch" "$pid" <<'PY'
import json, os, socket, sys, time
path, arch, pid = sys.argv[1:]
expected = {"amd64": "x86_64", "arm64": "aarch64"}[arch]
deadline = time.monotonic() + 720
while time.monotonic() < deadline:
    os.kill(int(pid), 0)
    try:
        with socket.socket(socket.AF_UNIX) as sock:
            sock.settimeout(5)
            sock.connect(path)
            sock.sendall(b'{"execute":"guest-get-osinfo"}\n')
            with sock.makefile('rb') as stream:
                data = json.loads(stream.readline())['return']
            assert data['machine'] == expected, data
            assert data['kernel-release'], data
            print(data['name'], data['kernel-release'], data['machine'], flush=True)
            break
    except (FileNotFoundError, OSError, ValueError, KeyError):
        time.sleep(3)
else:
    sys.exit("Gästens operativsystem svarade inte inom tolv minuter.")
PY
then
  tail -80 "$work/console" >&2 || true
  exit 1
fi
