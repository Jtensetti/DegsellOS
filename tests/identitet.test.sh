#!/usr/bin/env bash
# Testar identiteten, dagens princip och fokusläget.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
fail() { echo "FEL: $*" >&2; exit 1; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# 1. Terminalen och panelen visar samma princip samma dag.
export FORSKAROS_PRINCIPER="$PWD/system_files/usr/share/forskaros/principer.txt"
for d in 2026-11-17 2027-01-01 2027-06-30; do
  term=$(bash system_files/usr/bin/forskaros-princip "$d" | sed 's/\x1b\[[0-9;]*m//g; s/^◌ ForskarOS · //')
  panel=$(node -e '
    const M=require("node:module"),o=M._load;M._load=function(r,...a){return r==="obsidian"?{Plugin:class{},ItemView:class{},Notice:class{},Modal:class{}}:o.call(this,r,...a)};
    const {engine:e}=require("./vault/.obsidian/plugins/forskaros-core/main.js");
    const P=e.PRINCIPLES, d=e.daysBetween("2026-01-01", process.argv[1]);
    console.log(P[((d % P.length) + P.length) % P.length]);' "$d")
  [[ "$term" == "$panel" ]] || fail "$d: terminalen '$term' ≠ panelen '$panel'"
done

# 2. Principfilen innehåller exakt panelens principer.
node -e '
  const M=require("node:module"),o=M._load;M._load=function(r,...a){return r==="obsidian"?{Plugin:class{},ItemView:class{},Notice:class{},Modal:class{}}:o.call(this,r,...a)};
  const {engine:e}=require("./vault/.obsidian/plugins/forskaros-core/main.js");
  const f=require("fs").readFileSync(process.argv[1],"utf8").trim().split("\n");
  if (JSON.stringify(f)!==JSON.stringify(e.PRINCIPLES)) { console.error("principer.txt är inte i synk med tillägget"); process.exit(1); }' "$FORSKAROS_PRINCIPER"

# 3. Fokusläget, med ersättare för gsettings, notify-send och systemd-run.
mkdir -p "$TMP/bin" "$TMP/home/ForskarOS/08 REFLEKTION"
for cmd in gsettings notify-send systemd-run; do
  printf '#!/bin/sh\necho "%s $*" >> "%s/anrop"\n' "$cmd" "$TMP" > "$TMP/bin/$cmd"; chmod +x "$TMP/bin/$cmd"
done
export PATH="$TMP/bin:$PATH" HOME="$TMP/home" XDG_RUNTIME_DIR="$TMP" FORSKAROS_VAULT="$TMP/home/ForskarOS"
bash system_files/usr/bin/forskaros-fokus 25 >/dev/null
grep -q 'gsettings set org.gnome.desktop.notifications show-banners false' "$TMP/anrop" || fail "notiser stängs inte av"
grep -q 'systemd-run .*--on-active=25m /usr/bin/forskaros-fokus av' "$TMP/anrop" || fail "fokuspasset avslutas inte automatiskt"
[[ -f "$TMP/forskaros-fokus.start" ]] || fail "starttiden sparas inte"
bash system_files/usr/bin/forskaros-fokus av >/dev/null
grep -q 'show-banners true' "$TMP/anrop" || fail "notiser slås inte på igen"
grep -qE '^- [0-9-]+ [0-9:]+–[0-9:]+ \(0 av 25 min\)' "$TMP/home/ForskarOS/08 REFLEKTION/Fokuslogg.md" || fail "fokuspasset loggas inte"
grep -q 'typ: fokuslogg' "$TMP/home/ForskarOS/08 REFLEKTION/Fokuslogg.md" || fail "fokusloggen saknar typ"
! bash system_files/usr/bin/forskaros-fokus 1000 >/dev/null 2>&1 || fail "orimlig längd accepterades"

# 4. Logotyp och bakgrunder är giltig SVG med sju faser, och dconf pekar rätt.
python3 -I - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path
d = Path("system_files/usr/share/forskaros/identitet")
for f in ["forskaros-logotyp.svg", "forskaros-bakgrund-ljus.svg", "forskaros-bakgrund-mork.svg"]:
    root = ET.parse(d / f).getroot()
    arcs = root.findall(".//{http://www.w3.org/2000/svg}path")
    assert len(arcs) == 7, f"{f}: {len(arcs)} bågar"
PY
for f in $(grep -o "file:///usr/share/forskaros/identitet/[^']*" system_files/etc/dconf/db/local.d/01-forskaros | sed 's#file://##'); do
  [[ -f "system_files$f" ]] || fail "dconf pekar på $f som saknas"
done
for desktop in system_files/usr/share/applications/*.desktop; do
  grep -q '^Icon=forskaros$' "$desktop" || fail "$desktop använder inte ForskarOS-ikonen"
done

echo "OK: identitet, dagens princip i terminal och panel, fokusläge"
