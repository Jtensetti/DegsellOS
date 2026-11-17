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
mkdir -p "$HOME"
PLUGIN=".obsidian/plugins/forskaros-core"

# 1. Första inloggning skapar vaulten.
"$INIT" >/dev/null
test -f "$HOME/ForskarOS/00 START/Hem.md"
test -f "$HOME/ForskarOS/$PLUGIN/main.js"

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

echo "OK: forskaros-init skapar, bevarar och uppdaterar korrekt"
