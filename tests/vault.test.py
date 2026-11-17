"""Kontrollerar att varje intern länk ([[...]]) i vaulten pekar på en sida som finns."""
import re
from pathlib import Path

vault = Path(__file__).resolve().parent.parent / "vault"
pages = {p.relative_to(vault).with_suffix("").as_posix() for p in vault.rglob("*.md")}
names = {p.split("/")[-1] for p in pages}
bad = []
for f in vault.rglob("*.md"):
    if ".obsidian" in f.parts:
        continue
    for m in re.finditer(r"\[\[([^\]|#]+)", f.read_text(encoding="utf-8")):
        target = m.group(1).strip().removesuffix(".md")
        if target not in pages and target not in names:
            bad.append(f"{f.relative_to(vault)} → {target}")
assert not bad, "Trasiga länkar:\n  " + "\n  ".join(bad)
handbok = sorted((vault / "00 START/Forskarhandboken").glob("*.md"))
assert len(handbok) == 13, len(handbok)
for kap in handbok[1:]:
    assert "## Övning utan AI" in kap.read_text(encoding="utf-8"), f"{kap.name} saknar övning utan AI"
print(f"OK: vaulten: {len(pages)} sidor, inga trasiga länkar, handboken har övningar utan AI")
