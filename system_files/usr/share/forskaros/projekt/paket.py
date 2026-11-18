"""En körning som forskningspaket i öppet format: RO-Crate 1.1 med Process Run Crate 0.5.

Paketet beskriver det som redan finns i körningsmappen. Det ändrar inga filer
och ingår inte i körningens kontrollsummor, så det kan skrivas om när en
upprepning har loggats.
"""
import json
import mimetypes
from pathlib import Path

RO_CRATE = "https://w3id.org/ro/crate/1.1"
PROCESS_RUN = "https://w3id.org/ro/wfrun/process/0.5"
# environment och containerImage kommer från Workflow Run-vokabulären.
CONTEXT = ["https://w3id.org/ro/crate/1.1/context", "https://w3id.org/ro/terms/workflow-run/context"]
FORMAT = {".csv": "text/csv", ".md": "text/markdown", ".py": "text/x-python", ".bib": "application/x-bibtex",
          ".json": "application/json", ".svg": "image/svg+xml", ".html": "text/html", ".txt": "text/plain",
          ".r": "text/x-r"}


def _read(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _file(folder, name, digest):
    path = folder / name
    entity = {"@id": name, "@type": "File", "name": Path(name).name,
              "contentSize": str(path.stat().st_size) if path.exists() else None,
              "encodingFormat": FORMAT.get(path.suffix.lower()) or mimetypes.guess_type(name)[0],
              "identifier": f"sha256:{digest}"}
    return {k: v for k, v in entity.items() if v is not None}


def _claims(folder):
    """Manusets länkade påståenden och de underlag de bygger på."""
    try:
        import sys
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from belagg import inspect
        return inspect(folder / "underlag")
    except (ValueError, OSError, KeyError):
        return {}


def _license(domain):
    """Licensen väljer forskaren i projekt.json. ForskarOS hittar aldrig på en."""
    value = domain.get("licens")
    if isinstance(value, str) and value.startswith(("https://", "http://")):
        return {"@id": value, "@type": "CreativeWork", "name": value}
    if domain.get("skydd") == "skyddad":
        text = "Skyddat material. Får inte spridas utan forskningshuvudmannens tillstånd."
    elif value:
        text = str(value)
    else:
        text = "Ingen licens angiven. Ange licens i projekt.json innan paketet sprids."
    return {"@id": "#licens", "@type": "CreativeWork", "name": "Användningsvillkor", "description": text}


def _update_verifications(crate, folder):
    """Uppdatera verifieringshistoriken och bevara paketets ursprungliga metadata."""
    verifications = _read(folder / "verifieringar.json", [])
    if not verifications:
        return
    graph = crate["@graph"]
    dataset = next(node for node in graph if node["@id"] == "./")
    inputs = next(node["object"] for node in graph if node["@id"] == "#korning")
    actions = []
    for i, entry in enumerate(verifications):
        ok = entry["utfall"] == "samma"
        actions.append({"@id": f"#upprepning-{i}", "@type": "CreateAction",
                      "name": f'Upprepning {entry["tid"]}', "description": entry["detalj"],
                      "instrument": {"@id": "upprepa.py"}, "object": inputs,
                      "endTime": entry["tid"],
                      "actionStatus": {"@id": "http://schema.org/CompletedActionStatus" if ok
                                       else "http://schema.org/FailedActionStatus"},
                      **({} if ok else {"error": entry["detalj"]})})

    def previous_action(node):
        return node["@id"].startswith("#upprepning-")

    graph[:] = [node for node in graph if not previous_action(node)]
    graph.extend(actions)
    dataset["mentions"] = [node for node in dataset.get("mentions", []) if not previous_action(node)]
    dataset["mentions"].extend({"@id": action["@id"]} for action in actions)
    log = {"@id": "verifieringar.json"}
    if log not in dataset["hasPart"]:
        dataset["hasPart"].append(log)
    if not any(node["@id"] == log["@id"] for node in graph):
        graph.append({**log, "@type": "File", "name": "verifieringar.json", "encodingFormat": "application/json",
                      "description": "Logg över upprepningar av körningen, även misslyckade."})


def build_crate(folder, domain=None):
    folder = Path(folder)
    manifest = json.loads((folder / "korning.json").read_text(encoding="utf-8"))
    inputs = {f"underlag/{k}": v for k, v in manifest["underlag"].items()}
    outputs = {f"resultat/{k}": v for k, v in manifest["resultat"].items()}
    programs = {name: manifest[name] for name in ("upprepa.py", "belagg.py") if name in manifest}
    files = [_file(folder, name, digest) for name, digest in {**inputs, **outputs, **programs}.items()]
    files.append({"@id": "korning.json", "@type": "File", "name": "korning.json",
                  "encodingFormat": "application/json",
                  "description": "ForskarOS förteckning: SHA-256 för underlag och resultat, programversioner och isolering."})
    env = manifest.get("miljö", {})
    shield = manifest.get("skydd") or {}
    title = (domain or {}).get("titel") or folder.parent.parent.name
    license = _license(domain or {})
    analysis = "underlag/analys.py"
    graph = [
        {"@id": "ro-crate-metadata.json", "@type": "CreativeWork",
         "conformsTo": {"@id": RO_CRATE}, "about": {"@id": "./"}},
        {"@id": "./", "@type": "Dataset", "name": f"{title}: körning {folder.name}",
         "description": "Körning i ett ForskarOS-forskningsprojekt: underlag, analys, resultat och rapport. "
                        "Kör python3 upprepa.py för att återskapa resultaten och jämföra SHA-256.",
         "datePublished": manifest.get("slut") or manifest.get("start") or folder.name[:10],
         "conformsTo": {"@id": PROCESS_RUN},
         "license": {"@id": license["@id"]},
         "hasPart": [{"@id": f["@id"]} for f in files],
         "mentions": [{"@id": "#korning"}]},
        {"@id": PROCESS_RUN, "@type": "CreativeWork", "name": "Process Run Crate", "version": "0.5"},
        license,
        {"@id": "https://www.python.org/", "@type": "SoftwareApplication", "name": "Python",
         "url": "https://www.python.org/", "version": env.get("python", "")},
        {"@id": "https://pandoc.org/", "@type": "SoftwareApplication", "name": "Pandoc",
         "url": "https://pandoc.org/", "version": env.get("pandoc", "").replace("pandoc ", "")},
    ]
    for f in files:
        # Analysen och ForskarOS egna program är körbar källkod, inte bara filer.
        if f["@id"] in (analysis, *programs):
            f["@type"] = ["File", "SoftwareSourceCode"]
            f["programmingLanguage"] = {"@id": "https://www.python.org/"}
        graph.append(f)

    environment = [{"@id": "#isolering", "@type": "PropertyValue", "name": "isolering",
                    "value": shield.get("mekanism") or "ingen"},
                   {"@id": "#natverk", "@type": "PropertyValue", "name": "nätverk",
                    "value": shield.get("nätverk") or "okänt"},
                   {"@id": "#skyddsniva", "@type": "PropertyValue", "name": "skyddsnivå",
                    "value": shield.get("nivå") or (domain or {}).get("skydd") or "okänd"},
                   {"@id": "#arkitektur", "@type": "PropertyValue", "name": "arkitektur",
                    "value": env.get("arkitektur", "")}]
    graph.extend(environment)
    run = {"@id": "#korning", "@type": "CreateAction", "name": f"Analys och rapport {folder.name}",
           "instrument": {"@id": analysis}, "object": [{"@id": k} for k in inputs],
           "result": [{"@id": k} for k in outputs],
           "environment": [{"@id": e["@id"]} for e in environment],
           "actionStatus": {"@id": "http://schema.org/CompletedActionStatus"}}
    if manifest.get("start"):
        run["startTime"] = manifest["start"]
    if manifest.get("slut"):
        run["endTime"] = manifest["slut"]
    if manifest.get("labb"):
        graph.append({"@id": "#labb", "@type": "SoftwareApplication", "name": "ForskarOS-labbet",
                      "identifier": manifest["labb"]})
        run["containerImage"] = {"@id": "#labb"}
    graph.append(run)

    for key, claim in _claims(folder).items():
        based = []
        for item in claim["underlag"]:
            spec = item["spec"]
            if "fil" in spec and f'underlag/{spec["fil"]}' in inputs:
                based.append({"@id": f'underlag/{spec["fil"]}'})
            if "källa" in spec:
                based.append({"@id": f'#kalla-{spec["källa"]}'})
        for item in claim["underlag"]:
            spec = item["spec"]
            if "källa" in spec and not any(e.get("@id") == f'#kalla-{spec["källa"]}' for e in graph):
                graph.append({"@id": f'#kalla-{spec["källa"]}', "@type": "CreativeWork",
                              "name": item.get("titel") or spec["källa"], "identifier": spec["källa"]})
        graph.append({"@id": f"#belagg-{key}", "@type": "CreativeWork", "name": claim["text"],
                      "description": f'Påstående i manus.md. Status vid körningen: {claim["status"]}.',
                      "isBasedOn": based})
        graph[1]["mentions"].append({"@id": f"#belagg-{key}"})
    crate = {"@context": CONTEXT, "@graph": graph}
    _update_verifications(crate, folder)
    return crate


def write_crate(folder, domain=None, *, verification_only=False):
    folder = Path(folder)
    path = folder / "ro-crate-metadata.json"
    if verification_only:
        crate = json.loads(path.read_text(encoding="utf-8"))
        _update_verifications(crate, folder)
    else:
        crate = build_crate(folder, domain)
    tmp = folder / ".ro-crate-metadata.json.tmp"
    tmp.write_text(json.dumps(crate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path
