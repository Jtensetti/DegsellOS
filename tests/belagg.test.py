"""Från ett länkat påstående till rättat underlag, mänsklig omprövning och fryst rapport."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(root / "system_files/usr/share/degsellos/projekt"))
from belagg import add_source, inspect, review_changes, source_choices
cmd = root / "system_files/usr/bin/degsellos-projekt"


def call(*args, fail=False):
    result = subprocess.run([cmd, *args], capture_output=True, text=True)
    assert (result.returncode != 0) == fail, (args, result.stdout, result.stderr)
    return result.stderr if fail else result.stdout.strip()


def accept(project, key):
    fingerprint = call("belägg", project, key).split("Avtryck: ")[-1]
    call("granska", project, key, "--avtryck", fingerprint)
    return fingerprint


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if "id" in attr:
            self.targets.append(attr["id"])
        if tag == "a":
            self.links.append(attr.get("href"))


with tempfile.TemporaryDirectory() as temp:
    for method, affected, other in [("kvantitativ", "saklig", "neutral"),
                                    ("kvalitativ", "omprovning", "auktoritet")]:
        project = Path(temp) / method
        call("skapa", method, project)
        folder = project / "underlag"
        assert all(c["status"] == "Ej granskad" for c in inspect(folder).values())
        accept(project, "material")  # Påståendet som bygger på en källpassage, inte på data.csv.
        with ThreadPoolExecutor(max_workers=2) as pool:
            otherwise, fingerprint = pool.map(lambda key: accept(project, key), [other, affected])
        assert all(c["status"] == "Granskad" for c in inspect(folder).values())
        first = Path(call("kör", project))
        report = (first / "resultat/rapport.html").read_text()
        links = Links()
        links.feed(report)
        assert f"#belagg-{affected}" in links.links and links.targets.count(f"belagg-{affected}") == 1
        assert "../underlag/data.csv" in links.links and "Granskad" in report
        data = folder / "data.csv"
        rows = data.read_text().splitlines()
        data.write_text("\n".join([rows[0], *reversed(rows[1:])]) + "\n")
        assert all(c["status"] == "Granskad" for c in inspect(folder).values())
        if method == "kvantitativ":
            before, after = "Saklig respons,1", "Saklig respons,0"
        else:
            assert 'Motbelägg' in report and "handledaren" in report
            before, after = "andra mätningen gav samma resultat.", "andra mätningen gav ett annat resultat."
        data.write_text(data.read_text().replace(before, after, 1) if method == "kvantitativ"
                        else data.read_text().replace(before, after))
        current = inspect(folder)
        assert current[affected]["status"] == "Ompröva" and current[other]["status"] == "Granskad"
        assert current[affected]["ändrat"][0].startswith("Stöd · data.csv")
        views = review_changes(folder, current[affected])
        old, new = views[current[affected]["ändrat"][0]]
        assert old != new
        if method == "kvalitativ":
            assert before in old and after not in old
            assert after in new and before not in new
        assert not (first / "underlag/granskningsunderlag.json").exists()
        # Äldre beslut utan visningstext går fortfarande att ompröva.
        sidecar = project / "granskningsunderlag.json"
        saved = sidecar.read_bytes()
        sidecar.unlink()
        legacy_old, legacy_new = review_changes(folder, current[affected])[current[affected]["ändrat"][0]]
        assert "saknar sparad jämförelsetext" in legacy_old and legacy_new == new
        sidecar.write_bytes(saved)
        assert "ändrats sedan visningen" in call("granska", project, affected, "--avtryck", fingerprint, fail=True)
        second = Path(call("kör", project))
        assert "Ompröva" in (second / "resultat/rapport.html").read_text()
        assert (first / "resultat/rapport.html").read_text() == report
        call("upprepa", first)
        call("upprepa", second)
        accept(project, affected)
        assert all(c["status"] == "Granskad" for c in inspect(folder).values())
        if method == "kvalitativ":
            data.write_text(data.read_text().replace("Jag antog att handledaren redan kände till svaret.", "Rättat citat."))
            changed = inspect(folder)
            assert all(c["status"] == "Ompröva" for k, c in changed.items() if k != "material")
            assert changed["material"]["status"] == "Granskad", "en ändrad intervju berör inte källpassagen"
            assert changed[affected]["ändrat"][0].startswith("Motbelägg")
            # En rättad passage jämförs mot precis det citat som godkändes.
            config = folder / "belagg.json"
            settings = json.loads(config.read_text())
            spec = settings["påståenden"]["material"]["underlag"][0]
            old_quote = spec["citat"]
            spec["citat"] = "De beskriver inga verkliga elever."
            config.write_text(json.dumps(settings, ensure_ascii=False))
            c = inspect(folder)["material"]
            previous, current_text = review_changes(folder, c)[c["ändrat"][0]]
            assert old_quote in previous and spec["citat"] in current_text
            data.write_text("\n".join(line for line in data.read_text().splitlines() if ",auktoritet," not in line) + "\n")
            assert inspect(folder)[affected]["status"] == "Underlag saknas"
            now = inspect(folder)[affected]["avtryck"]
            assert "saknade underlaget" in call("granska", project, affected, "--avtryck", now, fail=True)
        else:
            # Byte av analystext berör båda kvantitativa påståendena.
            analysis = folder / "analys.py"
            analysis.write_text(analysis.read_text() + "\n# alternativ analysversion\n")
            assert all(c["ändrat"] == ["Metod · analys.py"] for k, c in inspect(folder).items() if k != "material")
            assert inspect(folder)["material"]["status"] == "Granskad", "en ändrad analys berör inte källpassagen"
            accept(project, affected)
            manus = folder / "manus.md"
            manus.write_text(manus.read_text().replace("två av tre", "en av tre"))
            assert inspect(folder)[affected]["ändrat"] == ["Påståendets lydelse"]
            # Ett äldre projekt utan belägg kan få sin första källa via skrivbordets funktion.
            legacy = Path(temp) / "tidigare projekt"
            shutil.copytree(folder, legacy)
            (legacy / "manus.md").write_text("En ny mening.\n")
            (legacy / "belagg.json").unlink()
            assert inspect(legacy) == {}
            spec = next(v for _, v in source_choices(legacy) if v.get("urval", {}).get("villkor") == "Saklig respons")
            add_source(legacy, "mitt-id", dict(spec, roll="stöd"))
            (legacy / "manus.md").write_text("[En ny mening.](#belagg-mitt-id)\n")
            assert inspect(legacy)["mitt-id"]["status"] == "Ej granskad"
            (legacy / "manus.md").write_text("[En mening](#belagg-okant)\n")
            try:
                inspect(legacy)
            except ValueError as e:
                assert "saknar definition" in str(e)
            else:
                raise AssertionError("Odefinierad länk passerade")
print("OK: klickbara underlag, stöd och motbelägg, riktad omprövning, granskningsbeslut och äldre projekt")
