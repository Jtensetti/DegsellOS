"""Acceptanstest 1–4 ur ForskarOS 3.0 (dokument 14, avsnitt 12) för forskningsdomänen.

1. Projektisolering   – skyddat projekt körs utan nätverk och hemkatalog, annars inte alls
2. Reproducerbarhet   – täckningsgrad: dokumenterad, återkörbar, återkörd (med logg)
3. Evidenskedja       – påstående kopplat till en källpassage, omprövning när källan ändras
4. Forskningspaket    – varje körning är ett giltigt RO-Crate 1.1 / Process Run Crate 0.5

Miljövariabler:
  FORSKAROS_KRAV_SANDLADA=1     fel i stället för överhoppning om bubblewrap inte fungerar
  FORSKAROS_KRAV_ROCRATE=1      fel i stället för överhoppning om valideraren saknas
  FORSKAROS_ROCRATE_VALIDATOR   sökväg till rocrate-validator
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
cmd = root / "system_files/usr/bin/forskaros-projekt"
sys.dont_write_bytecode = True
sys.path.insert(0, str(root / "system_files/usr/share/forskaros/projekt"))
from upprepa import sandbox_probe  # noqa: E402


def call(*args, fail=False, env=None):
    result = subprocess.run([str(cmd), *map(str, args)], capture_output=True, text=True,
                            env={**os.environ, **(env or {})})
    assert (result.returncode != 0) == fail, (args, result.stdout, result.stderr)
    return result.stderr if fail else result.stdout.strip()


def runs(project):
    return sorted(p for p in (project / "korningar").iterdir() if not p.name.startswith("."))


def level(project, run):
    line = next(l for l in call("status", project).splitlines() if l.startswith(run.name))
    return line.split(" · ")[1]


def skip(what, variable):
    if os.environ.get(variable) == "1":
        raise AssertionError(f"{what} krävs men saknas ({variable}=1)")
    print(f"  HOPPAR ÖVER: {what} saknas här")


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    try:
        sandbox_probe(tmp)
        sandbox = True
    except ValueError as error:
        sandbox = False
        print(f"  bubblewrap fungerar inte här: {error}")

    open_project = tmp / "Öppen studie"
    call("skapa", "kvantitativ", open_project)
    open_run = Path(call("kör", open_project))
    manifest = json.loads((open_project / "projekt.json").read_text())
    assert manifest["skydd"] == "öppen" and len(manifest["id"]) == 36 and manifest["titel"] == "Öppen studie"
    assert json.loads((open_run / "korning.json").read_text())["skydd"]["nivå"] == "öppen"

    # ---- 1. Projektisolering -------------------------------------------------
    print("1. Projektisolering")
    protected = tmp / "Skyddad studie"
    call("skapa", "kvalitativ", protected, "--skydd", "skyddad")
    assert json.loads((protected / "projekt.json").read_text())["skydd"] == "skyddad"
    refused = call("kör", protected, fail=True, env={"FORSKAROS_BWRAP": "/bin/false"})
    assert "kör inte analysen utan skydd" in refused and runs(protected) == [], refused
    print("  ✓ vägrar köra när sandlådan inte kan startas, och lämnar ingen körning")
    if not sandbox:
        skip("En fungerande bubblewrap", "FORSKAROS_KRAV_SANDLADA")
        protected_run = None
    else:
        protected_run = Path(call("kör", protected, env={"FORSKAROS_TEST_HEMLIGHET": "läckt"}))
        shield = json.loads((protected_run / "korning.json").read_text())["skydd"]
        assert shield["nivå"] == "skyddad" and shield["nätverk"] == "avstängt" and shield["hemkatalog"] == "dold"
        assert shield["mekanism"].startswith("bubblewrap"), shield
        analysis = protected / "underlag/analys.py"
        original = analysis.read_text()
        secret = tmp / "hemlig.txt"
        secret.write_text("får inte läsas\n")
        attempts = {
            "nätverk": ("import socket\nsocket.create_connection(('1.1.1.1', 443), timeout=3)\n", "unreachable"),
            "fil utanför körningen": (f"open({str(secret)!r}).read()\n", "No such file"),
            "miljövariabel": ("import os\nassert os.environ.get('FORSKAROS_TEST_HEMLIGHET') is None, 'läckt'\n", None),
            "hemkatalog": ("import os\nassert not any(os.scandir('/home')) if os.path.isdir('/home') else True\n"
                           "assert not os.path.isdir('/root') or not any(os.scandir('/root'))\n", None),
        }
        for name, (code, expected) in attempts.items():
            analysis.write_text(original + code)
            out = call("kör", protected, fail=name != "miljövariabel" and name != "hemkatalog",
                       env={"FORSKAROS_TEST_HEMLIGHET": "läckt"})
            if expected:
                assert expected in out, (name, out)
            print(f"  ✓ {name}: {'stoppad' if expected else 'inte åtkomlig'} i sandlådan")
        analysis.write_text(original)
        for extra in runs(protected):
            if extra != protected_run:
                shutil.rmtree(extra)  # Lyckade provkörningar med miljövariabel och hemkatalog.
        assert runs(protected) == [protected_run]

    # ---- 2. Reproducerbarhet med täckningsgrad --------------------------------
    print("2. Reproducerbarhet med täckningsgrad")
    assert level(open_project, open_run) == "Dokumenterad"
    print("  ✓ öppen körning utan isolering: Dokumenterad")
    tampered = tmp / "manipulerad"
    shutil.copytree(open_run, tampered)
    call("upprepa", open_run)
    assert level(open_project, open_run) == "Återkörd"
    log = json.loads((open_run / "verifieringar.json").read_text())
    assert log[-1]["utfall"] == "samma" and log[-1]["miljö"]["pandoc"]
    print("  ✓ efter upprepning med samma SHA-256: Återkörd, med tid och miljö i loggen")
    (tampered / "resultat/resultat.csv").write_text("villkor,antal\nändrat,1\n")
    assert "resultat.csv" in call("upprepa", tampered, fail=True)
    entry = json.loads((tampered / "verifieringar.json").read_text())[-1]
    assert entry["utfall"] == "avviker" and "resultat.csv" in entry["detalj"]
    print("  ✓ en manipulerad körning loggas som avvikande, inte som återkörd")
    if protected_run:
        assert level(protected, protected_run) == "Återkörbar"
        colleague = tmp / "kollegans kopia"
        shutil.copytree(protected_run, colleague)
        call("upprepa", protected_run)
        assert level(protected, protected_run) == "Återkörd"
        assert json.loads((protected_run / "verifieringar.json").read_text())[-1]["skydd"] == "bubblewrap"
        print("  ✓ skyddad körning: Återkörbar, sedan Återkörd i sandlådan")
        # Kollegan har Python och Pandoc men ingen bubblewrap.
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        for tool in ("python3", "pandoc"):
            (bin_dir / tool).symlink_to(shutil.which(tool))
        bare = {"PATH": str(bin_dir), "FORSKAROS_BWRAP": ""}
        result = subprocess.run([sys.executable, "-I", str(colleague / "upprepa.py")], capture_output=True,
                                text=True, cwd=tmp, env={**os.environ, **bare})
        assert result.returncode and "--utan-skydd" in result.stderr, result
        assert not (colleague / "verifieringar.json").exists()
        result = subprocess.run([sys.executable, "-I", str(colleague / "upprepa.py"), "--utan-skydd"],
                                capture_output=True, text=True, cwd=tmp, env={**os.environ, **bare})
        assert result.returncode == 0, result
        assert json.loads((colleague / "verifieringar.json").read_text())[-1]["skydd"] is None
        print("  ✓ utan bubblewrap vägrar upprepa.py, --utan-skydd loggas som oskyddad upprepning")

    # ---- 3. Evidenskedja från källpassage ------------------------------------
    print("3. Evidenskedja från källpassage")
    folder = open_project / "underlag"
    shown = call("belägg", open_project, "material")
    assert "»De beskriver inga verkliga elever.«" in shown and "Konstruerat övningsmaterial" in shown
    assert "Citatet finns i kallor/ovning.md" in shown
    call("granska", open_project, "material", "--avtryck", shown.split("Avtryck: ")[-1])
    bib = folder / "kallor.bib"
    original_bib = bib.read_text()
    bib.write_text(original_bib.replace("year = {2026},", "year = {2026},\n  file = {/home/forskare/Zotero/a.pdf},\n"
                                        "  abstract = {Ny sammanfattning},"))
    assert "material · Granskad" in call("belägg", open_project), "ny export med fil och sammanfattning är inget falsklarm"
    print("  ✓ ny Zotero-export med fil och sammanfattning ger inget falsklarm")
    bib.write_text(original_bib.replace("Konstruerat övningsmaterial", "Rättat övningsmaterial"))
    changed = call("belägg", open_project, "material")
    assert "Ompröva" in changed and "Stöd · källa ovning · s. 1" in changed
    listing = call("belägg", open_project)
    assert "saklig · Ej granskad" in listing and "neutral · Ej granskad" in listing, "datapåståendena berörs inte"
    print("  ✓ ändrad källa (titel) ger Ompröva för påståendet")
    bib.write_text(original_bib.replace("@misc{ovning,", "@misc{annan,"))
    assert "Källan ovning saknas i kallor.bib" in call("belägg", open_project, "material")
    assert "material · Underlag saknas" in call("belägg", open_project)
    print("  ✓ borttagen källa ger Underlag saknas")
    bib.write_text(original_bib)
    text = folder / "kallor/ovning.md"
    original_text = text.read_text()
    text.write_text(original_text.replace("De beskriver inga verkliga elever.", "De beskriver verkliga elever."))
    assert "Citatet finns inte i kallor/ovning.md" in call("belägg", open_project, "material")
    print("  ✓ ett citat som inte står i källtexten upptäcks")
    text.write_text(original_text)
    # Samma väg som dialogen Koppla underlag: välj källpassagen och klistra in citatet.
    from belagg import add_source, source_choices
    spec = next(v for label, v in source_choices(folder) if label.startswith("Källpassage · ovning"))
    try:
        add_source(folder, "nytt", dict(spec, roll="stöd"))
    except ValueError as error:
        assert "citatet" in str(error)
    else:
        raise AssertionError("En källpassage utan citat sparades")
    add_source(folder, "nytt", dict(spec, roll="stöd", citat="De kommer inte från verkliga intervjuer.",
                                    sida="s. 1", fil="kallor/ovning.md"))
    manus = folder / "manus.md"
    manus.write_text(manus.read_text() + "\n[Även intervjuerna är konstruerade.](#belagg-nytt)\n")
    assert "nytt · Ej granskad" in call("belägg", open_project)
    print("  ✓ en källpassage kopplas som i dialogen; citat krävs")
    report = (Path(call("kör", open_project)) / "resultat/rapport.html").read_text()
    assert "<blockquote>De beskriver inga verkliga elever.</blockquote>" in report and 'id="belagg-material"' in report
    print("  ✓ rapporten visar källpassagen vid påståendet")

    # ---- 4. Forskningspaket i öppet format ------------------------------------
    print("4. Forskningspaket (RO-Crate)")
    validator = os.environ.get("FORSKAROS_ROCRATE_VALIDATOR") or shutil.which("rocrate-validator")
    crates = [r for r in runs(open_project)] + ([protected_run] if protected_run else [])
    for crate in crates:
        data = json.loads((crate / "ro-crate-metadata.json").read_text())
        ids = {e["@id"]: e for e in data["@graph"]}
        action = ids["#korning"]
        assert action["instrument"] == {"@id": "underlag/analys.py"}
        assert {"@id": "underlag/data.csv"} in action["object"]
        assert {"@id": "resultat/rapport.html"} in action["result"]
        assert ids["./"]["license"]["@id"] in ids
        claim = ids["#belagg-material"]
        # Både källan och källtexten i projektet, där citatet har kontrollerats.
        assert claim["isBasedOn"] == [{"@id": "underlag/kallor/ovning.md"}, {"@id": "#kalla-ovning"}], claim
        assert ids["#kalla-ovning"]["name"] == "Konstruerat övningsmaterial för forskningsprojekt"
    assert any(e["@type"] == "CreateAction" and e["@id"].startswith("#upprepning")
               for e in json.loads((open_run / "ro-crate-metadata.json").read_text())["@graph"])
    print("  ✓ körning, underlag, resultat, licens, påståenden och upprepningar beskrivs")
    if protected_run:
        license = next(e for e in json.loads((protected_run / "ro-crate-metadata.json").read_text())["@graph"]
                       if e["@id"] == "#licens")
        assert "forskningshuvudmannens tillstånd" in license["description"]
        print("  ✓ skyddat projekt: paketet säger att materialet inte får spridas")
    if not validator:
        skip("rocrate-validator", "FORSKAROS_KRAV_ROCRATE")
    else:
        for crate in (open_run, protected_run):
            if crate is None:
                continue
            for profile in ("ro-crate-1.1", "process-run-crate-0.5"):
                result = subprocess.run([validator, "validate", "--no-paging", "-p", profile, str(crate)],
                                        capture_output=True, text=True)
                assert result.returncode == 0 and "[OK]" in result.stdout, (profile, crate, result.stdout[-3000:])
        print("  ✓ godkänt av rocrate-validator: RO-Crate 1.1 och Process Run Crate 0.5")

    # ---- Äldre projekt -----------------------------------------------------
    legacy = tmp / "äldre projekt"
    shutil.copytree(open_project, legacy)
    (legacy / "projekt.json").unlink()
    assert call("status", legacy).startswith("äldre projekt · öppen")
    Path(call("kör", legacy))
    print("Äldre projekt utan projekt.json körs som öppna")

print("OK: acceptanstest 1–4 för forskningsdomänen")
