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

I en 275 pixlar bred sidopanel fick alla sju fasnamn plats över fyra rader. Fysisk hårdvara, UTM på en Mac och en genomförd installation från ISO återstår att pröva.

### Första inloggningen på den publicerade PC-disken

Den 18 november 2026 hämtades den 3 922 984 960 byte stora amd64-disken från Internet Archive på nytt. SHA-256 stämde med tabellen ovan. QEMU startade från en tom skrivbar överlagring med UEFI, fyra virtuella processorer och 4 GiB minne.

Efter lösenordsbytet öppnades ForskarOS verktygslåda. Det första installationsförsöket nådde inte Flathub eftersom gästens DNS inte kunde slå upp värdnamnet. Efter att testnätets proxy och dess rotcertifikat hade ställts in gick samma menyval igenom. Verktygslådan installerade Obsidian 1.15.1 från Flathub. Därefter valdes `~/ForskarOS` i mappväljaren och det medföljande Core 0.3.1 aktiverades i Obsidians förtroendedialog.

Med *Ny forskningsfråga* skapades ”Hur ofta byter elever hypotes efter konkret respons?”. Motiveringen beskrev ett sätt att skilja förståelse från följsamhet. Core sparade frågan som en lokal Markdown-fil med status `aktiv` och fas `utforska`.

Obsidian stängdes och hela VM:n startades om. Efter ny inloggning öppnades samma fråga och motivering i Obsidian. Gammalt och nytt Linux-start-ID skilde sig åt. Anteckningens SHA-256 var `4887c364db4c1a312c298243a0b050265edf5b13b75529d040536e531eeb0264` både före och efter omstarten. [Skärmdump direkt från QEMU efter omstarten](bilder/beta2-forskningsfraga-qemu.png).

### Vad fasmarkeringarna visar

Tre små prov kördes direkt mot regelmotorn i Core 0.3.1. Provfrågan gällde varför elever byter hypotes efter återkoppling. Två möjliga förklaringar var att eleven förstått belägget och att eleven följer lärarens signal. Ett sätt att skilja dem åt är att ge eleven en ny uppgift utan läraren och be eleven motivera sitt svar.

| Prov | Utfall i beta2 |
|---|---|
| Bara den första hypotesen hade en förutsägelse. Bara den andra hade ett falsifieringskriterium och angiven konfidens. Frågans motivering och avgränsning var ifyllda. | Alla fem krav i *Välj* blev godkända. Ingen enskild hypotes innehöll alla tre uppgifterna. |
| Ett experiment hade status `planerat`. Under *Resultat* stod ”Inga data har samlats in ännu.” | Kravet på ett experiment eller arbetsprov med resultat blev godkänt. |
| En testbar förutsägelse på 17 ord jämfördes med ”Jag ska fundera på det.” upprepat tio gånger. | Bara den upprepade texten nådde gränsen på 50 egna ord för AI:s prövningsläge. |

Som jämförelse installerades forskningsmappen med `scripts/install-vault.sh` på en Linuxvärd utanför ForskarOS. En rekursiv filjämförelse visade att den innehöll samma mallar och tillägg som källträdet för beta2. Den installerade Core-filen `main.js` hade också samma SHA-256 på Linuxvärden som i den nystartade VM:ns forskningsmapp.

## Internet Archive

Den 18 november 2026 hämtades samtliga tre originalfiler i sin helhet från Internet Archive. För varje fil stämde den beräknade SHA-256-summan både med byggresultatet i tabellen ovan och med den `.sha256`-fil som publicerats på samma arkivpost. [Verifiering av de tre nedladdningarna](https://github.com/Jtensetti/researchOS/actions/runs/44221943913).

| Arkivpost | Originalfil | SHA-256 |
|---|---|---|
| [VM för PC](https://archive.org/details/forskaros-2027.1-beta2-amd64-vm) | [ForskarOS-2027.1-beta2-amd64.qcow2](https://archive.org/download/forskaros-2027.1-beta2-amd64-vm/ForskarOS-2027.1-beta2-amd64.qcow2) | [Kontrollsumma](https://archive.org/download/forskaros-2027.1-beta2-amd64-vm/ForskarOS-2027.1-beta2-amd64.qcow2.sha256) |
| [VM för Apple Silicon](https://archive.org/details/forskaros-2027.1-beta2-arm64-vm) | [ForskarOS-2027.1-beta2-arm64.qcow2](https://archive.org/download/forskaros-2027.1-beta2-arm64-vm/ForskarOS-2027.1-beta2-arm64.qcow2) | [Kontrollsumma](https://archive.org/download/forskaros-2027.1-beta2-arm64-vm/ForskarOS-2027.1-beta2-arm64.qcow2.sha256) |
| [Installations-ISO](https://archive.org/details/forskaros-2027.1-beta2-amd64-iso) | [ForskarOS-2027.1-beta2-amd64.iso](https://archive.org/download/forskaros-2027.1-beta2-amd64-iso/ForskarOS-2027.1-beta2-amd64.iso) | [Kontrollsumma](https://archive.org/download/forskaros-2027.1-beta2-amd64-iso/ForskarOS-2027.1-beta2-amd64.iso.sha256) |

Vid uppladdningen den 17 november fördröjde Archives kvotkontroll publiceringen. De redan uppladdade filerna blev tillgängliga på de tre befintliga posterna. [Tidigare omkörning](https://github.com/Jtensetti/researchOS/actions/runs/44168783298) · [Diagnos](https://github.com/Jtensetti/researchOS/actions/runs/44169257154).
