# ForskarOS Core

ForskarOS Core är ett Obsidian-tillägg för att formulera forskningsfrågor, pröva hypoteser och dokumentera beslut. Anteckningarna är vanliga Markdown-filer. Core kan användas på en befintlig dator utan att installera operativsystemet ForskarOS.

## I ForskarOS

Välj Obsidian under **Välj forskningsverktyg**. Öppna mappen `~/ForskarOS` som en vault i Obsidian och aktivera **ForskarOS Core** under **Settings → Community plugins**. Mappen skapas vid första inloggningen.

## På en annan dator

Installera Obsidian och klona repot. Kör följande från repots rot i ett Bash-skal:

```bash
bash scripts/install-vault.sh
```

Skriptet skapar `~/ForskarOS`. För en annan plats anger du sökvägen som argument:

```bash
bash scripts/install-vault.sh /sökväg/till/forskningsmapp
```

En befintlig mapp skrivs inte över. På en dator utan Bash kan du kopiera hela `vault/`, inklusive den dolda mappen `.obsidian`, till en ny mapp.

Öppna mappen som en vault i Obsidian. Aktivera **ForskarOS Core** under **Settings → Community plugins** och öppna panelen med hjärnikonen.

## Arbetsgång

1. Skapa en forskningsfråga eller utgå från det medföljande förslaget.
2. Arbeta genom faserna **Utforska, Kombinera, Välj, Pröva, Utveckla, Ompröva och Dela**. Panelen visar kraven inför nästa fas.
3. Spara hypoteser, källor, motprov och forskningsmöten med länkar till frågan.
4. Följ upp beslut och omprövningar i frågans logg.

Core förbereder AI-konsultationer som text att kopiera. Tillägget gör inga nätverksanrop. Du väljer själv vilken tjänst som får texten.

Core-anteckningarna och skrivbordsappens forskningsprojekt är separata mappar. Appens projekt ligger normalt i `~/Forskningsprojekt`; Core-vaulten ligger normalt i `~/ForskarOS`.

## Uppdatering och säkerhetskopiering

I ForskarOS uppdateras tilläggets filer, verktygskorten och Forskarhandboken vid inloggning. Lägg egna anteckningar utanför `00 START/Verktyg` och `00 START/Forskarhandboken`. Ett borttaget Core-tillägg återinstalleras inte automatiskt.

I en fristående installation uppdaterar du tillägget genom att kopiera `main.js`, `manifest.json` och `styles.css` från `vault/.obsidian/plugins/forskaros-core/` till motsvarande mapp i din vault. Säkerhetskopiera hela vaulten, inklusive `.obsidian`, före uppdateringen.

[Arbetsmetoden](../vault/00%20START/Arbetsmetod.md) · [Forskarhandboken](../vault/00%20START/Forskarhandboken/00%20Innehåll.md)
