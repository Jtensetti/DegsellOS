import csv
from collections import defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagram import bars, rows

out = Path(sys.argv[1])
groups = defaultdict(list)
for row in rows(["villkor", "bytte_hypotes"]):
    group = row["villkor"].strip()
    answer = row["bytte_hypotes"].strip()
    if not group or answer not in ("0", "1"):
        raise ValueError("Varje observation behöver ett villkor och bytte_hypotes 0 eller 1.")
    groups[group].append(int(answer))

values = []
with (out / "resultat.csv").open("w", newline="", encoding="utf-8") as stream:
    table = csv.writer(stream)
    table.writerow(["villkor", "antal", "byten", "andel_procent"])
    for group, answers in sorted(groups.items()):
        changes = sum(answers)
        rate = 100 * changes / len(answers)
        table.writerow([group, len(answers), changes, f"{rate:.1f}"])
        values.append((group, rate, f"{changes}/{len(answers)} ({rate:.0f} %)"))
bars(out / "figur.svg", "Andel elever som bytte hypotes", values, 100)
