# Designsystem

ForskarOS ska vara mycket enkelt att använda utan att verktygen blir svagare. Det här dokumentet gäller hela systemet: skrivbordet, appen ForskarOS, forskningsmappen i Obsidian och den delade rapporten.

Färger och typsnitt finns på ett ställe, [`katalog/design.json`](../katalog/design.json). `python3 scripts/identitet.py` skapar allt som bygger på dem: logotypen, skrivbordsbakgrunderna, GNOME-inställningarna, typsnittsinställningarna, Obsidians utseende och färgerna i rapportens stilmall. `tests/identitet.test.sh` kontrollerar att filerna är i synk, att avbildningen installerar typsnitten och att all text i rapporten klarar kontrastkravet.

<p align="center"><img src="bilder/designsystem.png" alt="ForskarOS designsystem: tre typsnitt (Adwaita Sans för gränssnitt, Noto Serif för läsning, JetBrains Mono för kod och data), accentfärgen teal, papperstoner, statusfärgerna Granskad, Ompröva, Underlag saknas och Ej granskad, och forskningscykelns sju fasfärger." width="900"></p>

## Principer

Fem referenser jämfördes (utbildningsplattform, konsumentapp, två AI-labb, produktsajt). Inga typsnitt, färger eller varumärken är hämtade från dem. Det som återkommer i alla fem är principerna nedan.

| Princip | Det betyder i ForskarOS |
|---|---|
| **En primär handling per vy** | Varje vy har högst en fylld knapp. I ett projekt är det *Nästa steg*. Allt annat är vanliga rader eller knappar utan fyllning. |
| **Platta ytor** | Kort och grupper avgränsas av ton och hårfina linjer. Appen använder Adwaitas kort som de är; inga egna skuggor eller gradienter. Skrivbordsbakgrunden är en jämn papperston. |
| **Färg är funktion** | Accentfärgen betyder *gör det här*. Statusfärger betyder *så här står det till*. Forskningscykelns färger är identitet och används bara i logotypen och bakgrunden. |
| **Luft och typografi ger ordning** | Rubrikstorlek och avstånd skapar hierarki, inte ramar och linjer. |
| **Läsytor är redaktionella** | Det som ska läsas länge, rapporten, sätts i seriff med smal spalt. Allt man arbetar i är sans-serif. |

Till det kommer en princip som är vår egen:

**Native först.** ForskarOS körs i GNOME; avbildningen har GTK 4.22 och libadwaita 1.9 från Bluefin LTS. Appen byggs med GTK 4 och libadwaita och följer GNOME:s riktlinjer, mörkt läge och systemets textstorlek. Typsnitten är GNOME:s egna eller vanliga öppna typsnitt från distributionen. Att se ut och bete sig som resten av skrivbordet är den största förenklingen. ForskarOS identitet syns i innehållet: forskningscykeln, statusraderna och rapporten.

## Enkelt utan att bli svagare

1. **Visa nästa steg, inte alla steg.** Projektvyn räknar ut ett enda nästa steg ur projektets läge (påståenden att granska, underlag som ändrats, körningar som inte upprepats) och erbjuder det som den primära knappen. Stegraden *Granska › Bygg › Upprepa › Dela* visar var i arbetsflödet projektet är. Logiken finns i `oversikt.py` och testas utan gränssnitt.
2. **Kraften ligger ett klick bort.** Allt som kommandoraden kan göra finns kvar: i raderna, i rubrikradens meny och i `forskaros-projekt`. Inget tas bort för att göra det enklare.
3. **Ingen terminal för vanligt arbete.** Välkomst, verktygsval, projekt, granskning och upprepning görs i appen. Terminalen är ett tillval för den som vill.
4. **Säg vad som händer, i ord.** Status står alltid i ord (*Granskad*, *Ompröva*, *Underlag saknas*), aldrig bara i färg. Ett fel säger vad som gick fel och vad du kan göra.
5. **Fråga bara när svaret spelar roll.** Standardval där det går: projekt hamnar i `~/Forskningsprojekt`, öppet material är förvalt, ID för ett påstående föreslås ur meningen. Aktiva val (skyddat material, licens, molntjänster) förklaras på en rad där de görs.
6. **Inget går förlorat.** Inga åtgärder skriver över forskarens filer eller inställningar. Det som inte kan ångras (skicka text till en molntjänst) kräver ett uttryckligt val.

