# Färdplan

Den senaste publicerade förhandsversionen är **2027.1-beta4**. `main` innehåller utvecklingen mot nästa utgåva. Tidigare leveranser beskrivs i [ändringsloggen](../CHANGELOG.md). [Forskningsdomänens mål och acceptanskriterier](FORSKAROS-3.md)

## Inför 2027.1

- [x] Publicera en signerad systemavbildning för amd64 och arm64 samt installationsmedier för beta4. [Versioner och nedladdningar](../README.md#ladda-ner)
- [x] Starta båda VM-diskarna och genomföra ett forskningsprojekt på ett nyinstallerat beta4-system i en virtuell PC. [Installationsprov](BETA4.md)
- [ ] Slutföra en installation med den publicerade `-interaktiv-r2.iso` på två anslutna virtuella diskar. Verifiera vald startdisk och oförändrat innehåll på den andra disken efter omstart.
- [ ] Upprepa en tidigare skyddad forskningskörning efter systemuppgradering.
- [ ] Prova arm64-disken i UTM på MacBook Neo, från lösenordsbyte till delad mapp och analys i labbet. [Mac-guide](MAC.md)
- [ ] Paketera en dubbelklickbar UTM-maskin med en mall från UTM. [Mall och paketering](../vm/utm/README.md)
- [ ] Låta forskare med tre olika forskningsprofiler lösa samma uppgift i ForskarOS och sin vanliga miljö. Mät handgrepp, tid, hjälpbehov och fel.
- [ ] Prova arbetsmetoden under fyra veckor. Granska om måtten speglar självständigt arbete och om forskaren kan visa fråga, hypotes, motprov, belägg, osäkerhet och slutsats.
- [ ] Släppa kvartalsversionen 2027.1. [Släpprocess](RELEASE.md)

## Forskningsprojekt på main

- [x] Koppla manusets påståenden till data, källpassager och analys. Visa berörda påståenden när ett underlag ändras.
- [x] Köra skyddade analyser och rapportbyggen i sandlåda och spara körningen i RO-Crate-format.
- [x] Hantera en kvalitativ studie och en observationstabell från projektstart till en rapport som kan köras om.
- [x] Visa senaste verifieringens utfall när en upprepning avviker.
- [x] Jämföra gammalt och nytt belägg i granskningsvyn.
- [x] Läsa användarvalda passager från Zoteros lokala API med källa, sida och citat.
- [x] Erbjuda en projektmall för källtolkning med motstridiga källor.
- [x] Sätta ForskarOS som visningsnamn i systemavbildningens metadata.
- [ ] Bekräfta namnet i nästa utgåvas startmeny och välkomstguide.

## Fortsatt utveckling

Följande förslag har ännu ingen planerad utgåva.

- **Dataskydd.** Automatisk krypterad säkerhetskopiering och klientpolicy för verifiering av systemavbildningens signatur.
- **Lokal AI.** Koppla Core:s konsultationslägen till Ollama och utvärdera självhostad sökning.
- **Öppen editor.** Redigera Markdown med frontmatter, wikilänkar och bakåtlänkar, och utreda stöd för Core i en egen Flatpak-app.
- **Körmiljöer.** Utvärdera Nix eller Guix per studie och en avbildning för direkt uppstart på Apple Silicon när den aktuella hårdvaran stöds.
