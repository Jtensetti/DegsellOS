# Paketera en UTM-maskin

Den publicerade arm64-disken kan importeras direkt enligt [Mac-guiden](../../docs/MAC.md). Med en egen UTM-mall kan du dessutom skapa ett paket som kan öppnas i UTM efter uppackning.

1. Skapa en QEMU-baserad ARM64/Linuxmaskin i UTM på Mac. Använd UEFI, VirtIO-disk, bildskärm och delat nätverk. Behåll den inbyggda ikonen. Låt eventuella flyttbara enheter vara tomma.
2. Spara maskinen, välj **Visa i Finder** och öppna **Visa paketinnehåll** för att hitta `config.plist`.
3. Kör kommandot nedan från repots rot med sökvägen till den sparade filen och den hämtade ForskarOS-disken.

```bash
python3 scripts/paketera_utm.py /sökväg/till/config.plist \
  ForskarOS-2027.1-beta4-arm64.qcow2 ForskarOS.utm.zip
```

Paketet innehåller en ny maskinidentitet och en kopia av ForskarOS-disken. Packa upp det på Macen och öppna `ForskarOS.utm`. Välj eventuell delad mapp i maskinens inställningar på den Mac där maskinen ska köras.
