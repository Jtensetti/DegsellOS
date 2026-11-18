# Arkitektur

ForskarOS bygger en bootc-avbildning för amd64 och arm64 ovanpå Bluefin LTS. Forskaren arbetar i två slags mappar. Skrivbordsappen hanterar projekt med underlag och sparade körningar. ForskarOS Core hanterar forskningsfrågor och arbetsmetod i en separat Markdown-vault för Obsidian.

| Del | Ansvar | Källkod |
|---|---|---|
| Skrivbordsapp och projektkommando | Skapa projekt, granska belägg, bygga rapporter och upprepa körningar | [Projektmoduler och mallar](../system_files/usr/share/forskaros/projekt), [systemkommandon](../system_files/usr/bin) |
| ForskarOS Core | Frågor, faser och beslutslogg i lokala anteckningar | [Tillägg](../vault/.obsidian/plugins/forskaros-core), [forskningsmapp](../vault) |
| ForskarOS-labbet | Versionsbunden R- och Pythonmiljö i en container | [labb](../labb) |
| Verktyg och utseende | Verktygsprofiler, programmeny, typsnitt och färger | [Katalog](../katalog), [generatorer](../scripts) |
| System och installation | Bootc-avbildning, systemtjänster, GNOME-inställningar samt ISO- och VM-diskar | [Containerfile](../Containerfile), [byggskript](../build_files/build.sh), [systemfiler](../system_files), [diskinställningar](../disk_config) |

## Projektets filer

`projekt.json` identifierar projektet och dess skyddsnivå. I `underlag/` finns arbetsmaterial, manus och kopplingar mellan påståenden och källor. Appen och kommandot `forskaros-projekt` använder samma filer och projektlogik. Varje lyckad analys sparas i en egen mapp under `korningar/` med en kopia av underlaget, resultaten och deras kontrollsummor. [Projektens filformat och arbetsgång](PROJEKT.md) · [Projektets krav](FORSKAROS-3.md)

## Verktyg och första inloggning

`forskaros-grund.service` hämtar grundprofilens program från Flathub när nätåtkomst finns. Fler profiler installeras från appen eller med `forskaros-setup`. Obsidian installeras separat. Skrivbordsappen och Pandoc ingår i systemavbildningen.

`forskaros-init` skapar `~/ForskarOS` från vaultens mall vid första inloggningen. Vid senare inloggningar uppdateras de medföljande verktygskorten, handbokssidorna och ett befintligt Core-tillägg. Forskarens egna anteckningar ligger kvar.

## Ändra och bygga

Ändra verktyg i `katalog/verktyg.json` och generera profiler, programmenyer och verktygskort med `python3 scripts/generera.py`. Ändra färger och typografi i `katalog/design.json` och kör `python3 scripts/identitet.py`. [Designsystem](DESIGN.md)

Kör `bash scripts/check.sh` för projekttesterna. Bygg systemavbildningen från repots rot med `podman build -t localhost/forskaros .` på en Linuxvärd med Podman. CI bygger varje arkitektur på en separat värd. [Byggflöden](../.github/workflows) · [Släpprocess](RELEASE.md) · [Färdplan](ROADMAP.md)
