#!/usr/bin/env python3
"""Genererar DegsellOS-filer från verktygskatalogen (katalog/verktyg.json).

Katalogen är den enda källan. Härifrån skapas:
  - verktygsprofiler        system_files/usr/share/degsellos/profiler/*.profil
  - startare för Python-verktyg  system_files/usr/share/degsellos/startare/*.desktop
  - programmenyn per fas    system_files/etc/dconf/db/local.d/02-degsellos-meny
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

PROFILDIR = Path("system_files/usr/share/degsellos/profiler")
STARTDIR = Path("system_files/usr/share/degsellos/startare")
MENYFIL = Path("system_files/etc/dconf/db/local.d/02-degsellos-meny")
KORTDIR = Path("vault/00 START/Verktyg")

FASNAMN = {
    "utforska": "Utforska", "kombinera": "Kombinera", "välj": "Välj", "pröva": "Pröva",
    "utveckla": "Utveckla", "ompröva": "Ompröva", "dela": "Dela",
}

# DegsellOS egna program, i en egen mapp först i menyn.
EGNA = ["io.github.jtensetti.DegsellOS.desktop", "degsellos-handbok.desktop"]
# DegsellOS egna program som hör till en fas. Fokusläget hör till Välj: koncentration.
EGNA_PER_FAS = {"välj": ["degsellos-fokus.desktop"], "utveckla": ["degsellos-labb.desktop"]}


def desktop_ids(t):
    if t["typ"] == "flatpak":
        return t.get("desktop", [f'{t["id"]}.desktop'])
    if t["typ"] == "uv" and t.get("starta"):
        return [f'degsellos-{t["id"]}.desktop']
    if t["typ"] == "webb":
        return [f'degsellos-webb-{t["id"]}.desktop']
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
            assert not t.get("rekommenderat"), f'{t["id"]}: aktivt val kan inte ingå i det rekommenderade urvalet'
        if t["profil"] == "grund":
            assert t["typ"] == "flatpak", "grundprofilen installeras som Flatpak"
    assert sum(1 for t in verktyg if t.get("rekommenderat")) == 10, "det rekommenderade urvalet ska ha tio verktyg"

    # 1. Profiler.
    (out / PROFILDIR).mkdir(parents=True)
    for n, p in enumerate(kat["profiler"], start=1):
        members = [t for t in verktyg if (t.get("rekommenderat") if p["id"] == "rekommenderat" else t["profil"] == p["id"])]
        lines = [
            "# Genererad från katalog/verktyg.json. Ändra inte för hand.",
            f'# namn: {p["namn"]}',
            f'# beskrivning: {p["beskrivning"]}',
        ]
        if p.get("aktivt_val"):
            assert p["aktivt_val"] in ("licens", "moln"), p["id"]
            lines.append(f'# aktivt-val: {p["aktivt_val"]}')
        lines += [profile_line(t) for t in members]
        (out / PROFILDIR / f'{n:02d}-{p["id"]}.profil').write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 2. Startare för Python-verktyg (kopieras av degsellos-setup vid installation).
    (out / STARTDIR).mkdir(parents=True)
    for t in verktyg:
        if t["typ"] == "uv" and t.get("starta"):
            (out / STARTDIR / f'degsellos-{t["id"]}.desktop').write_text(
                "[Desktop Entry]\nType=Application\n"
                f'Name={t["namn"]}\nComment={t["kort"]}\n'
                f'Exec=@HOME@/.local/bin/{t["starta"]}\nTerminal=true\n'
                "Icon=applications-science\nCategories=Education;Science;\n",
                encoding="utf-8")

    # 3. Programmenyn: en mapp per fas i forskningscykeln.
    folders = [("degsellos-0", "DegsellOS", EGNA)]
    for i, f in enumerate(faser, start=1):
        apps = EGNA_PER_FAS.get(f["id"], []) + [d for t in verktyg if t["fas"] == f["id"] for d in desktop_ids(t)]
        assert apps, f'fasen {f["id"]} har inga program i menyn'

        folders.append((f"degsellos-{i}", f["mapp"], apps))
    meny = ["# Genererad från katalog/verktyg.json.",
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
        moln = " Det du skriver skickas till tjänsten." if t["typ"] == "webb" else ""
        card = [
            "---", "typ: verktygskort", f'fas: {t["fas"]}', f'profil: {t["profil"]}', "---",
            f'# {t["namn"]}', "",
            f'> {t["kort"]}', "",
            f'**Fas:** {fas_index[t["fas"]] + 1} · {fas}  ',
            f'**Profil:** {p["namn"]}' + ("  \n**Ingår i det rekommenderade urvalet**" if t.get("rekommenderat") else ""), "",
            "## Vad det används till", "", t["metod"] + moln, "",
            "## Installera", "",
            f'Öppna appen *DegsellOS*, välj **Välj forskningsverktyg** och installera **{p["namn"]}**, eller kör:', "",
            "```bash", f'degsellos-setup --profil {t["profil"]}', "```", "",
            "## Läs mer", "",
            f'- [Dokumentation]({t["läs_mer"]})',
            f'- [Paketet]({install_link(t)})', "",
            "> Den här sidan uppdateras av systemet. Skriv egna erfarenheter i en egen anteckning.", "",
        ]
        (out / KORTDIR / f'{safe_filename(t["namn"])}.md').write_text("\n".join(card), encoding="utf-8")

    overview = ["---", "typ: verktygskort", "---", "# Verktygen per fas", "",
                "> Programmenyn har en mapp per fas med samma indelning.",
                "> Genererad från verktygskatalogen.", ""]
    for i, f in enumerate(faser, start=1):
        overview.append(f'## {f["mapp"]}')
        overview.append("")
        for t in verktyg:
            if t["fas"] == f["id"]:
                star = " (rekommenderad)" if t.get("rekommenderat") else ""
                cloud = " (molntjänst)" if t["typ"] == "webb" else ""
                overview.append(f'- [[00 START/Verktyg/{safe_filename(t["namn"])}|{t["namn"]}]]{star}{cloud}: {t["kort"]}')
        overview.append("")
    (out / KORTDIR / "Översikt.md").write_text("\n".join(overview) + "\n", encoding="utf-8")


CORE = Path("vault/.obsidian/plugins/degsellos-core/main.js")
# Arbetssätt som hör till varje fas, före programmen i panelens verktygsrad.
FASENS_ARBETE = {
    "utforska": ["perspektivkarta"],
    "kombinera": ["hypotes"],
    "välj": ["förregistrering (OSF)", "etikprövning", "fokusläge"],
    "pröva": ["motprov", "forskningsmöte"],
    "utveckla": ["appen DegsellOS", "labbet (R, Python)"],
    "ompröva": ["omprövning", "felrättning", "förmågegranskning"],
    "dela": ["rapporten", "Zenodo"],
}


def phase_tools(kat):
    """Panelens verktygsrad per fas: arbetssättet och programmen ur katalogen, utan molntjänster."""
    lines = ["const PHASE_TOOLS = {"]
    for i, fas in enumerate(f["id"] for f in kat["faser"]):
        tools = [t for t in kat["verktyg"] if t["fas"] == fas and t["typ"] != "webb"]
        tools.sort(key=lambda t: t["profil"] not in ("grund", "samarbete"))  # människor och grund först
        names = FASENS_ARBETE[fas] + [t["namn"] for t in tools]
        comma = "," if i < len(kat["faser"]) - 1 else ""
        lines.append(f"  {fas}: '{', '.join(names)}'{comma}")
    return "\n".join(lines + ["};"])


def with_phase_tools(source, kat):
    start = source.index("const PHASE_TOOLS = {")
    end = source.index("};", start) + 2
    return source[:start] + phase_tools(kat) + source[end:]


def tree(base: Path):
    return {p.relative_to(base) for p in base.rglob("*") if p.is_file()}


def main():
    check = "--kontroll" in sys.argv
    kat = json.loads(KATALOG.read_text(encoding="utf-8"))
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
            core = (ROOT / CORE).read_text(encoding="utf-8")
            if with_phase_tools(core, kat) != core:
                bad.append(str(CORE))
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
        core = (ROOT / CORE).read_text(encoding="utf-8")
        (ROOT / CORE).write_text(with_phase_tools(core, kat), encoding="utf-8")
        print("Genererat: profiler, startare, programmeny och verktygskort")


if __name__ == "__main__":
    main()
