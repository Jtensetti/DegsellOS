# ForskarOS på Mac

## Apple Silicon (M1–M5, MacBook Neo)

Linux kan i dag inte startas direkt på en MacBook Neo. Dess A18 Pro-chip har bara
[mycket tidigt stöd](https://asahilinux.org/docs/platform/feature-support/m4/) i
Asahi Linux. Därför kör vi ForskarOS i en **virtuell maskin**, vilket fungerar på
alla Apple Silicon-Macar.

1. Installera [UTM](https://mac.getutm.app/).
2. Hämta artefakten `forskaros-arm64-qcow2` från arbetsflödet
   *Bygg installationsmedia* i GitHub Actions och packa upp den.
3. I UTM: **Create a New Virtual Machine → Virtualize → Linux**.
   Välj *Import VHD/QCOW2 drive* (eller lägg till disken under *Drives*).
4. Ge maskinen minst **4 GB RAM** (8 GB rekommenderas om du ska köra lokal AI)
   och 4 CPU-kärnor.
5. Starta. GNOME:s välkomstguide skapar ditt konto. Kör sedan
   *ForskarOS – installera verktyg* från programmenyn.

> **Ej verifierat än:** att disken startar i UTM och att välkomstguiden
> skapar kontot. Det är det första vi testar tillsammans på din MacBook Neo.

## Varför inte direkt uppstart?

| Chip | Asahi Linux-stöd |
|---|---|
| M1, M2 | Moget. Installeras från macOS med Asahis installerare (dual boot) |
| M3 | Nyligen officiellt stöd, men utan GPU-acceleration |
| M4, M5, A18 Pro (Neo) | Tidigt utvecklingsarbete, går inte att installera |

När Asahi stödjer Neo kan vi lägga till en Asahi-baserad avbildning. Vaulten och
tillägget följer med oförändrade.

## Intel-Mac

Använd installations-ISO:n för amd64 (`forskaros-amd64-anaconda-iso`).
Macar med T2-chip (2018–2020) kan behöva [t2linux](https://t2linux.org/)-patchar
för tangentbord, styrplatta och wifi.
