#!/usr/bin/env bash
# Lokala kontroller som inte kräver att avbildningen byggs.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

node --check vault/.obsidian/plugins/forskaros-core/main.js
node tests/engine.test.js
node tests/plugin.test.js

for f in build_files/build.sh scripts/*.sh system_files/usr/bin/*; do
  bash -n "$f"
done
echo "OK: skalskriptens syntax"

bash tests/init.test.sh

python3 - <<'PY'
import json
from pathlib import Path
root = Path('vault')
manifest = json.loads((root / '.obsidian/plugins/forskaros-core/manifest.json').read_text())
assert manifest['id'] == 'forskaros-core'
assert len(list(root.rglob('*.md'))) >= 4
assert Path('Containerfile').is_file()
for line in Path('system_files/usr/share/forskaros/flatpaks.list').read_text().splitlines():
    line = line.strip()
    assert not line or line.startswith('#') or line.count('.') >= 2, line
print('OK: manifest, vault, Containerfile, Flatpak-lista')
PY
