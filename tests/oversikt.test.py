"""Nästa steg genom ett projekts hela livscykel."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(root / "system_files/usr/share/forskaros/projekt"))
from projekt import domain  # noqa: E402
from oversikt import (next_step, overview, pending_claims, progress, recent_projects, remember_project, run_label,
                      suggest_key)  # noqa: E402

cmd = root / "system_files/usr/bin/forskaros-projekt"


def call(*args):
    return subprocess.run([str(cmd), *map(str, args)], capture_output=True, text=True, check=True).stdout.strip()


def step(project):
    return next_step(overview(project, domain))


def steps(project):
    return [s for _, s in progress(overview(project, domain))]


def accept_all(project):
    for line in call("belägg", project).splitlines():
        key = line.split(" · ")[0]
        stamp = call("belägg", project, key).split("Avtryck: ")[-1]
        call("granska", project, key, "--avtryck", stamp)


with tempfile.TemporaryDirectory() as tmp:
    project = Path(tmp) / "Studie"
    call("skapa", "kvantitativ", project)

    action, title, _ = step(project)
    assert (action, title) == ("granska", "3 påståenden att granska"), title
    assert steps(project) == ["nu", "senare", "senare", "senare"]
    accept_all(project)
    assert step(project)[:2] == ("bygg", "Bygg den första rapporten")
    assert steps(project) == ["klar", "nu", "senare", "senare"]

    run = Path(call("kör", project))
    state = overview(project, domain)
    assert state["körningar"][-1]["nivå"] == "Dokumenterad" and not state["underlag_ändrat"]
    assert step(project)[:2] == ("upprepa", "Upprepa den senaste körningen")
    assert steps(project) == ["klar", "klar", "nu", "senare"]

    call("upprepa", run)
    # Appen läser inte om oförändrat underlag när fönstret får fokus igen.
    from belagg import inspect
    first, again = inspect(project / "underlag", cached=True), inspect(project / "underlag", cached=True)
    key = next(k for k, c in first.items() if c["underlag"][0]["rader"])
    assert first[key]["underlag"][0]["rader"] is again[key]["underlag"][0]["rader"]
    assert inspect(project / "underlag")[key]["avtryck"] == first[key]["avtryck"], "samma avtryck utan cache"

    assert step(project)[:2] == ("rapport", "Läs och dela rapporten")
    assert steps(project) == ["klar", "klar", "klar", "nu"]

    # En ny avvikelse måste synas även efter en tidigare lyckad verifiering.
    result_file = run / "resultat/resultat.csv"
    original = result_file.read_bytes()
    result_file.write_text("rättelse\n")
    failed = subprocess.run([cmd, "upprepa", run], text=True, capture_output=True)
    assert failed.returncode and "resultat.csv" in failed.stderr
    assert " · Avviker · " in call("status", project)
    action, title, why = step(project)
    assert (action, title) == ("upprepa", "Senaste upprepningen avviker") and "resultat.csv" in why
    assert steps(project) == ["klar", "klar", "nu", "senare"]
    crate = json.loads((run / "ro-crate-metadata.json").read_text())
    history = [node for node in crate["@graph"] if node["@id"].startswith("#upprepning-")]
    assert len(history) == 2 and history[-1]["actionStatus"]["@id"].endswith("/FailedActionStatus")
    result_file.write_bytes(original)
    call("upprepa", run)
    assert step(project)[:2] == ("rapport", "Läs och dela rapporten")
    assert [e["utfall"] for e in json.loads((run / "verifieringar.json").read_text())] == ["samma", "avviker", "samma"]

    done = overview(project, domain)
    assert next_step(dict(done, skydd="skyddad"))[1] == "Läs rapporten lokalt"
    empty = dict(done, påståenden={})
    assert "inga länkade påståenden" in next_step(empty)[2]
    assert progress(empty)[0][1] == "saknas"
    mixed = dict(done, påståenden={"ny": {"status": "Ej granskad"}, "rättad": {"status": "Ompröva"},
                                  "borta": {"status": "Underlag saknas"}})
    assert pending_claims(mixed) == ["borta", "rättad", "ny"]
    assert "saknar underlag" in next_step(mixed)[1]

    data = project / "underlag/data.csv"
    data.write_text(data.read_text().replace("Saklig respons,1", "Saklig respons,0", 1))
    assert step(project)[:2] == ("granska", "1 påstående att ompröva"), step(project)
    assert steps(project) == ["nu", "senare", "senare", "senare"], "ändrat underlag gör körningen inaktuell"
    accept_all(project)
    assert step(project)[:2] == ("bygg", "Bygg rapporten igen")

    bib = project / "underlag/kallor.bib"
    original = bib.read_text()
    bib.write_text(original.replace("@misc{ovning,", "@misc{annan,"))
    assert step(project)[:2] == ("granska", "1 påstående saknar underlag"), "saknat underlag före allt annat"
    bib.write_text(original)

    manus = project / "underlag/manus.md"
    manus.write_text(manus.read_text() + "\n[Odefinierat](#belagg-okand)\n")
    action, title, why = step(project)
    assert action == "manus" and "okand" in why, why

    assert run_label(run).endswith("UTC") and " 20" in run_label(run)

    config = Path(tmp) / "config"
    other = Path(tmp) / "Annan"
    call("skapa", "kvalitativ", other)
    remember_project(config, project)
    remember_project(config, other)
    remember_project(config, project)
    assert recent_projects(config) == [project, other]
    (other / "underlag").rename(other / "flyttad")
    assert recent_projects(config) == [project], "borttagna projekt visas inte"

assert suggest_key("Även intervjuerna i exemplet är konstruerade.") == "aven-intervjuerna-exemplet"
assert suggest_key("I grupp 2 bytte fler.", {"grupp-2-bytte"}) == "grupp-2-bytte-2"
assert suggest_key("…") == "pastaende"

print("OK: nästa steg och arbetsflödets steg genom projektets livscykel, senaste projekt, förslag på ID")
