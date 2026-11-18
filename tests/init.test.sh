#!/usr/bin/env bash
# Testar forskaros-init mot en tillfällig "systemkatalog" och hemkatalog.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Kör skriptet med seed-sökvägen omdirigerad till repots vault.
INIT="$TMP/forskaros-init"
sed "s#^SEED=.*#SEED='$PWD/vault'#" system_files/usr/bin/forskaros-init > "$INIT"
chmod +x "$INIT"
export HOME="$TMP/home"
export XDG_CONFIG_HOME="$HOME/.config"  # CI-miljöer sätter ofta en egen
mkdir -p "$HOME"
PLUGIN=".obsidian/plugins/forskaros-core"

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
test -f "$HOME/ForskarOS/00 START/Hem.md"
test -f "$HOME/ForskarOS/$PLUGIN/main.js"
test "$(readlink "$HOME/Delad")" = /var/mnt/delad

# 2. Forskarens anteckningar och ändringar finns kvar efter ny inloggning.
echo "min hypotes" > "$HOME/ForskarOS/02 HYPOTESER/Min.md"
echo "egen ändring" >> "$HOME/ForskarOS/00 START/Hem.md"
"$INIT" >/dev/null
grep -q "min hypotes" "$HOME/ForskarOS/02 HYPOTESER/Min.md"
grep -q "egen ändring" "$HOME/ForskarOS/00 START/Hem.md"

# 3. Ett gammalt tillägg uppdateras efter en OS-uppdatering.
echo "// gammal version" > "$HOME/ForskarOS/$PLUGIN/main.js"
"$INIT" | grep -q "uppdaterade"
cmp -s vault/$PLUGIN/main.js "$HOME/ForskarOS/$PLUGIN/main.js"

# 4. Om forskaren tagit bort tillägget återskapas det inte.
rm -rf "$HOME/ForskarOS/$PLUGIN"
"$INIT" >/dev/null
test ! -e "$HOME/ForskarOS/$PLUGIN"

# 5. Systemets verktygskort uppdateras, forskarens egna anteckningar rörs inte.
echo "gammalt" > "$HOME/ForskarOS/00 START/Verktyg/JASP.md"
"$INIT" | grep -q "uppdaterade 00 START/Verktyg/JASP.md"
cmp -s "vault/00 START/Verktyg/JASP.md" "$HOME/ForskarOS/00 START/Verktyg/JASP.md"
grep -q "min hypotes" "$HOME/ForskarOS/02 HYPOTESER/Min.md"

# 6. Typsnitten för Flatpak-program läggs i användarens fontconfig en gång.
CONF="$HOME/.config/fontconfig/conf.d/52-forskaros-typsnitt.conf"
FORSKAROS_TYPSNITT="$PWD/system_files/usr/share/forskaros/identitet/52-forskaros-typsnitt.conf" "$INIT" >/dev/null
cmp -s system_files/usr/share/forskaros/identitet/52-forskaros-typsnitt.conf "$CONF"
rm "$CONF"
FORSKAROS_TYPSNITT="$PWD/system_files/usr/share/forskaros/identitet/52-forskaros-typsnitt.conf" "$INIT" >/dev/null
test ! -e "$CONF"  # borttagen av forskaren: kommer inte tillbaka

echo "OK: forskaros-init skapar, bevarar och uppdaterar korrekt, typsnitt för Flatpak en gång"
