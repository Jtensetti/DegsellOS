#!/usr/bin/env bash
# Körs inne i avbildningen under bygget. Håll den liten: allt som går att
# installera som Flatpak eller via Homebrew görs i stället av forskaros-setup,
# så att basavbildningens uppdateringar inte krockar med våra ändringar.
set -euxo pipefail

# Systemfiler (kommandon, autostart, programmeny, Brewfile, Flatpak-lista).
cp -a /ctx/system_files/. /
chmod 0755 /usr/bin/forskaros-init /usr/bin/forskaros-setup

# Seed-vaulten. Kopieras till användarens hemkatalog vid första inloggning.
install -d /usr/share/forskaros
rm -rf /usr/share/forskaros/vault
cp -a /ctx/vault /usr/share/forskaros/vault
find /usr/share/forskaros/vault -name .gitkeep -delete

# Versionsmärkning så att forskaros-init kan avgöra om tillägget ska uppdateras.
sed -n 's/.*"version": *"\([^"]*\)".*/\1/p' \
  /usr/share/forskaros/vault/.obsidian/plugins/forskaros-core/manifest.json \
  > /usr/share/forskaros/VERSION
test -s /usr/share/forskaros/VERSION
