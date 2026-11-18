"""Prova de två projektmallarna med riktiga Python- och Pandocprocesser."""
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

command = Path(__file__).resolve().parents[1] / "system_files/usr/bin/forskaros-projekt"


def call(*args, ok=True):
    result = subprocess.run([command, *args], text=True, capture_output=True)
    assert (result.returncode == 0) == ok, (args, result.stdout, result.stderr)
    return result.stdout.strip() if ok else result.stderr


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    for method in ("kvantitativ", "kvalitativ"):
        project = root / ("Studie med mellanslag " + method)
        call("skapa", method, project)
        call("skapa", method, project, ok=False)
        first = Path(call("kör", project))
        table = list(csv.reader((first / "resultat/resultat.csv").open(encoding="utf-8")))
        if method == "kvantitativ":
            assert ["Saklig respons", "3", "2", "66.7"] in table
        else:
            assert len(table) == 5 and any(r[:3] == ["belägg", "Exempelintervju A", "1"] for r in table)
        html = (first / "resultat/rapport.html").read_text()
        assert ('data:image/svg+xml' in html or '<svg' in html) and 'id="ref-ovning"' in html
        assert "Övningsmaterial" in html or "Konstruerat övningsmaterial" in html
        copy = root / ("Kollegans körning " + method)
        shutil.copytree(first, copy)
        subprocess.run([sys.executable, "-I", str(copy / "upprepa.py")], cwd=root, check=True)
        manifest = json.loads((copy / "korning.json").read_text())
        assert manifest["miljö"]["pandoc"] and "analys.py" in manifest["underlag"]
        (project / "underlag/data.csv").write_text("fel kolumner\n")
        call("kör", project, ok=False)
        assert list((project / "korningar").iterdir()) == [first]
        call("upprepa", first)
        (copy / "underlag/data.csv").write_text("ändrat\n")
        assert "data.csv" in call("upprepa", copy, ok=False)
        shutil.copyfile(first / "underlag/data.csv", copy / "underlag/data.csv")
        (copy / "resultat/figur.svg").write_text("ändrad\n")
        assert "figur.svg" in call("upprepa", copy, ok=False)
    data = project / "underlag/data.csv"
    shutil.copyfile(first / "underlag/data.csv", data)
    with ThreadPoolExecutor(max_workers=2) as pool:
        paths = list(pool.map(lambda _: call("kör", project), range(2)))
    assert len(set(paths)) == 2
    (project / "underlag/länk").symlink_to(data)
    assert "vanliga filer" in call("kör", project, ok=False)
print("OK: projektmallar, referenser, inbäddad figur, flytt, omkörning, avvikelser och samtidiga körningar")
