# Versioner

ForskarOS släpps kvartalsvis med versioner som `2027.1`, `2027.2` …
Mellan släppen bygger standardgrenen `ÅÅÅÅ.N-dev`. Se `docs/RELEASE.md`.

## 2027.1 (under arbete)

Första officiella släppet.

**Metoden i systemet**
- Den kreativa forskningscykeln i sju faser med faskrav och öppen fasbeslutslogg
- Revisorn granskar vaulten mot metoden
- Tänk först, AI-roller och AI-lägen, loggade konsultationer
- Självständighetsmått, förmågegranskning, epistemisk märkning, idéparkering, vila

**Menyn är metoden**
- Programmenyn har en mapp per fas, från *1 · Utforska* till *7 · Dela*
- Verktygskatalog med verktygskort, nio profiler inklusive *Topp 10 för forskare*
- Forskningsportal med öppna och svenska resurser per fas

**Arbetsplatsen**
- Bluefin LTS som grund (amd64 och arm64), atomära uppdateringar
- Grundverktygen installeras vid första start, verktygslådan öppnas vid första inloggningen
- VM: kontot `forskare`/`forskare` med krav på lösenordsbyte, delad mapp, gästagenter för UTM/QEMU, UTM-paketering
- Identitet: logotyp, bakgrund, dagens princip i terminalen, fokusläge

**Reproducerbarhet**
- ForskarOS-labbet: låst analysmiljö med R, tidyverse, RStudio Server och Python

**Forskarhandboken**
- Tolv kapitel med övningar utan AI
