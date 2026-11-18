# ForskarOS 3.0: målarkitektur och status

Målarkitekturen kommer från en arkitekturgranskning med tio simulerade expertperspektiv (18 november 2026). Kärnan: **forskningsprojektet blir systemets centrala resurs**, en forskningsdomän med egna data, behörigheter, körmiljö, proveniens och evidenskedja. Granskningen satte fem acceptanstester. Det här dokumentet visar var ForskarOS står mot dem.

Status gäller [2027.1-beta4 och installationsprovet](BETA4.md). "Automatiserat" betyder att testet körs i CI vid varje push (`tests/doman.test.py`).

## Acceptanstesten

| Test | Krav | Status |
|---|---|---|
| **1. Projektisolering** | Ett skyddat projekts data är otillgängliga för obehöriga processer inom den definierade hotmodellen | **Automatiserat för analysen och rapportbygget.** Ett analysskript som försöker nå nätet, läsa en fil utanför körningen, läsa hemkatalogen eller läsa sessionens miljövariabler stoppas. Kan sandlådan inte startas vägrar ForskarOS köra. Se hotmodellen nedan. |
| **2. Reproducerbarhet** | Ett dokumenterat testexperiment kan återköras på en annan installation med redovisat resultat | **Automatiserat.** Täckningsgrad (dokumenterad, återkörbar, återkörd) och logg över varje upprepning, även avvikande. Flytt mellan installationer provades manuellt i beta3 (amd64-VM till Debian). |
| **3. Evidenskedja** | En forskare kan följa ett påstående bakåt till det specificerade underlaget | **Automatiserat** för datarader, hela filer och, från beta4, källpassager (BibTeX-nyckel, sida, citat, valfri källtext). |
| **4. Omprövning** | En ändring i ett känt beroende identifierar berörda påståenden utan orimligt många falsklarm | **Automatiserat.** Ändrat urval, metodfil, lydelse eller källa ger *Ompröva* för just de påståenden som bygger på det. Testerna kontrollerar också att andra påståenden inte flaggas och att en ny Zotero-export inte ger falsklarm. Andelen falsklarm i verkligt bruk är inte mätt. |
| **5. Användbarhet** | Forskare gör relevanta uppgifter med mindre administrativ friktion än i en jämförbar miljö | **Inte gjort.** Kräver användartester med riktiga forskare. |

## De sex systemfunktionerna

| Funktion | I ForskarOS | Saknas |
|---|---|---|
| **Research Domain** | Projektmapp med `projekt.json` (identitet, titel, skyddsnivå, licens). Skyddsnivån styr hur analysen körs. | Datakällor, projektspecifika program och behörigheter som systemet aktiverar när projektet öppnas |
| **Research Ledger** | `korning.json` (SHA-256, miljö, isolering, tider) och `verifieringar.json` | Körningar på externa kluster med körningskvitto och täckningsgrad för ofullständig proveniens |
| **Evidence Engine** | `belagg.json`, granskningsbeslut, omprövning, källpassager | Ämnesspecifika granskningsmodeller, t.ex. motstridiga tolkningar av historiska källor |
| **Research Guard** | bubblewrap utan nätverk och hemkatalog för analysen; Podman utan nätverk i labbet | Isolering av skrivbordsprogram, AI-policy som upprätthålls på systemnivå, krypterad lagring per projekt, penetrationstest |
| **Research Capsule** | Körningsmappen som RO-Crate 1.1 / Process Run Crate 0.5, godkänd av `rocrate-validator` | Export av ett helt projekt, W3C PROV-export |
| **Research Companion** | AI-konsultationer i ForskarOS Core: lägen, eget utkast först, logg | Lokala modeller anslutna direkt, gränser för vilka data AI får läsa |

## Hotmodell för skyddade projekt

Skyddet gäller processer som ForskarOS själv startar för analys och rapport. I sandlådan:

- finns inget nätverk (egen nätverksnamnrymd)
- är `/home`, `/var/home`, `/root`, `/run`, `/tmp`, `/var/tmp`, `/mnt`, `/media` och `/srv` dolda; `/run` döljs eftersom en skrivskyddad montering inte hindrar anslutning till systemets och sessionens uttag
- är resten av systemet skrivskyddat och bara körningsmappen skrivbar
- följer inga miljövariabler med från sessionen

Skyddet omfattar **inte** program som forskaren själv öppnar, urklipp, AI-tjänster i webbläsaren, eller en användare med administratörsbehörighet. Det har inte penetrationstestats. ForskarOS påstår därför inte att skyddat material inte kan lämna datorn, bara att analysen och rapportbygget inte kan skicka det.

## Avvikelser från målarkitekturen

- **Bluefin LTS i stället för NixOS.** Granskningen föreslog NixOS för deklarativ konfiguration. ForskarOS bygger på Bluefin LTS (bootc) eftersom den finns för både amd64 och arm64, uppdateras atomärt och kan backas. Avbildningen beskrivs deklarativt i `Containerfile`.
- **Ingen `researchd` än.** Domänen hanteras av `forskaros-projekt` och dess filer. En systemtjänst med lokalt API behövs först när flera program ska dela projektkontext samtidigt.

## Nästa steg (P1–P4 i granskningen)

1. Testa upprepning av en skyddad beta4-körning efter nästa systemuppgradering. På den nyinstallerade beta4-datorn gick den skyddade körningen att upprepa med SELinux i enforcing-läge.
2. Zotero: läs annoteringar direkt via Zoteros lokala API i stället för kopiera och klistra in.
3. Ett tolkande, humanistiskt arbetsflöde med motstridiga källor (granskningens scenario D).
4. Användartester med tre forskarprofiler (test 5).
