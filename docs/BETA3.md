# ForskarOS 2027.1-beta3

Beta3 distribuerades som en bootc-uppdatering för amd64 och arm64. Den lade till forskningsprojekt med manus, analyskod och länkar från påståenden till tabellrader och intervjuutdrag. För att återskapa miljön kan du starta från en [beta2-disk](BETA2.md) och välja beta3-avbildningen.

```bash
sudo bootc switch ghcr.io/jtensetti/researchos:2027.1-beta3
sudo systemctl reboot
```

| Avbildning | Digest |
|---|---|
| Flerarkitektursmanifest | `sha256:820de8e06a6ae38424dcd1eb7121fc83e3af27c1ef694378ac1acf3c6a4766e8` |
| amd64 | `sha256:27b1fdf10ac46174e886854f767cdd9c94514b88f3721dd744683d5df46366c6` |
| arm64 | `sha256:b6ddd247fdf8d492cc1331e3c73c11534e3d2790990e5e2cef0658f28ed6d42d` |

[Bygge och signering](https://github.com/Jtensetti/researchOS/actions/runs/44269852234) · [Källkod för beta3](https://github.com/Jtensetti/researchOS/tree/2d99075c052aad8b29c4408c238cadfd6de1bead) · [Aktuell nedladdning](../README.md#ladda-ner)
