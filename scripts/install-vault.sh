#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$HOME/ForskarOS}"
if [[ -e "$DEST" ]]; then
  echo "Målet finns redan: $DEST. Inget skrivs över." >&2
  exit 1
fi
mkdir -p "$(dirname "$DEST")"
cp -R "$ROOT/vault" "$DEST"
chmod -R u+rwX "$DEST"
printf 'ForskarOS-vault skapad: %s\n' "$DEST"
printf 'Öppna Obsidian → Open folder as vault → välj denna mapp.\n'
printf 'Inställningar → Community plugins → aktivera ForskarOS Core.\n'
