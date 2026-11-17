#!/usr/bin/env bash
# Körs inne i avbildningen under bygget. Håll den liten: allt som går att
# installera som Flatpak eller via Homebrew görs i stället av forskaros-setup,
# så att basavbildningens uppdateringar inte krockar med våra ändringar.
set -euxo pipefail

# Systemfiler (kommandon, tjänster, autostart, programmeny, verktygsprofiler).
cp -a /ctx/system_files/. /
chmod 0755 /usr/bin/forskaros-* /usr/libexec/forskaros-*

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

# Virtuell maskin: delat urklipp, automatisk skärmstorlek och ren avstängning
# i UTM/QEMU. Tjänsterna startar bara när motsvarande virtuella enhet finns.
dnf -y install spice-vdagent qemu-guest-agent
dnf clean all

# Grundverktygen installeras vid första start med nätverk.
systemctl enable forskaros-grund.service forskaros-forskare.service forskaros-delad-mapp.service

# Identitet: logotypen som programikon.
install -Dm644 /usr/share/forskaros/identitet/forskaros-logotyp.svg /usr/share/icons/hicolor/scalable/apps/forskaros.svg

# Arbetsytans standardinställningar (dockan m.m.).
if command -v dconf >/dev/null 2>&1; then dconf update; fi
