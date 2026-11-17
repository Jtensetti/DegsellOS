# Så släpps ForskarOS

ForskarOS släpps **kvartalsvis**: `2027.1` (mars), `2027.2` (juni), `2027.3` (september), `2027.4` (december).

| Fil | Innehåll |
|---|---|
| `VERSION` | `2027.1-dev` mellan släpp, `2027.1-beta1` för förhandsversioner, `2027.1` vid släpp |
| `CHANGELOG.md` | Vad som är nytt, skrivet för forskare, inte för utvecklare |

## Mellan släpp
Varje push till `main` bygger och publicerar `latest` och en datumtagg. Installerade system får uppdateringarna via bootc.

## Vid släpp
1. Sätt `VERSION` till t.ex. `2027.1` (eller `2027.1-beta1` för en otestad förhandsversion) och skriv avsnittet i `CHANGELOG.md`.
2. Pusha. CI publicerar då även taggen `2027.1` för OS:et och labbet.
3. Testa diskarna med *Bygg installationsmedia*: start i UTM på Mac, ISO i en virtuell PC, inloggning, verktygslåda, labbet.
4. Först när testerna är gjorda: kör *Släpp färdig VM* med versionen. Den laddar upp till Internet Archive.
En release kan också startas genom en push till `main` där commitmeddelandet börjar med `[release-media] `. Då publiceras alla tre medier från det signerade manifestets digest efter godkänt bygge.

5. Sätt `VERSION` till nästa `-dev`.

> Labbet får en ny version bara när `labb/` ändras. Gamla versioner tas inte bort,
> så att analyser kan köras om i exakt samma miljö.