## Typografi

Tre typsnitt med var sin roll. Alla är öppna (SIL Open Font License) och finns som paket i CentOS Stream 10 och EPEL 10.

| Roll | Typsnitt | Används till |
|---|---|---|
| **Gränssnitt** | Adwaita Sans 11 | GNOME, appen ForskarOS, Obsidian och rubrikerna i rapporten. GNOME:s eget typsnitt från GNOME 48, byggt på Inter. Lättläst i små storlekar. |
| **Läsning** | Noto Serif 12 | Rapportens brödtext, GNOME:s typsnitt för dokument och webbsidor som ber om seriff. Byggt för skärm och har alla tecken i svenska och övriga europeiska språk. |
| **Kod och data** | JetBrains Mono 11 | Terminalen, analyskod och tabeller med data. Skiljer tydligt mellan 0 och O, 1, l och I. |

Så når typsnitten hela systemet:

- **GNOME** får dem som standardinställningar (dconf): gränssnitt, dokument och monospace.
- **Alla program på datorn** får dem genom fontconfig (`52-forskaros-typsnitt.conf`). En webbsida eller ett program som ber om *sans-serif*, *serif* eller *monospace* får ForskarOS typsnitt.
- **Flatpak-program** (Firefox, LibreOffice, Obsidian, Zotero) läser inte systemets fontconfig. `forskaros-init` lägger därför samma fil i användarens fontconfig, en gång.
- **Obsidian** får typsnitten i nya forskningsmappar (`.obsidian/appearance.json`).
- **Rapporten** anger typsnitten med reserver, så att den ser ordentlig ut även på en dator utan ForskarOS.

Storlekar: appen använder Adwaitas stilklasser (`title-1`, `title-2`, `heading`, `caption`), aldrig fasta pixlar, så att systemets textskalning fungerar. Rapporten har 19 px brödtext, högst 68 tecken per rad och radavstånd 1,55.

## Färg

Allt följer systemets ljusa eller mörka läge.

| Roll | Värde | Används till |
|---|---|---|
| **Accent** | GNOME:s *teal* (`#2190a4`) | Primär handling, vald rad och nästa steg i GNOME, appen och Obsidian. Ett av GNOME:s egna accentval, så forskaren kan byta i Inställningar. |
| **Länktext i rapporten** | `#1f6f93` ljust, `#5fb3d6` mörkt | Länkar och markerat belägg. Mörkare än accenten för att klara kontrastkravet mot papperet. |
| **Skrivbord** | `#f4f1ea` ljust, `#1c1b19` mörkt | Bakgrundens papperston. |
| **Papper** | `#faf8f4` ljust, `#1c1b19` mörkt | Rapportens bakgrund och exempelfiguren. |
| **Text** | `#1f1d1a` ljust, `#ebe7e0` mörkt | Bläck på papper. Aldrig helt svart eller helt vitt. |

Status använder samma betydelse överallt, alltid tillsammans med ord:

| Status | I appen | I rapporten | Betyder |
|---|---|---|---|
| Granskad, Återkörd | Adwaitas `success` | `#2c6e49` | Bedömd mot det underlag som finns nu, eller upprepad med samma resultat |
| Ompröva | `warning` | `#8a5a00` | Underlaget har ändrats sedan granskningen |
| Underlag saknas | `error` | `#b42318` | En fil, källa eller ett citat saknas |
| Ej granskad, Dokumenterad, Återkörbar | neutral | dämpad | Ingen bedömning än, eller inte upprepad |

