# Paketera en UTM-maskin

`vm/utm/config.plist` är en ARM64-mall för UTM:s QEMU-backend. Den har UEFI, VirtIO-disk, bildskärm, delat nätverk och VirtFS för delade mappar. Paketeraren ger varje bygge en ny maskinidentitet och nätverksadress. När du startar maskinen första gången skapar UTM dess EFI-variabler.

Mallen är anpassad från [Homebridges UTM-maskin](https://github.com/homebridge/homebridge-vm-image/blob/49aed1492c2929326ce54e3a980c3ca26dedfca4/assets/template-utm-config.plist). Tredjepartslicensen i `config.LICENSE` följer med i paketet.

Kör från repots rot med DegsellOS-disken för den utgåva du vill paketera.

```bash
python3 scripts/paketera_utm.py vm/utm/config.plist \
  ForskarOS-2027.1-beta4-arm64.qcow2 ForskarOS-2027.1-beta4-arm64.utm.zip --minne 4096
```

Packa upp arkivet på Macen och dubbelklicka på `DegsellOS.utm`. Välj eventuell delad mapp i maskinens inställningar. [Mac-guide](../../docs/MAC.md)
