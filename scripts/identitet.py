#!/usr/bin/env python3
"""Ritar DegsellOS identitet och utseende ur katalog/design.json.

  python3 scripts/identitet.py              skriv om filerna
  python3 scripts/identitet.py --kontroll   kontrollera att filerna är i synk

Skapar:
  - logotypen för ljus och mörk bakgrund, ur katalog/logotyp.svg
  - symbolen: programikon och menyknappen uppe till vänster
  - skrivbordsbakgrunder, ljus och mörk, med logotypen
  - typsnittsinställningar (fontconfig) för gränssnitt, läsning och kod
  - GNOME-inställningar: accentfärg, typsnitt och bakgrund (dconf)
  - Obsidians utseende i forskningsmappen
  - färger och typsnitt överst i rapportens stilmall
"""
import json
import re
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

YTOR, TYP, LOGO = DESIGN["ytor"], DESIGN["typsnitt"], DESIGN["logotyp"]
# GNOME:s accentfärger (libadwaita 1.6 och senare). Bara dessa namn går att välja i Inställningar.
GNOME_ACCENTER = {"blue", "teal", "green", "yellow", "orange", "red", "pink", "purple", "slate"}

# Logotypen: symbolen och ordmärket ur katalog/logotyp.svg.
KÄLLA = (ROOT / LOGO["källa"]).read_text(encoding="utf-8")
SYMBOL_TRANSFORM = re.search(r'<g id="symbol"[^>]*transform="([^"]+)"', KÄLLA).group(1)
SYMBOL = re.findall(r'<path d="([^"]+)"', KÄLLA.split('<g id="symbol"', 1)[1].split("</g>", 1)[0])
ORDMÄRKE = re.findall(r'<path id="[^"]*" d="([^"]+)"', KÄLLA.split('<g id="wordmark"', 1)[1].split("</g>", 1)[0])
LOGO_W, LOGO_H = 1280, 320


def symbol_paths():
    return "\n    ".join(f'<path d="{d}"/>' for d in SYMBOL)


def logo_group(mode):
    """Hela logotypen i sina egna koordinater (1280 × 320)."""
    words = "\n    ".join(f'<path d="{d}"/>' for d in ORDMÄRKE)
    return (f'<g fill="{LOGO["symbol"]}" transform="{SYMBOL_TRANSFORM}">\n    {symbol_paths()}\n  </g>\n'
            f'  <g fill="{LOGO["ordmärke"][mode]}">\n    {words}\n  </g>')


def logo(mode):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LOGO_W} {LOGO_H}" width="{LOGO_W}" height="{LOGO_H}" role="img">
  <title>DegsellOS</title>
  {logo_group(mode)}
</svg>
"""


def symbol():
    """Symbolen ensam, kvadratisk: programikon och menyknappen uppe till vänster."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 -32 496 496" width="256" height="256" role="img">
  <title>DegsellOS</title>
  <g fill="{LOGO["symbol"]}">
    {symbol_paths()}
  </g>
</svg>
"""


def wallpaper(mode):
    """Papperston med logotypen i mitten, något över mittlinjen så att dockan inte skymmer den."""
    w, h = 3840, 2160
    scale = 1.05
    x = (w - LOGO_W * scale) / 2
    y = h * 0.46 - LOGO_H * scale / 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <title>DegsellOS</title>
  <rect width="{w}" height="{h}" fill="{YTOR['skrivbord'][mode]}"/>
  <g transform="translate({x:.1f} {y:.1f}) scale({scale})">
  {logo_group(mode)}
  </g>
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

[org/gnome/shell/extensions/Logo-menu]
use-custom-icon=true
custom-icon-path='{INSTALLERAD}/degsellos-symbol.svg'
symbolic-icon=false

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
        f"{IDENTITET}/degsellos-logotyp.svg": logo("ljus"),
        f"{IDENTITET}/degsellos-logotyp-mork.svg": logo("mörk"),
        f"{IDENTITET}/degsellos-symbol.svg": symbol(),
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
