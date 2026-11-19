# DegsellOS

DegsellOS är en Linuxdistribution för forskare som vill kunna följa en slutsats tillbaka till underlaget. I skrivbordsappen kopplar du en mening i ditt manus till exempelvis en tabellrad eller ett intervjuutdrag. Rättar du utdraget markerar appen vilka meningar du behöver läsa om.

Varje analys sparas tillsammans med data, kod och rapport. En kollega kan öppna rapporten, följa en källhänvisning och köra om analysen. Skrivbordet är GNOME på Bluefin LTS.

![En rättelse i intervjumaterialet har markerat ett av manusets tre påståenden för omprövning.](docs/bilder/degsellos-projekt.png)

## Ladda ner

**Förhandsversion 2027.1-beta4**

| Dator | Nedladdning | Installation |
|---|---|---|
| PC, virtuell maskin | [VM-disk för amd64](https://archive.org/download/degsellos-2027.1-beta4-amd64-vm/DegsellOS-2027.1-beta4-amd64.qcow2) | Importera disken i QEMU eller virt-manager och välj UEFI. |
| Mac med Apple Silicon | [VM-disk för arm64](https://archive.org/download/degsellos-2027.1-beta4-arm64-vm/DegsellOS-2027.1-beta4-arm64.qcow2) | [Öppna disken i UTM](docs/MAC.md) |
| PC eller Intel-Mac, installation på disk | [Installations-ISO för amd64, revision r2](https://archive.org/download/degsellos-2027.1-beta4-amd64-iso/DegsellOS-2027.1-beta4-amd64-interaktiv-r2.iso) | [Installera på PC](docs/INSTALLATION.md#installera-på-pc) · [Intel-Mac](docs/MAC.md#intel-mac) |

I en färdig VM är både användarnamn och lösenord `forskare`. Du väljer ett eget lösenord vid första inloggningen. På fysisk disk, använd ISO-filen som slutar på `-interaktiv-r2.iso` och kontrollera vilka diskar som är markerade. Den ursprungliga beta4-ISO:n kan radera anslutna diskar automatiskt. [Kontrollsummor för nedladdningarna](docs/VERSIONS.md#20271-beta4)

## Ditt första projekt

Öppna **DegsellOS → Nytt forskningsprojekt**. Välj observationstabeller eller kodade intervjuutdrag för att börja med exempeldata. Under **Granska** ser du meningen i manuset och de källor du kopplat till den. Välj **Bygg rapport** för att spara en körning och **Upprepa** för att kontrollera resultaten. [Guide till forskningsprojekt](docs/PROJEKT.md)

Du kan även använda **DegsellOS Core** i en befintlig Obsidian-installation. Tillägget samlar forskningsfrågor, hypoteser och granskningsbeslut i lokala Markdown-filer. [Installera Core](docs/CORE.md)

[Dokumentation](docs/README.md) · [Verktygskatalog](vault/00%20START/Verktyg/Översikt.md) · [Projektskydd](docs/SECURITY.md) · [Bidra och bygga från källkod](CONTRIBUTING.md) · [Ändringslogg](CHANGELOG.md) · [MIT-licens](LICENSE)

`main` innehåller utvecklingsversionen. Förändringar efter beta4 beskrivs under *Under utveckling* i ändringsloggen.
