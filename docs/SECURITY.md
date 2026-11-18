# Säkerhet och integritet

## Skyddat forskningsprojekt

Skyddsnivån styr de processer ForskarOS startar för analys och rapportbygge. De körs med nätverket avstängt och hemkatalogen dold. Om isoleringen misslyckas avbryts körningen. Program som öppnas separat på skrivbordet har sina vanliga behörigheter. Det gäller även webbläsaren och dess AI-tjänster. [Forskningsdomänens hotmodell](FORSKAROS-3.md#hotmodell-för-skyddade-projekt)

## Data på datorn

Anteckningar och forskningsprojekt lagras som lokala filer. Vid uppdatering ersätts de medföljande filerna för Core, verktygskorten och Forskarhandboken. Lägg egna anteckningar utanför dessa systemunderhållna mappar. Ta en separat säkerhetskopia av egna anteckningar och projekt.

En exporterad körning kan innehålla ursprungliga data och citat. Kontrollera vad mappen innehåller och vem som får ta del av materialet före delning.

## Program och externa tjänster

Grundprofilen hämtas från Flathub och innehåller bland annat Zotero och LibreOffice. Obsidian och genvägar till molntjänster kräver ett separat val. Andra program och tillägg har egna villkor och behörigheter. ForskarOS Core gör inga nätverksanrop. Vid en AI-konsultation väljer forskaren själv vilken text som kopieras till en annan tjänst.

## Avbildningar

Systemet bygger på Bluefin LTS. GitHub Actions bygger avbildningen och signerar dess manifest med sigstore/cosign. Kontrollsummorna för installationsmedierna publiceras tillsammans med nedladdningarna. Automatisk signaturkontroll på klienten kräver en separat policy. [Nedladdningar och kontrollsummor](BETA4.md#installationsmedier)
