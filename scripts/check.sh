#!/usr/bin/env bash
# Lokala kontroller som inte kräver att avbildningen byggs.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

node --check vault/.obsidian/plugins/forskaros-core/main.js
node tests/engine.test.js
node tests/plugin.test.js
node tests/begrepp.test.js

for f in build_files/build.sh scripts/*.sh tests/*.sh system_files/usr/bin/* system_files/usr/libexec/*; do
  bash -n "$f"
done
echo "OK: skalskriptens syntax"

bash tests/init.test.sh
bash tests/profiles.test.sh
python3 -I tests/utm.test.py
bash tests/identitet.test.sh
bash tests/labb.test.sh
python3 -I tests/projekt.test.py
python3 -I tests/belagg.test.py
python3 -I tests/vault.test.py

python3 - <<'PY'
import json
from pathlib import Path
root = Path('vault')
manifest = json.loads((root / '.obsidian/plugins/forskaros-core/manifest.json').read_text())
assert manifest['id'] == 'forskaros-core'
assert len(list(root.rglob('*.md'))) >= 4
assert Path('Containerfile').is_file()
assert any(Path('system_files/usr/share/forskaros/profiler').glob('*.profil'))
print('OK: manifest, vault, Containerfile, verktygsprofiler')
PY
