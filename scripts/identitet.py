#!/usr/bin/env python3
"""Ritar DegsellOS identitet och utseende ur katalog/design.json.

  python3 scripts/identitet.py              skriv om filerna
  python3 scripts/identitet.py --kontroll   kontrollera att filerna är i synk

Skapar:
  - logotypen: forskningscykeln, sju bågar (en per fas) runt frågan
  - skrivbordsbakgrunder, ljus och mörk
  - typsnittsinställningar (fontconfig) för gränssnitt, läsning och kod
  - GNOME-inställningar: accentfärg, typsnitt och bakgrund (dconf)
  - Obsidians utseende i forskningsmappen
  - färger och typsnitt överst i rapportens stilmall
"""
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
DESIGN = json.loads((ROOT / "katalog/design.json").read_text(encoding="utf-8"))
IDENTITET = "system_files/usr/share/degsellos/identitet"
INSTALLERAD = "/usr/share/degsellos/identitet"
TYPSNITTSFIL = "52-degsellos-typsnitt.conf"
RAPPORT = "system_files/usr/share/degsellos/projekt/mallar/gemensamt/rapport.css"
START, SLUT = "/* designvärden: början */", "/* designvärden: slut */"
GENERERAD = "Genererad av scripts/identitet.py från katalog/design.json. Ändra inte för hand."

FASER = [f["namn"] for f in DESIGN["faser"]]
FASFÄRGER = [f["färg"] for f in DESIGN["faser"]]
YTOR, TYP = DESIGN["ytor"], DESIGN["typsnitt"]
# GNOME:s accentfärger (libadwaita 1.6 och senare). Bara dessa namn går att välja i Inställningar.
GNOME_ACCENTER = {"blue", "teal", "green", "yellow", "orange", "red", "pink", "purple", "slate"}


def arc(cx, cy, r, a0, a1):
    p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0))
    p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
    large = 1 if (a1 - a0) > math.pi else 0
    return f"M {p0[0]:.2f} {p0[1]:.2f} A {r} {r} 0 {large} 1 {p1[0]:.2f} {p1[1]:.2f}"


def ring(cx, cy, r, width, gap_deg=7, opacity=1.0):
    """Sju bågar, en per fas, medurs från Utforska högst upp."""
    parts = []
    step = 2 * math.pi / 7
    gap = math.radians(gap_deg)
    for i, color in enumerate(FASFÄRGER):
        a0 = -math.pi / 2 + i * step + gap / 2
        a1 = a0 + step - gap
        parts.append(f'<path d="{arc(cx, cy, r, a0, a1)}" fill="none" stroke="{color}" '
                     f'stroke-width="{width}" stroke-linecap="round" opacity="{opacity}"><title>{FASER[i]}</title></path>')
    return "\n  ".join(parts)


def logo():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <title>DegsellOS</title>
  {ring(128, 128, 92, 22)}
  <circle cx="128" cy="128" r="19.8" fill="{YTOR['skrivbord']['ljus']}" stroke="{YTOR['text']['ljus']}" stroke-width="4.8"/>
</svg>
"""


def wallpaper(mode):
    """Lugn yta i papperston. Cykeln stor och lätt, förskjuten från mitten så att fönster och docka får plats."""
    w, h = 3840, 2160
    cx, cy, r = w * 0.64, h * 0.56, h * 0.36
    opacity = 0.62 if mode == "mörk" else 0.55
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <title>DegsellOS</title>
  <rect width="{w}" height="{h}" fill="{YTOR['skrivbord'][mode]}"/>
  {ring(cx, cy, round(r), 30, gap_deg=6, opacity=opacity)}
  <circle cx="{cx:.0f}" cy="{cy:.0f}" r="24" fill="{YTOR['text'][mode]}" opacity="0.6"/>
</svg>
"""


def fontconfig():
    def alias(generic, role):
        return (f"  <alias binding=\"same\">\n    <family>{generic}</family>\n"
                f"    <prefer><family>{TYP[role]['familj']}</family></prefer>\n  </alias>")
    return "\n".join([
        '<?xml version="1.0"?>',
        '<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">',
        f"<!-- {GENERERAD}",
        "     Nummer 52: efter användarens egna inställningar (50), före systemets standardval (56 och uppåt). -->",
        "<fontconfig>",
        "  <description>DegsellOS: typsnitt för gränssnitt, läsning och kod</description>",
        alias("sans-serif", "gränssnitt"),
        alias("system-ui", "gränssnitt"),
        alias("serif", "läsning"),
        alias("monospace", "kod"),
        "</fontconfig>",
        ""])


