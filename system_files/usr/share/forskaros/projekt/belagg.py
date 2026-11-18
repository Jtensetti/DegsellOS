"""Uttryckliga samband mellan manusets påståenden och projektets underlag."""
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import hashlib
from html import escape
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import quote


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def text_of(node):
    if isinstance(node, list):
        return "".join(map(text_of, node))
    if not isinstance(node, dict):
        return ""
    kind, content = node.get("t"), node.get("c")
    if kind == "Str":
        return content
    if kind in ("Code", "Math"):
        return content[1]
    if kind in ("Space", "SoftBreak", "LineBreak"):
        return " "
    return text_of(content)


def claim_links(manus):
    proc = subprocess.run(["pandoc", "-f", "markdown", "-t", "json", str(manus)],
                          capture_output=True, text=True, check=True)
    links = {}

    def visit(node):
        if isinstance(node, list):
            for item in node:
                visit(item)
        elif isinstance(node, dict):
            value = node.get("c")
            if node.get("t") == "Link" and value[2][0].startswith("#belagg-"):
                key = value[2][0][len("#belagg-"):]
                if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", key):
                    raise ValueError(f"Ogiltigt belägg-ID i manus.md: {key}")
                statement = text_of(value[1]).strip()
                if not statement or (key in links and links[key] != statement):
                    raise ValueError(f"Använd ett eget belägg-ID för varje påstående: {key}")
                links[key] = statement
            else:
                visit(value)
    visit(json.loads(proc.stdout)["blocks"])
    return links


