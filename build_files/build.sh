#!/usr/bin/env bash
# Installerar systemkomponenterna i avbildningen. Användarverktyg installeras
# separat med degsellos-setup via Flatpak, Homebrew eller uv.
set -euxo pipefail

# Systemfiler (kommandon, tjänster, autostart, programmeny, verktygsprofiler).
cp -a /ctx/system_files/. /
chmod 0755 /usr/bin/degsellos-* /usr/libexec/degsellos-*

# Seed-vaulten. Kopieras till användarens hemkatalog vid första inloggning.
install -d /usr/share/degsellos
rm -rf /usr/share/degsellos/vault
cp -a /ctx/vault /usr/share/degsellos/vault
find /usr/share/degsellos/vault -name .gitkeep -delete

# Versionsmärkning så att degsellos-init kan avgöra om tillägget ska uppdateras.
sed -n 's/.*"version": *"\([^"]*\)".*/\1/p' \
  /usr/share/degsellos/vault/.obsidian/plugins/degsellos-core/manifest.json \
  > /usr/share/degsellos/VERSION
test -s /usr/share/degsellos/VERSION
cp /ctx/VERSION /usr/share/degsellos/RELEASE

# GNOME och ISO-byggaren läser produktnamnet från os-release.
# Behåll basens ID, VERSION_ID och PLATFORM_ID för drivrutiner och pakethantering.
release=$(cat /ctx/VERSION)
[[ "$release" =~ ^[0-9]{4}\.[1-4](-[a-z0-9]+)?$ ]]
for metadata in /usr/lib/os-release /etc/os-release; do
  sed --follow-symlinks -i \
    -e 's/^NAME=.*/NAME="DegsellOS"/' \
    -e "s/^PRETTY_NAME=.*/PRETTY_NAME=\"DegsellOS $release\"/" \
    -e 's/^LOGO=.*/LOGO=degsellos/' "$metadata"
  grep -Fxq 'NAME="DegsellOS"' "$metadata"
  grep -Fxq "PRETTY_NAME=\"DegsellOS $release\"" "$metadata"
done

# Virtuell maskin: delat urklipp, automatisk skärmstorlek och ren avstängning
# i UTM/QEMU. Tjänsterna startar bara när motsvarande virtuella enhet finns.
# Appen DegsellOS använder GTK 4 och libadwaita. Rapportvyn utan webbläsare använder WebKitGTK.
dnf -y install spice-vdagent qemu-guest-agent gtk3 gtk4 libadwaita python3-gobject webkit2gtk4.1
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
/usr/bin/python3 -c 'import gi; gi.require_version("Gtk", "3.0"); gi.require_version("WebKit2", "4.1")'
/usr/bin/python3 -c 'import gi; gi.require_version("Gtk", "4.0"); gi.require_version("Adw", "1"); from gi.repository import Adw, Gtk'

# Skyddade forskningsprojekt kör sin analys i en bubblewrap-sandlåda.
# Utan bwrap vägrar DegsellOS köra dem, så den måste finnas i avbildningen.
command -v bwrap >/dev/null || dnf -y install bubblewrap
bwrap --version

# Grundverktygen installeras vid första start med nätverk.
systemctl enable degsellos-grund.service degsellos-forskare.service degsellos-delad-mapp.service

# Identitet: logotypen som programikon.
install -Dm644 /usr/share/degsellos/identitet/degsellos-logotyp.svg /usr/share/icons/hicolor/scalable/apps/degsellos.svg

# Typsnitt för gränssnitt, läsning och kod (katalog/design.json, docs/DESIGN.md).
# Bluefin har dem oftast redan; installera bara det som saknas.
for pkg in adwaita-sans-fonts google-noto-serif-vf-fonts jetbrains-mono-fonts; do
  rpm -q "$pkg" >/dev/null || dnf -y install "$pkg"
done
ln -sf /usr/share/degsellos/identitet/52-degsellos-typsnitt.conf /etc/fonts/conf.d/52-degsellos-typsnitt.conf
fc-cache -f >/dev/null
for pair in 'sans\-serif=Adwaita Sans' 'serif=Noto Serif' 'monospace=JetBrains Mono'; do
  got=$(fc-match -f '%{family[0]}' "${pair%%=*}")
  [[ "$got" == "${pair#*=}" ]] || { echo "Typsnittet för ${pair%%=*} blev $got, inte ${pair#*=}" >&2; exit 1; }
done

# Arbetsytans standardinställningar (dockan m.m.).
if command -v dconf >/dev/null 2>&1; then dconf update; fi

# Länkar degsellos:// från forskningsmappen i Obsidian öppnar appen.
update-desktop-database /usr/share/applications
grep -q 'x-scheme-handler/degsellos=io.github.jtensetti.DegsellOS.desktop' /usr/share/applications/mimeinfo.cache
