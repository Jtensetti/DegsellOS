# ForskarOS på Mac

## Apple Silicon (M1–M5, MacBook Neo)

Linux kan i dag inte startas direkt på en MacBook Neo. Dess A18 Pro-chip har bara
[mycket tidigt stöd](https://asahilinux.org/docs/platform/feature-support/m4/) i
Asahi Linux. Därför kör vi ForskarOS i en **virtuell maskin**, vilket fungerar på
alla Apple Silicon-Macar.

1. Installera [UTM](https://mac.getutm.app/).
2. Ladda ner `ForskarOS-<version>-arm64.qcow2` från Internet Archive
   (länkar under *Ladda ner* i README). Välj direktlänken, eller torrenten
   om du har en torrentklient. Kontrollera gärna filen mot `.sha256`.
3. I UTM: **Create a New Virtual Machine → Virtualize → Linux**.
   Hoppa över ISO-steget, och lägg sedan till qcow2-filen under *Drives*
   som en befintlig disk (*Import*). Ta bort den tomma disken UTM skapade.
4. Ge maskinen minst **4 GB RAM** (8 GB rekommenderas om du ska köra lokal AI)
   och 4 CPU-kärnor.
5. Starta och logga in som **forskare** med lösenordet **forskare**. Du måste
   byta lösenord direkt. Vid första
   inloggningen öppnas *ForskarOS – verktygslåda* där du väljer verktyg.

När UTM-mallen finns (se `vm/utm/README.md`) blir steg 2–4 ett enda steg:
packa upp `ForskarOS.utm.zip` och dubbelklicka.

## Dela filer mellan Mac och ForskarOS

- **Apple Virtualization-läget** i UTM delar mappar via virtiofs. ForskarOS
  monterar den delade mappen automatiskt, och den syns som `~/Delad`.
- **QEMU-läget** delar via 9p, som basens kärna troligen saknar. Använd då
  nätverksdelning: på Macen, *Systeminställningar → Allmänt → Delning →
  Fildelning*. I ForskarOS: *Filer → Andra platser → Anslut till server* och
  skriv `smb://192.168.64.1` (Macens adress i UTM:s delade nätverk).
- Zotero, e-post och molnlagring fungerar som vanligt via nätverket.

Vid första start installeras grundverktygen automatiskt i bakgrunden (kräver
nätverk, tar en stund). Vid första inloggningen öppnas verktygslådan där du
väljer fler verktyg. Delat urklipp och automatisk skärmstorlek fungerar i
UTM:s QEMU-läge tack vare `spice-vdagent`.

> **Ej verifierat än:** att disken startar i UTM, inloggningen med
> lösenordsbyte och den delade mappen. Det är det första vi testar på din
> MacBook Neo.

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
