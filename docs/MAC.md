# Installera DegsellOS på Mac

## Apple Silicon

Installera [UTM](https://mac.getutm.app/). En färdig virtuell maskin kan öppnas med ett dubbelklick. Hämta [UTM-maskinen](https://archive.org/download/degsellos-2027.1-beta5-arm64-vm/DegsellOS-2027.1-beta5-arm64.utm.zip) och dess [kontrollsumma](https://archive.org/download/degsellos-2027.1-beta5-arm64-vm/DegsellOS-2027.1-beta5-arm64.utm.zip.sha256) till samma mapp.

1. Kör `shasum -a 256 -c DegsellOS-2027.1-beta5-arm64.utm.zip.sha256` i mappen.
2. Packa upp `.utm.zip` och dubbelklicka på `DegsellOS.utm`. Starta maskinen i UTM.

### Importera VM-disken från Internet Archive

1. Hämta [arm64-disken](https://archive.org/download/degsellos-2027.1-beta5-arm64-vm/DegsellOS-2027.1-beta5-arm64.qcow2) och dess [kontrollsumma](https://archive.org/download/degsellos-2027.1-beta5-arm64-vm/DegsellOS-2027.1-beta5-arm64.qcow2.sha256). Kör `shasum -a 256 -c DegsellOS-2027.1-beta5-arm64.qcow2.sha256` i samma mapp.
2. Välj **Create a New Virtual Machine → Virtualize → Linux** i UTM. Välj QEMU, ARM64, fyra processorkärnor och minst 4 GB minne. Hoppa över ISO-steget.
3. Öppna maskinens inställningar. Välj **Drives → New… → Import** och välj qcow2-filen. Ta bort eventuell tom disk som UTM nyss skapat i den nya maskinen. Placera DegsellOS-disken först i startordningen. [UTM:s diskguide](https://docs.getutm.app/settings-qemu/drive/)

### Logga in och dela filer

Logga in som `forskare` med lösenordet `forskare` och välj ett nytt lösenord. Öppna sedan **DegsellOS → Nytt forskningsprojekt**.

För att dela filer väljer du **VirtFS** i maskinens delningsinställningar och anger en mapp på Macen. I DegsellOS finns mappen under `/var/mnt/delad` när den har monterats. För nätverksdelning använder du **Fildelning** i macOS och **Filer → Andra platser → Anslut till server** i DegsellOS.

## Intel-Mac

Använd installations-ISO:n för amd64. På modeller med T2-krets kan tangentbord, styrplatta och trådlöst nätverk kräva särskilda drivrutiner. [Installera på PC eller Intel-Mac](INSTALLATION.md#installera-på-pc) · [t2linux](https://t2linux.org/)
