# ForskarOS 2027.1-beta3

Beta3 är en publicerad bootc-uppdatering för amd64 och arm64. En ny VM kan starta från en av [beta2-diskarna](BETA2.md). Byt till den versionsmärkta avbildningen i den startade VM:n och starta om.

```bash
sudo bootc switch ghcr.io/jtensetti/researchos:2027.1-beta3
sudo systemctl reboot
```

Efter omstart visar `cat /usr/share/forskaros/RELEASE` den installerade ForskarOS-versionen. Öppna **ForskarOS – forskningsprojekt** och välj **Granska påståenden** i ett projekt. [Prova med en rättad observation](PROJEKT.md#pröva-en-rättelse).

GitHub Actions testade projektet och publicerade ett signerat manifest för båda arkitekturerna. Den versionsbundna referensen är `ghcr.io/jtensetti/researchos@sha256:820de8e06a6ae38424dcd1eb7121fc83e3af27c1ef694378ac1acf3c6a4766e8`. [Bygge och signering](https://github.com/Jtensetti/researchOS/actions/runs/44269852234) · [Källkod för avbildningen](https://github.com/Jtensetti/researchOS/tree/2d99075c052aad8b29c4408c238cadfd6de1bead).

De 17 installerade projektfilerna, startkommandot och versionsuppgiften inräknade, kontrollerades mot beta3-källan direkt i respektive publicerad avbildning.

| Arkitektur | Avbildningens digest |
|---|---|
| amd64 | `sha256:27b1fdf10ac46174e886854f767cdd9c94514b88f3721dd744683d5df46366c6` |
| arm64 | `sha256:b6ddd247fdf8d492cc1331e3c73c11534e3d2790990e5e2cef0658f28ed6d42d` |

En amd64-VM med den publicerade beta2-disken som grund uppgraderades med kommandot ovan. Efter en full omstart rapporterade bootc beta3-taggens amd64-digest. Forskarens befintliga projekt behöll sina granskningsbeslut. En tidigare kvantitativ körning och en nyskapad kvalitativ körning gick att upprepa i det uppgraderade systemet. På arm64 kontrollerades bygget och de publicerade filerna.

## Vad som provades

| Ändring i övningsmaterialet | Utfall |
|---|---|
| En observation ändrades från 1 till 0 för saklig respons. | Andelen byten blev 1 av 3. Påståendet om 2 av 3 fick **Ompröva**. Påståendet om den neutrala gruppen behöll **Granskad**. |
| Ett utdrag om en andra mätning rättades i intervjumaterialet. | Den kopplade tolkningen fick **Ompröva**. Påståendet som enbart byggde på handledarens auktoritet behöll **Granskad**. |
| Det citerade motbelägget ändrades, sedan togs det bort. | Ändringen syntes på de båda påståenden som använde utdraget. När det togs bort visades **Underlag saknas**. |
| Forskaren försökte bekräfta med ett äldre avtryck efter en rättelse. | Granskningen stoppades tills det ändrade underlaget kunde läsas igen. |
| De två studiernas körningar före och efter rättelsen flyttades från en amd64-VM till Debian. | Alla fyra gick att återskapa med samma SHA-256 för rapport, figur och resultattabell. Båda miljöerna använde Pandoc 3.8.3. |

I det grafiska provet öppnade ett klick på påståendet dess observationsrader i rapporten. Därifrån öppnades körningens sparade analyskod. [Skärmdump från QEMU](bilder/beta3-omprovning-qemu.png).

Kopplingarna är forskarens uttryckliga urval. En källhierarki, ett beroende eller en invändning som aldrig har registrerats behöver fortfarande upptäckas av forskaren. Provet visar spårbarhet i de här två arbetsflödena. Tidsvinsten för en forskargrupp återstår att mäta.
