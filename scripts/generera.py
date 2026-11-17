#!/usr/bin/env python3
"""Genererar ForskarOS-filer från verktygskatalogen (katalog/verktyg.json).

Katalogen är den enda källan. Härifrån skapas:
  - verktygsprofiler        system_files/usr/share/forskaros/profiler/*.profil
  - startare för Python-verktyg  system_files/usr/share/forskaros/startare/*.desktop
  - programmenyn per fas    system_files/etc/dconf/db/local.d/02-forskaros-meny
  - verktygskort            vault/00 START/Verktyg/*.md

  python3 scripts/generera.py             skriv filerna
  python3 scripts/generera.py --kontroll  kontrollera att filerna är i synk (CI)
"""
import json
import sys
import tempfile
import filecmp
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KATALOG = ROOT / "katalog" / "verktyg.json"

PROFILDIR = Path("system_files/usr/share/forskaros/profiler")
STARTDIR = Path("system_files/usr/share/forskaros/startare")
MENYFIL = Path("system_files/etc/dconf/db/local.d/02-forskaros-meny")
KORTDIR = Path("vault/00 START/Verktyg")

FASNAMN = {
    "utforska": "Utforska", "kombinera": "Kombinera", "välj": "Välj", "pröva": "Pröva",
    "utveckla": "Utveckla", "ompröva": "Ompröva", "dela": "Dela",
}

# ForskarOS egna program, i en egen mapp först i menyn.
EGNA = ["forskaros-setup.desktop", "forskaros-handbok.desktop"]
# ForskarOS egna program som hör till en fas. Fokusläget hör till Välj: koncentration.
EGNA_PER_FAS = {"välj": ["forskaros-fokus.desktop"], "utveckla": ["forskaros-labb.desktop"]}


def desktop_ids(t):
    if t["typ"] == "flatpak":
        return t.get("desktop", [f'{t["id"]}.desktop'])
    if t["typ"] == "uv" and t.get("starta"):
        return [f'forskaros-{t["id"]}.desktop']
    if t["typ"] == "webb":
        return [f'forskaros-webb-{t["id"]}.desktop']
    return []  # kommandoradsverktyg syns inte i menyn


def profile_line(t):
    ident = f'{t["id"]}|{t["url"]}' if t["typ"] == "webb" else t["id"]
    return f'{t["typ"]:<8}{ident:<40}{t["namn"]} – {t["kort"]}'


def install_link(t):
    if t["typ"] == "flatpak":
        return f'https://flathub.org/apps/{t["id"]}'
    if t["typ"] == "brew":
        return f'https://formulae.brew.sh/formula/{t["id"]}'
    if t["typ"] == "uv":
        return f'https://pypi.org/project/{t["id"]}/'
    return t["url"]


def safe_filename(name):
    return "".join(c for c in name if c not in '\\/:*?"<>|#^[]').strip()


