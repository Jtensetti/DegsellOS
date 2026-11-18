# Ändringslogg

[Släpprocess och versionsnummer](docs/RELEASE.md)

## Under utveckling

- Projektöversikten visar den senaste upprepningens utfall och pekar ut körningar med avvikande resultat. En flyttad körning behåller sin licens vid upprepning.
- Granskningsvyn visar tidigare och aktuellt underlag bredvid varandra och ger direkt åtkomst till meningen i manuset.
- Valda PDF-markeringar kan importeras från Zotero på samma dator, med referens, sida och citat.
- Projektmallen *Källtolkning* jämför motstridiga uppgifter i skriftliga källor.
- Systemavbildningar använder ForskarOS som produktnamn. En redan monterad delad VM-mapp får en genväg vid inloggning.
- ARM64-diskar kan paketeras som en UTM-maskin samtidigt som den fristående disken behålls.
- Dokumentationen har separata guider för installation, forskningsprojekt, Core och utveckling.

## 2027.1-beta4

- GTK-appen samlar projekt, granskning, rapporter och verktygsinstallation. Projektet visar nästa steg och läses om efter ändringar i en extern editor.
- Påståenden kan kopplas till källpassager med referens, sida och citat. Granskning sker påstående för påstående.
- Skyddade projekt kör analys och rapportbygge utan nätverk och med hemkatalogen dold. Körningen avbryts om skyddet inte kan upprättas.
- Varje körning sparar projektmetadata, kontrollsummor, isolering och upprepningar samt RO-Crate-metadata.
- Rapporter har en gemensam stilmall med ljust och mörkt läge, utskriftslayout och en lokal läsare.
- Färger och typsnitt hämtas från en gemensam katalog för GNOME, appen, Obsidian och rapporter.
- Grundinstallationens förlopp visas i appen. Obsidian och molntjänster kräver separata val.
- Installationsmedier finns för amd64 och VM-diskar för amd64 och arm64. ISO-revisionen `-interaktiv-r2` ersätter de tidigare beta4-ISO:erna med diskval och fungerande svenskt språkval. [Installationsguide](docs/INSTALLATION.md)

## 2027.1-beta3

- Forskningsprojekt kan skapas från skrivbordet med exempel för observationstabeller och kodade intervjuutdrag.
- CSV, Markdown och BibTeX blir en rapport med figur och referenser. Körningsmappar kan flyttas och upprepas separat.
- Rapportens länkade påståenden visar observationer, intervjuutdrag, motbelägg och analyskod.
- Ändrat underlag eller ändrad lydelse ger status *Ompröva* för berörda påståenden. Tidigare körningar behåller sina granskningsbeslut.

## 2027.1-beta2

- Första inloggningen visar grundinstallationens läge och ger tillgång till startsida och installationslogg.
- Core 0.3.1 kräver ett aktivt val av prestationsläge när anteckningen har färre än 50 egna ord.
- Fasraden radbryts i smala paneler.

## 2027.1-beta1

- Första förhandsversionen av systemavbildningen för amd64 och arm64, byggd på Bluefin LTS.
- ForskarOS Core med forskningsfaser, faskrav, beslutslogg, AI-konsultationer och uppföljning.
- Verktygsprofiler, fasindelad programmeny, fokusläge och Forskarhandboken.
- Grundverktyg installeras vid nätanslutning. Obsidian är en separat profil.
- ForskarOS-labbet med R, tidyverse, RStudio Server och Python.
- VM-stöd för lösenordsbyte vid första inloggningen, gästagenter och delade mappar.
