# Forskningsprojektets krav

Ett forskningsprojekt har en arbetsmapp och en separat mapp för varje sparad körning. Projektets skyddsnivå styr var analysen körs. Manusets länkar till underlaget följer med när en körning lämnas till en kollega. [Filformat och arbetsgång](PROJEKT.md)

| Krav | Vad forskaren ska kunna göra |
|---|---|
| Isolering | Köra analys och rapportbygge med avstängt nätverk och dold hemkatalog. Körningen ska avbrytas om isoleringen misslyckas. |
| Reproducerbarhet | Flytta en körning till en annan installation, återskapa resultaten och se vilka filer som eventuellt avviker. |
| Spårbarhet | Gå från ett påstående i manuset till den valda tabellraden, källpassagen eller analysfilen. |
| Omprövning | Se vilka påståenden som påverkas när ett registrerat underlag ändras. Oberoende granskningsbeslut ska behållas. |
| Användbarhet | Genomföra en forskningsuppgift med mindre administrativt arbete än i den vanliga arbetsmiljön. Jämförelsen omfattar tid, handgrepp, fel och hjälpbehov. |

## Hotmodell för skyddade projekt

Det lokala analys- och rapportbygget i ett skyddat projekt använder en egen nätverksnamnrymd. Hemkataloger, `/run`, temporära kataloger och monteringsplatserna `/mnt`, `/media` och `/srv` döljs. Övriga systemfiler är skrivskyddade. Processen kan skriva i körningsmappen och får en separat uppsättning miljövariabler.

Skyddet gäller de processer som ForskarOS startar för körningen. Andra skrivbordsprogram, urklipp och användare med administratörsbehörighet har sina vanliga åtkomsträttigheter. En exporterad körning innehåller en kopia av sina underlag. [Säkerhet och integritet](SECURITY.md)
