# Gränssnitt och typografi

Skrivbordsappen använder GTK 4 och libadwaita och följer GNOME:s inställningar för textstorlek, accentfärg och mörkt läge. ForskarOS färger och typsnitt definieras i [design.json](../katalog/design.json).

![Typsnitt, färger för granskningsstatus och forskningscykelns sju fasfärger.](bilder/designsystem.png)

## Projektvyn

Projektöversikten visar den åtgärd som behöver göras härnäst. Status visas alltid i text. Använd Adwaitas `success` för **Granskad** och **Återkörd**, `warning` för **Ompröva** och `error` för **Underlag saknas** och **Avviker**. **Ej granskad**, **Dokumenterad** och **Återkörbar** har neutral stil.

Använd verb på knappar, som **Bygg rapport** och **Upprepa**. När ett underlag har ändrats visas tidigare och aktuell version tillsammans. Knapparna för att ändra meningen och bekräfta granskningen har samma vikt.

## Typografi och färg

| Användning | Typsnitt |
|---|---|
| Skrivbord, app och rubriker | Adwaita Sans |
| Dokument och rapporttext | Noto Serif |
| Terminal, analyskod och data | JetBrains Mono |

Appen använder Adwaitas textstilar och GNOME:s symboliska ikoner. HTML-rapportens brödtext har en maximal radlängd på 68 tecken och radavståndet 1,55. Rapportens stilmall stöder ljust och mörkt läge. Forskningscykelns sju färger används i logotypen och skrivbordsbakgrunden.

## Ändra utseendet

1. Ändra typsnitt eller färger i `katalog/design.json`.
2. Kör `python3 scripts/identitet.py` för att uppdatera logotyp, bakgrunder, GNOME-inställningar, Obsidian och rapportens stilmall.
3. Kör `bash tests/identitet.test.sh` för att kontrollera de genererade filerna och rapporttextens kontrast. Lägg till nya typsnittspaket i `build_files/build.sh`.

GNOME-inställningarna är standardvärden som användaren kan ändra. Obsidian får sina utseendeinställningar när en forskningsmapp skapas.
