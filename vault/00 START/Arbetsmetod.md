# Arbetsmetod

## Faser

Varje forskningsfråga går igenom sju faser. Panelen visar kraven för att gå vidare. Kraven går att hoppa över, men motiveringen sparas under *Fasbeslut* i frågan.

| Fas | Krav för att gå vidare |
|---|---|
| 1. Utforska | Motivering på minst 30 ord; minst tre saker du undrar över; vem som bryr sig om svaret; en perspektivkarta med minst tre perspektiv, varav ett från ett oväntat fält, och var de motsäger varandra |
| 2. Kombinera | En hypotes som anger etablerad kunskap den bygger på, vad som är nytt, vilket antagande den utmanar och vem som företräder antagandet |
| 3. Välj | Falsifieringskriterium, prediktioner, angiven konfidens, vad som förändras om frågan besvaras, vad som väljs bort |
| 4. Pröva | Ett besvarat motprov, ett forskningsmöte där någon utanför projektet framfört en invändning, och ett möte med någon som företräder det antagande hypotesen utmanar |
| 5. Utveckla | Ett experiment eller arbetsprov med resultat, till exempel en körning i appen ForskarOS; någon mer arbetar med frågan (en medarbetare eller ett möte om samarbete) |
| 6. Ompröva | En omprövning och nedskrivna lärdomar |
| 7. Dela | En sammanfattning för någon utanför fältet (50–200 ord); resultatet har delats med någon som kan granska det; vilken ny fråga svaret öppnar; analysen i appen är upprepad med samma resultat |

Efter Dela börjar en ny cykel. En fråga avslutas med *Avsluta* och ett utfall: besvarad, hypotesen förkastad eller övergiven. En förkastad hypotes räknas som ett resultat. Frågan som svaret öppnar läggs i idébanken, så att arbetet fortsätter framåt.

## Regler

- **Högst två aktiva och fyra öppna frågor.** Vilande frågor räknas som öppna. Nya idéer sparas i idébanken (*Parkera en idé*).
- **Människor först.** AI-stödet är avstängt tills du väljer en nivå. Med AI påslaget kräver utvecklings- och prövningsläget minst 50 egna ord i anteckningen.
- **Varje hypotes ska ha ett motprov**, och minst en person utanför projektet ska ha sett idén.
- **Märk påståenden** som belagt (med källa), tolkning eller spekulation.
- **Rätta fel öppet** med en felrättning.
- **Vila.** En fråga kan läggas att vila i två veckor. Den återupptas från panelen med en mening om varför den fortfarande är viktig.

## AI-konsultationer

Forskningen görs i första hand av människor. AI-stödet är frivilligt och avstängt från början. Välj nivå under *Inställningar → ForskarOS Core*:

| Nivå | Vad AI får göra |
|---|---|
| **Av** (standard) | Inget. Panelen, granskningen och måtten nämner inte AI. |
| **Handledning** | Ställa frågor och leta fel i det du redan skrivit, efter minst 50 egna ord. Inga färdiga svar. |
| **Fullt** | Alla lägen, även hjälp att producera text och kod. |

*Be AI om hjälp* skapar en text som du kopierar till valfri AI. Inget skickas automatiskt. Konsultationen loggas i `08 REFLEKTION/AI`, där du klistrar in svaret och skriver vad du tar med dig.

| Uppgift | Används till |
|---|---|
| Alternativa perspektiv | Andra teorier och fält, forskningsluckor |
| Kritisk granskning | Invändningar och alternativa förklaringar |
| Handledning | Metod och teori du inte behärskar än |
| Metod och analys | Försöksdesign och analys |
| Uppföljning | Granskning av tidigare slutsatser |

**Lägen:** *utveckling* (frågor och ledtrådar, inte svar), *prövning* (leta fel) och *prestation* (hjälp att producera). Prestationsläget kräver inget eget utkast men räknas separat.

Med profilen *Lokal AI* körs modellerna på datorn. Molntjänster installeras bara som tillval.

## Granskning

Panelens lista *Att åtgärda* bygger på reglerna ovan:

- **Frågor:** fler än två aktiva eller fyra öppna; tre påbörjade på 90 dagar utan att någon avslutats; en fråga som vilat tre gånger; en fråga som stått still i över 30 dagar; vilande frågor som är redo att tas upp igen.
- **Kritik:** hypoteser utan motprov; fördjupning utan motprov.
- **Människor:** inget forskningsmöte på 30 dagar; möten med uppföljningar som inte gjorts; alla möten med samma person; alla möten med den närmaste kretsen; ingen återkoppling från någon med ämnes-, metod- eller annan fältkompetens under ett halvår; inga nya kontakter under ett halvår.
- **Projekt i appen:** påståenden vars underlag har ändrats och som behöver omprövas.
- **Arbete:** inga forskarpass, fokuspass eller experiment på 14 dagar; inga nya idéer eller perspektiv på 60 dagar; forskarpass där inget skrivits under *Det jag inte förstår*.
- **AI:** konsultationer utan eget utkast eller utan sammanfattning; sjunkande andel konsultationer med eget utkast jämfört med förra månaden.
- **Förmåga:** utebliven förmågegranskning; skattningar utan länkat arbetsprov; ingen övning för den lägst skattade förmågan på 30 dagar.
- **Felrättningar** som varit öppna i över två veckor.

## Mått

Panelen visar andelen AI-konsultationer med eget utkast, övningar utan AI, motprov, omprövningar, felrättningar, forskningsmöten och nya kontakter, fokuspass och avslutade frågor. Förmågegranskningen skattar sju förmågor 1–5 en gång i månaden. Måtten är självskattningar och inte validerade.

## Samspelet mellan programmen

Metoden bärs av flera program som lämnar över till varandra:

- **Obsidian med ForskarOS Core** håller tanken: frågan, hypoteserna, motproven, mötena och omprövningarna.
- **Appen ForskarOS** håller handlingen: data, analys, manus och rapport. Ett projekt kopplas till en fråga och den hypotes det prövar. Projektets läge skrivs till `04 EXPERIMENT` som ett experiment: senaste körning, hur säker den är och vilka påståenden som behöver omprövas. Panelen läser det och visar projekten under frågan. *Nytt projekt i appen* i panelen, eller kommandot *Pröva i ett nytt projekt* på en hypotes, öppnar appen med frågan vald. Appens startsida visar frågorna med sina projekt.
- **Kontakter, Kalender och Jitsi Meet** (programmenyn, *4 · Pröva*) är till för mötena som metoden kräver. **Element** och **Syncthing** (*5 · Utveckla*) är till för medarbetare som arbetar med underlaget.
- **Zotero** lämnar källor till projektets referenser, och appen kontrollerar citaten mot dem.

Varje fas har sina program i en egen mapp i programmenyn. [[00 START/Begreppen|Begreppen]] beskriver vad hela systemet bygger på.

## Bakgrund

Se [[00 START/Bakgrund]] för forskningen metoden bygger på.
