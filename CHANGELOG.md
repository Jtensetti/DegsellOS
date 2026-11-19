# Ändringslogg

[Utgåvor och kontrollsummor](docs/VERSIONS.md) · [Släpprocess](docs/RELEASE.md)

## Under utveckling

- Appen och Obsidian öppnar varandra. Panelen visar projekten under varje forskningsfråga och kan starta ett nytt projekt med frågan och hypotesen valda. Appens startsida visar frågorna med sina projekt. Projektets anteckning i forskningsmappen följer med när projektet flyttas, och två projekt med samma namn krockar inte.
- Obsidian öppnar forskningsmappen direkt vid första start.
- Panelens verktyg per fas kommer från samma katalog som programmenyn, med programmen för möten först i Pröva.
- Ett forskningsprojekt kan kopplas till en forskningsfråga och den hypotes det prövar. Projektets körningar, täckningsgrad och påståenden att ompröva skrivs till forskningsmappen och styr fasernas krav i ForskarOS Core. Appens sista steg leder tillbaka till frågan. [Koppla projektet](docs/PROJEKT.md#koppla-projektet-till-en-forskningsfråga)
- Arbetsmetoden bärs av 25 begrepp, från nyfikenhet till framtiden. Varje begrepp har ett krav eller en regel som slår till när det brister, och sidan *Begreppen* i forskningsmappen visar var det finns.
- Nya krav: saker du undrar över och vem som bryr sig om svaret (Utforska), vem som företräder antagandet hypotesen utmanar (Kombinera) och ett möte med den personen (Pröva), att någon mer arbetar med frågan (Utveckla), och vilken ny fråga svaret öppnar (Dela). Nästa fråga hamnar i idébanken när frågan avslutas.
- Kontakter och Kalender ingår i grundprofilen. Den nya profilen Möten och samarbete har Jitsi Meet, Element, Syncthing och Evolution.

- I granskningsvyn går det att jämföra tidigare och aktuellt underlag. Forskaren kan ändra meningen i manuset eller bekräfta den mot det nya underlaget.
- Källtolkning har en egen projektmall för motstridiga skriftliga källor. PDF-markeringar kan importeras från Zotero på samma dator med källa, sida och citat.
- Projektöversikten visar vilken upprepning som avviker. En flyttad körning behåller sin licens när den upprepas.
- Systemavbildningen använder ForskarOS som produktnamn. Bygget för Apple Silicon ger både en fristående VM-disk och ett UTM-paket. Redan monterade delade mappar får en genväg vid första inloggningen.

- Installationsmedier från det manuella byggflödet får egna SHA-256-filer. Domäntestet redovisar vilka kontroller som inte kunde köras.
- Dokumentationen har separata guider för installation, forskningsprojekt, Core och utveckling.

## 2027.1-beta4

- ForskarOS skrivbordsapp samlar projekt, verktygsval och grundinstallation. Granskningen visar påståenden i tur och ordning med deras underlag.
- Ett påstående kan knytas till ett citat med källa och sida. Projektvyn läser in rättelser när forskaren kommer tillbaka från sin editor.
- Skyddade projekt kör analys och rapportbygge med avstängt nätverk och dold hemkatalog. Körningsmappen innehåller RO-Crate-metadata med programversioner, kontrollsummor och verifieringar.
- HTML-rapporten kan läsas direkt i appen. Rapport, skrivbord och Obsidian har gemensamma inställningar för typsnitt, färger och mörkt läge.
- Installations-ISO:n för amd64 fick en interaktiv revision med manuellt diskval och stöd för svenskt språkval. [Installationsmedier och äldre ISO-filer](docs/INSTALLATION.md)

## 2027.1-beta3

- Projekt med observationsdata eller kodade intervjuutdrag kan bygga en rapport med figurer och referenser. Sparade körningar kan flyttas och upprepas på en annan dator.
- Påståenden i manuset kan kopplas till tabellrader, utdrag och analyskod. När ett underlag ändras markeras berörda påståenden för omprövning. [Systemavbildning för beta3](docs/VERSIONS.md#20271-beta3)

## 2027.1-beta2

- Verktygsmenyn visar hur installationen går, kan öppna den lokala startsidan utan nät och ger tillgång till installationsloggen.
- I ForskarOS Core 0.3.1 kräver prestationsläget ett uttryckligt val för anteckningar med färre än 50 egna ord. Fasnamnen kan radbrytas i en smal panel. [Installationsmedier för beta2](docs/VERSIONS.md#20271-beta2)

## 2027.1-beta1

- Första förhandsversionen av arbetsstationen på Bluefin LTS. ForskarOS Core organiserar forskningsfrågor, hypoteser, motprov och beslut i Obsidian. Verktygsprofiler, forskarhandbok och ett separat R- och Python-labb ingår. [VM-disk för beta1](docs/VERSIONS.md#20271-beta1)
