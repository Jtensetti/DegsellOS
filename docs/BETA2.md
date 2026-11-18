# ForskarOS 2027.1-beta2

Samtliga tre medier utgår från [samma källkod](https://github.com/Jtensetti/researchOS/commit/751099d6ac0dd275d7c536019e22257ad21b07fd) och samma signerade manifest, `ghcr.io/jtensetti/researchos@sha256:827a5b51be407b9d163881b9eeb39dfdd6f4cef1025bb180b210e91d2d4fb2fa`. [Bygge och medietester i GitHub Actions](https://github.com/Jtensetti/researchOS/actions/runs/44161601161).

| Medium | Prov på beta2 | Verifierad SHA-256 för hela originalfilen |
|---|---|---|
| amd64 qcow2 | UEFI-start i QEMU, Linux-gästen rapporterade x86_64 och kärnversion | `755784ff18e305eb880bddd78258a9203610802fb724f230378127450d5322c6` |
| arm64 qcow2 | UEFI-start i QEMU, Linux-gästen rapporterade aarch64 och kärnversion | `bb6c70e9eb058f0b01c5af106d0ea5e0541e899d4c67963622dd6a78db98d6bf` |
| amd64 ISO | Startkatalogen innehöll en UEFI-startpost | `504ccca93bf106a35084102f36a89158d4a468c5ecaa1ad721a8c2483fbf8f8d` |

## Forskarens första fråga

Vid första inloggningen visar verktygslådan hur installationen går. Den kan öppna Obsidian, visa startsidan som text och hämta de senaste installationsmeddelandena. I ett prov med simulerat nätfel gick det att fortsätta till den lokala startsidan direkt efter en misslyckad installation. Licensfrågan för Obsidian kräver ett uttryckligt svar även med `--ja`.

Core 0.3.1 från beta2 provades separat i Obsidian 1.15.1 i den [tidigare amd64-testmaskinen](VM-TEST-2026-11-17.md). Obsidian var manuellt installerat där. Arbetsmetodens 22 begrepp ingår även i den ordinarie kontrollsviten.

| Anteckning | Utfall i den riktiga AI-dialogen |
|---|---|
| 0 egna ord | Inget valt läge, tom förhandsvisning och avstängd kopiering. Ett uttryckligt val av prestation aktiverade knappen och skapade en lokal loggpost med `egen_tanke_först: nej`. |
| 49 egna ord | Samma utgångsläge. Utveckling och prövning var spärrade. |
| 50 egna ord | Utveckling var förvalt och texten gick att kopiera. |

I en 275 pixlar bred sidopanel fick alla sju fasnamn plats över fyra rader. Fysisk hårdvara, UTM på en Mac, en genomförd installation från ISO och den fullständiga Flatpak-installationen återstår att pröva.

## Internet Archive

Den 18 november 2026 hämtades samtliga tre originalfiler i sin helhet från Internet Archive. För varje fil stämde den beräknade SHA-256-summan både med byggresultatet i tabellen ovan och med den `.sha256`-fil som publicerats på samma arkivpost. [Verifiering av de tre nedladdningarna](https://github.com/Jtensetti/researchOS/actions/runs/44221943913).

| Arkivpost | Originalfil | SHA-256 |
|---|---|---|
| [VM för PC](https://archive.org/details/forskaros-2027.1-beta2-amd64-vm) | [ForskarOS-2027.1-beta2-amd64.qcow2](https://archive.org/download/forskaros-2027.1-beta2-amd64-vm/ForskarOS-2027.1-beta2-amd64.qcow2) | [Kontrollsumma](https://archive.org/download/forskaros-2027.1-beta2-amd64-vm/ForskarOS-2027.1-beta2-amd64.qcow2.sha256) |
| [VM för Apple Silicon](https://archive.org/details/forskaros-2027.1-beta2-arm64-vm) | [ForskarOS-2027.1-beta2-arm64.qcow2](https://archive.org/download/forskaros-2027.1-beta2-arm64-vm/ForskarOS-2027.1-beta2-arm64.qcow2) | [Kontrollsumma](https://archive.org/download/forskaros-2027.1-beta2-arm64-vm/ForskarOS-2027.1-beta2-arm64.qcow2.sha256) |
| [Installations-ISO](https://archive.org/details/forskaros-2027.1-beta2-amd64-iso) | [ForskarOS-2027.1-beta2-amd64.iso](https://archive.org/download/forskaros-2027.1-beta2-amd64-iso/ForskarOS-2027.1-beta2-amd64.iso) | [Kontrollsumma](https://archive.org/download/forskaros-2027.1-beta2-amd64-iso/ForskarOS-2027.1-beta2-amd64.iso.sha256) |

Vid uppladdningen den 17 november fördröjde Archives kvotkontroll publiceringen. De redan uppladdade filerna blev tillgängliga på de tre befintliga posterna. [Tidigare omkörning](https://github.com/Jtensetti/researchOS/actions/runs/44168783298) · [Diagnos](https://github.com/Jtensetti/researchOS/actions/runs/44169257154).
