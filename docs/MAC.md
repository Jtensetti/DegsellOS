# ForskarOS på Mac

## Apple Silicon

Importera beta4:s arm64-disk i en virtuell Linuxmaskin. Du behöver [UTM](https://mac.getutm.app/) och [arm64-filen med tillhörande kontrollsumma](../README.md#ladda-ner).

1. Hämta både `.qcow2` och `.sha256` till samma mapp. Kontrollera nedladdningen där med `shasum -a 256 -c ForskarOS-2027.1-beta4-arm64.qcow2.sha256`.
2. Välj **Create a New Virtual Machine → Virtualize → Linux** i UTM. Använd QEMU som backend och välj ARM64 som arkitektur. Hoppa över ISO-steget. Ge maskinen 4 CPU-kärnor och minst 4 GB minne.
3. Öppna maskinens inställningar. Välj **Drives → New… → Import** och välj den hämtade qcow2-filen. Om UTM skapade en extra tom disk tar du bort den från den nya virtuella maskinen. Flytta den importerade disken överst i startordningen. [UTM:s diskguide](https://docs.getutm.app/settings-qemu/drive/drive/)
4. Logga in som **forskare** med lösenordet **forskare** och välj ett nytt lösenord. Öppna **ForskarOS → Nytt forskningsprojekt**. Exempelprojekten fungerar medan grundverktygen hämtas.

Den publicerade arm64-disken har startprovats i QEMU. Första inloggningen, delad mapp och labbet på en fysisk MacBook Neo återstår att verifiera. [Färdplan](ROADMAP.md)

## Dela filer med Macen

Välj en mapp att dela i UTM:s inställningar. ForskarOS försöker montera den vid `/var/mnt/delad` via virtiofs eller 9p. När den är monterad kan du öppna sökvägen i **Filer**. Vid inloggning kan en genväg även visas som `~/Delad`.

För nätverksdelning kan du aktivera **Fildelning** under **Systeminställningar → Allmänt → Delning** i macOS. Öppna sedan **Filer → Andra platser → Anslut till server** i ForskarOS och ange Macens SMB-adress.

## Intel-Mac

För installation på en Intel-Mac används amd64-ISO:n med ändelsen `-interaktiv-r2.iso`. Kontrollera diskvalet innan du startar installationen. T2-modeller kan behöva särskilda drivrutiner för tangentbord, styrplatta och wifi. [Installationsguide](BETA4.md#installera-på-pc) · [t2linux](https://t2linux.org/)