**Forskningscykelns sju färger** (Utforska till Dela) är ForskarOS identitet. De används i logotypen och skrivbordsbakgrunden, aldrig för status eller som dekoration i ett gränssnitt.

**Kontrast:** all text i rapporten klarar WCAG AA (minst 4,5:1) mot papperet och de upphöjda ytorna, i både ljust och mörkt läge. Testet räknar om det vid varje ändring.

## Skrivbordet

- **Bakgrund:** en jämn papperston med forskningscykeln stor och lätt, förskjuten åt höger så att fönster och docka får plats. Ljus och mörk variant; låsskärmen använder den mörka.

<p align="center"><img src="bilder/bakgrund.png" alt="Skrivbordsbakgrunden i ljust och mörkt läge: papperston med forskningscykelns sju tunna bågar i en stor ring till höger om mitten." width="900"></p>

- **Dockan** är ordnad efter arbetet: appen ForskarOS först, sedan Firefox, Obsidian, Zotero, Writer, JASP, Filer, Terminal och Fokusläge.
- **Programmenyn** har en mapp per fas i forskningscykeln, plus en mapp för ForskarOS egna program.
- **Första inloggningen** öppnar appen ForskarOS, som visar hur installationen av grundverktygen går.
- **Fokusläget** stänger av notiser under ett arbetspass och loggar passet.

## Det vi inte ändrar, och varför

- **Inget eget GTK-, skal- eller ikontema.** Egna teman går sönder när GNOME uppdateras, och program skulle se annorlunda ut än i resten av GNOME. ForskarOS ändrar bara det GNOME själv låter användaren välja: accentfärg, typsnitt och bakgrund.
- **Bluefins docka, tillägg och tangentbordsgenvägar behålls.** De fungerar och dokumenteras av Bluefin.
- **Forskarens egna val vinner.** Allt är standardvärden, inget är låst. Typsnittsfilen har nummer 52, efter användarens egna inställningar (50). Obsidians utseende sätts bara i nya forskningsmappar. Typsnittsfilen för Flatpak läggs dit en gång; tar forskaren bort den kommer den inte tillbaka.

## Former och avstånd

- Kort: Adwaitas `card` (12 px hörn). Rapportens beläggsrutor har samma hörn.
- Primär knapp: `suggested-action` och `pill`. Högst en per vy. Sekundära handlingar är platta knappar bredvid eller rader.
- Framsteg: stegraden i projektets kort. Klara steg har en bock, nästa steg accentfärg. Status- och stegnamn står alltid i text och läses upp av skärmläsare.
- Grupper: `Adw.PreferencesGroup` med `Adw.ActionRow`, 24 px mellan grupper, smal spalt (`Adw.Clamp`, max 720 px) så att texten går att läsa även på stora skärmar.
- Ikoner: GNOME:s symboliska ikoner, aldrig färgade. ForskarOS egna program har logotypen som ikon.

## Skrivregler

- Svenska, du-tilltal, korta meningar. Verb först på knappar: *Bygg rapport*, *Granska*, *Upprepa*.
- Inga utropstecken, ingen jargong (*körning* i stället för *job*, *underlag* i stället för *input*).
- Hjälptext förklarar följden: *Analysen körs utan nätverk och utan åtkomst till hemkatalogen.*

## Ändra designen

1. Ändra värdet i `katalog/design.json`.
2. Kör `python3 scripts/identitet.py`. Det skriver om bakgrunder, logotyp, typsnittsinställningar, GNOME-inställningar, Obsidians utseende och rapportens färger.
3. Kör `bash scripts/check.sh`. Testet säger till om något inte är i synk, om ett typsnitt inte installeras i avbildningen eller om en färg inte klarar kontrastkravet.

Ett nytt typsnitt behöver också läggas in i `build_files/build.sh`, som installerar paketet och kontrollerar med `fc-match` att det används.
