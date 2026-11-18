# Installera ForskarOS på Mac

## Apple Silicon

Installera [UTM](https://mac.getutm.app/). En färdig virtuell maskin kan öppnas med ett dubbelklick. Hämta beta4-paketet medan det finns på GitHub eller importera VM-disken från Internet Archive enligt anvisningarna nedan. [UTM-paket för beta4, tillgängligt till 16 februari 2027, GitHub-inloggning krävs](https://github.com/Jtensetti/researchOS/actions/runs/44338731185/artifacts/14442862777)

1. Packa upp nedladdningen från GitHub. Där ligger `.utm.zip` och dess `.sha256` tillsammans.
2. Kör `shasum -a 256 -c ForskarOS-2027.1-beta4-arm64.utm.zip.sha256` i den uppackade mappen.
3. Packa upp `.utm.zip` och dubbelklicka på `ForskarOS.utm`. Starta maskinen i UTM.

### Importera VM-disken från Internet Archive

1. Hämta [arm64-disken](https://archive.org/download/forskaros-2027.1-beta4-arm64-vm/ForskarOS-2027.1-beta4-arm64.qcow2) och dess [kontrollsumma](https://archive.org/download/forskaros-2027.1-beta4-arm64-vm/ForskarOS-2027.1-beta4-arm64.qcow2.sha256). Kör `shasum -a 256 -c ForskarOS-2027.1-beta4-arm64.qcow2.sha256` i samma mapp.
2. Välj **Create a New Virtual Machine → Virtualize → Linux** i UTM. Välj QEMU, ARM64, fyra processorkärnor och minst 4 GB minne. Hoppa över ISO-steget.
3. Öppna maskinens inställningar. Välj **Drives → New… → Import** och välj qcow2-filen. Ta bort eventuell tom disk som UTM nyss skapat i den nya maskinen. Placera ForskarOS-disken först i startordningen. [UTM:s diskguide](https://docs.getutm.app/settings-qemu/drive/)

### Logga in och dela filer

Logga in som `forskare` med lösenordet `forskare` och välj ett nytt lösenord. Öppna sedan **ForskarOS → Nytt forskningsprojekt**.

För att dela filer väljer du **VirtFS** i maskinens delningsinställningar och anger en mapp på Macen. I ForskarOS finns mappen under `/var/mnt/delad` när den har monterats. För nätverksdelning använder du **Fildelning** i macOS och **Filer → Andra platser → Anslut till server** i ForskarOS.

## Intel-Mac

Använd amd64-ISO:n med ändelsen `-interaktiv-r2.iso`. På modeller med T2-krets kan tangentbord, styrplatta och trådlöst nätverk kräva särskilda drivrutiner. [Installera på PC eller Intel-Mac](BETA4.md#installera-på-pc) · [t2linux](https://t2linux.org/)
