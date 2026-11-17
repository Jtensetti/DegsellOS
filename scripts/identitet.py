#!/usr/bin/env python3
"""Ritar ForskarOS identitet: logotyp och skrivbordsbakgrunder (SVG).

Logotypen är forskningscykeln: sju bågar, en per fas (Utforska → Dela),
runt en punkt som är frågan. Kör om skriptet för att återskapa filerna.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "system_files/usr/share/forskaros/identitet"

# En färg per fas, från kall nyfikenhet till varm delning.
FASFÄRGER = ["#2E86AB", "#3FA7A0", "#7BB662", "#E0A458", "#D9724A", "#A45DA8", "#5B6CC4"]
FASER = ["Utforska", "Kombinera", "Välj", "Pröva", "Utveckla", "Ompröva", "Dela"]


def arc(cx, cy, r, a0, a1):
    p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0))
    p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
    large = 1 if (a1 - a0) > math.pi else 0
    return f"M {p0[0]:.2f} {p0[1]:.2f} A {r} {r} 0 {large} 1 {p1[0]:.2f} {p1[1]:.2f}"


def ring(cx, cy, r, width, gap_deg=7, opacity=1.0, center="#F4F1EA", outline=None):
    parts = []
    step = 2 * math.pi / 7
    gap = math.radians(gap_deg)
    for i, color in enumerate(FASFÄRGER):
        a0 = -math.pi / 2 + i * step + gap / 2
        a1 = a0 + step - gap
        parts.append(f'<path d="{arc(cx, cy, r, a0, a1)}" fill="none" stroke="{color}" '
                     f'stroke-width="{width}" stroke-linecap="round" opacity="{opacity}"><title>{FASER[i]}</title></path>')
    stroke = f' stroke="{outline}" stroke-width="{width * 0.22:.1f}"' if outline else ""
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{width * 0.9:.1f}" fill="{center}"{stroke} opacity="{opacity}"/>')
    return "\n  ".join(parts)


def logo():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <title>ForskarOS</title>
  {ring(128, 128, 92, 22, center="#F4F1EA", outline="#1B2A3A")}
</svg>
"""


def wallpaper(dark: bool):
    w, h = 3840, 2160
    bg0, bg1 = ("#0F1B2A", "#1B2A3A") if dark else ("#F4F1EA", "#E6E1D6")
    text = "#C9D3DD" if dark else "#3A4654"
    center = "#F4F1EA" if dark else "#1B2A3A"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <defs>
    <radialGradient id="bg" cx="50%" cy="45%" r="75%">
      <stop offset="0" stop-color="{bg1}"/>
      <stop offset="1" stop-color="{bg0}"/>
    </radialGradient>
  </defs>
  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  {ring(w / 2, h * 0.45, 360, 70, opacity=0.92, center=center)}
  <text x="{w / 2}" y="{h * 0.45 + 620}" text-anchor="middle" fill="{text}"
        font-family="Cantarell, Inter, sans-serif" font-size="64" letter-spacing="4" opacity="0.8">Framtiden är den viktigaste tiden.</text>
</svg>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "forskaros-logotyp.svg").write_text(logo(), encoding="utf-8")
    (OUT / "forskaros-bakgrund-ljus.svg").write_text(wallpaper(dark=False), encoding="utf-8")
    (OUT / "forskaros-bakgrund-mork.svg").write_text(wallpaper(dark=True), encoding="utf-8")
    print(f"Skapade identiteten i {OUT}")


if __name__ == "__main__":
    main()
