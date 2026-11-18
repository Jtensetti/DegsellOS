# ForskarOS 2027.1-beta4

Beta4 samlar forskningsprojekten i en egen skrivbordsapp. Ett påstående kan knytas till en tabellrad, en fil eller en citerad passage med referens och sida. Projektet sparar granskningsbeslutet och visar när forskaren behöver läsa underlaget igen. För ett skyddat projekt kör systemet analys och rapportbygge i en sandlåda. Arbetsflödet går att använda utan Obsidian.

## Installationsmedier

| Plattform | Original från Internet Archive | Storlek i byte | SHA-256 |
|---|---|---:|---|
| Interaktiv installation på PC | [ForskarOS-2027.1-beta4-amd64-interaktiv-r2.iso](https://archive.org/download/forskaros-2027.1-beta4-amd64-iso/ForskarOS-2027.1-beta4-amd64-interaktiv-r2.iso) | 4 658 583 552 | `289914752f514402f77b21f7b584c9ed6c0b1fadbe214a01bf254ac813e82099` |
| Virtuell PC | [ForskarOS-2027.1-beta4-amd64.qcow2](https://archive.org/download/forskaros-2027.1-beta4-amd64-vm/ForskarOS-2027.1-beta4-amd64.qcow2) | 3 968 204 800 | `e07bd61f2fca2b6e40830b9122171c184dc2bf14a674124835550e3110f84105` |
| Apple Silicon (UTM) | [ForskarOS-2027.1-beta4-arm64.qcow2](https://archive.org/download/forskaros-2027.1-beta4-arm64-vm/ForskarOS-2027.1-beta4-arm64.qcow2) | 3 744 989 184 | `4a56bfd88ae2ca2a978dccf2b50018d7478a701fd60053f5d4f302e0b5074c60` |

Hela originalfilerna hämtades från Internet Archive. För varje fil stämde den lokalt beräknade SHA-256 med både byggjobbets separat sparade kvitto och kontrollsummefilen på Archive.

[Bygge, signering och startprov av båda VM-diskarna](https://github.com/Jtensetti/researchOS/actions/runs/44297403777) · [Bygge av den interaktiva ISO:n](https://github.com/Jtensetti/researchOS/actions/runs/44313541729) · [Systemets källkod](https://github.com/Jtensetti/researchOS/tree/30bd0b6b472aa7da524a1ed13252afbccd72dad9). Båda byggena utgår från samma publicerade systemavbildning, `ghcr.io/jtensetti/researchos@sha256:a2aa2f6d758df4c6cc4b11cfddcffcb0fb46460b2cd4796473e3d83600189bc0`.

### Om du redan hämtat den första ISO:n

Den första filen, `ForskarOS-2027.1-beta4-amd64.iso`, började partitionera den tomma provdisken direkt efter startmenyn. Använd den endast i en tom virtuell maskin. Den ligger kvar i arkivet med en varning för den som redan har laddat ned den. Den mellanliggande filen `ForskarOS-2027.1-beta4-amd64-interaktiv.iso` kunde stanna vid svenskt språkval. Filen i tabellen ovan slutar på `-interaktiv-r2.iso`. Bygget kontrollerar installerarens konfiguration inuti den färdiga filen före uppladdning.

## Installera på PC

1. Starta filen med `-interaktiv-r2.iso` i namnet. Startmenyn kallar systemet **Bluefin LTS 10**. Välj **Svenska (Sverige)**.
2. Öppna **Installationsmål**. Kontrollera diskarnas namn och storlek. I provet var båda diskarna förvalda. Jag avmarkerade datadisken och kontrollerade att sammanfattningen visade **1 disk vald** innan jag valde **Klar**. [Så såg det ut med två virtuella diskar](bilder/beta4-diskval-qemu.png).
3. Kontrollera tangentbord och tidszon. Vill du hämta grundverktygen vid första inloggningen kan du aktivera nätverkskortet under **Nätverk & värdnamn**. Du kan också skapa ditt lokala konto här.
4. Välj **Börja Installation** när uppgifterna stämmer. Vid installationsprovets start hade den valda 48 GiB-disken fortfarande noll skrivna gästsektorer. Den separata 32 GiB-disken var identisk med provkopian.

Den publicerade revisionen gick förbi det svenska språkvalet och inväntade bekräftelse. Kontrollen efter installationen på de två anslutna diskarna pågår.

## Forskarens arbetsprov

På en tom virtuell PC installerades den signerade amd64-avbildningen från den första ISO:n. Installationsmediet matades ut. Efter omstart visade systemet `2027.1-beta4`, arkitekturen `x86_64` och SELinux `Enforcing`. Bootc rapporterade det inbäddade amd64-manifestet `sha256:546495317c07bbcb40f14e17c7056713b72d5dae06be75ecac31b7ed8e0b0ab2`. Jag jämförde den slutliga ISO:ns OCI-konfiguration och samtliga 73 okomprimerade lageridentifierare med det signerade registrets amd64-avbildning. De stämde. Den svenska GNOME-guiden skapade ett lokalt konto. ForskarOS öppnades automatiskt vid första inloggningen. Grundverktygen väntade då på nätåtkomst.

Jag skapade det skyddade kvalitativa projektet *Vad får en forskare att ändra sig* i appen. Allt intervjumaterial var konstruerat. Provet omfattade följande arbetsgång.

| I den installerade arbetsstationen | Resultat |
|---|---|
| Läste och granskade manusets tre påståenden i tur och ordning. | För materialets ursprung visades ett citat med referens och sida. För tolkningen visades både det kodade intervjuutdraget och ett motbelägg. |
| Valde **Bygg rapport** och **Upprepa** i appen. | Rapport, figur och resultattabell fick samma SHA-256 vid upprepningen. Körningen fick RO-Crate-metadata och registrerade bubblewrap 0.10.0, avstängt nätverk och dold hemkatalog. Nästa steg blev **Läs rapporten lokalt**. |
| Importerade en korrigerad CSV i Taguettes format genom filväljaren. | Intervju A ändrades från ”Jag bytte när den andra mätningen gav samma resultat” till ”Jag stod fast även efter den andra mätningen”. Precis ett av tre påståenden fick **Ompröva**. Knappen **Granska** öppnade rätt mening. De andra två behöll sina granskningsbeslut. |
| Öppnade rapporten från den tidigare körningen och upprepade den igen. | Den äldre rapporten visade den ursprungliga tolkningen och gick fortfarande att återskapa med samma kontrollsummor. Den inbyggda läsaren fungerade innan någon extern webbläsare hade installerats. |

[Projektet efter rättelsen](bilder/beta4-installation-qemu.png) · [Tolkningen och de två intervjuutdragen](bilder/beta4-motbelagg-qemu.png). Båda skärmdumparna kommer från det installerade systemet i QEMU med de medföljande skrivbordsinställningarna.

## Är ett helt operativsystem motiverat?

För en forskargrupp som vill kunna skicka samma arbetsmiljö till en kollega finns ett konkret skäl. I den rena installationen gick det att granska en källa, köra en analys med avstängt nätverk och återskapa rapporten innan externa program var på plats. Det blev också tydligt *vilken mening* som måste läsas om när data ändrades. För en forskare som främst läser och skriver i ett befintligt Zotero- och Obsidian-bibliotek räcker det här provet knappast som skäl att byta operativsystem.

Två saker kostade uppmärksamhet. Installationsprogrammet och GNOME:s välkomstguide presenterade systemet som Bluefin LTS. Först efter inloggningen blev det tydligt att jag hade installerat rätt produkt. I själva granskningsvyn stod det rättade citatet fortfarande under **Stöd**, eftersom det var den roll forskaren ursprungligen hade gett det. Citatet sade nu motsatsen till meningen. Jag skulle prioritera att visa gammalt och nytt citat intill varandra och ge **Ändra meningen** lika stor vikt som att bekräfta. Därefter kommer direktimport av markerade passager från Zotero, med referens, sida och citat bevarade.

Provet visar hur en registrerad koppling reagerar på en ändring. Att upptäcka ett oregistrerat motbelägg, värdera en tolkning och avgöra om en studie håller är fortfarande forskarens uppgifter. Tidsvinsten för en forskargrupp behöver mätas i användartester. Isoleringen gäller analys och rapportbygge. [Projektskyddets omfattning](FORSKAROS-3.md#hotmodell-för-skyddade-projekt).
