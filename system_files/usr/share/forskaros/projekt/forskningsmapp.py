"""Forskningsmappen i Obsidian sedd från ett forskningsprojekt.

Tanken och handlingen hänger ihop: ett projekt kan kopplas till en
forskningsfråga och en hypotes i forskningsmappen (ForskarOS Core). Projektets
läge skrivs då tillbaka som ett experiment i `04 EXPERIMENT`, med senaste
körning, täckningsgrad och påståendenas status. Core läser anteckningen: en
körning med resultat uppfyller kravet i fasen Utveckla, en återkörd körning
krävs innan resultatet delas, och påståenden att ompröva syns i panelen.

Forskarens egna avsnitt i anteckningen skrivs aldrig över.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile

EXPERIMENTMAPP = "04 EXPERIMENT"
ÄGDA = ("typ", "fråga", "hypotes", "projekt", "projekt_id", "medarbetare", "körning", "nivå", "att_ompröva", "status")


def vault_root():
    return Path(os.environ.get("FORSKAROS_VAULT") or Path.home() / "ForskarOS")


def split_frontmatter(text):
    """(fält, brödtext). Klarar den enkla YAML som Core och Obsidian skriver."""
    m = re.match(r"---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return {}, text
    fields = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(":")
        if not sep or line.startswith((" ", "-", "#")):
            continue
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            try:
                value = json.loads(value)
            except ValueError:
                value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        fields[key.strip()] = value
    return fields, text[m.end():]


def render_frontmatter(fields):
    lines = []
    for key, value in fields.items():
        value = str(value)
        if re.search(r"[:#\[\]{}]", value) or value != value.strip():
            value = json.dumps(value, ensure_ascii=False)
        lines.append(f"{key}: {value}")
    return "---\n" + "\n".join(lines) + "\n---\n"


def link_target(value):
    """'[[02 HYPOTESER/H|H]]' -> '02 HYPOTESER/H'."""
    m = re.search(r"\[\[([^\]|#]+)", str(value or ""))
    return (m.group(1) if m else str(value or "")).strip().removesuffix(".md") or None


_HUVUDEN = {}


def _head(path):
    """Frontmatter och rubrik. Läser bara början av filen och återanvänder oförändrade."""
    st = path.stat()
    key = (str(path), st.st_size, st.st_mtime_ns)
    if key not in _HUVUDEN:
        with path.open("rb") as stream:
            text = stream.read(16384).decode("utf-8", errors="replace")
        fields, body = split_frontmatter(text)
        heading = re.search(r"^# (.+)$", body, re.M)
        _HUVUDEN[key] = (fields, heading.group(1).strip() if heading else path.stem)
    return _HUVUDEN[key]


def scan(root=None):
    """Alla anteckningar med typ i forskningsmappen, läst en gång."""
    root = Path(root or vault_root())
    if not root.is_dir():
        return []
    out = []
    for path in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        try:
            fields, title = _head(path)
        except OSError:
            continue
        if fields.get("typ"):
            ref = path.relative_to(root).with_suffix("").as_posix()
            out.append({"ref": ref, "titel": title, "fm": fields})
    return out


def _notes(root, typ, notes=None):
    return [n for n in (scan(root) if notes is None else notes) if n["fm"].get("typ") == typ]


def _same(target, ref):
    return bool(target) and (target == ref or target == ref.rsplit("/", 1)[-1])


def questions(root=None, notes=None):
    """Forskningsfrågor som går att arbeta med: aktiva, vilande och förslag."""
    found = _notes(root, "forskningsfråga", notes)
    return [q for q in found if q["fm"].get("status", "aktiv") in ("aktiv", "vilar", "förslag")]


def hypotheses(question_ref, root=None):
    return [h for h in _notes(root, "hypotes")
            if _same(link_target(h["fm"].get("fråga")), question_ref)]


def question(ref, root=None):
    """Frågan som ett projekt är kopplat till, eller None om den inte finns längre."""
    if not ref:
        return None
    return next((q for q in _notes(root, "forskningsfråga") if _same(ref, q["ref"])), None)


def note_path(project, root=None, project_id=None):
    """Projektets anteckning. Hittas på projektets ID, så att den följer med när projektet flyttas."""
    folder = Path(root or vault_root()) / EXPERIMENTMAPP
    project = Path(project).resolve()
    if project_id is None:
        try:
            project_id = json.loads((project / "projekt.json").read_text(encoding="utf-8")).get("id")
        except (OSError, ValueError):
            project_id = None
    taken = {}
    for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        try:
            fields, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        if project_id and fields.get("projekt_id") == project_id:
            return path
        taken[path.name] = fields.get("projekt")
    base, n = f"Projekt {project.name}", 1
    while True:
        name = f"{base}.md" if n == 1 else f"{base} {n}.md"
        if name not in taken or taken[name] == str(project):
            return folder / name
        n += 1


def projects_for(question_ref, root=None, notes=None):
    """Projekt i appen som prövar en fråga, från deras anteckningar i forskningsmappen."""
    return [e for e in _notes(root, "experiment", notes)
            if e["fm"].get("projekt") and _same(link_target(e["fm"].get("fråga")), question_ref)]


def app_uri(action, **params):
    """Länk som öppnar appen ForskarOS, till exempel från en anteckning i Obsidian."""
    from urllib.parse import urlencode
    return f"forskaros://{action}?" + urlencode({k: v for k, v in params.items() if v})


def _result_section(state):
    if not state["körningar"]:
        return ""
    last = state["körningar"][-1]
    report = Path(last["mapp"]) / "resultat" / "rapport.html"
    lines = [f'Senaste körning {last["namn"]}: {last["nivå"]}. {last["varför"]}',
             f"[Öppna rapporten]({report.as_uri()}) · "
             f'[Öppna projektet i appen ForskarOS]({app_uri("projekt", mapp=str(state["projekt"]))})', ""]
    claims = list(state["påståenden"].values())
    if claims:
        lines.append("Påståendena i manuset:")
        lines += [f'- {c["status"]}: {c["text"]}' for c in claims]
    return "\n".join(lines)


def _replace_section(body, heading, content):
    pattern = re.compile(rf"(^## {re.escape(heading)}\n)(.*?)(?=^## |\Z)", re.S | re.M)
    replacement = lambda m: m.group(1) + (content + "\n\n" if content else "\n")  # noqa: E731
    if pattern.search(body):
        return pattern.sub(replacement, body, count=1)
    return body.rstrip("\n") + f"\n\n## {heading}\n" + (content + "\n" if content else "")


def sync(project, state, manifest, root=None):
    """Skriv projektets läge till forskningsmappen. True om anteckningen ändrades.

    Gör ingenting för projekt som inte är kopplade till en forskningsfråga, eller
    när forskningsmappen saknas.
    """
    root = Path(root or vault_root())
    ref = manifest.get("fråga")
    if not ref or not root.is_dir():
        return False
    path = note_path(project, root, manifest.get("id"))
    old_text = path.read_text(encoding="utf-8") if path.is_file() else None
    fields, body = split_frontmatter(old_text) if old_text else ({}, None)
    hyp = manifest.get("hypotes")
    if body is None:
        body = (f"# Projekt {Path(project).name}\n\n"
                "## Vilken hypotes prövas?\n" + (f"[[{hyp}]]\n" if hyp else "\n") + "\n"
                "## Resultat\n\n"
                "## Vad betyder resultatet, och vad betyder det inte?\n\n")
        fields["datum"] = datetime.now(timezone.utc).date().isoformat()
    last = state["körningar"][-1] if state["körningar"] else None
    owned = {
        "typ": "experiment",
        "status": "genomfört" if last else "planerat",
        "fråga": f"[[{ref}]]",
        "hypotes": f"[[{hyp}]]" if hyp else None,
        "projekt": str(Path(project).resolve()),
        "projekt_id": manifest.get("id"),
        "medarbetare": ", ".join(manifest.get("medarbetare") or []) or None,
        "körning": Path(last["mapp"]).name if last else None,
        "nivå": last["nivå"] if last else None,
        "att_ompröva": sum(c["status"] in ("Ompröva", "Underlag saknas") for c in state["påståenden"].values()),
    }
    merged = {k: v for k, v in fields.items() if k not in ÄGDA}
    merged = {**{k: v for k, v in owned.items() if v is not None}, **merged}
    text = render_frontmatter(merged) + _replace_section(body, "Resultat", _result_section(state))
    if text == old_text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8", suffix=".tmp") as tmp:
        tmp.write(text)
    os.replace(tmp.name, path)
    return True


# Avsnitt ur hypotesen som visas i rapporten, i den ordning läsaren behöver dem.
FÖRUTSÄGELSE = [
    ("Hypotes (min formulering)", "Hypotesen"),
    ("Vilket etablerat antagande", "Antagandet som utmanas"),
    ("Prediktioner", "Förutsägelsen"),
    ("Falsifiering", "Det som skulle tala emot hypotesen"),
]


def _sections(body):
    out, current = {}, None
    for line in body.splitlines():
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            current = m.group(1).strip()
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return out


def _clean(lines):
    """Forskarens egen text: utan mallens hjälprader, tomma punkter och wikilänkar."""
    kept = []
    for line in lines:
        if line.lstrip().startswith(">") or re.fullmatch(r"\s*(?:[-*]|\d+\.)\s*", line):
            continue
        line = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", line)
        line = re.sub(r"\[\[([^\]]+)\]\]", lambda m: m.group(1).rsplit("/", 1)[-1], line)
        kept.append(line.replace("@", "\\@"))  # inga oavsiktliga källhänvisningar
    return "\n".join(kept).strip()


def prediction(manifest, root=None, when=None):
    """Hypotesen och förutsägelsen som de står i forskningsmappen nu, som Markdown för rapporten."""
    root = Path(root or vault_root())
    ref = manifest.get("hypotes")
    if not ref:
        return None
    path = root / f"{ref}.md"
    try:
        fields, body = split_frontmatter(path.read_text(encoding="utf-8"))
        changed = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    except OSError:
        return None
    sections = _sections(body)
    parts = []
    for prefix, heading in FÖRUTSÄGELSE:
        name = next((k for k in sections if k.startswith(prefix)), None)
        text = _clean(sections[name]) if name else ""
        if text and "\n" not in text:
            text = re.sub(r"^(?:[-*]|\d+\.)\s+", "", text)  # en ensam punkt läses som en mening
        if text:
            parts.append(f"**{heading}.** {text}" if "\n" not in text else f"**{heading}.**\n\n{text}")
    if not parts:
        return None
    q = question(manifest.get("fråga"), root)
    when = when or datetime.now(timezone.utc)
    title = q["titel"].rstrip(".") if q else ""
    stop = "" if title.endswith(("?", "!")) else "."
    origin = (f"Ur forskningsfrågan ”{title}”{stop} " if q else "") + (
        f"Hämtad ur forskningsmappen när analysen kördes {when:%Y-%m-%d %H:%M} UTC. "
        f"Hypotesen ändrades senast {changed:%Y-%m-%d %H:%M} UTC.")
    return ("::: {.forutsagelse}\n## Hypotesen som prövas {#forutsagelse}\n\n" + f"{origin}\n\n"
            + "\n\n".join(parts) + "\n:::\n")


def parse_app_uri(uri):
    """forskaros://projekt?mapp=… eller forskaros://nytt-projekt?fråga=…&hypotes=… som startval för appen."""
    from urllib.parse import parse_qs, urlsplit
    parts = urlsplit(uri)
    if parts.scheme != "forskaros":
        raise ValueError(f"Okänd länk: {uri}")
    query = {k: v[0] for k, v in parse_qs(parts.query).items()}
    if parts.netloc == "projekt" and query.get("mapp"):
        return {"projekt": query["mapp"]}
    if parts.netloc == "nytt-projekt":
        return {"nytt": {k: query[k] for k in ("fråga", "hypotes") if query.get(k)}}
    raise ValueError(f"Okänd länk: {uri}")


def obsidian_uri(ref, root=None):
    """Länk som öppnar en anteckning i Obsidian."""
    from urllib.parse import quote
    root = Path(root or vault_root())
    return f"obsidian://open?vault={quote(root.name)}&file={quote(ref + '.md')}"
