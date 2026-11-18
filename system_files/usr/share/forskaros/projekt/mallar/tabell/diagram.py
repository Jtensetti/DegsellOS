"""Läs tabellmaterial och skriv en SVG som går att öppna i en webbläsare."""
import csv
from html import escape
from pathlib import Path


def rows(fields):
    with Path("data.csv").open(encoding="utf-8-sig", newline="") as stream:
        first = stream.readline()
        stream.seek(0)
        delimiter = ";" if ";" in first and "," not in first else ","
        reader = csv.DictReader(stream, delimiter=delimiter)
        if not set(fields).issubset(reader.fieldnames or ()):
            raise ValueError("data.csv behöver kolumnerna " + ", ".join(fields))
        for row in reader:
            if None in row or any(row[f] is None for f in fields):
                raise ValueError(f"Fel antal fält på rad {reader.line_num}.")
            yield row


def bars(file, title, values, maximum):
    if not values:
        raise ValueError("Inga observationer att analysera.")
    height = 66 + 48 * len(values)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title" viewBox="0 0 720 {height}">',
             f'<title id="title">{escape(title)}</title>',
             # Figuren följer läsarens ljusa eller mörka läge, även inbäddad i rapporten.
             '<style>.figur-yta{fill:#faf8f4}.figur-text{fill:#1f1d1a}.figur-stapel{fill:#27736e}'
             '@media (prefers-color-scheme: dark){.figur-yta{fill:#1c1b19}.figur-text{fill:#ebe7e0}'
             '.figur-stapel{fill:#5fb3a9}}</style>',
             '<rect class="figur-yta" width="100%" height="100%"/>',
             '<g class="figur-text" font-family="\'Adwaita Sans\', \'Noto Sans\', sans-serif">',
             f'<text x="16" y="29" font-size="19">{escape(title)}</text>']
    for index, (label, value, display) in enumerate(values):
        y = 59 + 48 * index
        width = 550 * value / maximum
        parts.extend([f'<text x="16" y="{y}">{escape(label)}</text>',
                      f'<rect class="figur-stapel" x="16" y="{y+6}" width="{width:.2f}" height="11"/>',
                      f'<text x="580" y="{y+16}">{escape(display)}</text>'])
    file.write_text("\n".join(parts + ["</g></svg>"]) + "\n", encoding="utf-8")