def source_path(folder, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError(f"Ange en relativ fil i underlag/: {name}")
    path = folder / name
    if folder.is_symlink() or any(p.is_symlink() for p in (path, *path.parents) if p == folder or folder in p.parents):
        raise ValueError(f"Länk tillåts inte som underlag: {name}")
    return path


def read_json(path):
    if path.is_symlink():
        raise ValueError(f"Använd en vanlig fil: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(text):
    return " ".join(text.split())


# Fält som identifierar källan. Ändras de behöver kopplade påståenden omprövas.
# Andra fält (fil, sammanfattning, nyckelord) ändras ofta vid ny export.
KALLFALT = ("author", "editor", "title", "year", "date", "journal", "journaltitle", "booktitle",
            "publisher", "volume", "number", "pages", "edition", "doi", "url", "isbn")


def bib_value(body, name):
    match = re.search(r"(?:^|[,{\s])" + name + r"\s*=\s*", body, re.I)
    if not match:
        return None
    rest = body[match.end():]
    if rest.startswith("{"):
        depth = 0
        for index, char in enumerate(rest):
            depth += {"{": 1, "}": -1}.get(char, 0)
            if depth == 0:
                return normalized(rest[1:index])
    if rest.startswith('"'):
        end = rest.find('"', 1)
        return normalized(rest[1:end]) if end > 0 else None
    word = re.match(r"[^,}\s]+", rest)
    return word.group(0) if word else None


def bib_entries(path):
    """BibTeX-poster (som Zotero exporterar dem): nyckel -> (identifierande fält, titel)."""
    text = path.read_text(encoding="utf-8-sig") if path.is_file() and not path.is_symlink() else ""
    entries = {}
    for match in re.finditer(r"@\s*([A-Za-z]+)\s*\{\s*([^,\s]+)\s*,", text):
        if match.group(1).lower() in ("comment", "preamble", "string"):
            continue
        depth, end = 0, None
        for index in range(text.index("{", match.start()), len(text)):
            depth += {"{": 1, "}": -1}.get(text[index], 0)
            if depth == 0:
                end = index
                break
        if end is None:
            raise ValueError(f"Ofullständig BibTeX-post: {match.group(2)}")
        body = text[match.end():end]
        fields = {name: value for name in KALLFALT if (value := bib_value(body, name)) is not None}
        fields["typ"] = match.group(1).lower()
        title = (fields.get("title") or "").replace("{", "").replace("}", "")
        entries[match.group(2)] = (fields, title)
    return entries


def passage(folder, spec, item):
    """En markerad passage i en källa: BibTeX-nyckel, sida och ordagrant citat."""
    key, quote = spec["källa"], spec.get("citat", "")
    if not isinstance(key, str) or not key or not isinstance(quote, str) or not quote.strip():
        raise ValueError(f"Ange källans BibTeX-nyckel och citatet ur källan för {key}.")
    entries = bib_entries(folder / "kallor.bib")
    if key not in entries:
        item["fel"] = f"Källan {key} saknas i kallor.bib"
        return item
    item["post"], item["titel"] = entries[key]
    if "fil" in spec:
        # Har forskaren lagt källans text i projektet kontrolleras att citatet står där.
        path = source_path(folder, spec["fil"])
        if not path.is_file():
            item["fel"] = f"Källtexten {spec['fil']} saknas"
        elif normalized(quote) not in normalized(path.read_text(encoding="utf-8-sig", errors="replace")):
            item["fel"] = f"Citatet finns inte i {spec['fil']}"
    return item


def evidence(folder, spec):
    role = spec["roll"]
    if role not in ("stöd", "motbelägg", "metod"):
        raise ValueError(f"Okänd roll för belägg: {role}")
    if "källa" in spec:
        return passage(folder, spec, {"spec": spec, "rader": [], "fel": ""})
    path = source_path(folder, spec["fil"])
    item = {"spec": spec, "rader": [], "fel": ""}
    if not path.is_file():
        item["fel"] = "Filen saknas"
        return item
    if "urval" not in spec and "kolumner" not in spec:
        with path.open("rb") as stream:
            fingerprint = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                fingerprint.update(chunk)
        item["sha256"] = fingerprint.hexdigest()
        return item
    match, fields = spec["urval"], spec["kolumner"]
    if not isinstance(match, dict) or not isinstance(fields, list) or not fields or not all(
            isinstance(v, str) for v in [*match, *match.values(), *fields]):
        raise ValueError(f"Kontrollera urval och kolumner för {path.name}.")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        header = stream.readline()
        stream.seek(0)
        reader = csv.DictReader(stream, delimiter=";" if ";" in header and "," not in header else ",")
        missing = (set(match) | set(fields)) - set(reader.fieldnames or ())
        if missing:
            item["fel"] = "Kolumner saknas: " + ", ".join(sorted(missing))
            return item
        for row in reader:
            if None in row or any(row[k] is None for k in (*match, *fields)):
                raise ValueError(f"Fel antal CSV-fält i {path.name} på rad {reader.line_num}.")
            if all(row[k] == v for k, v in match.items()):
                item["rader"].append([row[k] for k in fields])
    item["rader"].sort()  # Ordningen från kalkylprogrammet påverkar inte det deklarerade urvalet.
    if not item["rader"]:
        item["fel"] = "Urvalet saknar träffar"
    return item


def source_label(spec):
    if "källa" in spec:
        page = f' · {spec["sida"]}' if spec.get("sida") else ""
        return f'{spec["roll"].capitalize()} · källa {spec["källa"]}{page}'
    condition = ", ".join(f"{k}={v}" for k, v in sorted(spec.get("urval", {}).items()))
    return f'{spec["roll"].capitalize()} · {spec["fil"]}' + (f" · {condition}" if condition else "")


def inspect(folder):
    config_file = folder / "belagg.json"
    if not config_file.exists():
        manus = folder / "manus.md"
        if "#belagg-" in manus.read_text(encoding="utf-8") and claim_links(manus):
            raise ValueError("Manuset länkar till belägg men belagg.json saknas.")
        return {}
    config = read_json(config_file)
    if config.get("format") != 1 or not isinstance(config.get("påståenden"), dict):
        raise ValueError("Okänt format i belagg.json.")
    reviews_file = folder / "granskningar.json"
    reviews = read_json(reviews_file) if reviews_file.exists() else {}
    claims = {}
    for key, title in claim_links(folder / "manus.md").items():
        if key not in config["påståenden"]:
            raise ValueError(f"Påståendet {key} i manus.md saknar definition i belagg.json.")
        definition = config["påståenden"][key]
        if not isinstance(definition.get("underlag"), list) or not definition["underlag"]:
            raise ValueError(f"Ange minst ett underlag för {key}.")
        sources = [evidence(folder, spec) for spec in definition["underlag"]]
        components = {"Påståendets lydelse": digest(title),
                      "Forskarens kommentar": digest(definition.get("kommentar", ""))}
        # Skilda urval och roller jämförs separat. Behåll även flera poster med samma namn.
        grouped = {}
        for item in sources:
            grouped.setdefault(source_label(item["spec"]), []).append(digest(item))
        components.update({name: digest(sorted(values)) for name, values in grouped.items()})
        stamp = digest(components)
        prior = reviews.get(key)
        changes = [] if not prior else sorted(k for k in components.keys() | prior["delar"].keys()
                                              if components.get(k) != prior["delar"].get(k))
        if any(s["fel"] for s in sources):
            state = "Underlag saknas"
        elif prior is None:
            state = "Ej granskad"
        else:
            state = "Ompröva" if changes else "Granskad"
        claims[key] = dict(id=key, text=title, kommentar=definition.get("kommentar", ""),
                           underlag=sources, status=state, ändrat=changes, delar=components,
                           avtryck=stamp, tidigare=prior)
    return claims


@contextmanager
def locked(folder):
    import fcntl  # Projektredigering körs på Linux. Den flyttbara rapporten behöver inget fillås.
    # Lås katalogen, inte den fil som byts atomärt.
    fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def save_json(path, value):
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, encoding="utf-8", delete=False) as stream:
        tmp = Path(stream.name)
        try:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(tmp, path)
        finally:
            tmp.unlink(missing_ok=True)


def approve(folder, key, stamp):
    with locked(folder):
        claims = inspect(folder)
        if key not in claims:
            raise ValueError(f"Okänt påstående: {key}")
        claim = claims[key]
        if stamp != claim["avtryck"]:
            raise ValueError("Underlaget har ändrats sedan visningen. Läs det igen före granskning.")
        if claim["status"] == "Underlag saknas":
            raise ValueError("Komplettera det saknade underlaget före granskning.")
        path = folder / "granskningar.json"
        reviews = read_json(path) if path.exists() else {}
        reviews[key] = {"tid": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "delar": claim["delar"]}
        save_json(path, reviews)


def source_choices(folder):
    """Vanliga överlämningar från Calc och Taguette, samt övriga vanliga projektfiler."""
    choices = []
    data = source_path(folder, "data.csv")
    if data.is_file():
        with data.open(encoding="utf-8-sig", newline="") as stream:
            first = stream.readline()
            stream.seek(0)
            reader = csv.DictReader(stream, delimiter=";" if ";" in first and "," not in first else ",")
            fields = reader.fieldnames or []
            if {"villkor", "bytte_hypotes"} <= set(fields):
                keys, columns = ["villkor"], ["villkor", "bytte_hypotes"]
            elif {"id", "document", "tag", "content"} <= set(fields):
                keys, columns = ["document", "id"], ["document", "id", "tag", "content"]
            else:
                keys, columns = [], []
            if keys:
                matches = {tuple(row[k] for k in keys) for row in reader if all(row.get(k) for k in keys)}
                for values in sorted(matches):
                    spec = {"fil": "data.csv", "urval": dict(zip(keys, values)), "kolumner": columns}
                    choices.append((" · ".join(f"{k}={v}" for k, v in zip(keys, values)), spec))
    for key, (_, title) in bib_entries(folder / "kallor.bib").items():
        choices.append((f"Källpassage · {key}" + (f" · {title}" if title else ""), {"källa": key}))
    for file in sorted(folder.rglob("*")):
        name = file.relative_to(folder).as_posix()
        if file.is_file() and not file.is_symlink() and name not in ("belagg.json", "granskningar.json"):
            choices.append((f"Hela filen · {name}", {"fil": name}))
    return choices


def add_source(folder, key, spec):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", key):
        raise ValueError("Använd bokstäver a–z, siffror och bindestreck i påståendets ID.")
    with locked(folder):
        item = evidence(folder, spec)
        if item["fel"]:
            raise ValueError(item["fel"])
        path = folder / "belagg.json"
        config = read_json(path) if path.exists() else {"format": 1, "påståenden": {}}
        if config.get("format") != 1:
            raise ValueError("Okänt format i belagg.json.")
        claim = config["påståenden"].setdefault(key, {"underlag": []})
        if spec not in claim["underlag"]:
            claim["underlag"].append(spec)
            save_json(path, config)


def detail(claim):
    lines = [claim["text"], claim["status"]]
    if claim["tidigare"]:
        lines.append("Senast granskat: " + claim["tidigare"]["tid"])
    if claim["ändrat"]:
        lines.append("Ändrat sedan granskningen: " + "; ".join(claim["ändrat"]))
    if claim["kommentar"]:
        lines.append(claim["kommentar"])
    for item in claim["underlag"]:
        spec = item["spec"]
        lines.extend(["", source_label(spec)])
        if item["fel"]:
            lines.append(item["fel"])
        elif "källa" in spec:
            lines.append(item.get("titel") or spec["källa"])
            lines.append("»" + normalized(spec["citat"]) + "«")
            if "fil" in spec:
                lines.append(f'Citatet finns i {spec["fil"]}.')
        elif "sha256" in item:
            lines.append("Hela filen · SHA-256 " + item["sha256"])
        else:
            lines.append(f'{len(item["rader"])} matchande rader')
            content = io.StringIO()
            writer = csv.writer(content, delimiter="\t", lineterminator="\n")
            writer.writerow(spec["kolumner"])
            writer.writerows(item["rader"][:40])
            lines.append(content.getvalue().rstrip("\n"))
            if len(item["rader"]) > 40:
                lines.append("De första 40 visas. Hela urvalet ingår i kontrollen.")
    return "\n".join(lines)


def appendix(claims):
    parts = ['<section aria-label="Belägg"><h2>Belägg och omprövning</h2>',
             '<p>Bedömningarna gäller det underlag som sparades i den här körningen.</p>']
    for key, claim in claims.items():
        parts.append(f'<section id="belagg-{key}"><h3>{escape(claim["text"])}</h3>'
                     f'<p><strong>{escape(claim["status"])}</strong></p>')
        if claim["tidigare"]:
            parts.append(f'<p>Senast granskat: {escape(claim["tidigare"]["tid"])}</p>')
        if claim["ändrat"]:
            parts.append('<p>Ändrat sedan granskningen: ' + escape("; ".join(claim["ändrat"])) + '</p>')
        if claim["kommentar"]:
            parts.append(f'<p>{escape(claim["kommentar"])}</p>')
        for item in claim["underlag"]:
            spec = item["spec"]
            parts.append(f'<h4>{escape(source_label(spec))}</h4>')
            if item["fel"]:
                parts.append(f'<p>{escape(item["fel"])}</p>')
            elif "källa" in spec:
                parts.append(f'<blockquote>{escape(normalized(spec["citat"]))}</blockquote>'
                             f'<p>{escape(item.get("titel") or spec["källa"])}'
                             + (f', {escape(spec["sida"])}' if spec.get("sida") else "") + '</p>')
            elif "sha256" in item:
                parts.append(f'<p>SHA-256 <code>{item["sha256"]}</code></p>')
            else:
                parts.append(f'<p>{len(item["rader"])} matchande rader.</p><table><thead><tr>')
                parts.extend(f'<th scope="col">{escape(col)}</th>' for col in spec["kolumner"])
                parts.append('</tr></thead><tbody>')
                for row in item["rader"][:40]:
                    parts.append('<tr>' + ''.join(f'<td>{escape(cell)}</td>' for cell in row) + '</tr>')
                parts.append('</tbody></table>')
                if len(item["rader"]) > 40:
                    parts.append('<p>De första 40 visas. Hela urvalet ingår i kontrollen.</p>')
            if not item["fel"] and "fil" in spec:
                url = escape(quote(spec["fil"]), quote=True)
                parts.append(f'<p><a href="../underlag/{url}">Öppna {escape(spec["fil"])} i körningsmappen</a></p>')
        parts.append('</section>')
    return "\n".join([*parts, '</section>'])
