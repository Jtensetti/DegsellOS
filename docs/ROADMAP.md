# Färdplan

ForskarOS utvecklas mot den första stabila kvartalsutgåvan, 2027.1. Publicerad förhandsversion och nedladdningar finns i [README](../README.md#ladda-ner). Levererade funktioner beskrivs i [ändringsloggen](../CHANGELOG.md).

## Inför stabil utgåva

| Område | Krav |
|---|---|
| Användbarhet | Forskare från tre forskningsprofiler genomför samma uppgift i ForskarOS och sin ordinarie miljö. Jämför tid, handgrepp, hjälpbehov och fel. |
| Arbetsmetod | Följ användningen under fyra veckor. Bedöm hur frågor, motprov, belägg, osäkerhet och slutsatser dokumenteras. Självskattningsmåtten behöver prövas mot arbetsproven. |
| Hårdvara | Genomför hela flödet med inloggning, delad mapp och labb i UTM på fysisk Apple Silicon-Mac samt installation på fysisk PC. |
| Utgivning | Publicera versionsbundna, signerade avbildningar och installationsmedier enligt [släpprocessen](RELEASE.md). |

Automatiska tester kan kontrollera funktioner och filformat. Minskad administration och metodens nytta behöver beläggas genom användarstudier.

## Vidare utveckling

Följande områden har ännu ingen fastställd utgåva.

- **Projektskydd:** krypterad lagring och säkerhetskopiering, signaturpolicy i klienten samt avgränsade behörigheter för fler skrivbordsprogram.
- **Gemensam projektkontext:** ett lokalt API när flera program behöver dela det öppna projektets miljö och datakällor.
- **Forskningspaket:** export av hela projekt, W3C PROV och dokumentation av körningar på externa kluster.
- **Källgranskning:** fler ämnesspecifika arbetsflöden och mätning av falsklarm vid ändrat underlag.
- **Lokal AI:** koppla Core:s konsultationslägen till lokala modeller med uttryckliga gränser för dataåtkomst och undersöka självhostad litteratursökning.
- **Editor och körmiljöer:** undersöka en öppen editor för Core och deklarativa analysmiljöer per studie med Nix eller Guix. Direkt uppstart på kompatibel Apple Silicon-hårdvara är ett separat utvecklingsspår.
