# Bidra till ForskarOS

ForskarOS består av en GTK-app och projektmotor i Python, ett Obsidian-tillägg i JavaScript och en bootc-systemavbildning. [Arkitekturen](docs/ARCHITECTURE.md) beskriver delarna och deras filformat.

## Köra lokalt

Klona repot och arbeta från dess rot. Grundkontrollerna kräver Bash, Node.js, Python 3 och Pandoc 3:

```bash
bash scripts/check.sh
```

Sviten kontrollerar projektmallar, belägg, omprövning, upprepning, Zotero-import, Core, verktygsprofiler och systemskript. Tester som kräver GTK, bubblewrap eller RO-Crate-valideraren anger uttryckligen när de hoppas över.

Starta appen på en Linuxdator med GTK 4, libadwaita och PyGObject:

```bash
system_files/usr/bin/forskaros
```

Projektkommandot kan användas utan grafisk miljö:

```bash
system_files/usr/bin/forskaros-projekt skapa kvantitativ /tmp/min-studie
system_files/usr/bin/forskaros-projekt kör /tmp/min-studie
```

Välj en ny projektmapp; en befintlig mapp skrivs inte över. Installation av verktygsprofiler är avsedd för ForskarOS. Inspektera exempelvis statistikprofilen utan installation med:

```bash
FORSKAROS_PROFILDIR="$PWD/system_files/usr/share/forskaros/profiler" system_files/usr/bin/forskaros-setup --profil statistik --torrkörning
```

## Fullständig kontrollsvit

Utöver grundverktygen behövs en fungerande bubblewrap, PyGObject med GTK 4 och libadwaita, Xvfb samt `roc-validator==0.14.0` i en Pythonmiljö. Python som används för appen behöver kunna importera `gi`.

```bash
FORSKAROS_KRAV_SANDLADA=1 FORSKAROS_KRAV_ROCRATE=1 FORSKAROS_KRAV_APP=1 FORSKAROS_ROCRATE_VALIDATOR=/sökväg/till/venv/bin/rocrate-validator bash scripts/check.sh
```

Med dessa flaggor är en saknad testförutsättning ett fel. GitHub Actions kör denna variant och kontrollerar även tillgängligheten för verktyg på amd64 och arm64. Paket och miljöinställningar för CI finns i [byggflödet](.github/workflows/build.yml).

Appens befintliga självtest kan spara skärmdumpar i en valfri mapp:

```bash
FORSKAROS_SKARMDUMPAR=/tmp/forskaros-skarmdumpar bash tests/app.test.sh
```

## Genererade filer

| Ändring | Källa | Generera med |
|---|---|---|
| Verktyg, profiler och programmenyer | `katalog/verktyg.json` | `python3 scripts/generera.py` |
| Färger, typsnitt och systemets utseende | `katalog/design.json` | `python3 scripts/identitet.py` |

Ändra källan och ta med de genererade filerna i samma commit. Kontrollsviten upptäcker om de skiljer sig åt. [Designsystem](docs/DESIGN.md)

## Bygga systemet

På en Linuxvärd med Podman:

```bash
podman build -t localhost/forskaros .
```

CI bygger amd64 och arm64 på separata värdar. ISO, VM-diskar, UTM-paket och signering beskrivs i [släpprocessen](docs/RELEASE.md).

## Föreslå en ändring

Beskriv problemet, den förväntade funktionen och hur ändringen har kontrollerats. Lägg till ett regressionstest när ett fel behöver skydd mot att återkomma. Använd konstruerat material i tester och exempelprojekt. Dokumentera användning och gränssnitt i guiderna; versionsförändringar hör hemma i [ändringsloggen](CHANGELOG.md).
