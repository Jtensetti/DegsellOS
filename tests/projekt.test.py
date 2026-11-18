"""Prova projektmallarna med riktiga Python- och Pandocprocesser."""
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
        path = project / "projekt.json"
        manifest = json.loads(path.read_text())
        manifest["licens"] = "https://creativecommons.org/licenses/by/4.0/"
        path.write_text(json.dumps(manifest))
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
        graph = json.loads((copy / "ro-crate-metadata.json").read_text())["@graph"]
        crate = next(node for node in graph if node["@id"] == "./")
        assert crate["license"]["@id"] == "https://creativecommons.org/licenses/by/4.0/"
        assert project.name in crate["name"]
        shutil.copyfile(first / "underlag/data.csv", copy / "underlag/data.csv")
        (copy / "resultat/figur.svg").write_text("ändrad\n")
        assert "figur.svg" in call("upprepa", copy, ok=False)
    data = project / "underlag/data.csv"
    shutil.copyfile(first / "underlag/data.csv", data)
    with ThreadPoolExecutor(max_workers=2) as pool:
        paths = list(pool.map(lambda _: call("kör", project), range(2)))
    assert len(set(paths)) == 2
    run = Path(paths[0])
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: call("upprepa", run), range(2)))
    history = json.loads((run / "verifieringar.json").read_text())
    assert [entry["utfall"] for entry in history] == ["samma", "samma"]
    graph = json.loads((run / "ro-crate-metadata.json").read_text())["@graph"]
    assert len([node for node in graph if node["@id"].startswith("#upprepning-")]) == 2
    (project / "underlag/länk").symlink_to(data)
    assert "vanliga filer" in call("kör", project, ok=False)

    archive = root / "Två källor"
    call("skapa", "källtolkning", archive)
    for key in ("initiativ", "forsokstid"):
        detail = call("belägg", archive, key)
        stamp = detail.split("Avtryck: ")[-1]
        call("granska", archive, key, "--avtryck", stamp)
    original = Path(call("kör", archive))
    with (original / "resultat/resultat.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    linked = [(r["roll"], r["källa"], r["sida"]) for r in rows if r["påstående"] == "initiativ"]
    assert linked == [("stöd", "protokoll", "s. 3"), ("motbelägg", "minnen", "s. 12")]
    html = (original / "resultat/rapport.html").read_text(encoding="utf-8")
    assert 'id="ref-protokoll"' in html and 'id="ref-minnen"' in html and 'id="belagg-initiativ"' in html
    # En rättad transkription gör tidigare citerad lydelse otillgänglig.
    memoir = archive / "underlag/kallor/minnen.md"
    memoir.write_text(memoir.read_text().replace("redan bestämt", "ännu inte bestämt"))
    status = call("belägg", archive)
    assert "initiativ · Underlag saknas" in status and "forsokstid · Granskad" in status
    call("upprepa", original)
print("OK: projektmallar, referenser, inbäddad figur, flytt, omkörning, avvikelser och samtidiga körningar")
