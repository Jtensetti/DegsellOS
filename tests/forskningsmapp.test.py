"""Från tanke till handling: forskningsfrågan i Obsidian och projektet i appen hänger ihop."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(root / "system_files/usr/share/forskaros/projekt"))
import forskningsmapp as fm  # noqa: E402
from oversikt import next_step, overview  # noqa: E402
from projekt import domain  # noqa: E402

cmd = root / "system_files/usr/bin/forskaros-projekt"


def call(*args, ok=True):
    result = subprocess.run([str(cmd), *map(str, args)], capture_output=True, text=True)
    assert result.returncode == 0 or not ok, result.stderr
    return result.stdout.strip()


def accept_all(project):
    for line in call("belägg", project).splitlines():
        key = line.split(" · ")[0]
        call("granska", project, key, "--avtryck", call("belägg", project, key).split("Avtryck: ")[-1])


def core(question, notes):
    """Kör ForskarOS Core:s faskrav på anteckningarna, som panelen i Obsidian gör."""
    script = """
const Module = require('node:module'); const orig = Module._load;
Module._load = function (r, ...a) { return r === 'obsidian' ? { Plugin: class {}, ItemView: class {}, Notice: class {}, Modal: class {} } : orig.call(this, r, ...a); };
const { engine } = require(process.argv[1]);
const [q, notes] = JSON.parse(require('fs').readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify({ krav: engine.phaseRequirements(q, notes), granskning: engine.audit(notes, q.fm.datum) }));
"""
    data = json.dumps([question, notes])
    out = subprocess.run(["node", "-e", script, str(root / "vault/.obsidian/plugins/forskaros-core/main.js")],
                         input=data, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def note(path, vault):
    fields, body = fm.split_frontmatter(path.read_text(encoding="utf-8"))
    return {"path": path.relative_to(vault).as_posix(), "fm": fields, "body": body, "created": "2026-11-19"}


with tempfile.TemporaryDirectory() as tmp:
    vault = Path(tmp) / "ForskarOS"
    (vault / "01 RIKTNING").mkdir(parents=True)
    (vault / "02 HYPOTESER").mkdir()
    (vault / "01 RIKTNING/Hypotesbyten.md").write_text(
        "---\ntyp: forskningsfråga\nstatus: aktiv\nfas: utveckla\ndatum: 2026-11-19\n---\n"
        "# Byter elever hypotes efter saklig respons?\n\n## Medarbetare\n\n", encoding="utf-8")
    (vault / "02 HYPOTESER/Saklig respons.md").write_text(
        '---\ntyp: hypotes\nfråga: "[[01 RIKTNING/Hypotesbyten]]"\n---\n# Hypotes\n\n'
        "## Hypotes (min formulering)\nSaklig respons får fler elever att byta hypotes.\n\n"
        "## Vilket etablerat antagande utmanar hypotesen?\n\n"
        "## Prediktioner\n1. Högre andel byten efter saklig respons (se @smith2020).\n2.\n\n"
        "## Falsifiering: vilken observation skulle tala emot hypotesen?\n"
        "> Mallens hjälptext.\nLika stor andel byten i båda grupperna, jfr [[03 EVIDENS/Karta|kartan]].\n",
        encoding="utf-8")
    (vault / "01 RIKTNING/Avslutad.md").write_text("---\ntyp: forskningsfråga\nstatus: avslutad\n---\n# Gammal\n")
    os.environ["FORSKAROS_VAULT"] = str(vault)

    assert [q["ref"] for q in fm.questions()] == ["01 RIKTNING/Hypotesbyten"], "avslutade frågor visas inte"
    assert fm.questions()[0]["titel"] == "Byter elever hypotes efter saklig respons?"
    assert [h["ref"] for h in fm.hypotheses("01 RIKTNING/Hypotesbyten")] == ["02 HYPOTESER/Saklig respons"]

    # Ett projekt utan koppling rör inte forskningsmappen.
    fri = Path(tmp) / "Fri"
    call("skapa", "kvantitativ", fri)
    accept_all(fri)
    call("kör", fri)
    assert not (vault / "04 EXPERIMENT").exists()

    project = Path(tmp) / "Studie"
    call("skapa", "kvantitativ", project, "--fråga", "01 RIKTNING/Hypotesbyten",
         "--hypotes", "02 HYPOTESER/Saklig respons", "--medarbetare", "Anna, Björn")
    manifest = json.loads((project / "projekt.json").read_text())
    assert manifest["fråga"] == "01 RIKTNING/Hypotesbyten" and manifest["medarbetare"] == ["Anna", "Björn"]
    experiment = vault / "04 EXPERIMENT/Projekt Studie.md"
    fields, body = fm.split_frontmatter(experiment.read_text())
    assert fields["status"] == "planerat" and fields["hypotes"] == "[[02 HYPOTESER/Saklig respons]]"
    assert "## Vilken hypotes prövas?\n[[02 HYPOTESER/Saklig respons]]" in body

    q = note(vault / "01 RIKTNING/Hypotesbyten.md", vault)
    krav = {k["text"]: k["ok"] for k in core(q, [note(experiment, vault)])["krav"]}
    assert not krav["Minst ett experiment eller arbetsprov med resultat"], "inget resultat innan analysen körts"
    assert krav["Någon mer arbetar med frågan: en medarbetare eller ett möte om samarbete"], "projektets medarbetare räknas"

    accept_all(project)
    run = Path(call("kör", project))
    # Rapporten börjar med hypotesen och förutsägelsen som de stod när analysen kördes.
    prediction = (run / "forutsagelse.md").read_text()
    assert "Saklig respons får fler elever att byta hypotes." in prediction and "Byter elever hypotes" in prediction
    assert "Mallens hjälptext" not in prediction and "Antagandet som utmanas" not in prediction, "tomma avsnitt visas inte"
    assert "jfr kartan" in prediction and "\\@smith2020" in prediction
    report = " ".join((run / "resultat/rapport.html").read_text().split())
    assert report.index("Hypotesen som prövas") < report.index("Fråga"), "förutsägelsen står först"
    assert "Lika stor andel byten i båda grupperna" in report
    assert "forutsagelse.md" in json.loads((run / "korning.json").read_text())
    crate = json.loads((run / "ro-crate-metadata.json").read_text())
    assert {"@id": "forutsagelse.md"} in next(e for e in crate["@graph"] if e["@id"] == "./")["hasPart"]

    fields, body = fm.split_frontmatter(experiment.read_text())
    assert fields["status"] == "genomfört" and fields["nivå"] == "Dokumenterad" and fields["körning"] == run.name
    assert "- Granskad: I gruppen med saklig respons bytte två av tre elever hypotes." in body
    assert (run / "resultat/rapport.html").as_uri() in body
    krav = {k["text"]: k["ok"] for k in core(q, [note(experiment, vault)])["krav"]}
    assert krav["Minst ett experiment eller arbetsprov med resultat"], "körningen i appen är handlingen"

    # Forskarens egna ord och fält skrivs aldrig över.
    text = experiment.read_text().replace("## Vad betyder resultatet, och vad betyder det inte?\n",
                                          "## Vad betyder resultatet, och vad betyder det inte?\nBara tre elever per grupp.\n")
    experiment.write_text(text.replace("---\ntyp:", "---\netikett: pilot\ntyp:", 1))
    call("upprepa", run)
    fields, body = fm.split_frontmatter(experiment.read_text())
    assert fields["nivå"] == "Återkörd" and fields["etikett"] == "pilot"
    assert "Bara tre elever per grupp." in body

    # Ändras hypotesen efteråt följer den sparade förutsägelsen med körningen, och en ändrad kopia upptäcks.
    hyp = vault / "02 HYPOTESER/Saklig respons.md"
    hyp.write_text(hyp.read_text().replace("fler elever", "många elever"))
    call("upprepa", run)
    saved = (run / "forutsagelse.md").read_text()
    (run / "forutsagelse.md").write_text(saved.replace("fler elever", "alla elever"))
    assert "Förutsägelse avviker" in call("upprepa", run, ok=False) + subprocess.run(
        [str(cmd), "upprepa", str(run)], capture_output=True, text=True).stderr
    (run / "forutsagelse.md").write_text(saved)
    call("upprepa", run)

    # Hypotesen skrevs om efter resultatet. Appen föreslår en ny körning, och rapporten säger det öppet.
    import time
    time.sleep(1.1)
    hyp.touch()
    assert next_step(overview(project, domain))[:2] == ("bygg", "Hypotesen har ändrats")
    run2 = Path(call("kör", project))
    second = (run2 / "forutsagelse.md").read_text()
    assert "många elever" in second and "Ändrad efter tidigare resultat" in second and run.name in second
    assert "Ändrad" not in saved, "den första körningen har ingen ändring att redovisa"
    call("upprepa", run2)
    run = run2

    dela = dict(q, fm=dict(q["fm"], fas="dela"))
    krav = {k["text"]: k["ok"] for k in core(dela, [note(experiment, vault)])["krav"]}
    assert krav["Analysen bakom resultatet är upprepad med samma resultat (appen ForskarOS)"]
    assert next_step(overview(project, domain))[0] == "fråga", "sista steget leder tillbaka till frågan"

    # Ändrat underlag syns som påstående att ompröva i Core.
    data = project / "underlag/data.csv"
    data.write_text(data.read_text().replace("Saklig respons,1", "Saklig respons,0", 1))
    call("koppla", project, "--medarbetare", "Anna")
    fields, _ = fm.split_frontmatter(experiment.read_text())
    assert fields["att_ompröva"] == "1" and fields["medarbetare"] == "Anna"
    granskning = core(q, [note(experiment, vault)])["granskning"]
    assert any(f["princip"] == "Påstående att ompröva" for f in granskning), granskning

    # Appen och forskningsmappen pekar på varandra.
    assert "forskaros://projekt?mapp=" in experiment.read_text()
    assert [e["ref"] for e in fm.projects_for("01 RIKTNING/Hypotesbyten")] == ["04 EXPERIMENT/Projekt Studie"]

    # Ett projekt med samma namn i en annan mapp får en egen anteckning.
    other = Path(tmp) / "annan" / "Studie"
    other.parent.mkdir()
    call("skapa", "kvantitativ", other, "--fråga", "01 RIKTNING/Hypotesbyten")
    assert (vault / "04 EXPERIMENT/Projekt Studie 2.md").is_file()
    assert fm.split_frontmatter(experiment.read_text())[0]["projekt"] == str(project.resolve())

    # Ett flyttat projekt behåller sin anteckning.
    moved = Path(tmp) / "Flyttad studie"
    project.rename(moved)
    call("koppla", moved, "--medarbetare", "Anna")
    fields, body = fm.split_frontmatter(experiment.read_text())
    assert fields["projekt"] == str(moved.resolve()) and "Bara tre elever per grupp." in body
    assert not (vault / "04 EXPERIMENT/Projekt Flyttad studie.md").exists()
    project = moved

    # Länkar från panelen i Obsidian öppnar rätt vy i appen.
    from_core = subprocess.run(["node", "-e", """
