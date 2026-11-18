"""Kopiera en Zotero-markering till projektet och bygg en rapport med citatet."""
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "system_files/usr/share/forskaros/projekt"))
from belagg import add_source, bib_entries, inspect
from projekt import create, run
from zotero import annotation_link, import_reference, read_annotation


link = "zotero://open-pdf/groups/123/items/ATTACH22?page=7&annotation=HIGHL222"
copied = f"»Fel slutsats.« ([Källa](zotero://select/groups/123/items/PARENT22)) ([pdf]({link}))"
api = {
    "groups/123/items/HIGHL222": {"data": {"itemType": "annotation", "parentItem": "ATTACH22",
                                           "annotationText": "Den nya mätningen avvek.", "annotationPageLabel": "vii"}},
    "groups/123/items/ATTACH22": {"data": {"itemType": "attachment", "parentItem": "PARENT22"}},
    "groups/123/items/PARENT22": {"data": {"itemType": "book", "title": "Skolans nya mätserier",
        "creators": [{"creatorType": "author", "lastName": "Lind", "firstName": "Eva"}],
        "date": "2026", "extra": "Projektintern anteckning"}},
}

source = read_annotation(copied, api.__getitem__)
assert source["sida"] == "vii" and source["citat"] == "Den nya mätningen avvek."
assert annotation_link(link.replace("groups/123", "library"))[0] == "library"
for invalid in ("zotero://select/library/items/PARENT22", link + " " + link.replace("HIGHL222", "HIGHL333")):
    try:
        annotation_link(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Ogiltig eller tvetydig markering accepterades")

with tempfile.TemporaryDirectory() as tmp:
    project = create("kvantitativ", Path(tmp) / "Källprov")
    folder = project / "underlag"
    bib = folder / "kallor.bib"
    original = bib.read_text()
    key = import_reference(folder, source)
    after = bib.read_text()
    assert original.strip() in after and "Projektintern anteckning" not in after
    assert bib_entries(bib)[key][0]["author"] == "Lind, Eva"
    assert import_reference(folder, source) == key and bib.read_text() == after
    add_source(folder, "konkurrerande", {"källa": key, "sida": "s. vii", "citat": source["citat"], "roll": "motbelägg"})
    with (folder / "manus.md").open("a") as stream:
        stream.write("\n[En ny mätning motsade den första.](#belagg-konkurrerande)\n")
    claim = inspect(folder)["konkurrerande"]
    assert claim["status"] == "Ej granskad" and claim["underlag"][0]["titel"] == "Skolans nya mätserier"
    report = (run(project) / "resultat/rapport.html").read_text()
    assert "Den nya mätningen avvek." in report and "s. vii" in report and "Skolans nya mätserier" in report
    try:
        import_reference(folder, dict(source, bibtex=source["bibtex"].replace("Skolans nya mätserier", "Annan bok")))
    except ValueError:
        pass
    else:
        raise AssertionError("En befintlig referens skrevs över")
    assert bib.read_text() == after

print("OK: vald Zotero-markering, referens, sida, citat, omimport och rapport")
