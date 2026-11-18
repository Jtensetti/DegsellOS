#!/usr/bin/env bash
# Appen ForskarOS: går igenom alla vyer med ett riktigt projekt under Xvfb.
# Kräver GTK 4, libadwaita, PyGObject och Xvfb. Hoppar annars över, om inte
# FORSKAROS_KRAV_APP=1. FORSKAROS_SKARMDUMPAR=mapp sparar en PNG per vy.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

check='import gi; gi.require_version("Gtk", "4.0"); gi.require_version("Adw", "1"); from gi.repository import Adw'
python=""
for candidate in python3 python3.12 python3.13; do
  if command -v "$candidate" >/dev/null && "$candidate" -c "$check" 2>/dev/null; then python=$(command -v "$candidate"); break; fi
done
if [[ -z "$python" ]] || ! command -v xvfb-run >/dev/null; then
  [[ "${FORSKAROS_KRAV_APP:-}" != 1 ]] || { echo "FEL: GTK 4, libadwaita eller xvfb-run saknas" >&2; exit 1; }
  echo "HOPPAR ÖVER: appens självtest (GTK 4, libadwaita eller xvfb-run saknas här)"
  exit 0
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
# Varningar från GTK eller libadwaita (CRITICAL) räknas som fel.
G_DEBUG=fatal-criticals GDK_BACKEND=x11 NO_AT_BRIDGE=1 \
  xvfb-run -a -s "-screen 0 1000x900x24" \
  "$python" -I system_files/usr/share/forskaros/projekt/app.py --sjalvtest "$tmp" 2> "$tmp.log" || {
    grep -v "libEGL\|dbus-launch\|^$" "$tmp.log" >&2 || true
    rm -f "$tmp.log"; exit 1; }
rm -f "$tmp.log"