def dconf():
    def font(role):
        return f"{TYP[role]['familj']} {TYP[role]['storlek']}"
    return f"""# {GENERERAD}
# Utseende för hela skrivbordet. Forskaren kan ändra allt i Inställningar.

[org/gnome/desktop/interface]
accent-color='{DESIGN['accent']['gnome']}'
font-name='{font('gränssnitt')}'
document-font-name='{font('läsning')}'
monospace-font-name='{font('kod')}'

[org/gnome/desktop/background]
picture-uri='file://{INSTALLERAD}/degsellos-bakgrund-ljus.svg'
picture-uri-dark='file://{INSTALLERAD}/degsellos-bakgrund-mork.svg'
picture-options='zoom'
primary-color='{YTOR['skrivbord']['ljus']}'

[org/gnome/desktop/screensaver]
picture-uri='file://{INSTALLERAD}/degsellos-bakgrund-mork.svg'
primary-color='{YTOR['skrivbord']['mörk']}'
"""


def obsidian():
    appearance = {
        "accentColor": DESIGN["accent"]["gnome_hex"],
        "theme": "system",
        "interfaceFontFamily": TYP["gränssnitt"]["familj"],
        "textFontFamily": TYP["gränssnitt"]["familj"],
        "monospaceFontFamily": TYP["kod"]["familj"],
        "baseFontSize": 16,
    }
    return json.dumps(appearance, ensure_ascii=False, indent=2) + "\n"


def stack(role):
    names = [TYP[role]["familj"], *TYP[role]["reserv"]]
    generic = {"serif", "sans-serif", "monospace", "system-ui", "ui-monospace"}
    return ", ".join(n if n in generic else f'"{n}"' for n in names)


def report_tokens():
    names = {"papper": "papper", "text": "text", "dämpad": "dampad", "linje": "linje", "upphöjd": "yta"}

    def block(mode, indent):
        pad = " " * indent
        lines = [f"{pad}--{css}: {YTOR[key][mode]};" for key, css in names.items()]
        lines.append(f"{pad}--accent: {DESIGN['accent']['text'][mode]};")
        lines += [f"{pad}--{key}: {value[mode]};" for key, value in DESIGN["status"].items()]
        return "\n".join(lines)
    return f"""{START}
/* {GENERERAD} */
:root {{
  color-scheme: light dark;
  --lasning: {stack('läsning')};
  --granssnitt: {stack('gränssnitt')};
  --kod: {stack('kod')};
{block('ljus', 2)}
}}

@media (prefers-color-scheme: dark) {{
  :root {{
{block('mörk', 4)}
  }}
}}
{SLUT}"""


def with_report_tokens(css):
    if START not in css or SLUT not in css:
        raise SystemExit(f"{RAPPORT} saknar markeringarna för designvärden")
    head, rest = css.split(START, 1)
    return head + report_tokens() + rest.split(SLUT, 1)[1]


def outputs():
    files = {
        f"{IDENTITET}/degsellos-logotyp.svg": logo(),
        f"{IDENTITET}/degsellos-bakgrund-ljus.svg": wallpaper("ljus"),
        f"{IDENTITET}/degsellos-bakgrund-mork.svg": wallpaper("mörk"),
        f"{IDENTITET}/{TYPSNITTSFIL}": fontconfig(),
        "system_files/etc/dconf/db/local.d/03-degsellos-utseende": dconf(),
        "vault/.obsidian/appearance.json": obsidian(),
    }
    files[RAPPORT] = with_report_tokens((ROOT / RAPPORT).read_text(encoding="utf-8"))
    return files


def main(argv):
    if DESIGN["accent"]["gnome"] not in GNOME_ACCENTER:
        raise SystemExit(f'Accentfärgen måste vara en av GNOME:s: {", ".join(sorted(GNOME_ACCENTER))}')
    stale = []
    for name, content in outputs().items():
        path = ROOT / name
        if "--kontroll" in argv:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if stale:
        raise SystemExit("Inte i synk med katalog/design.json (kör python3 scripts/identitet.py): " + ", ".join(stale))
    print("OK: identitet och utseende är i synk med katalog/design.json" if "--kontroll" in argv
          else "Skapade identitet och utseende ur katalog/design.json")


if __name__ == "__main__":
    main(sys.argv[1:])
