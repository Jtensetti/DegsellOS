"""Läs en vald PDF-markering från Zotero på den här datorn."""
from http.client import HTTPConnection
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import parse_qs

from belagg import bib_entries, locked, source_path


def annotation_link(text):
    """Quick Copy kan innehålla både citatet, en referenslänk och en PDF-länk."""
    links = re.findall(r"zotero://open-pdf/(library|groups/[0-9]+)/items/([A-Z0-9]{8})\?([^\s)<>\"]+)", text)
    found = set()
    for library, attachment, query in links:
        for annotation in parse_qs(query).get("annotation", []):
            if re.fullmatch(r"[A-Z0-9]{8}", annotation):
                found.add((library, attachment, annotation))
    if len(found) != 1:
        raise ValueError("Kopiera en PDF-markering i Zotero med Zotero-länkar aktiverade under Export.")
    return found.pop()


def local_json(path):
    # Direkt anslutning utan proxy eller omdirigering.
    connection = HTTPConnection("127.0.0.1", 23119, timeout=5)
    try:
        connection.request("GET", "/api/" + path, headers={"Zotero-API-Version": "3"})
        response = connection.getresponse()
        if response.status == 403:
            raise ValueError("Tillåt lokala program att kommunicera med Zotero under Inställningar → Avancerat.")
        if response.status == 404:
            raise ValueError("Markeringen eller referensen finns inte i det lokala Zotero-biblioteket.")
        if response.status != 200:
            raise ValueError(f"Zotero svarade med HTTP {response.status}.")
        return json.loads(response.read())
    except OSError as error:
        raise ValueError("Kunde inte nå Zotero. Starta Zotero och tillåt kommunikation under Inställningar → Avancerat.") from error
    finally:
        connection.close()


def read_annotation(text, read=local_json):
    library, attachment_key, annotation_key = annotation_link(text)
    base = ("users/0" if library == "library" else library) + "/items/"
    annotation = read(base + annotation_key)["data"]
    if annotation.get("itemType") != "annotation" or annotation.get("parentItem") != attachment_key:
        raise ValueError("Markeringen hör inte till PDF-filen i länken.")
    quote = annotation.get("annotationText", "").strip()
    if not quote:
        raise ValueError("Välj en markering som innehåller text.")
    attachment = read(base + attachment_key)["data"]
    parent = attachment.get("parentItem", "")
    if attachment.get("itemType") != "attachment" or not re.fullmatch(r"[A-Z0-9]{8}", parent):
        raise ValueError("Koppla PDF-filen till en bibliografisk post i Zotero först.")
    item = read(base + parent)
    data = item["data"]
    if not data.get("title"):
        raise ValueError("Referensen saknar titel i Zotero.")
    key = f"zotero-{library.replace('/', '-')}-{parent}"
    # Läs bibliografiska fält ur samma lokala svar som identifierar posten.
    types = {"journalArticle": "article-journal", "magazineArticle": "article-magazine",
             "newspaperArticle": "article-newspaper", "bookSection": "chapter",
             "conferencePaper": "paper-conference", "book": "book", "thesis": "thesis",
             "report": "report", "webpage": "webpage", "manuscript": "manuscript"}
    # "und" gör att Pandoc behåller titelns versaler även när språket är okänt.
    source = {"id": key, "type": types.get(data["itemType"], "document"), "title": data["title"], "language": "und"}
    for field, target in (("publicationTitle", "container-title"), ("bookTitle", "container-title"),
                          ("proceedingsTitle", "container-title"), ("university", "publisher"),
                          ("institution", "publisher"), ("publisher", "publisher"), ("place", "publisher-place"),
                          ("volume", "volume"), ("issue", "issue"), ("pages", "page"), ("edition", "edition"),
                          ("DOI", "DOI"), ("ISBN", "ISBN"), ("ISSN", "ISSN"), ("url", "URL")):
        if data.get(field):
            source[target] = data[field]
    for creator in data.get("creators", []):
        role = creator["creatorType"]
        if role in ("author", "editor", "translator"):
            name = ({"literal": creator["name"]} if creator.get("name")
                    else {"family": creator["lastName"], "given": creator.get("firstName", "")})
            source.setdefault(role, []).append(name)
    date = item.get("meta", {}).get("parsedDate") or data.get("date")
    if date:
        source["issued"] = {"literal": date}
    result = subprocess.run(["pandoc", "--from=csljson", "--to=bibtex"], input=json.dumps([source]),
                            capture_output=True, text=True, check=True)
    return {"källa": key, "titel": source["title"], "citat": quote, "sida": annotation.get("annotationPageLabel") or "",
            "bibtex": result.stdout.strip()}


def import_reference(folder, annotation):
    """Lägg till referensen en gång. Andra poster i projektet ska bevaras."""
    path = source_path(folder, "kallor.bib")
    with locked(folder), tempfile.NamedTemporaryFile(mode="w", dir=folder, encoding="utf-8", delete=False) as stream:
        tmp = Path(stream.name)
        try:
            stream.write(annotation["bibtex"] + "\n")
            stream.flush()
            key = annotation["källa"]
            imported = bib_entries(tmp)[key]
            existing = bib_entries(path)
            if key in existing and existing[key] != imported:
                raise ValueError(f"Referensen {key} finns med andra uppgifter. Kontrollera kallor.bib innan du importerar den igen.")
            for known_key, entry in existing.items():
                if entry == imported:
                    return known_key
            previous = path.read_text(encoding="utf-8-sig") if path.exists() else ""
            stream.seek(0)
            stream.truncate()
            stream.write((previous.rstrip() + "\n\n" if previous.strip() else "") + annotation["bibtex"] + "\n")
            stream.flush()
            os.replace(tmp, path)
            return key
        finally:
            tmp.unlink(missing_ok=True)
