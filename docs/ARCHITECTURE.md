# Arkitektur

ForskarOS är en bootc-avbildning för amd64 och arm64 ovanpå Bluefin LTS. Skrivbordsappen hanterar forskningsprojekt med underlag och sparade körningar. Det valfria Obsidian-tillägget ForskarOS Core hanterar forskningsfrågor och arbetsmetod i en separat Markdown-vault.

## Projektets krav

| Krav | Vad forskaren ska kunna göra |
|---|---|
| Isolering | Köra analys och rapportbygge med avstängt nätverk och dold hemkatalog. Körningen ska avbrytas om isoleringen misslyckas. |
| Reproducerbarhet | Flytta en körning till en annan installation, återskapa resultaten och se vilka filer som eventuellt avviker. |
| Spårbarhet | Gå från ett påstående i manuset till den valda tabellraden, källpassagen eller analysfilen. |
| Omprövning | Se vilka påståenden som påverkas när ett registrerat underlag ändras. Oberoende granskningsbeslut ska behållas. |
| Användbarhet | Genomföra en forskningsuppgift med mindre administrativt arbete än i den vanliga arbetsmiljön. Jämförelsen omfattar tid, handgrepp, fel och hjälpbehov. |

Användbarhetskravet behöver prövas med forskare enligt [färdplanen](ROADMAP.md).

## Källkodens delar

| Del | Ansvar | Källkod |
|---|---|---|
| Skrivbordsapp | Projektvyer, granskning och verktygsval med GTK 4 och libadwaita | [app.py](../system_files/usr/share/forskaros/projekt/app.py), [oversikt.py](../system_files/usr/share/forskaros/projekt/oversikt.py) |
| Projektmotor | Skapa projekt, köra analyser och upprepa sparade körningar | [projekt.py](../system_files/usr/share/forskaros/projekt/projekt.py), [upprepa.py](../system_files/usr/share/forskaros/projekt/upprepa.py) |
| Belägg och källor | Kopplingar, granskningsbeslut, omprövning och Zotero-import | [belagg.py](../system_files/usr/share/forskaros/projekt/belagg.py), [zotero.py](../system_files/usr/share/forskaros/projekt/zotero.py) |
| Forskningspaket | RO-Crate-metadata för en körning | [paket.py](../system_files/usr/share/forskaros/projekt/paket.py) |
| Rapportläsare | Lokal visning av HTML-rapporter med WebKitGTK | [rapportvy.py](../system_files/usr/share/forskaros/projekt/rapportvy.py) |
| Core | Frågor, faser och beslutslogg i Obsidian | [Tillägg](../vault/.obsidian/plugins/forskaros-core), [forskningsmapp](../vault) |
| Labb | Containerbaserad analysmiljö med R och Python | [labb](../labb) |
| Verktyg och utseende | Kataloger och generatorer för profiler, programmenyer och design | [katalog](../katalog), [scripts](../scripts) |
| System och installation | Systemkommandon, tjänster, GNOME-inställningar och installationsmedier | [Containerfile](../Containerfile), [byggskript](../build_files/build.sh), [systemfiler](../system_files), [diskinställningar](../disk_config) |

## Projektformat

Appen och `forskaros-projekt` använder samma projektlogik och filer. Projekten kräver ingen bakgrundstjänst eller central databas.

| Fil eller mapp | Innehåll |
|---|---|
| `projekt.json` | Formatversion, projekt-ID, titel, metod, skyddsnivå, skapandetid och valfri licens |
| `underlag/` | Arbetsmaterial, analyskod, manus och referenser |
| `underlag/belagg.json` | Påståenden med ID, lydelse och kopplingar till data eller källor |
| `underlag/granskningar.json` | Beslut kopplade till avtryck av det granskade underlaget |
| `granskningsunderlag.json` | Tidigare visat underlag för jämförelse vid omprövning |
| `korningar/` | En separat mapp för varje slutförd analys |

Äldre projekt utan `projekt.json` behandlas som öppna. Underlag måste bestå av vanliga filer och mappar; symboliska länkar följer inte med i körningar.

## Körningar och upprepning

En körning kopierar `underlag/` till en tillfällig arbetsmapp. Analysen skapar resultat och Pandoc bygger rapporten. Först efter att båda har lyckats publiceras körningsmappen under `korningar/`.

Varje körning innehåller underlag, resultat, körprogram och `korning.json` med SHA-256, programversioner och isolering. `ro-crate-metadata.json` beskriver samma material i RO-Crate 1.1 med profilen Process Run Crate 0.5. Upprepningar loggas i `verifieringar.json`.

Vid upprepning kontrolleras filerna mot de sparade kontrollsummorna. Analysen körs på en ny kopia och resultaten jämförs byte för byte. Projektöversikten visar den senaste kontrollens utfall. En containerkörning sparar labbavbildningens digest; samma avbildning används vid upprepning på kompatibel arkitektur.

[Arbeta med projekt och körningar](PROJEKT.md) · [Isolering och hotmodell](SECURITY.md)

## Verktyg och första inloggning

`forskaros-grund.service` hämtar grundprofilens program från Flathub när nätåtkomst finns. Fler profiler installeras från appen eller med `forskaros-setup`. Obsidian installeras separat. Skrivbordsappen, Python och Pandoc ingår i systemavbildningen.

`forskaros-init` skapar `~/ForskarOS` från vaultens mall vid första inloggningen. Vid senare inloggningar uppdateras medföljande verktygskort, handbokssidor och ett befintligt Core-tillägg. Användarens övriga anteckningar och inställningar bevaras.

## Bygga och ändra

Systemavbildningen definieras av `Containerfile` och `build_files/build.sh`. Under `system_files/` speglas de sökvägar som installeras i systemet. Profiler och designfiler genereras från katalogerna.

[Utvecklingsmiljö och tester](../CONTRIBUTING.md) · [Designsystem](DESIGN.md) · [Byggflöden](../.github/workflows) · [Släpprocess](RELEASE.md)
