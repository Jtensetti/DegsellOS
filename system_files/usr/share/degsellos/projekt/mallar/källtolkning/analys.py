"""Samla de källpassager som forskaren har kopplat till respektive tolkning."""
import csv
import json
from pathlib import Path
import sys

claims = json.loads(Path("belagg.json").read_text(encoding="utf-8"))["påståenden"]
with (Path(sys.argv[1]) / "resultat.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["påstående", "roll", "källa", "sida", "citat"])
    for key, claim in claims.items():
        for source in claim["underlag"]:
            if "källa" in source:
                writer.writerow([key, source["roll"], source["källa"], source.get("sida", ""), source["citat"]])
