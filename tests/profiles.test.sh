#!/usr/bin/env bash
# Testar verktygsprofilerna och forskaros-setup utan att installera något.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

DIR=system_files/usr/share/forskaros/profiler
SETUP=system_files/usr/bin/forskaros-setup
export FORSKAROS_PROFILDIR="$PWD/$DIR"
export FORSKAROS_STARTDIR="$PWD/system_files/usr/share/forskaros/startare"
fail() { echo "FEL: $*" >&2; exit 1; }

# 1. Varje profil har namn, beskrivning och giltiga rader.
for p in "$DIR"/*.profil; do
  grep -q '^# namn: ' "$p" || fail "$p saknar namn"
  grep -q '^# beskrivning: ' "$p" || fail "$p saknar beskrivning"
  while read -r kind id desc; do
    [[ -n "$desc" ]] || fail "$p: $id saknar beskrivning"
    case "$kind" in
      flatpak) [[ "$id" =~ ^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+){2,}$ ]] || fail "$p: ogiltigt Flatpak-id $id" ;;
      brew|uv) [[ "$id" =~ ^[a-z0-9@._+-]+$ ]] || fail "$p: ogiltigt paketnamn $id" ;;
      webb) [[ "$id" =~ ^[a-z0-9-]+\|https://[^[:space:]]+$ ]] || fail "$p: ogiltig webbrad $id" ;;
      *) fail "$p: okänd typ $kind" ;;
    esac
  done < <(grep -vE '^\s*(#|$)' "$p")
done

# 2. Proprietärt och moln finns bara i en profil som kräver aktivt val.
grep -l 'md.obsidian.Obsidian\|^webb' "$DIR"/*.profil | while read -r p; do
  grep -q '^# aktivt-val: ja' "$p" || fail "$p innehåller proprietärt/moln utan aktivt val"
done

# 3. Grundprofilen installeras automatiskt: bara Flatpak, bara öppet.
! grep -vE '^\s*(#|$)' "$DIR/01-grund.profil" | grep -qv '^flatpak' || fail "grund får bara innehålla Flatpak"

# 4. Torrkörning: rätt kommandon, inget körs på riktigt.
out=$(bash "$SETUP" --profil skriva,statistik --ja --torrkörning)
grep -q '+ flatpak install --user -y --noninteractive flathub com.zettlr.Zettlr' <<<"$out" || fail "Zettlr installeras inte"
grep -q '+ brew install pandoc' <<<"$out" || fail "pandoc installeras inte"
grep -q '+ uv tool install jupyterlab' <<<"$out" || fail "jupyterlab installeras inte"
grep -q '+ skapa startare forskaros-jupyterlab.desktop' <<<"$out" || fail "startare för JupyterLab saknas"

# 5. 'alla' i interaktivt läge tar inte med det som kräver aktivt val.
out=$(echo alla | bash "$SETUP" --torrkörning)
grep -q 'org.libreoffice.LibreOffice' <<<"$out" || fail "'alla' ska ta med grundprofilen"
! grep -q 'md.obsidian.Obsidian\|perplexity' <<<"$out" || fail "'alla' får inte ta med proprietärt/moln"

# 6. Okänd profil avvisas.
! bash "$SETUP" --profil finnsinte --torrkörning >/dev/null 2>&1 || fail "okänd profil accepterades"

# 7. Molngenvägar skapas bara som genvägar, med tydlig märkning.
out=$(bash "$SETUP" --profil proprietart --torrkörning)
grep -q 'skapa genväg .*forskaros-webb-perplexity.desktop → https://www.perplexity.ai' <<<"$out" || fail "Perplexity-genväg saknas"

# 8. Det rekommenderade urvalet har tio verktyg.
[[ $(grep -cvE '^\s*(#|$)' "$DIR"/02-rekommenderat.profil) -eq 10 ]] || fail "det rekommenderade urvalet ska ha tio verktyg"

# 9. Programmenyn har en mapp per fas och genererade filer är i synk med katalogen.
grep -q "name='3 · Välj'" system_files/etc/dconf/db/local.d/02-forskaros-meny || fail "mappen Välj saknas"
python3 -I scripts/generera.py --kontroll >/dev/null || fail "kör python3 scripts/generera.py"

# 10. Grundtjänsten och dockan pekar på program som finns i profilerna.
grep -q 'ExecStart=/usr/libexec/forskaros-grund' system_files/usr/lib/systemd/system/forskaros-grund.service || fail "tjänsten pekar fel"
for app in $(grep -o "'[^']*\.desktop'" system_files/etc/dconf/db/local.d/01-forskaros | tr -d "'" | sed 's/\.desktop$//'); do
  case "$app" in
    org.gnome.*|forskaros-*) continue ;;
    org.libreoffice.LibreOffice.writer) app=org.libreoffice.LibreOffice ;;
  esac
  grep -q "^flatpak *$app " "$DIR"/*.profil || fail "dockan visar $app som inte finns i någon profil"
done

echo "OK: verktygsprofiler, aktivt val, torrkörning, grundtjänst och docka"
