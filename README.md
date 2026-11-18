# ForskarOS

ForskarOS är en Linuxdistribution för forskningsarbete, byggd på Bluefin LTS. I skrivbordsappen kopplar du meningar i ett manus till exempelvis ett intervjuutdrag, en tabellrad eller en källpassage. När ett underlag ändras visar appen vilka meningar du behöver granska igen. En sparad körning innehåller underlag, analyskod och resultat så att en kollega kan återskapa rapporten.

![Projektet efter en rättelse i intervjumaterialet. En mening behöver omprövas och två är fortfarande granskade.](docs/bilder/beta4-installation-qemu.png)

## Ladda ner

Den publicerade utgåvan är **2027.1-beta4**. Utvecklingsversionen på `main` har också en projektmall för källtolkning med motstridiga källor. Välj fil efter dator och installationssätt.

| Ladda ner | För | SHA-256 |
|---|---|---|
| [ForskarOS-2027.1-beta4-arm64.qcow2](https://archive.org/download/forskaros-2027.1-beta4-arm64-vm/ForskarOS-2027.1-beta4-arm64.qcow2) | Apple Silicon-Mac i UTM, se [Mac-guiden](docs/MAC.md) | [Kontrollsumma](https://archive.org/download/forskaros-2027.1-beta4-arm64-vm/ForskarOS-2027.1-beta4-arm64.qcow2.sha256) |
| [ForskarOS-2027.1-beta4-amd64.qcow2](https://archive.org/download/forskaros-2027.1-beta4-amd64-vm/ForskarOS-2027.1-beta4-amd64.qcow2) | PC i QEMU eller virt-manager | [Kontrollsumma](https://archive.org/download/forskaros-2027.1-beta4-amd64-vm/ForskarOS-2027.1-beta4-amd64.qcow2.sha256) |
| [ForskarOS-2027.1-beta4-amd64-interaktiv-r2.iso](https://archive.org/download/forskaros-2027.1-beta4-amd64-iso/ForskarOS-2027.1-beta4-amd64-interaktiv-r2.iso) | Installation på PC och Intel-Mac | [Kontrollsumma](https://archive.org/download/forskaros-2027.1-beta4-amd64-iso/ForskarOS-2027.1-beta4-amd64-interaktiv-r2.iso.sha256) |

**Välj `-interaktiv-r2.iso` för installation på en dator.** Den första beta4-filen med ändelsen `-amd64.iso` kan automatiskt radera anslutna diskar. Mellanversionen `-interaktiv.iso` kan stanna vid svenskt språkval. Kontrollera vilka diskar som är valda före installationen. [Diskval och installationsanvisningar](docs/BETA4.md#installera-på-pc)

VM-diskarnas första inloggning är `forskare` med lösenordet `forskare`. Du väljer ett nytt lösenord vid inloggningen. En befintlig ForskarOS-installation kan byta till beta4 med `sudo bootc switch ghcr.io/jtensetti/researchos:2027.1-beta4` följt av omstart.

## Ditt första forskningsprojekt

1. Öppna **ForskarOS** och välj **Nytt forskningsprojekt**. Välj en observationstabell eller kodade intervjuutdrag för att börja med exempeldata.
2. Välj **Granska**. Läs meningen i manuset tillsammans med de källor som talar för eller emot den. Ditt beslut sparas med underlaget.
3. Välj **Bygg rapport** och sedan **Upprepa**. ForskarOS jämför rapporten, figuren och resultattabellen med den sparade körningen.
4. Rätta en observation eller ett utdrag. Öppna det påstående som fått status **Ompröva**.

Varje körning kan flyttas som en mapp med HTML-rapport och RO-Crate-metadata. Skyddade projekt kör analysen och rapportbygget utan nätåtkomst och med hemkatalogen dold. [Anvisningar för projektet](docs/PROJEKT.md) · [Skyddets omfattning](docs/SECURITY.md) · [Granskningsvyn i beta4](docs/bilder/beta4-motbelagg-qemu.png)

## Forskningsverktyg

Grundverktygen installeras när datorn får nätåtkomst. I appen väljer du **Välj forskningsverktyg** för att lägga till exempelvis JupyterLab, Taguette eller R. Alla profiler och deras innehåll finns i [verktygsöversikten](vault/00%20START/Verktyg/Översikt.md).

| För att | Använd |
|---|---|
| Lista verktygsprofiler i terminalen | `forskaros-setup --lista` |
| Installera en profil | `forskaros-setup --profil statistik` |
| Köra en analys i R- och Python-labbet | `forskaros-labb Rscript analys.R` |
| Hitta labbets exakta avbildning | `forskaros-labb version` |

### ForskarOS Core

Obsidian-tillägget organiserar forskningsfrågor, hypoteser, motprov och beslut i lokala Markdown-filer. Det kan även användas separat. Kör `bash scripts/install-vault.sh` från en klon av repot, öppna den skapade mappen `~/ForskarOS` i Obsidian och aktivera **ForskarOS Core** under **Settings → Community plugins**. [Arbetsmetoden](vault/00%20START/Arbetsmetod.md) · [Forskarhandboken](vault/00%20START/Forskarhandboken/00%20Innehåll.md)

## Utveckling

Kör `bash scripts/check.sh` från repots rot. Sviten omfattar projektflödet, Core, verktygsprofiler och systemskript. GitHub Actions kör även kontrollerna som kräver GTK, bubblewrap och RO-Crate-valideraren. [Arkitektur och källkod](docs/ARCHITECTURE.md) · [Färdplan](docs/ROADMAP.md) · [Hur ett släpp byggs](docs/RELEASE.md) · [Ändringslogg](CHANGELOG.md)

Tidigare prov och utgåvor finns i versionsdokumentationen. [Beta4](docs/BETA4.md) · [beta3](docs/BETA3.md) · [beta2](docs/BETA2.md) · [beta1](docs/VM-TEST-2026-11-17.md).

Projektets kod har [MIT-licens](LICENSE). Bluefin, GNOME och forskningsverktygen har egna licenser. Obsidian installeras separat efter ett aktivt val.
