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
cp /ctx/VERSION /usr/share/forskaros/RELEASE

# Virtuell maskin: delat urklipp, automatisk skärmstorlek och ren avstängning
# i UTM/QEMU. Tjänsterna startar bara när motsvarande virtuella enhet finns.
dnf -y install spice-vdagent qemu-guest-agent gtk3 python3-gobject webkit2gtk4.1
dnf clean all

# Projektens rapporter ska gå att bygga redan vid första start utan nät.
if ! command -v pandoc >/dev/null; then
  case "$(uname -m)" in
    x86_64) arch=amd64; sha=c224fab89f827d3623380ecb7c1078c163c769c849a14ac27e8d3bfbb914c9b4 ;;
    aarch64) arch=arm64; sha=166a5a37387eb10bd4c4f242a8109beef755ac1e8d4eb039c6b5ebd1d918d8d7 ;;
    *) exit 1 ;;
  esac
  curl -fLsS --retry 3 "https://github.com/jgm/pandoc/releases/download/3.8.3/pandoc-3.8.3-linux-${arch}.tar.gz" -o /tmp/pandoc.tar.gz
  echo "$sha  /tmp/pandoc.tar.gz" | sha256sum -c -
  tar xzf /tmp/pandoc.tar.gz -C /usr/bin --strip-components=2 pandoc-3.8.3/bin/pandoc
fi
pandoc --version
/usr/bin/python3 -c 'import gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk'

# Skyddade forskningsprojekt kör sin analys i en bubblewrap-sandlåda.
# Utan bwrap vägrar ForskarOS köra dem, så den måste finnas i avbildningen.
command -v bwrap >/dev/null || dnf -y install bubblewrap
bwrap --version

# Grundverktygen installeras vid första start med nätverk.
systemctl enable forskaros-grund.service forskaros-forskare.service forskaros-delad-mapp.service

# Identitet: logotypen som programikon.
install -Dm644 /usr/share/forskaros/identitet/forskaros-logotyp.svg /usr/share/icons/hicolor/scalable/apps/forskaros.svg

# Arbetsytans standardinställningar (dockan m.m.).
if command -v dconf >/dev/null 2>&1; then dconf update; fi
