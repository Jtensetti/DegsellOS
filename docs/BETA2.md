# ForskarOS 2027.1-beta2

Samtliga tre medier utgår från [samma källkod](https://github.com/Jtensetti/researchOS/commit/751099d6ac0dd275d7c536019e22257ad21b07fd) och samma signerade manifest, `ghcr.io/jtensetti/researchos@sha256:827a5b51be407b9d163881b9eeb39dfdd6f4cef1025bb180b210e91d2d4fb2fa`. [Bygge och medietester i GitHub Actions](https://github.com/Jtensetti/researchOS/actions/runs/44161601161).

| Medium | Prov på beta2 | SHA-256 från uppladdningens kontrollsummefil |
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

Den 17 november 2026 accepterade Internet Archive uppladdningen av samtliga tre medier. Vid efterkontrollen gick bara deras kontrollsummefiler att hämta. På varje post stod ett `book_op.php`-jobb i felläge före jobbet som lägger ut avbildningen. Archives Tasks API accepterade en omkörning per post, varefter loggarna åter visade fel i kvotkontrollen. Orsaken bakom kvotfelet och tidpunkten för en eventuell återställning är okända. [Omkörning](https://github.com/Jtensetti/researchOS/actions/runs/44168783298) · [Diagnos](https://github.com/Jtensetti/researchOS/actions/runs/44169257154).

| Arkivpost | Felande jobb |
|---|---|
| [VM för PC](https://archive.org/details/forskaros-2027.1-beta2-amd64-vm) | 5765734181 |
| [VM för Apple Silicon](https://archive.org/details/forskaros-2027.1-beta2-arm64-vm) | 5765738984 |
| [Installations-ISO](https://archive.org/details/forskaros-2027.1-beta2-amd64-iso) | 5765734950 |

Kontrollsummorna i tabellen ovan identifierar de filer som byggdes. En fullständig nedladdning och jämförelse återstår för varje arkivpost.
