#!/usr/bin/env bash
# Kontrollera installerarens faktiska konfiguration före leverans.
set -euo pipefail
iso=${1:?Ange sökvägen till den byggda ISO-filen}
produkt=${2:-}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
xorriso -indev "$iso" -report_el_torito plain > "$tmp/boot"
grep -E 'El Torito boot img.*UEFI' "$tmp/boot"
for fil in osbuild.ks osbuild-base.ks; do
  xorriso -osirrox on -indev "$iso" -extract "/$fil" "$tmp/$fil"
done
grep -Eq '^graphical([[:space:]]|$)' "$tmp/osbuild.ks"
grep -Eq '^ostreecontainer ' "$tmp/osbuild-base.ks"
if grep -Ein '^[[:space:]]*(clearpart|autopart|zerombr|reqpart|part|partition|ignoredisk|raid|logvol|volgroup|mount|reboot)([[:space:]]|$)' "$tmp"/*.ks; then
  echo 'Installeraren måste invänta diskval och godkännande.' >&2
  exit 1
fi
if [[ -n "$produkt" ]]; then
  for meny in /boot/grub2/grub.cfg /EFI/BOOT/grub.cfg; do
    xorriso -osirrox on -indev "$iso" -extract "$meny" "$tmp/meny"
    grep -Fq "menuentry 'Install $produkt " "$tmp/meny"
    rm "$tmp/meny"
  done
fi
