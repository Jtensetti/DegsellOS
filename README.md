# ForskarOS

**Ett forskningsorienterat operativsystem som tränar dig i att tänka bättre, inte tänker åt dig.**

ForskarOS bygger vi inte från grunden. Vi tar **[Bluefin LTS](https://projectbluefin.io/)** från Universal Blue, en färdig och välskött GNOME-distribution med atomära uppdateringar som kan backas, och lägger ett forskningslager ovanpå:

- **ForskarOS-vaulten:** en Obsidian-kompatibel kunskapsbas i ren Markdown med mappar för riktning, hypoteser, evidens, experiment, friktion, förändring, samverkan och reflektion.
- **ForskarOS Core:** metoden i praktiken, helt lokalt och utan nätverksanrop:
  - **Den kreativa forskningscykeln:** Utforska → Kombinera → Välj → Pröva → Utveckla → Ompröva → Dela, med krav för varje fas och öppen logg när du går vidare ändå.
  - **Tänk först:** AI-hjälp förbereds först när du skrivit din egen uppfattning. Du ser exakt vad som delas och väljer själv AI. Roller: Upptäckaren, Motståndaren, Handledaren, Laboratorieassistenten, Revisorn. Lägen: utveckling, prövning, prestation.
  - **Revisorn:** säger till när du utforskar utan att välja, fördjupar utan kritik, har för många frågor, saknar mänsklig återkoppling eller låter AI tänka åt dig.
  - **Självständighet som mått:** tänkte du först, övningar utan AI, månatlig förmågegranskning. Inte antal anteckningar.
  - **Epistemisk märkning** av vad som är belagt, tolkning och spekulation, plus idéparkering och vila (inkubation).
- **Systemintegration:** vaulten skapas vid första inloggning, tillägget uppdateras när OS:et uppdateras och verktygen installeras efter ett aktivt val.

Bakgrund och principer: [`Forskningsfilosofi`](vault/00%20START/Forskningsfilosofi.md), [`Arbetsmetod`](vault/00%20START/Arbetsmetod.md) och [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Hårdvara

| Maskin | Så kör du ForskarOS |
|---|---|
| PC (x86_64) | Installations-ISO från USB |
| Intel-Mac | Installations-ISO. T2-modeller (2018–2020) kan kräva extra drivrutiner |
| Apple Silicon, inklusive MacBook Neo | **Virtuell maskin i UTM** med arm64-disken, se [`docs/MAC.md`](docs/MAC.md) |

## Ladda ner

Färdiga diskar och ISO:er publiceras på Internet Archive, med direktlänk och torrent:

| Fil | För | Var |
|---|---|---|
| `ForskarOS-<version>-arm64.qcow2` | Apple Silicon-Mac i UTM | `archive.org/details/forskaros-<version>-arm64-vm` |
| `ForskarOS-<version>-amd64.qcow2` | PC i QEMU/virt-manager | `archive.org/details/forskaros-<version>-amd64-vm` |
| `ForskarOS-<version>-amd64.iso` | Installation på PC och Intel-Mac | `archive.org/details/forskaros-<version>-amd64-iso` |

Nya versioner släpps med arbetsflödet *Släpp färdig VM* i GitHub Actions.

## Hur det byggs och distribueras

```
Containerfile          FROM ghcr.io/ublue-os/bluefin:lts + vårt lager
build_files/build.sh   körs inne i avbildningen under bygget
system_files/          filer som kopieras in i OS:et (/usr/bin, /etc, /usr/share)
vault/                 seed-vaulten och ForskarOS Core
disk_config/           inställningar för ISO och virtuella diskar
.github/workflows/     bygg, publicera, signera, skapa installationsmedia
```

1. **Bygge:** varje push bygger och testar avbildningen för amd64 och arm64 i GitHub Actions. Vid push till `main`, och varje vecka, publiceras den som `ghcr.io/jtensetti/researchos:latest` och signeras med sigstore/cosign.
2. **Installationsmedia:** kör arbetsflödet *Bygg installationsmedia* manuellt. Det ger en ISO för PC och qcow2-diskar för virtuella maskiner som nedladdningsbara artefakter.
3. **Uppdateringar:** installerade system hämtar nya versioner automatiskt via bootc. Det går att backa med `sudo bootc rollback`.

Byter du en befintlig Bluefin LTS-installation till ForskarOS:

```bash
sudo bootc switch ghcr.io/jtensetti/researchos:latest
```

> Om repot är privat blir paketet i ghcr.io också privat. Gör paketet publikt under *Package settings* för att kunna hämta det utan inloggning.

## Prova vaulten utan att installera OS:et

```bash
bash scripts/install-vault.sh   # skapar ~/ForskarOS, skriver aldrig över
```

Öppna sedan `~/ForskarOS` som vault i Obsidian och aktivera **ForskarOS Core** under *Settings → Community plugins*.

## Kontroller

```bash
bash scripts/check.sh
```

Testar tillägget mot ett simulerat Obsidian-API, skalskriptens syntax och att `forskaros-init` skapar vaulten, bevarar forskarens anteckningar och uppdaterar tillägget.

## Status

- **Testat lokalt:** tillägget, vault-installationen och `forskaros-init`.
- **Ej testat än:** att själva avbildningen bygger i CI, ISO-installationen och uppstart i UTM. Se [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Licenser

- Projektets egen kod: MIT ([`LICENSE`](LICENSE)).
- Bluefin, Fedora/CentOS och GNOME har sina respektive fria licenser.
- **Obsidian är proprietärt** och ingår därför inte i avbildningen. Användaren installerar det själv från Flathub. Målet på sikt är en egen, öppen editor som kan öppna samma vault, se färdplanen.
