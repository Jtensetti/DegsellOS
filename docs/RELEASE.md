# Så släpps DegsellOS

Kvartalsversioner följer formen `2027.1` (mars), `2027.2` (juni), `2027.3` (september) och `2027.4` (december). En beta har ett suffix som `-beta4`. Mellan släpp innehåller [VERSION](../VERSION) ett utvecklingsnummer som `2027.1-dev`.

## Systemavbildning och installationsmedier

Utvecklingsbyggen för amd64 och arm64 publiceras på GHCR som `latest` och med en datumtagg. Versionsmärkta utgåvor har en separat släpprocess. [Byggflöde](../.github/workflows/build.yml)

1. Välj ett nytt versionsnummer, skriv det i `VERSION` och beskriv ändringarna i [ändringsloggen](../CHANGELOG.md).
2. Publicera en commit på `main` med prefixet `[release-media] ` i commitmeddelandet. CI testar koden, bygger för båda arkitekturerna, publicerar det versionsmärkta manifestet och signerar det med cosign.
3. Släppjobbet använder manifestets digest till amd64-ISO:n och båda VM-diskarna. Det startprovar diskarna, kontrollerar installerarens konfiguration och paketerar även arm64-disken som en UTM-maskin. Varje nedladdning får en egen SHA-256-summa på Internet Archive. [Släpp färdig VM](../.github/workflows/release-vm.yml)
4. Hämta de publicerade medierna, jämför kontrollsummorna med byggkvittot och prova den dokumenterade installationsvägen. Uppdatera nedladdningarna och guiderna för respektive plattform. Återgå sedan till ett utvecklingsnummer i `VERSION`.

## Enbart installeraren

Om samma systemavbildning ska paketeras i en rättad ISO, använd en commit med prefixet `[release-iso] ` på `main`. `VERSION` ska då identifiera den tidigare publicerade utgåvan. Ge en ersättande revision ett eget filnamn så att den kan skiljas från äldre nedladdningar. För beta4 heter den aktuella ISO:n `ForskarOS-2027.1-beta4-amd64-interaktiv-r2.iso`.

## Övriga byggen

- [Bygg installationsmedia](../.github/workflows/build-disk.yml) gör ISO, qcow2 och ett UTM-paket från en angiven tagg och sparar dem som GitHub Actions-artefakter för prov.
- [Återuppta en uppladdning](../.github/workflows/archive-retry.yml) kan inspektera en fördröjd arkivpost och begära omkörning av dess katalogjobb.
- [Bygg DegsellOS-labbet](../.github/workflows/labb.yml) har ett eget flöde för ändringar av labbet och dess bygginstruktioner. För en upprepningsbar analys sparas labbets digest.
