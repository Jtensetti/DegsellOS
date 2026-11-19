import csv
from collections import defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagram import bars, rows

out = Path(sys.argv[1])
codes = defaultdict(dict)
for row in rows(["id", "document", "tag", "content"]):
    tag = row["tag"].strip()
    if tag:
        if not row["id"].strip() or not row["document"].strip():
            raise ValueError("Ett kodat utdrag saknar id eller dokument.")
        codes[tag][(row["document"], row["id"])] = row["content"]

values = []
with (out / "resultat.csv").open("w", newline="", encoding="utf-8") as stream:
    table = csv.writer(stream)
    table.writerow(["kod", "dokument", "utdrags_id", "utdrag"])
    for tag, excerpts in sorted(codes.items()):
        for (document, identifier), text in sorted(excerpts.items()):
            table.writerow([tag, document, identifier, text])
        values.append((tag, len(excerpts), str(len(excerpts))))
bars(out / "figur.svg", "Antal kodade utdrag per kod", values,
     max((n for _, n, _ in values), default=1))
