#!/usr/bin/env bash
# Testar degsellos-labb med en ersättare för podman.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
fail() { echo "FEL: $*" >&2; exit 1; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cat > "$TMP/podman" <<STUB
#!/bin/sh
echo "podman \$*" >> "$TMP/anrop"
case "\$1 \$2" in
  "image exists") exit 0 ;;
  "image inspect") echo "sha256:abc123" ;;
esac
STUB
chmod +x "$TMP/podman"
export DEGSELLOS_PODMAN="$TMP/podman" HOME="$TMP/home"
mkdir -p "$HOME/DegsellOS" "$TMP/studie"
LABB="$PWD/system_files/usr/bin/degsellos-labb"

out=$(cd "$TMP/studie" && bash "$LABB" version)
grep -q 'Analysmiljö: ghcr.io/jtensetti/degsellos-labb@sha256:abc123' <<<"$out" || fail "version ger inte digest: $out"

(cd "$TMP/studie" && bash "$LABB" Rscript analys.R)
grep -q "run --rm -it --userns=keep-id -v $TMP/studie:/arbete:Z -w /arbete ghcr.io/jtensetti/degsellos-labb:latest Rscript analys.R" "$TMP/anrop" || fail "kommandot körs inte i aktuell mapp"

(cd "$HOME" && bash "$LABB" rstudio)
grep -q "127.0.0.1:8787:8787 -e DISABLE_AUTH=true -v $HOME/DegsellOS:/home/rstudio/arbete:Z" "$TMP/anrop" || fail "RStudio ska bara lyssna lokalt och arbeta i vaulten"

grep -q '127.0.0.1:8888' <(cd "$TMP/studie" && bash "$LABB" jupyter; cat "$TMP/anrop") || fail "Jupyter ska bara lyssna lokalt"
grep -q '^## Analysmiljö' <(node -e '
  const M=require("node:module"),o=M._load;M._load=function(r,...a){return r==="obsidian"?{Plugin:class{},ItemView:class{},Notice:class{},Modal:class{}}:o.call(this,r,...a)};
  const {engine:e}=require("./vault/.obsidian/plugins/degsellos-core/main.js");
  console.log(e.TYPES.experiment.render({date:"2026-11-17"}))') || fail "experimentmallen saknar Analysmiljö"
echo "OK: labbet: version, kommandon i aktuell mapp, RStudio och Jupyter bara lokalt"
