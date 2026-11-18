# ForskarOS

Linuxdistribution för forskningsarbete, byggd som ett lager ovanpå [Bluefin LTS](https://projectbluefin.io/). Den innehåller:

- **Appen ForskarOS** samlar forskningsprojekt, forskningsmappen och verktygen. Ett projekt knyter ihop påståenden i manuset med data, analyskod, referenser och rapport, och visar alltid ett enda nästa steg. En kollega kan köra om analysen från samma underlag.
- **Forskningsverktyg** i profiler som installeras efter behov, från appen eller terminalen. Programmenyn har en mapp per arbetsfas.
- **ForskarOS Core**, ett Obsidian-tillägg som strukturerar forskningsprojekt i faser och listar det som saknas.
- **ForskarOS-labbet**, en containeravbildning med R och Python för analyser som kan köras om i samma miljö.

**ForskarOS 2027.1-beta4** finns som installations-ISO för PC och som VM-disk för både PC och Apple Silicon. [Ladda ner](#ladda-ner) · [Installationsprov och kontrollsummor](docs/BETA4.md).

## Ditt första forskningsprojekt

Öppna **ForskarOS** och välj **Nytt forskningsprojekt**. Välj en observationstabell eller kodade intervjuutdrag. Exempeldata ingår. I projektet ser du vilket påstående som behöver din uppmärksamhet, varför det behöver granskas och vilket underlag det bygger på. En källpassage kan kopplas till en Zotero-referens, sida och citat.

<p align="center"><img src="docs/bilder/beta4-installation-qemu.png" alt="Det skyddade intervjuprojektet efter en rättelse. Ett påstående behöver omprövas och två är fortfarande granskade." width="1100"></p>

I provet ändrades ett intervjuutdrag från ”jag bytte” till ”jag stod fast”. Appen pekade ut den mening i manuset som byggde på utdraget. Den sparade rapporten gick fortfarande att återskapa. [Se citatet och motbelägget i den installerade appen](docs/bilder/beta4-motbelagg-qemu.png).

Varje körning sparar underlag, analyskod och resultat i en mapp med en HTML-rapport och RO-Crate-metadata. Du kan upprepa körningen och jämföra alla resultat. För skyddade projekt körs analysen och rapportbygget med nätverket avstängt och hemkatalogen dold. [Arbetsgång och exempel](docs/PROJEKT.md) · [Vad projektskyddet omfattar](docs/FORSKAROS-3.md#hotmodell-för-skyddade-projekt).

## Ladda ner

Båda VM-diskarna och installations-ISO:n hämtades i sin helhet från Internet Archive den 18 november 2026. För alla tre stämde SHA-256 med byggresultatet och med arkivets kontrollsummefil.

Om ForskarOS redan är installerat kan du byta till beta4 med `sudo bootc switch ghcr.io/jtensetti/researchos:2027.1-beta4` och sedan starta om.

| Ladda ner | För | SHA-256 |
|---|---|---|
| [ForskarOS-2027.1-beta4-arm64.qcow2](https://archive.org/download/forskaros-2027.1-beta4-arm64-vm/ForskarOS-2027.1-beta4-arm64.qcow2) | Apple Silicon-Mac i UTM, se [Mac-guiden](docs/MAC.md) | [Kontrollsumma](https://archive.org/download/forskaros-2027.1-beta4-arm64-vm/ForskarOS-2027.1-beta4-arm64.qcow2.sha256) |
| [ForskarOS-2027.1-beta4-amd64.qcow2](https://archive.org/download/forskaros-2027.1-beta4-amd64-vm/ForskarOS-2027.1-beta4-amd64.qcow2) | PC i QEMU eller virt-manager | [Kontrollsumma](https://archive.org/download/forskaros-2027.1-beta4-amd64-vm/ForskarOS-2027.1-beta4-amd64.qcow2.sha256) |
| [ForskarOS-2027.1-beta4-amd64-interaktiv-r2.iso](https://archive.org/download/forskaros-2027.1-beta4-amd64-iso/ForskarOS-2027.1-beta4-amd64-interaktiv-r2.iso) | Installation på PC och Intel-Mac | [Kontrollsumma](https://archive.org/download/forskaros-2027.1-beta4-amd64-iso/ForskarOS-2027.1-beta4-amd64-interaktiv-r2.iso.sha256) |

**Har du redan en fil som heter `ForskarOS-2027.1-beta4-amd64.iso`?** Den första ISO:n installerar automatiskt och kan radera anslutna diskar. För installation på en dator, hämta filen med `-interaktiv-r2.iso` i tabellen ovan. Revisionen med enbart `-interaktiv.iso` i namnet kan stanna vid valet av svenska.

[Installera på PC och välj rätt disk](docs/BETA4.md#installera-på-pc).

Tidigare utgåvor: [beta3](docs/BETA3.md) och [beta2](docs/BETA2.md).

## ForskarOS Core

Ett Obsidian-tillägg. Allt sker lokalt; tillägget gör inga nätverksanrop.

- **Faser:** varje forskningsfråga går igenom Utforska, Kombinera, Välj, Pröva, Utveckla, Ompröva och Dela. Varje fas har krav (till exempel ett besvarat motprov och ett möte med någon utanför projektet innan Pröva är klar). Kraven går att hoppa över, men motiveringen loggas i frågan.
- **Avslut:** en fråga avslutas med ett utfall: besvarad, hypotesen förkastad eller övergiven.
- **Att åtgärda:** en lista som bygger på vaultens innehåll, till exempel hypoteser utan motprov, frågor som stått still i 30 dagar, fler påbörjade än avslutade frågor och för många öppna frågor (vilande räknas).
- **AI-konsultationer:** tillägget skapar en text att kopiera till valfri AI och loggar konsultationen. Utvecklings- och prövningsläget kräver minst 50 egna ord. Med ett kortare utkast väljer du själv om du vill fortsätta i prestationsläge.
- **Mallar** för forskningsfrågor, hypoteser, motprov, perspektivkartor, experiment, omprövningar, forskningsmöten, felrättningar, övningar och en månatlig förmågegranskning.

Arbetsmetoden beskrivs i [`vault/00 START/Arbetsmetod.md`](vault/00%20START/Arbetsmetod.md) och bakgrunden i [`Bakgrund.md`](vault/00%20START/Bakgrund.md).

### Prova utan att installera OS:et

```bash
bash scripts/install-vault.sh   # skapar ~/ForskarOS, skriver aldrig över
```

Öppna `~/ForskarOS` som vault i Obsidian och aktivera ForskarOS Core under *Settings → Community plugins*.

## Verktyg

Verktygen definieras i [`katalog/verktyg.json`](katalog/verktyg.json). Därifrån genereras profiler, programmenyns mappar och en sida per verktyg i vaulten (`python3 scripts/generera.py`).

| Profil | Innehåll |
|---|---|
| Grund (installeras vid första start) | Firefox, LibreOffice, Zotero, JASP, Xournal++, Déjà Dup |
| Obsidian (krävs för ForskarOS Core) | Obsidian; inte öppen källkod, installeras efter licensgodkännande |
| Rekommenderat urval | Tio verktyg ur övriga profiler |
| Skriva och publicera | Zettlr, ONLYOFFICE, TeXstudio, Pandoc, Typst |
| Statistik och data | jamovi, LabPlot, R, DuckDB, JupyterLab |
| Programmering | VSCodium, uv, git-annex, DataLad, ripgrep |
| Kvalitativ forskning | Speech Note, Taguette |
| Idéer och modeller | draw.io, Freeplane, Rnote |
| Lokal AI | Ollama, Alpaca |
| AI-tjänster i molnet (tillval) | Genvägar till Perplexity, Elicit, Consensus |

I appen ForskarOS: **Välj forskningsverktyg**. Obsidian och molntjänsterna kräver ett aktivt val i en dialog. I terminalen:

```bash
forskaros-setup                       # välj profiler interaktivt
forskaros-setup --profil statistik    # installera en profil
forskaros-setup --lista               # visa profilerna
```

Allt utom Obsidian och molntjänsterna är öppen källkod. CI kontrollerar att varje verktyg finns för både amd64 och arm64 på Flathub, Homebrew eller PyPI.

## Labbet

```bash
forskaros-labb Rscript analys.R   # kör ett kommando i labbet, i aktuell mapp
forskaros-labb rstudio            # RStudio Server på localhost:8787
forskaros-labb version            # avbildningens digest, för att kunna köra om analysen
```

`ghcr.io/jtensetti/researchos-labb` bygger på `rocker/tidyverse:4.6.2` med Python 3.13 tillagt, och fungerar med Podman eller Docker på andra system.

## Hårdvara

| Maskin | Sätt |
|---|---|
| PC (x86_64) | Installations-ISO |
| Intel-Mac | Installations-ISO; T2-modeller kan behöva extra drivrutiner |
| Apple Silicon | Virtuell maskin i UTM, se [`docs/MAC.md`](docs/MAC.md) |

Diskavbildningarna för virtuella maskiner har kontot `forskare` med lösenordet `forskare`, som måste bytas vid första inloggningen.

## Bygga

```
Containerfile          FROM ghcr.io/ublue-os/bluefin:lts
build_files/build.sh   körs i avbildningen under bygget
system_files/          kommandon, tjänster, inställningar
vault/                 vaulten och ForskarOS Core
katalog/               verktygskatalogen
labb/                  labbets Containerfile
disk_config/           inställningar för ISO och diskavbildningar
```

- **Avbildning:** varje push bygger för amd64 och arm64. Pushar till `main` publiceras som `ghcr.io/jtensetti/researchos:latest` och signeras med cosign.
- **Diskar:** arbetsflödet *Bygg installationsmedia* gör ISO och qcow2 som nedladdningsbara artefakter.
- **Byta en befintlig Bluefin LTS-installation:** `sudo bootc switch ghcr.io/jtensetti/researchos:latest`
- **Versioner:** kvartalsvis (`2027.1`, `2027.2` …), se [`docs/RELEASE.md`](docs/RELEASE.md) och [`CHANGELOG.md`](CHANGELOG.md).

## Tester

```bash
bash scripts/check.sh
```

Kör tester för tilläggets regler, tillägget mot ett simulerat Obsidian-API, skalskripten, verktygsprofilerna, UTM-paketeringen, labbkommandot, länkarna i vaulten, forskningsprojektens acceptanstest och appens självtest. Självtestet går igenom alla vyer i appen under Xvfb och kräver GTK 4, libadwaita och `xvfb-run`; utan dem hoppas det över lokalt. I CI krävs det, och skärmbilderna sparas som artefakt.

## Licens

Projektets kod: MIT ([`LICENSE`](LICENSE)). Bluefin, CentOS Stream, GNOME och verktygen har sina egna licenser. Obsidian är proprietärt och ingår inte i avbildningen.
