#!/usr/bin/env bash
# Testar identiteten och fokusläget.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
fail() { echo "FEL: $*" >&2; exit 1; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

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
# 5. Utseendet kommer ur katalog/design.json och är i synk.
python3 -I scripts/identitet.py --kontroll >/dev/null || fail "kör python3 scripts/identitet.py"
python3 -I - <<'PY'
import json, re
import xml.etree.ElementTree as ET
from pathlib import Path
design = json.loads(Path("katalog/design.json").read_text())
typ = design["typsnitt"]
conf = ET.parse("system_files/usr/share/forskaros/identitet/52-forskaros-typsnitt.conf").getroot()
prefer = {a.find("family").text: a.find("prefer/family").text for a in conf.findall("alias")}
assert prefer == {"sans-serif": typ["gränssnitt"]["familj"], "system-ui": typ["gränssnitt"]["familj"],
                  "serif": typ["läsning"]["familj"], "monospace": typ["kod"]["familj"]}, prefer
build = Path("build_files/build.sh").read_text()
for role in typ.values():
    assert role["paket"] in build, f'build.sh installerar inte {role["paket"]}'
    assert role["familj"] in build, f'build.sh kontrollerar inte {role["familj"]}'
dconf = Path("system_files/etc/dconf/db/local.d/03-forskaros-utseende").read_text()
assert f"accent-color='{design['accent']['gnome']}'" in dconf
# Färger i rapportens exempelfigur och i appen ska finnas bland designvärdena.
values = json.dumps(design).lower()
figure = Path("system_files/usr/share/forskaros/projekt/mallar/gemensamt/diagram.py").read_text()
for color in set(re.findall(r"#[0-9a-fA-F]{6}", figure)):
    assert color.lower() in values, f"diagram.py använder {color} som inte finns i katalog/design.json"
# All text i rapporten klarar WCAG AA (4,5:1) mot papperet och de upphöjda ytorna, i båda lägena.
def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def contrast(a, b):
    hi, lo = sorted([lum(a), lum(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)
y = design["ytor"]
for mode in ("ljus", "mörk"):
    texts = [y["text"][mode], y["dämpad"][mode], design["accent"]["text"][mode],
             *(v[mode] for v in design["status"].values())]
    for bg in (y["papper"][mode], y["upphöjd"][mode]):
        for fg in texts:
            assert contrast(fg, bg) >= 4.5, f"{fg} mot {bg} ({mode}): {contrast(fg, bg):.2f}:1"
# Bara en källa: inga gamla färger kvar i dconf-filerna.
for f in Path("system_files/etc/dconf/db/local.d").glob("0*"):
    assert "#0F1B2A" not in f.read_text(), f
PY

for f in $(grep -ho "file:///usr/share/forskaros/identitet/[^']*" system_files/etc/dconf/db/local.d/0* | sed 's#file://##' | sort -u); do
  [[ -f "system_files$f" ]] || fail "dconf pekar på $f som saknas"
done
for desktop in system_files/usr/share/applications/*.desktop; do
  grep -q '^Icon=forskaros$' "$desktop" || fail "$desktop använder inte ForskarOS-ikonen"
done

echo "OK: identitet, fokusläge, designvärden i synk, typsnitt och kontrast"
