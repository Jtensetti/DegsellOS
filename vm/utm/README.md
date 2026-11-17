# UTM-mall

`config.plist` här blir mallen för det färdiga UTM-paketet (`ForskarOS.utm.zip`).
Den ska skapas av UTM självt, så att formatet alltid stämmer med UTM:s version.

## Så skapar du mallen (en gång, cirka två minuter)

1. Öppna UTM → **Create a New Virtual Machine → Virtualize → Linux**.
2. Välj **QEMU** (inte Apple Virtualization), hoppa över ISO-bilden.
3. Minne 8192 MB, 4 CPU-kärnor, disk valfri storlek (den byts ut).
4. Under *Shared Directory*: välj en mapp på din Mac om du vill dela filer.
5. Spara. Högerklicka på maskinen → **Show in Finder** → högerklicka på
   `.utm`-filen → **Visa paketinnehåll** → kopiera `config.plist`.
6. Lägg filen här som `vm/utm/config.plist`.

Byggskriptet `scripts/paketera_utm.py` byter namn, disk, minne, CPU och
MAC-adress och behåller resten av UTM:s inställningar.