const Module = require('node:module'); const orig = Module._load;
Module._load = function (r, ...a) { return r === 'obsidian' ? { Plugin: class {}, ItemView: class {}, Notice: class {}, Modal: class {} } : orig.call(this, r, ...a); };
const { engine } = require(process.argv[1]);
console.log(engine.appUri('nytt-projekt', { fråga: '01 RIKTNING/Hypotesbyten', hypotes: '02 HYPOTESER/Saklig respons' }));
console.log(engine.appUri('projekt', { mapp: process.argv[2] }));
""", str(root / "vault/.obsidian/plugins/forskaros-core/main.js"), str(project)],
        capture_output=True, text=True, check=True).stdout.split()
    assert fm.parse_app_uri(from_core[0]) == {"nytt": {"fråga": "01 RIKTNING/Hypotesbyten", "hypotes": "02 HYPOTESER/Saklig respons"}}
    assert fm.parse_app_uri(from_core[1]) == {"projekt": str(project)}
    assert fm.parse_app_uri(fm.app_uri("projekt", mapp=str(project))) == {"projekt": str(project)}

    # Kopplingen kan tas bort.
    assert call("koppla", project, "--fråga", "") == "Projektet är inte kopplat till någon forskningsfråga."
    assert "fråga" not in json.loads((project / "projekt.json").read_text())
    assert fm.obsidian_uri("01 RIKTNING/Hypotesbyten").startswith("obsidian://open?vault=ForskarOS&file=01%20RIKTNING")

# En ändring inne i en lista räknas, men inte var eller när texten hämtades.
text = "::: {.forutsagelse}\n## H\n\nUr forskningsfrågan ”X?” Hämtad.\n\n**Förutsägelsen.**\n\n1. A\n2. B\n:::\n"
assert fm._claims_of(text) != fm._claims_of(text.replace("2. B", "2. C"))
assert fm._claims_of(text) == fm._claims_of(text.replace("”X?”", "”Y?”"))

print("OK: forskningsfråga, hypotes och medarbetare kopplas till projektet; körning, upprepning och omprövning når Core")
