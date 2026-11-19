#!/usr/bin/env bash
# Testar verktygsprofilerna och degsellos-setup utan att installera något.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

DIR=system_files/usr/share/degsellos/profiler
SETUP=system_files/usr/bin/degsellos-setup
export DEGSELLOS_PROFILDIR="$PWD/$DIR"
export DEGSELLOS_STARTDIR="$PWD/system_files/usr/share/degsellos/startare"
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
grep -l 'md.obsidian.Obsidian' "$DIR"/*.profil | while read -r p; do
  grep -q '^# aktivt-val: licens' "$p" || fail "$p: Obsidian kräver licensval"
  ! grep -q '^webb' "$p" || fail "$p: Obsidian ska inte ligga i samma profil som molntjänster"
done
grep -l '^webb' "$DIR"/*.profil | while read -r p; do
  grep -q '^# aktivt-val: moln' "$p" || fail "$p: molntjänster kräver aktivt val"
done

# 3. Grundprofilen installeras automatiskt: bara Flatpak, bara öppet.
! grep -vE '^\s*(#|$)' "$DIR/01-grund.profil" | grep -qv '^flatpak' || fail "grund får bara innehålla Flatpak"

# 4. Torrkörning: rätt kommandon, inget körs på riktigt.
out=$(bash "$SETUP" --profil skriva,statistik --ja --torrkörning)
grep -q '+ flatpak install --user -y --noninteractive flathub com.zettlr.Zettlr' <<<"$out" || fail "Zettlr installeras inte"
if command -v pandoc >/dev/null; then
  grep -q 'Pandoc finns redan' <<<"$out" || fail "systemets Pandoc ska återanvändas"
else
  grep -q '+ brew install pandoc' <<<"$out" || fail "pandoc installeras inte"
fi
grep -q '+ uv tool install jupyterlab' <<<"$out" || fail "jupyterlab installeras inte"
grep -q '+ skapa startare degsellos-jupyterlab.desktop' <<<"$out" || fail "startare för JupyterLab saknas"
out=$(bash "$SETUP" --profil kvalitativ --ja --torrkörning)
grep -Fq '+ uv tool install --with setuptools<81 taguette' <<<"$out" || fail "Taguettes körmiljö saknas"

# 5. 'alla' i interaktivt läge tar inte med det som kräver aktivt val.
out=$(echo alla | bash "$SETUP" --torrkörning)
grep -q 'org.libreoffice.LibreOffice' <<<"$out" || fail "'alla' ska ta med grundprofilen"
! grep -q 'md.obsidian.Obsidian\|perplexity' <<<"$out" || fail "'alla' får inte ta med profiler som kräver aktivt val"

# 6. Okänd profil avvisas.
! bash "$SETUP" --profil finnsinte --torrkörning >/dev/null 2>&1 || fail "okänd profil accepterades"

# 7. Molngenvägar skapas bara som genvägar.
out=$(bash "$SETUP" --profil obsidian --torrkörning)
grep -q "flathub md.obsidian.Obsidian" <<<"$out" || fail "Obsidian-profilen installerar inte Obsidian"
out=$(bash "$SETUP" --profil moln --torrkörning)
grep -q 'skapa genväg .*degsellos-webb-perplexity.desktop → https://www.perplexity.ai' <<<"$out" || fail "Perplexity-genväg saknas"

# 7b. Utan terminal hoppas aktiva val över; med --godkänt (appens dialog) görs de.
home=$(mktemp -d)
out=$(HOME="$home" bash "$SETUP" --profil moln --ja </dev/null)
grep -q 'Hoppar över' <<<"$out" || fail "moln utan bekräftelse ska hoppas över"
[[ ! -e "$home/.local/share/applications/degsellos-webb-perplexity.desktop" ]] || fail "molngenväg skapades utan val"
HOME="$home" bash "$SETUP" --profil moln --ja --godkänt </dev/null >/dev/null
grep -q 'Exec=xdg-open https://www.perplexity.ai' "$home/.local/share/applications/degsellos-webb-perplexity.desktop" \
  || fail "--godkänt skapar inte molngenvägen"
rm -rf "$home"

# 8. Det rekommenderade urvalet har tio verktyg.
[[ $(grep -cvE '^\s*(#|$)' "$DIR"/*-rekommenderat.profil) -eq 10 ]] || fail "det rekommenderade urvalet ska ha tio verktyg"

# 9. Programmenyn har en mapp per fas och genererade filer är i synk med katalogen.
grep -q "name='3 · Välj'" system_files/etc/dconf/db/local.d/02-degsellos-meny || fail "mappen Välj saknas"
python3 -I scripts/generera.py --kontroll >/dev/null || fail "kör python3 scripts/generera.py"

# 10. Grundtjänsten och dockan pekar på program som finns i profilerna eller i DegsellOS.
grep -q 'ExecStart=/usr/libexec/degsellos-grund' system_files/usr/lib/systemd/system/degsellos-grund.service || fail "tjänsten pekar fel"
for app in $(grep -o "'[^']*\.desktop'" system_files/etc/dconf/db/local.d/01-degsellos | tr -d "'" | sed 's/\.desktop$//'); do
  case "$app" in
    org.gnome.*|degsellos-*|io.github.jtensetti.DegsellOS) continue ;;
    org.libreoffice.LibreOffice.writer) app=org.libreoffice.LibreOffice ;;
  esac
  grep -q "^flatpak *$app " "$DIR"/*.profil || fail "dockan visar $app som inte finns i någon profil"
done

for own in $(grep -o "'\(degsellos-[^']*\|io\.github\.jtensetti\.DegsellOS\)\.desktop'" system_files/etc/dconf/db/local.d/0*-degsellos* | cut -d: -f2 | tr -d "'" | sort -u); do
  # Genvägar och startare som degsellos-setup skapar vid installation.
  case "$own" in degsellos-webb-*|degsellos-jupyterlab*|degsellos-taguette*) continue ;; esac
  [[ -f "system_files/usr/share/applications/$own" ]] || fail "dockan eller menyn pekar på $own som inte finns"
done

echo "OK: verktygsprofiler, aktivt val, torrkörning, grundtjänst och docka"
