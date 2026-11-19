"""Projektets läge och ett enda nästa steg. Ren logik utan gränssnitt, så att den kan testas.

Appen visar nästa steg som vyns primära knapp. Ordningen följer arbetsmetoden:
först det som är fel, sedan det som behöver bedömas, sedan att bygga och
upprepa, sist att dela.
"""
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from belagg import inspect
from upprepa import coverage, inventory

PROJEKTMAPP = "Forskningsprojekt"


def runs_of(project):
    folder = project / "korningar"
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if not p.name.startswith(".") and (p / "korning.json").is_file())


def run_label(run):
    """2026-11-18T095122Z-92bd4bfae6 -> 18 nov 2026 09.51"""
    try:
        when = datetime.strptime(run.name[:18], "%Y-%m-%dT%H%M%SZ")
    except ValueError:
        return run.name
    months = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
    return f"{when.day} {months[when.month - 1]} {when.year} {when:%H.%M} UTC"


def overview(project, domain):
    """Allt som projektvyn visar, i en ordbok."""
    project = Path(project)
    manifest = domain(project)
    state = {"projekt": project, "namn": manifest.get("titel") or project.name,
             "skydd": manifest["skydd"], "fel": None, "påståenden": {}, "körningar": [],
             "underlag_ändrat": False,
             "fråga": manifest.get("fråga"), "hypotes": manifest.get("hypotes"),
             "medarbetare": manifest.get("medarbetare") or []}
    try:
        state["påståenden"] = inspect(project / "underlag")
    except (ValueError, OSError, KeyError) as error:
        state["fel"] = str(error)
    runs = runs_of(project)
    for run in runs:
        level, why = coverage(run)
        state["körningar"].append({"mapp": run, "namn": run_label(run), "nivå": level, "varför": why})
    if runs:
        try:
            saved = json.loads((runs[-1] / "korning.json").read_text(encoding="utf-8"))["underlag"]
            state["underlag_ändrat"] = saved != inventory(project / "underlag")
        except (ValueError, OSError, KeyError):
            state["underlag_ändrat"] = True
    return state


def _count(n, one, many):
    return f"{n} {one if n == 1 else many}"


REVIEW_ORDER = ("Underlag saknas", "Ompröva", "Ej granskad")


def pending_claims(state):
    claims = state["påståenden"]
    return [key for status in REVIEW_ORDER for key, claim in claims.items() if claim["status"] == status]


def next_step(state):
    """(åtgärd, rubrik, förklaring). Åtgärden är ett av appens kommandon."""
    if state["fel"]:
        return ("manus", "Rätta underlaget",
                f'{state["fel"]} Öppna manuset eller belagg.json och rätta, så läser ForskarOS projektet igen.')
    claims = list(state["påståenden"].values())
    by_status = {s: [c for c in claims if c["status"] == s] for s in REVIEW_ORDER}
    if by_status["Underlag saknas"]:
        n = len(by_status["Underlag saknas"])
        return ("granska", _count(n, "påstående saknar underlag", "påståenden saknar underlag"),
                "En fil, en källa eller ett citat som påståendet bygger på finns inte längre. Laga kopplingen innan påståendet kan granskas.")
    if by_status["Ompröva"]:
        n = len(by_status["Ompröva"])
        return ("granska", _count(n, "påstående att ompröva", "påståenden att ompröva"),
                "Underlaget har ändrats sedan du granskade. Läs det nya underlaget och bedöm om påståendet håller.")
    if by_status["Ej granskad"]:
        n = len(by_status["Ej granskad"])
        return ("granska", _count(n, "påstående att granska", "påståenden att granska"),
                "Läs underlaget för varje påstående och bekräfta att det stöder det du skriver.")
    if not state["körningar"]:
        return ("bygg", "Bygg den första rapporten",
                "Analysen körs på en kopia av underlaget. Rapport, figur och tabell sparas i en ny körning.")
    if state["underlag_ändrat"]:
        return ("bygg", "Bygg rapporten igen",
                "Underlaget har ändrats sedan senaste körningen. Den gamla körningen finns kvar.")
    last = state["körningar"][-1]
    if last["nivå"] == "Avviker":
        return ("upprepa", "Senaste upprepningen avviker",
                f'{last["varför"]} Kontrollera körningens filer och upprepa kontrollen.')
    if last["nivå"] != "Återkörd":
        return ("upprepa", "Upprepa den senaste körningen",
                "Upprepningen bygger om resultaten från underlaget och kontrollerar att de blir exakt desamma.")
    if state["skydd"] == "skyddad":
        return ("rapport", "Läs rapporten lokalt",
                "Rapporten kan innehålla citat och observationer från det skyddade materialet. Knappen öppnar din sparade kopia.")
    if not claims:
        return ("rapport", "Läs den upprepade rapporten",
                "Resultaten gick att återskapa. Manuset har inga länkade påståenden att granska.")
    if state.get("fråga"):
        return ("fråga", "Ta resultatet till forskningsfrågan",
                "Påståendena är granskade och körningen är upprepad. Resultatet finns i forskningsmappen. "
                "Ompröva frågan där, och dela resultatet med någon som kan granska det.")
    return ("rapport", "Läs och dela rapporten",
            "Alla påståenden är granskade och den senaste körningen är upprepad med samma resultat.")


STEG = [("granska", "Granska"), ("bygg", "Bygg"), ("upprepa", "Upprepa"), ("rapport", "Läs")]


def progress(state):
    """Arbetsflödets fyra steg som (namn, "klar" | "nu" | "senare"). Steget "nu" är nästa steg."""
    action = next_step(state)[0]
    action = {"manus": "granska", "fråga": "rapport"}.get(action, action)
    runs = state["körningar"]
    built = bool(runs) and not state["underlag_ändrat"]
    done = {"granska": bool(state["påståenden"]) and not state["fel"] and all(c["status"] == "Granskad" for c in state["påståenden"].values()),
            "bygg": built, "upprepa": built and runs[-1]["nivå"] == "Återkörd", "rapport": False}
    return [(name, "nu" if key == action else "klar" if done[key] else
             "saknas" if key == "granska" and not state["påståenden"] else "senare") for key, name in STEG]


STATUS_STYLE = {"Granskad": "success", "Återkörd": "success", "Avviker": "error", "Ompröva": "warning",
                "Underlag saknas": "error", "Ej granskad": "", "Dokumenterad": "", "Återkörbar": ""}


def suggest_key(sentence, taken=()):
    """ID för ett nytt påstående ur meningens ord: "Även intervjuerna i exemplet …" -> "aven-intervjuerna-exemplet"."""
    plain = unicodedata.normalize("NFKD", sentence.lower()).encode("ascii", "ignore").decode()
    words = [w for w in re.findall(r"[a-z0-9]+", plain) if len(w) > 2 or w.isdigit()]
    base = "-".join(words[:3]) or "pastaende"
    key, n = base, 2
    while key in taken:
        key, n = f"{base}-{n}", n + 1
    return key


def recent_projects(config_dir, limit=6):
    """Senast öppnade projekt som fortfarande finns."""
    path = Path(config_dir) / "forskaros" / "projekt.json"
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        items = []
    return [Path(p) for p in items if (Path(p) / "underlag").is_dir()][:limit]


def remember_project(config_dir, project):
    path = Path(config_dir) / "forskaros" / "projekt.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    items = [str(project)] + [str(p) for p in recent_projects(config_dir, 20) if Path(p) != Path(project)]
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(items[:20], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