def generate(out: Path):
    kat = json.loads(KATALOG.read_text(encoding="utf-8"))
    faser = kat["faser"]
    profiler = {p["id"]: p for p in kat["profiler"]}
    verktyg = kat["verktyg"]
    fas_index = {f["id"]: i for i, f in enumerate(faser)}

    # Kontroller av katalogen.
    ids = [t["id"] for t in verktyg]
    assert len(ids) == len(set(ids)), "dubbla id i katalogen"
    for t in verktyg:
        assert t["profil"] in profiler, f'{t["id"]}: okänd profil {t["profil"]}'
        assert t["fas"] in fas_index, f'{t["id"]}: okänd fas {t["fas"]}'
        assert t["typ"] in ("flatpak", "brew", "uv", "webb"), f'{t["id"]}: okänd typ'
        if profiler[t["profil"]].get("aktivt_val"):
            assert not t.get("topp10"), f'{t["id"]}: aktivt val kan inte ingå i topp 10'
        if t["profil"] == "grund":
            assert t["typ"] == "flatpak", "grundprofilen installeras som Flatpak"
    assert sum(1 for t in verktyg if t.get("topp10")) == 10, "topp 10 ska ha exakt tio verktyg"

    # 1. Profiler.
    (out / PROFILDIR).mkdir(parents=True)
    for n, p in enumerate(kat["profiler"], start=1):
        members = [t for t in verktyg if (t.get("topp10") if p["id"] == "topp10" else t["profil"] == p["id"])]
        lines = [
            "# Genererad från katalog/verktyg.json. Ändra inte för hand.",
            f'# namn: {p["namn"]}',
            f'# beskrivning: {p["beskrivning"]}',
        ]
        if p.get("aktivt_val"):
            lines.append("# aktivt-val: ja")
        lines += [profile_line(t) for t in members]
        (out / PROFILDIR / f'{n:02d}-{p["id"]}.profil').write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 2. Startare för Python-verktyg (kopieras av forskaros-setup vid installation).
    (out / STARTDIR).mkdir(parents=True)
    for t in verktyg:
        if t["typ"] == "uv" and t.get("starta"):
            (out / STARTDIR / f'forskaros-{t["id"]}.desktop').write_text(
                "[Desktop Entry]\nType=Application\n"
                f'Name={t["namn"]}\nComment={t["kort"]}\n'
                f'Exec=@HOME@/.local/bin/{t["starta"]}\nTerminal=true\n'
                "Icon=applications-science\nCategories=Education;Science;\n",
                encoding="utf-8")

    # 3. Programmenyn: en mapp per fas i forskningscykeln.
    folders = [("forskaros-0", "ForskarOS", EGNA)]
    for i, f in enumerate(faser, start=1):
        apps = EGNA_PER_FAS.get(f["id"], []) + [d for t in verktyg if t["fas"] == f["id"] for d in desktop_ids(t)]
        assert apps, f'fasen {f["id"]} har inga program i menyn'

        folders.append((f"forskaros-{i}", f["mapp"], apps))
    meny = ["# Genererad från katalog/verktyg.json. Programmenyn följer forskningscykeln.",
            "[org/gnome/desktop/app-folders]",
            "folder-children=[" + ", ".join(f"'{fid}'" for fid, _, _ in folders) + "]", ""]
    for fid, name, apps in folders:
        meny += [f"[org/gnome/desktop/app-folders/folders/{fid}]",
                 f"name='{name}'",
                 "translate=false",
                 "apps=[" + ", ".join(f"'{a}'" for a in apps) + "]", ""]
    (out / MENYFIL).parent.mkdir(parents=True)
    (out / MENYFIL).write_text("\n".join(meny), encoding="utf-8")

    # 4. Verktygskort i vaulten.
    (out / KORTDIR).mkdir(parents=True)
    for t in verktyg:
        p = profiler[t["profil"]]
        fas = FASNAMN[t["fas"]]
        moln = " Det här är en molntjänst: det du skriver lämnar datorn." if t["typ"] == "webb" else ""
        card = [
            "---", "typ: verktygskort", f'fas: {t["fas"]}', f'profil: {t["profil"]}', "---",
            f'# {t["namn"]}', "",
            f'> {t["kort"]}', "",
            f'**Fas:** {fas_index[t["fas"]] + 1} · {fas}  ',
            f'**Profil:** {p["namn"]}' + ("  \n**Topp 10 för forskare**" if t.get("topp10") else ""), "",
            "## Hur det tjänar metoden", "", t["metod"] + moln, "",
            "## Installera", "",
            f'Öppna *ForskarOS – verktygslåda* och välj **{p["namn"]}**, eller kör:', "",
            "```bash", f'forskaros-setup --profil {t["profil"]}', "```", "",
            "## Läs mer", "",
            f'- [Dokumentation]({t["läs_mer"]})',
            f'- [Paketet]({install_link(t)})', "",
            "> Den här sidan uppdateras av systemet. Skriv egna erfarenheter i en egen anteckning.", "",
        ]
        (out / KORTDIR / f'{safe_filename(t["namn"])}.md').write_text("\n".join(card), encoding="utf-8")

    overview = ["---", "typ: verktygskort", "---", "# Verktygen per fas", "",
                "> Programmenyn har en mapp per fas i forskningscykeln, med samma verktyg som här.",
                "> Genererad från verktygskatalogen.", ""]
    for i, f in enumerate(faser, start=1):
        overview.append(f'## {f["mapp"]}')
        overview.append("")
        for t in verktyg:
            if t["fas"] == f["id"]:
                star = " ⭐" if t.get("topp10") else ""
                cloud = " ☁️" if t["typ"] == "webb" else ""
                overview.append(f'- [[00 START/Verktyg/{safe_filename(t["namn"])}|{t["namn"]}]]{star}{cloud}: {t["kort"]}')
        overview.append("")
    overview.append("⭐ = Topp 10 för forskare · ☁️ = molntjänst, aktivt val")
    (out / KORTDIR / "Översikt.md").write_text("\n".join(overview) + "\n", encoding="utf-8")


def tree(base: Path):
    return {p.relative_to(base) for p in base.rglob("*") if p.is_file()}


def main():
    check = "--kontroll" in sys.argv
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        generate(out)
        targets = [PROFILDIR, STARTDIR, KORTDIR]
        if check:
            bad = []
            for d in targets:
                want, have = tree(out / d), tree(ROOT / d) if (ROOT / d).exists() else set()
                bad += [f"{d}/{p}" for p in sorted(want ^ have)]
                bad += [f"{d}/{p}" for p in sorted(want & have) if not filecmp.cmp(out / d / p, ROOT / d / p, shallow=False)]
            if not (ROOT / MENYFIL).exists() or not filecmp.cmp(out / MENYFIL, ROOT / MENYFIL, shallow=False):
                bad.append(str(MENYFIL))
            if bad:
                print("Ej i synk med katalogen (kör python3 scripts/generera.py):\n  " + "\n  ".join(bad))
                sys.exit(1)
            print("OK: genererade filer är i synk med verktygskatalogen")
            return
        for d in targets:
            shutil.rmtree(ROOT / d, ignore_errors=True)
            shutil.copytree(out / d, ROOT / d)
        (ROOT / MENYFIL).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(out / MENYFIL, ROOT / MENYFIL)
        print("Genererat: profiler, startare, programmeny och verktygskort")


if __name__ == "__main__":
    main()
