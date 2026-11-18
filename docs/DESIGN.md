# Designspråk

ForskarOS ska vara mycket enkelt att använda utan att verktygen blir svagare. Det här dokumentet styr appen ForskarOS (start, projekt, granskning och verktyg) och den delade rapporten.

## Utgångspunkt

Fem referenser jämfördes (utbildningsplattform, konsumentapp, två AI-labb, produktsajt). Inga typsnitt, färger eller varumärken är hämtade från dem. Det som återkommer i alla fem är principerna nedan.

| Princip | Det betyder i ForskarOS |
|---|---|
| **En primär handling per vy** | Varje vy har högst en fylld knapp. I ett projekt är det *Nästa steg*. Allt annat är vanliga rader eller knappar utan fyllning. |
| **Platta ytor** | Kort och grupper avgränsas av ton och hårfina linjer. Appen använder Adwaitas kort som de är; inga egna skuggor eller gradienter. |
| **Färg är funktion** | Accentfärgen betyder *gör det här*. Statusfärger betyder *så här står det till*. Ingen färg som dekoration. |
| **Luft och typografi ger ordning** | Rubrikstorlek och avstånd skapar hierarki, inte ramar och linjer. |
| **Läsytor är redaktionella** | Den delade rapporten är en text att läsa: seriff, smal spalt, lugnt. Gränssnittet är sans-serif. |

Till det kommer en princip som är vår egen:

**Native först.** ForskarOS körs i GNOME. Appen byggs med GTK 4 och libadwaita, följer GNOME:s riktlinjer, mörkt läge och systemets textstorlek. Att se ut och bete sig som resten av skrivbordet är den största förenklingen. ForskarOS identitet syns i innehållet: forskningscykelns färger, statusraderna och rapporten.

## Enkelt utan att bli svagare

1. **Visa nästa steg, inte alla steg.** Projektvyn räknar ut ett enda nästa steg ur projektets läge (påståenden att granska, underlag som ändrats, körningar som inte upprepats) och erbjuder det som den primära knappen. Stegraden *Granska › Bygg › Upprepa › Dela* visar var i arbetsflödet projektet är. Logiken finns i `oversikt.py` och testas utan gränssnitt.
2. **Kraften ligger ett klick bort.** Allt som kommandoraden kan göra finns kvar: i raderna, i rubrikradens meny och i `forskaros-projekt`. Inget tas bort för att göra det enklare.
3. **Ingen terminal för vanligt arbete.** Välkomst, verktygsval, projekt, granskning och upprepning görs i appen. Terminalen är ett tillval för den som vill.
4. **Säg vad som händer, i ord.** Status står alltid i ord (*Granskad*, *Ompröva*, *Underlag saknas*), aldrig bara i färg. Ett fel säger vad som gick fel och vad du kan göra.
5. **Fråga bara när svaret spelar roll.** Standardval där det går: projekt hamnar i `~/Forskningsprojekt`, öppet material är förvalt. Aktiva val (skyddat material, licens, molntjänster) förklaras på en rad där de görs.
6. **Inget går förlorat.** Inga åtgärder skriver över forskarens filer. Det som inte kan ångras (skicka text till en molntjänst) kräver ett uttryckligt val.

## Färger

Appen använder Adwaitas färger, så att ljust och mörkt läge och den accentfärg forskaren valt i GNOME fungerar. ForskarOS egna färger finns i rapporten, som läses utanför skrivbordet:

| Roll | Ljust | Mörkt | Används till |
|---|---|---|---|
| Accent (rapport) | `#1f6f93` | `#5fb3d6` | Länkar och markerat belägg. Blått ur logotypens fas *Utforska*. Kontrast mot pappersytan ≥ 4,5:1. |
| Pappersyta (rapport) | `#faf8f4` | `#1c1b19` | Bakgrund i rapporten och i exempelfiguren. |

Status använder Adwaitas semantiska färger tillsammans med text:

| Status | Stil | Betyder |
|---|---|---|
| Granskad, Återkörd | `success` | Bedömd mot det underlag som finns nu, eller upprepad med samma resultat |
| Ompröva | `warning` | Underlaget har ändrats sedan granskningen |
| Underlag saknas | `error` | En fil, källa eller ett citat saknas |
| Ej granskad, Dokumenterad, Återkörbar | neutral | Ingen bedömning än, eller inte upprepad |

## Typografi

- **Gränssnitt:** systemets typsnitt via Adwaitas stilklasser (`title-1` för vyns rubrik, `heading` för grupper, `caption` för hjälptext, `dim-label` för sekundär text). Ingen fast pixelstorlek, så systemets textskalning fungerar.
- **Rapport:** seriff för brödtext (systemets seriff), 18–20 px, radlängd högst 68 tecken, radavstånd 1,55. Sans-serif för tabeller, figurtexter och beläggsavsnittet.

## Former och avstånd

- Kort: Adwaitas `card` (12 px hörn), ingen skugga.
- Primär knapp: `suggested-action` och `pill`. Högst en per vy. Sekundära handlingar är platta knappar bredvid eller rader.
- Framsteg: stegraden i projektets kort. Klara steg har en bock, nästa steg accentfärg. Status- och stegnamn står alltid i text och läses upp av skärmläsare.
- Grupper: `Adw.PreferencesGroup` med `Adw.ActionRow`, 24 px mellan grupper, smal spalt (`Adw.Clamp`, max 720 px) så att texten går att läsa även på stora skärmar.
- Ikoner: GNOME:s symboliska ikoner, aldrig färgade.

## Skrivregler

- Svenska, du-tilltal, korta meningar. Verb först på knappar: *Bygg rapport*, *Granska*, *Upprepa*.
- Inga utropstecken, ingen jargong (*körning* i stället för *job*, *underlag* i stället för *input*).
- Hjälptext förklarar följden: *Analysen körs utan nätverk och utan åtkomst till hemkatalogen.*
