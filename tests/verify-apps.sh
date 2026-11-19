#!/usr/bin/env bash
# Kontrollerar mot Flathub, Homebrew och PyPI att varje verktyg i profilerna
# finns, och att det finns för både amd64 och arm64 (PC och Mac i UTM).
# Kräver nätverk. Körs i CI.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

errors=0
warn() { echo "FEL: $*" >&2; errors=$((errors + 1)); }

while read -r kind id _; do
  case "$kind" in
    flatpak)
      arches=$(curl -fsS "https://flathub.org/api/v2/summary/$id" | python3 -c 'import json,sys; print(" ".join(json.load(sys.stdin).get("arches", [])))') \
        || { warn "Flatpak $id finns inte på Flathub"; continue; }
      [[ " $arches " == *" x86_64 "* && " $arches " == *" aarch64 "* ]] || warn "Flatpak $id saknar arkitektur (har: $arches)"
      echo "ok flatpak $id ($arches)" ;;
    brew)
      bottles=$(curl -fsS "https://formulae.brew.sh/api/formula/$id.json" | python3 -c 'import json,sys; print(" ".join(k for k in json.load(sys.stdin)["bottle"]["stable"]["files"] if "linux" in k))') \
        || { warn "Homebrew-formeln $id finns inte"; continue; }
      [[ "$bottles" == *x86_64_linux* && "$bottles" == *arm64_linux* ]] || warn "Homebrew $id saknar Linux-bygge (har: $bottles)"
      echo "ok brew $id ($bottles)" ;;
    uv)
      curl -fsS "https://pypi.org/pypi/$id/json" >/dev/null || { warn "PyPI-paketet $id finns inte"; continue; }
      echo "ok pypi $id" ;;
    webb) echo "ok webb ${id%%|*}" ;;
  esac
done < <(cat system_files/usr/share/degsellos/profiler/*.profil | grep -vE '^\s*(#|$)')

[[ $errors -eq 0 ]] || { echo "$errors fel" >&2; exit 1; }
echo "OK: alla verktyg finns för amd64 och arm64"
