#!/usr/bin/env bash
# Testar degsellos-init mot en tillfällig "systemkatalog" och hemkatalog.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Kör skriptet med seed-sökvägen omdirigerad till repots vault.
INIT="$TMP/degsellos-init"
sed "s#^SEED=.*#SEED='$PWD/vault'#" system_files/usr/bin/degsellos-init > "$INIT"
chmod +x "$INIT"
export HOME="$TMP/home"
export XDG_CONFIG_HOME="$HOME/.config"  # CI-miljöer sätter ofta en egen
mkdir -p "$HOME"
PLUGIN=".obsidian/plugins/degsellos-core"

# I en VM kan delningen redan vara monterad vid första inloggningen.
mkdir "$TMP/bin"
cat > "$TMP/bin/mountpoint" <<'SH'
#!/bin/sh
test "$1" = "-q" && test "$2" = "/var/mnt/delad"
SH
chmod +x "$TMP/bin/mountpoint"
export PATH="$TMP/bin:$PATH"

# 1. Första inloggning skapar vaulten och genvägen till den monterade mappen.
"$INIT" >/dev/null
test -f "$HOME/DegsellOS/00 START/Hem.md"
test -f "$HOME/DegsellOS/$PLUGIN/main.js"
test "$(readlink "$HOME/Delad")" = /var/mnt/delad

# 2. Forskarens anteckningar och ändringar finns kvar efter ny inloggning.
echo "min hypotes" > "$HOME/DegsellOS/02 HYPOTESER/Min.md"
echo "egen ändring" >> "$HOME/DegsellOS/00 START/Hem.md"
"$INIT" >/dev/null
grep -q "min hypotes" "$HOME/DegsellOS/02 HYPOTESER/Min.md"
grep -q "egen ändring" "$HOME/DegsellOS/00 START/Hem.md"

# 3. Ett gammalt tillägg uppdateras efter en OS-uppdatering.
echo "// gammal version" > "$HOME/DegsellOS/$PLUGIN/main.js"
"$INIT" | grep -q "uppdaterade"
cmp -s vault/$PLUGIN/main.js "$HOME/DegsellOS/$PLUGIN/main.js"

# 4. Om forskaren tagit bort tillägget återskapas det inte.
rm -rf "$HOME/DegsellOS/$PLUGIN"
"$INIT" >/dev/null
test ! -e "$HOME/DegsellOS/$PLUGIN"

# 5. Systemets verktygskort uppdateras, forskarens egna anteckningar rörs inte.
echo "gammalt" > "$HOME/DegsellOS/00 START/Verktyg/JASP.md"
"$INIT" | grep -q "uppdaterade 00 START/Verktyg/JASP.md"
cmp -s "vault/00 START/Verktyg/JASP.md" "$HOME/DegsellOS/00 START/Verktyg/JASP.md"
grep -q "min hypotes" "$HOME/DegsellOS/02 HYPOTESER/Min.md"

# 6. Typsnitten för Flatpak-program läggs i användarens fontconfig en gång.
CONF="$HOME/.config/fontconfig/conf.d/52-degsellos-typsnitt.conf"
DEGSELLOS_TYPSNITT="$PWD/system_files/usr/share/degsellos/identitet/52-degsellos-typsnitt.conf" "$INIT" >/dev/null
cmp -s system_files/usr/share/degsellos/identitet/52-degsellos-typsnitt.conf "$CONF"
rm "$CONF"
DEGSELLOS_TYPSNITT="$PWD/system_files/usr/share/degsellos/identitet/52-degsellos-typsnitt.conf" "$INIT" >/dev/null
test ! -e "$CONF"  # borttagen av forskaren: kommer inte tillbaka

# 6. Obsidian får forskningsmappen som valv, men bara om Obsidian saknar egna inställningar.
OBS="$HOME/.var/app/md.obsidian.Obsidian/config/obsidian/obsidian.json"
python3 -c "import json,sys; v=list(json.load(open(sys.argv[1]))['vaults'].values()); assert v[0]['path']==sys.argv[2] and v[0]['open'], v" "$OBS" "$HOME/DegsellOS"
echo '{"vaults":{}}' > "$OBS"
"$INIT" >/dev/null
grep -qx '{"vaults":{}}' "$OBS"  # forskarens egna Obsidian-inställningar rörs inte

# 7. Från ForskarOS: forskningsmapp, inställningar, tillägg och Obsidians valv flyttas.
OLDHOME="$TMP/gammal"
mkdir -p "$OLDHOME/ForskarOS/.obsidian/plugins/forskaros-core" "$OLDHOME/.config/forskaros" \
  "$OLDHOME/.var/app/md.obsidian.Obsidian/config/obsidian"
echo '["forskaros-core"]' > "$OLDHOME/ForskarOS/.obsidian/community-plugins.json"
echo '{"aiNivå":"av"}' > "$OLDHOME/ForskarOS/.obsidian/plugins/forskaros-core/data.json"
echo "min fråga" > "$OLDHOME/ForskarOS/Min fråga.md"
echo '["/p"]' > "$OLDHOME/.config/forskaros/projekt.json"
echo "{\"vaults\":{\"x\":{\"path\":\"$OLDHOME/ForskarOS\",\"open\":true}}}" > "$OLDHOME/.var/app/md.obsidian.Obsidian/config/obsidian/obsidian.json"
HOME="$OLDHOME" XDG_CONFIG_HOME="$OLDHOME/.config" "$INIT" >/dev/null
test ! -e "$OLDHOME/ForskarOS"
grep -q "min fråga" "$OLDHOME/DegsellOS/Min fråga.md"
test -f "$OLDHOME/DegsellOS/.obsidian/plugins/degsellos-core/data.json"
test -f "$OLDHOME/DegsellOS/.obsidian/plugins/degsellos-core/main.js"
grep -q '"degsellos-core"' "$OLDHOME/DegsellOS/.obsidian/community-plugins.json"
grep -q '/p' "$OLDHOME/.config/degsellos/projekt.json"
grep -q "\"path\":\"$OLDHOME/DegsellOS\"" "$OLDHOME/.var/app/md.obsidian.Obsidian/config/obsidian/obsidian.json"

echo "OK: degsellos-init skapar, bevarar och uppdaterar korrekt, typsnitt för Flatpak en gång, valv i Obsidian, flytt från ForskarOS"
