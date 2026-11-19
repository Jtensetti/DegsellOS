#!/usr/bin/env bash
# Lokala kontroller som inte kräver att avbildningen byggs.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

node --check vault/.obsidian/plugins/degsellos-core/main.js
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
python3 -I tests/zotero.test.py
python3 -I tests/doman.test.py
python3 -I tests/oversikt.test.py
python3 -I tests/forskningsmapp.test.py
bash tests/app.test.sh
python3 -I tests/vault.test.py

python3 - <<'PY'
import json
from pathlib import Path
root = Path('vault')
manifest = json.loads((root / '.obsidian/plugins/degsellos-core/manifest.json').read_text())
assert manifest['id'] == 'degsellos-core'
assert len(list(root.rglob('*.md'))) >= 4
assert Path('Containerfile').is_file()
assert any(Path('system_files/usr/share/degsellos/profiler').glob('*.profil'))
import re
workflows = ''.join(f.read_text() for f in Path('.github/workflows').glob('*.yml'))
assert 'GITHUB_REPOSITORY,,' not in workflows, 'avbildningens namn får inte bero på repots namn'
names = set(re.findall(r'(?<!LEGACY_)IMAGE_NAME: (ghcr\.io/\S+)', workflows))
assert names == {'ghcr.io/jtensetti/degsellos', 'ghcr.io/jtensetti/degsellos-labb'}, names
legacy = set(re.findall(r'LEGACY_IMAGE_NAME: (ghcr\.io/\S+)', workflows))
assert legacy == {'ghcr.io/jtensetti/researchos', 'ghcr.io/jtensetti/researchos-labb'}, 'installerade datorer måste få uppdateringar'
assert 'ghcr.io/jtensetti/degsellos-labb:latest' in Path('system_files/usr/share/degsellos/projekt/projekt.py').read_text()
assert 'ghcr.io/jtensetti/degsellos-labb:latest' in Path('system_files/usr/bin/degsellos-labb').read_text()
assert 'bootc switch ghcr.io/jtensetti/degsellos:' in Path('docs/INSTALLATION.md').read_text()
print('OK: manifest, vault, Containerfile, verktygsprofiler, avbildningarnas namn')
PY
