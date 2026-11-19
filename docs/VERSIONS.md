# Utgåvor och kontrollsummor

Använd den senaste förhandsversionen för en ny installation. Äldre utgåvor finns kvar för att kunna återskapa tidigare miljöer. [Installationsguide](INSTALLATION.md) · [Ändringslogg](../CHANGELOG.md)

## 2027.1-beta4

| Plattform | Originalfil | SHA-256 |
|---|---|---|
| PC och Intel-Mac | [Interaktiv ISO, revision r2](https://archive.org/download/forskaros-2027.1-beta4-amd64-iso/ForskarOS-2027.1-beta4-amd64-interaktiv-r2.iso) | `289914752f514402f77b21f7b584c9ed6c0b1fadbe214a01bf254ac813e82099` |
| Virtuell PC | [VM-disk för amd64](https://archive.org/download/forskaros-2027.1-beta4-amd64-vm/ForskarOS-2027.1-beta4-amd64.qcow2) | `e07bd61f2fca2b6e40830b9122171c184dc2bf14a674124835550e3110f84105` |
| Apple Silicon | [VM-disk för arm64](https://archive.org/download/forskaros-2027.1-beta4-arm64-vm/ForskarOS-2027.1-beta4-arm64.qcow2) | `4a56bfd88ae2ca2a978dccf2b50018d7478a701fd60053f5d4f302e0b5074c60` |

Jämför den hämtade filens SHA-256 med värdet i tabellen. På Linux kan du använda `sha256sum FILNAMN`, på macOS `shasum -a 256 FILNAMN` och i PowerShell `Get-FileHash FILNAMN -Algorithm SHA256`.

**Använd ISO-revisionen `-interaktiv-r2.iso`.** Den ursprungliga beta4-ISO:n kan partitionera anslutna diskar automatiskt. Revisionen `-interaktiv.iso` kan stanna vid svenskt språkval. [Diskval och installation](INSTALLATION.md#installera-på-pc)

Det signerade flerarkitektursmanifestet för beta4 har digest `sha256:a2aa2f6d758df4c6cc4b11cfddcffcb0fb46460b2cd4796473e3d83600189bc0`. [Systemavbildning](https://github.com/Jtensetti/DegsellOS/actions/runs/44297403777) · [Installations-ISO](https://github.com/Jtensetti/DegsellOS/actions/runs/44313541729)

## 2027.1-beta3

Beta3 distribuerades som en bootc-uppdatering för amd64 och arm64. Den lade till forskningsprojekt med manus, analyskod och länkar från påståenden till tabellrader och intervjuutdrag. För att återskapa miljön kan du starta från en [beta2-disk](#20271-beta2) och välja beta3-avbildningen.

```bash
sudo bootc switch ghcr.io/jtensetti/researchos:2027.1-beta3
sudo systemctl reboot
```

| Avbildning | Digest |
|---|---|
| Flerarkitektursmanifest | `sha256:820de8e06a6ae38424dcd1eb7121fc83e3af27c1ef694378ac1acf3c6a4766e8` |
| amd64 | `sha256:27b1fdf10ac46174e886854f767cdd9c94514b88f3721dd744683d5df46366c6` |
| arm64 | `sha256:b6ddd247fdf8d492cc1331e3c73c11534e3d2790990e5e2cef0658f28ed6d42d` |

[Bygge och signering](https://github.com/Jtensetti/DegsellOS/actions/runs/44269852234) · [Källkod för beta3](https://github.com/Jtensetti/DegsellOS/tree/2d99075c052aad8b29c4408c238cadfd6de1bead) · [Aktuell nedladdning](../README.md#ladda-ner)

## 2027.1-beta2

Beta2 innehåller DegsellOS Core 0.3.1 och en verktygsmeny som öppnas vid första inloggningen. För att använda Core, installera Obsidian från verktygsmenyn och öppna `~/DegsellOS` som valv.

| Medium | Nedladdning | SHA-256 |
|---|---|---|
| Virtuell PC | [amd64 qcow2](https://archive.org/download/degsellos-2027.1-beta2-amd64-vm/DegsellOS-2027.1-beta2-amd64.qcow2) | `755784ff18e305eb880bddd78258a9203610802fb724f230378127450d5322c6` |
| Virtuell ARM64-maskin | [arm64 qcow2](https://archive.org/download/degsellos-2027.1-beta2-arm64-vm/DegsellOS-2027.1-beta2-arm64.qcow2) | `bb6c70e9eb058f0b01c5af106d0ea5e0541e899d4c67963622dd6a78db98d6bf` |
| Installation på virtuell PC | [amd64 ISO](https://archive.org/download/degsellos-2027.1-beta2-amd64-iso/DegsellOS-2027.1-beta2-amd64.iso) | `504ccca93bf106a35084102f36a89158d4a468c5ecaa1ad721a8c2483fbf8f8d` |

Det signerade systemmanifestet har digest `sha256:827a5b51be407b9d163881b9eeb39dfdd6f4cef1025bb180b210e91d2d4fb2fa`. [Källkod för beta2](https://github.com/Jtensetti/DegsellOS/commit/751099d6ac0dd275d7c536019e22257ad21b07fd) · [Aktuell nedladdning](../README.md#ladda-ner)

## 2027.1-beta1

Den första förhandsversionen innehåller GNOME på Bluefin LTS och DegsellOS Core 0.3.0 för Obsidian. PC-disken använder UEFI. Logga in som `forskare` med lösenordet `forskare` och välj ett nytt lösenord.

| Medium | SHA-256 |
|---|---|
| [VM-disk för amd64](https://archive.org/download/degsellos-2027.1-beta1-amd64-vm/DegsellOS-2027.1-beta1-amd64.qcow2) | `d04096edb9629ec6be759a3d722ea85ee8ae8e2e8554c3169ecf9b7e07b781fa` |

[Källkod för beta1](https://github.com/Jtensetti/DegsellOS/commit/b9cf4f5cc020d2beca76150be92cab2b17bf9f87) · [Aktuell nedladdning](../README.md#ladda-ner)
